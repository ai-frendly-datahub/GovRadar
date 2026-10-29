from __future__ import annotations

from datetime import UTC, datetime

from govradar.models import Article, CategoryConfig, Source
from govradar.quality_report import build_quality_report
from govradar.run_collection import build_run_collection
from govradar.storage import RadarStorage


def _source(name: str, *, enabled: bool = True) -> Source:
    return Source(
        name=name,
        type="rss",
        url=f"https://example.com/{name}",
        enabled=enabled,
        config={"event_model": "application_deadline"},
    )


def test_run_collection_separates_this_run_from_old_window(tmp_path) -> None:
    seoul = _source("서울시 지원사업")
    policy = _source("서울시 정책뉴스")
    disabled = _source("정부24 보조금", enabled=False)
    fetched = Article(
        title="청년 모집",
        link="https://news.seoul.go.kr/gov/archives/581618",
        summary="참여자 모집",
        published=datetime(2026, 10, 26, tzinfo=UTC),
        source=policy.name,
        category="govsupport",
    )
    errors = ["서울시 지원사업: request failed: SSLError: unexpected eof"]
    storage = RadarStorage(tmp_path / "gov.duckdb")
    try:
        storage.upsert_articles(
            [
                Article(
                    title="지난 공고",
                    link="https://www.seoul.go.kr/news/old",
                    summary="이전 수집",
                    published=datetime(2026, 10, 22, tzinfo=UTC),
                    source=seoul.name,
                    category="govsupport",
                )
            ]
        )
        last_success = storage.last_collected_at_by_source("govsupport")
    finally:
        storage.close()

    run = build_run_collection(
        [seoul, policy, disabled],
        [fetched],
        errors,
        last_success_at=last_success,
    )
    counts = run["collected_counts"]
    assert isinstance(counts, dict)
    assert counts == {"서울시 지원사업": 0, "서울시 정책뉴스": 1}
    assert "정부24 보조금" not in counts
    failed = run["failed_sources"]
    assert isinstance(failed, list)
    assert failed == [
        {
            "source": "서울시 지원사업",
            "errors": ["서울시 지원사업: request failed: SSLError: unexpected eof"],
        }
    ]
    last = run["last_success_at"]
    assert isinstance(last, dict)
    assert isinstance(last["서울시 지원사업"], str)
    assert last["서울시 정책뉴스"] is None
    assert "Authorization" not in errors[0]

    report = build_quality_report(
        category=CategoryConfig(
            category_name="govsupport",
            display_name="Gov Support",
            sources=[seoul, policy],
            entities=[],
        ),
        articles=[],
        errors=errors,
        run_collection=run,
    )
    assert report["summary"]["run_collected_total"] == 1
    assert report["summary"]["run_failed_source_count"] == 1
    assert report["run"]["collected_counts"]["서울시 지원사업"] == 0
    assert report["sources"][0]["article_count"] == 0
