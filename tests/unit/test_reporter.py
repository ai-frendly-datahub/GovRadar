from __future__ import annotations

from datetime import UTC, datetime

from govradar.models import Article, CategoryConfig
from govradar.reporter import generate_report


def test_generate_report_injects_operational_quality_panel(tmp_path, monkeypatch) -> None:
    fixed_now = datetime(2026, 4, 12, 9, 30, tzinfo=UTC)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    monkeypatch.setattr("radar_core.report_utils.datetime", FixedDateTime)

    output_path = tmp_path / "reports" / "govsupport_report.html"
    category = CategoryConfig(
        category_name="govsupport",
        display_name="Gov Support",
        sources=[],
        entities=[],
    )
    article = Article(
        title="서울시 지원사업 접수 마감",
        link="https://example.com/support",
        summary="서울 소상공인은 2026-04-30까지 신청",
        published=fixed_now,
        collected_at=fixed_now,
        source="서울시 지원사업",
        category="govsupport",
        matched_entities={
            "OperationalEvent": ["application_deadline"],
            "ApplicationDeadline": ["2026-04-30"],
        },
    )
    quality_report = {
        "summary": {
            "fresh_sources": 1,
            "stale_sources": 1,
            "missing_sources": 0,
            "missing_event_sources": 0,
            "application_deadline_events": 1,
            "eligibility_rule_events": 1,
            "selection_result_events": 1,
            "unique_program_key_count": 3,
            "events_with_evidence_url": 3,
        },
        "sources": [
            {
                "source": "서울시 지원사업",
                "status": "stale",
                "event_model": "application_deadline",
                "age_days": 3,
            }
        ],
        "events": [
            {
                "source": "서울시 지원사업",
                "event_model": "application_deadline",
                "title": "서울시 지원사업 접수 마감",
                "program_title": "서울시 지원사업 접수 마감",
                "application_deadline": "2026-04-30",
                "evidence_url": "https://example.com/support",
                "program_key": "application-deadline:seoul-program:2026-04-30",
            },
            {
                "source": "소상공인시장진흥공단",
                "event_model": "eligibility_rule",
                "title": "소상공인 정책자금",
                "program_title": "소상공인 정책자금",
                "eligibility_fields": {"Region": ["서울"], "TargetGroup": ["소상공인"]},
                "evidence_url": "https://example.com/eligibility",
                "program_key": "eligibility-rule:semas:2026-04-12",
            },
            {
                "source": "K-Startup 선정결과",
                "event_model": "selection_result",
                "title": "청년 창업지원사업 선정결과",
                "program_title": "청년 창업지원사업",
                "selection_result_date": "2026-04-15",
                "selected_count": "12",
                "execution_amount": "3억원",
                "evidence_url": "https://example.com/result",
                "program_key": "selection-result:kstartup:2026-04-15",
            },
        ],
    }

    generate_report(
        category=category,
        articles=[article],
        output_path=output_path,
        stats={"sources": 1, "collected": 1, "matched": 1, "window_days": 7},
        quality_report=quality_report,
    )

    html = output_path.read_text(encoding="utf-8")
    dated_html = (tmp_path / "reports" / "govsupport_20260412.html").read_text(
        encoding="utf-8"
    )

    for rendered in (html, dated_html):
        assert 'id="operational-quality"' in rendered
        assert "Operational Quality" in rendered
        assert "govsupport_quality.json" in rendered
        assert "deadline events" in rendered
        assert "eligibility events" in rendered
        assert "selection results" in rendered
        assert "program keys" in rendered
        assert "evidence URLs" in rendered
        assert "서울시 지원사업" in rendered
        assert "2026-04-30" in rendered
        assert "selected 12" in rendered
        assert "https://example.com/result" in rendered

    summary = (tmp_path / "reports" / "govsupport_20260412_summary.json").read_text(
        encoding="utf-8"
    )
    assert '"repo": "GovRadar"' in summary
    assert '"ontology_version": "0.1.0"' in summary
    assert '"govsupport.application_deadline"' in summary
