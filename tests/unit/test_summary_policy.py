from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import main as pipeline
from govradar.models import Article, Source
from govradar.storage import RadarStorage
from govradar.summary_policy import redact_summaries, summary_free_source_names

NEWS_SOURCE = "뉴스 A"
OTHER_SOURCE = "공공 B"
SUMMARY_TEXT = "소상공인 보조금 신청 안내 본문 전체가 여기에 들어 있다."


def _source(name: str = NEWS_SOURCE, **config: object) -> Source:
    return Source(name=name, type="rss", url="https://example.com/feed", config=dict(config))


def _article(
    source: str = NEWS_SOURCE,
    summary: str = SUMMARY_TEXT,
    link: str = "https://example.com/a1",
    title: str = "정책 소식",
) -> Article:
    return Article(
        title=title,
        link=link,
        summary=summary,
        published=datetime.now(UTC) - timedelta(hours=1),
        source=source,
        category="govsupport",
        matched_entities={"SupportType": ["보조금"]},
    )


@pytest.mark.unit
def test_only_boolean_false_on_enabled_sources_counts() -> None:
    disabled = _source("꺼진 소스", store_summary=False)
    disabled.enabled = False
    sources = [
        _source("끔", store_summary=False),
        _source("문자열", store_summary="false"),
        _source("켬", store_summary=True),
        _source("설정 없음"),
        disabled,
    ]
    assert summary_free_source_names(sources) == frozenset({"끔"})


@pytest.mark.unit
def test_redact_summaries_returns_copies_and_keeps_originals() -> None:
    news = _article()
    other = _article(source=OTHER_SOURCE, link="https://example.com/b1")
    sources = [_source(NEWS_SOURCE, store_summary=False), _source(OTHER_SOURCE)]

    result = redact_summaries([news, other], sources)

    assert result[0].summary == ""
    assert result[0].title == news.title and result[0].link == news.link
    assert result[0].source == NEWS_SOURCE
    assert result[0].matched_entities == news.matched_entities
    assert news.summary == SUMMARY_TEXT  # 필터에 쓰는 메모리 원본은 그대로
    assert result[1] is other and result[1].summary == SUMMARY_TEXT


@pytest.mark.unit
def test_clear_summaries_for_sources_only_touches_named_sources(tmp_duckdb: Path) -> None:
    storage = RadarStorage(tmp_duckdb)
    try:
        storage.upsert_articles(
            [
                _article(),
                _article(source=OTHER_SOURCE, link="https://example.com/b1"),
            ]
        )
        assert storage.clear_summaries_for_sources("govsupport", []) == 0
        assert storage.clear_summaries_for_sources("govsupport", [NEWS_SOURCE]) == 1
        assert storage.clear_summaries_for_sources("govsupport", [NEWS_SOURCE]) == 0
        rows = {a.source: a for a in storage.recent_articles("govsupport", days=30)}
    finally:
        storage.close()

    assert rows[NEWS_SOURCE].summary == ""
    assert rows[NEWS_SOURCE].title == "정책 소식"
    assert rows[OTHER_SOURCE].summary == SUMMARY_TEXT


@pytest.mark.unit
def test_report_selection_keeps_summary_free_articles_that_need_summary_text(
    tmp_duckdb: Path,
) -> None:
    # 제목만으로는 관련성 판정이 안 되는 항목이다. 저장된 summary가 비어도 보고서에서 빠지면 안 된다.
    sources = [_source(NEWS_SOURCE, store_summary=False), _source(OTHER_SOURCE)]
    storage = RadarStorage(tmp_duckdb)
    try:
        storage.upsert_articles(
            [
                _article(summary=""),
                _article(
                    source=OTHER_SOURCE,
                    summary="",
                    link="https://example.com/b1",
                ),
            ]
        )
        selected = pipeline._select_report_articles(
            storage, "govsupport", recent_days=7, sources=sources
        )
    finally:
        storage.close()

    assert [a.source for a in selected] == [NEWS_SOURCE]


