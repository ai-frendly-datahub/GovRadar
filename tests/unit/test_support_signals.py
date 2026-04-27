from __future__ import annotations

from datetime import UTC, datetime

from govradar.models import Article
from govradar.support_signals import (
    enrich_support_operational_fields,
    extract_application_window,
    extract_eligibility_fields,
    extract_selection_result_fields,
)


def test_extract_application_window_with_year_range() -> None:
    window = extract_application_window(
        "서울시 청년 창업지원 접수기간 2026년 4월 1일 ~ 2026년 4월 30일",
        reference_date=datetime(2026, 4, 1, tzinfo=UTC),
    )

    assert window.start_date == "2026-04-01"
    assert window.deadline == "2026-04-30"


def test_extract_application_window_uses_reference_year_for_month_day_deadline() -> None:
    window = extract_application_window(
        "소상공인 정책자금 신청은 4월 30일까지 접수",
        reference_date=datetime(2026, 4, 1, tzinfo=UTC),
    )

    assert window.start_date is None
    assert window.deadline == "2026-04-30"


def test_extract_application_window_ignores_phone_number_fragments() -> None:
    window = extract_application_window(
        "문의 02-2133-3831 등록일 2026-04-22 공고마감일자 2026-06-30 "
        "접수기간 : '26.4.22.(수) 09:00 ~ '26.6.30.(화) 17:00 까지",
        reference_date=datetime(2026, 4, 22, tzinfo=UTC),
    )

    assert window.start_date == "2026-04-22"
    assert window.deadline == "2026-06-30"


def test_extract_application_window_does_not_guess_without_application_context() -> None:
    window = extract_application_window(
        "정부는 2026년 4월 30일 지원사업 개선방안을 발표했다.",
        reference_date=datetime(2026, 4, 1, tzinfo=UTC),
    )

    assert window.start_date is None
    assert window.deadline is None


def test_extract_eligibility_fields_extracts_support_conditions() -> None:
    fields = extract_eligibility_fields(
        "서울 소재 예비창업자와 소상공인 대상 ICT 지원사업"
    )

    assert fields["target_group"] == ["소상공인"]
    assert fields["business_stage"] == ["예비창업자"]
    assert fields["industry"] == ["ICT"]
    assert fields["region"] == ["서울"]


def test_extract_selection_result_fields_extracts_result_and_execution_hints() -> None:
    fields = extract_selection_result_fields(
        "청년 창업지원사업 선정결과 발표: 2026년 4월 15일 25개사 선정, 총 10억원 집행",
        reference_date=datetime(2026, 4, 1, tzinfo=UTC),
    )

    assert fields["selection_result_date"] == ["2026-04-15"]
    assert fields["selected_count"] == ["25"]
    assert fields["execution_amount"] == ["10억원"]
    assert fields["program_title"] == ["청년 창업지원사업"]


def test_enrich_support_operational_fields_adds_matched_entities() -> None:
    article = Article(
        title="서울시 청년 창업지원 접수기간 안내",
        link="https://example.com/support",
        summary="서울 예비창업자와 소상공인은 2026년 4월 1일부터 2026년 4월 30일까지 신청",
        published=datetime(2026, 4, 1, tzinfo=UTC),
        source="서울시 지원사업",
        category="govsupport",
        matched_entities={"SupportType": ["지원사업"]},
    )

    enriched = enrich_support_operational_fields([article])[0]

    assert enriched.matched_entities["ApplicationStartDate"] == ["2026-04-01"]
    assert enriched.matched_entities["ApplicationDeadline"] == ["2026-04-30"]
    assert enriched.matched_entities["EligibilityRegion"] == ["서울"]
    assert enriched.matched_entities["OperationalEvent"] == [
        "application_deadline",
        "eligibility_rule",
    ]


def test_enrich_support_operational_fields_adds_selection_result_event() -> None:
    article = Article(
        title="지역 성장지원사업 선정결과 발표: 2026년 4월 15일 12개사 선정, 총 3억원 집행",
        link="https://example.com/result",
        summary="목록 페이지 요약에는 다른 지원사업 문구가 섞일 수 있다.",
        published=datetime(2026, 4, 15, tzinfo=UTC),
        source="K-Startup 선정결과",
        category="govsupport",
        matched_entities={"SupportType": ["지원사업"], "ApplicationInfo": ["선정결과"]},
    )

    enriched = enrich_support_operational_fields([article])[0]

    assert enriched.matched_entities["SelectionResultDate"] == ["2026-04-15"]
    assert enriched.matched_entities["SelectionSelectedCount"] == ["12"]
    assert enriched.matched_entities["SelectionExecutionAmount"] == ["3억원"]
    assert enriched.matched_entities["OperationalEvent"] == ["selection_result"]
