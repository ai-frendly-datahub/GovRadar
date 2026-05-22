from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from govradar import browser_collector
from govradar.models import Article, Source

pytestmark = pytest.mark.unit


def _source() -> Source:
    return Source(
        name="서울시 지원사업",
        type="javascript",
        url="https://example.com/notices",
        config={"wait_for": "table"},
    )


def test_collect_browser_sources_returns_empty_for_no_sources() -> None:
    assert browser_collector.collect_browser_sources([], "govsupport") == ([], [])


def test_collect_browser_sources_reports_unavailable_dependency(monkeypatch) -> None:
    monkeypatch.setattr(browser_collector, "_BROWSER_COLLECTION_AVAILABLE", False)
    monkeypatch.setattr(browser_collector, "_core_collect", None)

    articles, errors = browser_collector.collect_browser_sources([_source()], "govsupport")

    assert articles == []
    assert "Browser collection unavailable" in errors[0]


def test_collect_browser_sources_converts_core_articles(monkeypatch) -> None:
    published = datetime(2026, 5, 21, 9, 0, tzinfo=UTC)
    core_article = Article(
        title="지원사업 공고",
        link="https://example.com/a",
        summary="서울 소상공인 지원",
        published=published,
        source="서울시 지원사업",
        category="",
    )
    core_collect = Mock(return_value=([core_article], ["minor warning"]))
    monkeypatch.setattr(browser_collector, "_BROWSER_COLLECTION_AVAILABLE", True)
    monkeypatch.setattr(browser_collector, "_core_collect", core_collect)

    articles, errors = browser_collector.collect_browser_sources(
        [_source()],
        "govsupport",
        timeout=1234,
        health_db_path="health.duckdb",
    )

    assert errors == ["minor warning"]
    assert len(articles) == 1
    assert articles[0].category == "govsupport"
    assert articles[0].title == "지원사업 공고"
    core_collect.assert_called_once_with(
        sources=[
            {
                "name": "서울시 지원사업",
                "type": "javascript",
                "url": "https://example.com/notices",
                "config": {"wait_for": "table"},
            }
        ],
        category="govsupport",
        timeout=1234,
        health_db_path="health.duckdb",
    )


def test_collect_browser_sources_handles_import_error(monkeypatch) -> None:
    def raise_import_error(**kwargs: object) -> tuple[list[SimpleNamespace], list[str]]:
        raise ImportError("playwright")

    monkeypatch.setattr(browser_collector, "_BROWSER_COLLECTION_AVAILABLE", True)
    monkeypatch.setattr(browser_collector, "_core_collect", raise_import_error)

    articles, errors = browser_collector.collect_browser_sources([_source()], "govsupport")

    assert articles == []
    assert "Playwright not installed" in errors[0]


def test_collect_browser_sources_handles_runtime_failure(monkeypatch) -> None:
    def raise_runtime_error(**kwargs: object) -> tuple[list[SimpleNamespace], list[str]]:
        raise RuntimeError("blocked")

    monkeypatch.setattr(browser_collector, "_BROWSER_COLLECTION_AVAILABLE", True)
    monkeypatch.setattr(browser_collector, "_core_collect", raise_runtime_error)

    articles, errors = browser_collector.collect_browser_sources([_source()], "govsupport")

    assert articles == []
    assert errors == ["Browser collection failed: blocked"]