def _write_config(tmp_path: Path) -> tuple[Path, Path]:
    categories = tmp_path / "categories"
    categories.mkdir()
    (categories / "govsupport.yaml").write_text(
        "\n".join(
            [
                "category_name: govsupport",
                "display_name: 테스트",
                "sources:",
                f"- name: {NEWS_SOURCE}",
                "  type: rss",
                "  url: https://example.com/a.xml",
                "  language: ko",
                "  country: KR",
                "  trust_tier: T2_expert",
                "  collection_tier: C1_rss",
                "  config:",
                "    store_summary: false",
                f"- name: {OTHER_SOURCE}",
                "  type: rss",
                "  url: https://example.com/b.xml",
                "  language: ko",
                "  country: KR",
                "  trust_tier: T2_expert",
                "  collection_tier: C1_rss",
                "entities:",
                "- name: SupportType",
                "  display_name: 지원유형",
                "  keywords: [보조금]",
                "- name: TargetGroup",
                "  display_name: 대상",
                "  keywords: [소상공인]",
                "- name: ApplicationInfo",
                "  display_name: 신청",
                "  keywords: [신청]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                f'database_path: "{tmp_path / "db.duckdb"}"',
                f'report_dir: "{tmp_path / "reports"}"',
                f'raw_data_dir: "{tmp_path / "raw"}"',
                f'search_db_path: "{tmp_path / "search.db"}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config, categories


@pytest.mark.unit
def test_pipeline_never_persists_summary_for_flagged_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, categories = _write_config(tmp_path)
    collected = [
        _article(source=NEWS_SOURCE, link="https://example.com/a1"),
        _article(source=OTHER_SOURCE, link="https://example.com/b1"),
    ]
    for article in collected:
        article.matched_entities = {}

    def fake_collect(sources: list[Source], **_: object) -> tuple[list[Article], list[str]]:
        return list(collected), []

    monkeypatch.setattr(pipeline, "collect_sources", fake_collect)
    monkeypatch.setattr(pipeline, "collect_official_sources", lambda *a, **k: ([], []))
    monkeypatch.setattr(pipeline, "partition_robots_disallowed", lambda sources, **_: (sources, []))

    # 이전 실행이 이미 저장해 둔 summary는 이번 실행에서 비워져야 한다.
    storage = RadarStorage(tmp_path / "db.duckdb")
    try:
        storage.upsert_articles([_article(source=NEWS_SOURCE, link="https://example.com/old")])
    finally:
        storage.close()

    report_path = pipeline.run(
        category="govsupport",
        config_path=config,
        categories_dir=categories,
    )

    # DuckDB: 새 항목과 이전 항목 모두 summary가 비어 있고, 다른 소스는 그대로다.
    storage = RadarStorage(tmp_path / "db.duckdb")
    try:
        stored = {a.link: a for a in storage.recent_articles("govsupport", days=30)}
    finally:
        storage.close()
    assert stored["https://example.com/a1"].summary == ""
    assert stored["https://example.com/old"].summary == ""
    assert stored["https://example.com/a1"].title == "정책 소식"
    assert stored["https://example.com/b1"].summary == SUMMARY_TEXT

    # raw JSONL: 플래그 소스는 summary 필드가 비어 있다.
    raw_lines = {
        path.stem: [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        for path in (tmp_path / "raw").glob("*/*.jsonl")
    }
    assert [row["summary"] for row in raw_lines[NEWS_SOURCE]] == [""]
    assert [row["summary"] for row in raw_lines[OTHER_SOURCE]] == [SUMMARY_TEXT]

    # 보고서: 플래그 소스는 제목·링크·출처명만 나오고 본문 문장은 없다.
    html = report_path.read_text(encoding="utf-8")
    assert "https://example.com/a1" in html and NEWS_SOURCE in html
    assert "신청 안내 본문 전체" in html  # 다른 소스의 summary는 그대로
    assert html.count(SUMMARY_TEXT) == 1

    # 검색 색인: 플래그 소스의 본문이 들어가지 않는다.
    with sqlite3.connect(tmp_path / "search.db") as conn:
        bodies = {
            str(link): str(body) for link, body in conn.execute("SELECT link, body FROM documents")
        }
    assert bodies["https://example.com/a1"] == ""
    assert bodies["https://example.com/b1"] == SUMMARY_TEXT
