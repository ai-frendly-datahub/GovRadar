from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from govradar.models import Article, CategoryConfig, Source
from govradar.quality_report import build_quality_report, write_quality_report


def _source(name: str, event_model: str, sla_days: int | None = None) -> Source:
    config: dict[str, object] = {"event_model": event_model}
    if sla_days is not None:
        config["freshness_sla_days"] = sla_days
    return Source(name=name, type="rss", url=f"https://example.com/{name}", config=config)


def test_build_quality_report_tracks_deadline_and_eligibility_statuses() -> None:
    now = datetime(2026, 4, 12, tzinfo=UTC)
    category = CategoryConfig(
        category_name="govsupport",
        display_name="Gov Support",
        sources=[
            _source("Deadline Source", "application_deadline", 1),
            _source("Eligibility Source", "eligibility_rule", 2),
            _source("No Extracted Event", "eligibility_rule", 2),
            _source("Missing Source", "application_deadline", 1),
            _source("News Source", "support_program_notice", 2),
        ],
        entities=[],
    )
    articles = [
        Article(
            title="Deadline support notice",
            link="https://example.com/deadline",
            summary="Apply by 2026-04-30",
            published=now - timedelta(days=1),
            collected_at=now,
            source="Deadline Source",
            category="govsupport",
            matched_entities={
                "OperationalEvent": ["application_deadline"],
                "ApplicationDeadline": ["2026-04-30"],
            },
        ),
        Article(
            title="Eligibility support notice",
            link="https://example.com/eligibility",
            summary="서울 소상공인 대상",
            published=now - timedelta(days=5),
            collected_at=now,
            source="Eligibility Source",
            category="govsupport",
            matched_entities={
                "OperationalEvent": ["eligibility_rule"],
                "EligibilityRegion": ["서울"],
                "EligibilityTargetGroup": ["소상공인"],
            },
        ),
        Article(
            title="Unparsed eligibility notice",
            link="https://example.com/missing-event",
            summary="공고는 있으나 운영 이벤트가 없음",
            published=now,
            collected_at=now,
            source="No Extracted Event",
            category="govsupport",
            matched_entities={},
        ),
        Article(
            title="General policy notice",
            link="https://example.com/news",
            summary="지원사업 정책 안내",
            published=now,
            collected_at=now,
            source="News Source",
            category="govsupport",
            matched_entities={},
        ),
    ]

    report = build_quality_report(
        category=category,
        articles=articles,
        errors=["Deadline Source: timeout after retry"],
        quality_config={
            "data_quality": {
                "quality_outputs": {
                    "tracked_event_models": [
                        "support_program_notice",
                        "application_deadline",
                        "eligibility_rule",
                    ]
                }
            }
        },
        generated_at=now,
    )

    assert report["summary"]["fresh_sources"] == 2
    assert report["summary"]["stale_sources"] == 1
    assert report["summary"]["missing_event_sources"] == 1
    assert report["summary"]["missing_sources"] == 1
    assert report["summary"]["not_tracked_sources"] == 0
    assert report["summary"]["support_program_notice_events"] == 1
    assert report["summary"]["application_deadline_events"] == 1
    assert report["summary"]["eligibility_rule_events"] == 1
    assert report["summary"]["unique_program_key_count"] == 3
    assert report["summary"]["events_with_evidence_url"] == 3
    assert report["summary"]["collection_error_count"] == 1

    statuses = {row["source"]: row["status"] for row in report["sources"]}
    assert statuses == {
        "Deadline Source": "fresh",
        "Eligibility Source": "stale",
        "No Extracted Event": "missing_event",
        "Missing Source": "missing",
        "News Source": "fresh",
    }
    deadline_row = next(
        row for row in report["sources"] if row["source"] == "Deadline Source"
    )
    assert deadline_row["latest_application_deadline"] == "2026-04-30"
    assert deadline_row["latest_program_key"].startswith(
        "application-deadline:deadline-source:2026-04-30"
    )
    assert deadline_row["errors"] == ["Deadline Source: timeout after retry"]

    eligibility_row = next(
        row for row in report["sources"] if row["source"] == "Eligibility Source"
    )
    assert eligibility_row["latest_eligibility_fields"]["Region"] == ["서울"]
    assert eligibility_row["latest_eligibility_fields"]["TargetGroup"] == ["소상공인"]
    deadline_event = next(
        row for row in report["events"] if row["event_model"] == "application_deadline"
    )
    assert deadline_event["evidence_url"] == "https://example.com/deadline"
    assert deadline_event["program_key"].startswith(
        "application-deadline:deadline-source:2026-04-30"
    )


