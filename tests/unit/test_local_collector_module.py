from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from govradar.models import Article, Source

pytestmark = pytest.mark.unit


def _load_local_collector():
    path = Path(__file__).resolve().parents[2] / "govradar" / "collector.py"
    spec = importlib.util.spec_from_file_location("govradar._collector_local_under_test", path)
    if spec is None or spec.loader is None:
        raise AssertionError("collector spec not available")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_collector_resolves_worker_bounds() -> None:
    collector = _load_local_collector()

    assert collector._resolve_max_workers(None) == 5
    assert collector._resolve_max_workers(999) == 10
    assert collector._resolve_max_workers(-3) == 1
    assert collector._resolve_max_workers(1) == 1


def test_local_parse_rss_feed_builds_articles(monkeypatch) -> None:
    collector = _load_local_collector()
    response = SimpleNamespace(content="""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Mock</title>
<item>
  <title>지원사업 공고</title>
  <link>https://example.com/a</link>
  <description>서울 소상공인 지원</description>
  <pubDate>Wed, 20 May 2026 10:00:00 GMT</pubDate>
</item>
</channel></rss>
""".encode())
    monkeypatch.setattr(collector, "_fetch_url_with_retry", Mock(return_value=response))

    articles = collector._parse_rss_feed("https://example.com/feed.xml", timeout=3)

    assert len(articles) == 1
    assert articles[0].title == "지원사업 공고"
    assert articles[0].source == "example.com"
    assert articles[0].published == datetime(2026, 5, 20, 10, 0, tzinfo=UTC).replace(tzinfo=None)


def test_local_collect_sources_handles_rss_and_unsupported(monkeypatch) -> None:
    collector = _load_local_collector()
    article = Article(
        title="정책자금",
        link="https://example.com/a",
        summary="소상공인 정책자금",
        published=datetime(2026, 5, 20, tzinfo=UTC),
        source="before",
        category="before",
    )
    monkeypatch.setattr(collector, "_parse_rss_feed", Mock(return_value=[article]))

    articles, errors = collector.collect_sources(
        [
            Source(name="RSS", type="rss", url="https://example.com/feed.xml"),
            Source(name="Disabled", type="rss", url="https://example.com/disabled", enabled=False),
            Source(name="Unknown", type="mcp", url="https://example.com/mcp"),
        ],
        category="govsupport",
        max_workers=1,
    )

    assert [(item.source, item.category) for item in articles] == [("RSS", "govsupport")]
    assert errors == [
        "Unknown: Source type 'mcp' is cataloged but not collected by the standard pipeline"
    ]


def test_local_collect_sources_isolates_rss_errors(monkeypatch) -> None:
    collector = _load_local_collector()
    monkeypatch.setattr(collector, "_parse_rss_feed", Mock(side_effect=RuntimeError("boom")))

    articles, errors = collector.collect_sources(
        [Source(name="Broken RSS", type="rss", url="https://example.com/feed.xml")],
        category="govsupport",
        max_workers=1,
    )

    assert articles == []
    assert errors == ["Broken RSS: boom"]


def test_local_collect_sources_delegates_browser_and_reddit(monkeypatch) -> None:
    collector = _load_local_collector()
    js_article = Article(
        title="서울 지원",
        link="https://example.com/js",
        summary="서울 지원사업",
        published=None,
        source="서울시",
        category="govsupport",
    )
    reddit_article = Article(
        title="grant",
        link="https://reddit.com/r/test",
        summary="grant discussion",
        published=None,
        source="r/test",
        category="govsupport",
    )
    browser_collect = Mock(return_value=([js_article], ["js warning"]))
    reddit_collect = Mock(return_value=([reddit_article], ["reddit warning"]))

    import radar_core

    import govradar.browser_collector

    monkeypatch.setattr(govradar.browser_collector, "collect_browser_sources", browser_collect)
    monkeypatch.setattr(radar_core, "collect_reddit_sources", reddit_collect)

    articles, errors = collector.collect_sources(
        [
            Source(name="서울시", type="javascript", url="https://example.com/js"),
            Source(name="r/test", type="reddit", url="https://reddit.com/r/test"),
        ],
        category="govsupport",
        limit_per_source=2,
        timeout=5,
    )

    assert [article.link for article in articles] == [
        "https://example.com/js",
        "https://reddit.com/r/test",
    ]
    assert errors == ["js warning", "reddit warning"]
    browser_collect.assert_called_once()
    reddit_collect.assert_called_once()