def test_build_quality_report_tracks_selection_result_event() -> None:
    now = datetime(2026, 4, 20, tzinfo=UTC)
    category = CategoryConfig(
        category_name="govsupport",
        display_name="Gov Support",
        sources=[_source("Selection Result Source", "selection_result", 7)],
        entities=[],
    )
    articles = [
        Article(
            title="청년 창업지원사업 선정결과 발표",
            link="https://example.com/result",
            summary="최종 선정 결과",
            published=now,
            collected_at=now,
            source="Selection Result Source",
            category="govsupport",
            matched_entities={
                "OperationalEvent": ["selection_result"],
                "SelectionResultDate": ["2026-04-15"],
                "SelectionSelectedCount": ["12"],
                "SelectionExecutionAmount": ["3억원"],
            },
        )
    ]

    report = build_quality_report(
        category=category,
        articles=articles,
        quality_config={
            "data_quality": {
                "quality_outputs": {
                    "tracked_event_models": [
                        "support_program_notice",
                        "application_deadline",
                        "eligibility_rule",
                        "selection_result",
                    ]
                }
            }
        },
        generated_at=now,
    )

    assert report["summary"]["selection_result_events"] == 1
    assert report["summary"]["fresh_sources"] == 1
    event = report["events"][0]
    assert event["event_model"] == "selection_result"
    assert event["event_at"] == "2026-04-15T00:00:00+00:00"
    assert event["selected_count"] == "12"
    assert event["execution_amount"] == "3억원"
    source = report["sources"][0]
    assert source["status"] == "fresh"
    assert source["latest_selection_result_date"] == "2026-04-15"
    assert source["latest_selected_count"] == "12"
    assert source["latest_execution_amount"] == "3억원"
    assert source["latest_program_title"] == "청년 창업지원사업 선정결과 발표"


def test_disabled_gov_source_is_skipped_not_active_tracked() -> None:
    now = datetime(2026, 4, 20, tzinfo=UTC)
    source = _source("Credential Source", "eligibility_rule", 2)
    source.enabled = False
    source.config["skip_reason"] = "Missing credential."
    source.config["reenable_gate"] = "Credential and contract test required."
    category = CategoryConfig(
        category_name="govsupport",
        display_name="Gov Support",
        sources=[source],
        entities=[],
    )

    report = build_quality_report(
        category=category,
        articles=[
            Article(
                title="Eligibility notice",
                link="https://example.com/eligibility",
                summary="서울 소상공인 대상",
                published=now,
                collected_at=now,
                source="Credential Source",
                category="govsupport",
                matched_entities={"OperationalEvent": ["eligibility_rule"]},
            )
        ],
        quality_config={
            "data_quality": {
                "quality_outputs": {"tracked_event_models": ["eligibility_rule"]}
            }
        },
        generated_at=now,
    )

    row = report["sources"][0]
    assert row["tracked"] is False
    assert row["status"] == "skipped_disabled"
    assert row["skip_reason"] == "Missing credential."
    assert report["summary"]["tracked_sources"] == 0
    assert report["summary"]["skipped_disabled_sources"] == 1
    assert report["summary"]["eligibility_rule_events"] == 0


def test_write_quality_report_writes_latest_and_dated_files(tmp_path) -> None:
    report = {
        "category": "govsupport",
        "generated_at": "2026-04-12T03:04:05+00:00",
        "summary": {},
        "sources": [],
        "events": [],
        "errors": [],
    }

    paths = write_quality_report(
        report,
        output_dir=tmp_path,
        category_name="govsupport",
    )

    assert paths["latest"] == tmp_path / "govsupport_quality.json"
    assert paths["dated"] == tmp_path / "govsupport_20260412_quality.json"
    assert json.loads(paths["latest"].read_text(encoding="utf-8")) == report
    assert json.loads(paths["dated"].read_text(encoding="utf-8")) == report
