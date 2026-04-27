from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime

from .models import Article


_APPLICATION_MARKERS = (
    "신청",
    "접수",
    "모집",
    "공모",
    "마감",
    "접수기간",
    "신청기간",
    "deadline",
    "apply",
    "application",
)

_DEADLINE_CONTEXT_MARKERS = ("마감", "까지", "deadline", "closing")
_SELECTION_RESULT_MARKERS = (
    "선정결과",
    "선정 결과",
    "최종선정",
    "최종 선정",
    "예비선정",
    "예비 선정",
    "선발결과",
    "선발 결과",
    "합격자",
    "선정기업",
    "선정 기업",
    "선정자",
    "selected",
    "selection result",
)
_EXECUTION_MARKERS = ("집행", "집행실적", "교부", "지원금 지급", "execution", "disbursement")
_SELECTION_COUNT_RE = re.compile(
    r"(?P<count>\d{1,5}(?:,\d{3})*)\s*(?:개사|개\s*사|명|팀|건|곳)\s*"
    r"(?:을|를|이|가)?\s*(?:최종\s*)?(?:선정|선발|합격)"
)
_SELECTION_COUNT_REVERSED_RE = re.compile(
    r"(?:선정|선발|합격)(?:기업|자|팀|대상)?\s*"
    r"(?P<count>\d{1,5}(?:,\d{3})*)\s*(?:개사|개\s*사|명|팀|건|곳)"
)
_EXECUTION_AMOUNT_RE = re.compile(
    r"(?:(?:총|약|집행(?:액)?|교부(?:액)?|지원(?:금|액)?)\s*)"
    r"(?P<amount>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?P<unit>억\s*원|억원|만\s*원|만원|원)"
)
_PROGRAM_TITLE_RE = re.compile(
    r"(?P<title>[가-힣A-Za-z0-9·\-\s]{2,80}?"
    r"(?:창업지원사업|지원사업|보조사업|창업지원|정책자금|바우처|지원금|공모사업))"
)

_YEAR_DATE_RE = re.compile(
    r"(?P<year>20\d{2})\s*(?:년|[.\-/])\s*"
    r"(?P<month>\d{1,2})\s*(?:월|[.\-/])\s*"
    r"(?P<day>\d{1,2})\s*(?:일|\.)?"
)
_MONTH_DATE_RE = re.compile(
    r"(?<!\d)(?P<month>\d{1,2})\s*(?:월|[.\-/])\s*"
    r"(?P<day>\d{1,2})\s*(?:일|\.)?(?!\d)"
)


@dataclass(frozen=True)
class ApplicationWindow:
    start_date: str | None
    deadline: str | None


def _reference_year(reference_date: datetime | None) -> int:
    if reference_date is None:
        return datetime.now(UTC).year
    return reference_date.year


def _iso_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _overlaps(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(
        start < occupied_end and end > occupied_start
        for occupied_start, occupied_end in spans
    )


def _dedupe_ordered(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def extract_application_window(
    text: str, *, reference_date: datetime | None = None
) -> ApplicationWindow:
    """Extract a conservative application window from Korean support notice text."""
    haystack = text.strip()
    haystack_lower = haystack.lower()
    if not haystack or not any(marker in haystack_lower for marker in _APPLICATION_MARKERS):
        return ApplicationWindow(start_date=None, deadline=None)

    dates: list[str] = []
    occupied_spans: list[tuple[int, int]] = []
    for match in _YEAR_DATE_RE.finditer(haystack):
        parsed = _iso_date(
            int(match.group("year")), int(match.group("month")), int(match.group("day"))
        )
        if parsed:
            dates.append(parsed)
            occupied_spans.append(match.span())

    base_year = _reference_year(reference_date)
    for match in _MONTH_DATE_RE.finditer(haystack):
        if _overlaps(match.span(), occupied_spans):
            continue
        parsed = _iso_date(base_year, int(match.group("month")), int(match.group("day")))
        if parsed:
            dates.append(parsed)

    dates = _dedupe_ordered(dates)
    if not dates:
        return ApplicationWindow(start_date=None, deadline=None)

    if len(dates) >= 2:
        return ApplicationWindow(start_date=dates[0], deadline=dates[-1])

    if any(marker in haystack_lower for marker in _DEADLINE_CONTEXT_MARKERS):
        return ApplicationWindow(start_date=None, deadline=dates[0])

    return ApplicationWindow(start_date=None, deadline=None)


def extract_eligibility_fields(text: str) -> dict[str, list[str]]:
    """Extract lightweight eligibility hints without treating them as final decisions."""
    keyword_groups = {
        "target_group": [
            "소상공인",
            "중소기업",
            "스타트업",
            "청년",
            "신혼부부",
            "저소득",
            "취약계층",
            "농어민",
            "자영업자",
        ],
        "business_stage": ["예비창업자", "초기창업", "창업기업", "재창업", "벤처기업"],
        "industry": ["농업", "수산", "축산", "제조", "관광", "콘텐츠", "ICT", "AI", "바이오"],
        "region": [
            "서울",
            "경기",
            "인천",
            "부산",
            "대구",
            "광주",
            "대전",
            "울산",
            "세종",
            "강원",
            "충북",
            "충남",
            "전북",
            "전남",
            "경북",
            "경남",
            "제주",
        ],
    }

    matches: dict[str, list[str]] = {}
    for field_name, keywords in keyword_groups.items():
        hits = [keyword for keyword in keywords if keyword.lower() in text.lower()]
        if hits:
            matches[field_name] = _dedupe_ordered(hits)
    return matches


def extract_selection_result_fields(
    text: str, *, reference_date: datetime | None = None
) -> dict[str, list[str]]:
    """Extract conservative selection/execution result hints from support notices."""
    haystack = text.strip()
    haystack_lower = haystack.lower()
    if not haystack:
        return {}
    has_selection_marker = any(marker in haystack_lower for marker in _SELECTION_RESULT_MARKERS)
    has_execution_marker = any(marker in haystack_lower for marker in _EXECUTION_MARKERS)
    if not (has_selection_marker or has_execution_marker):
        return {}
    amount_match = _EXECUTION_AMOUNT_RE.search(haystack)
    if has_execution_marker and not has_selection_marker and amount_match is None:
        return {}

    fields: dict[str, list[str]] = {}
    dates = _extract_dates(haystack, reference_date=reference_date)
    if dates:
        fields["selection_result_date"] = [dates[0]]

    selected_count = _first_group_match(
        haystack,
        (_SELECTION_COUNT_RE, _SELECTION_COUNT_REVERSED_RE),
        "count",
    )
    if selected_count:
        fields["selected_count"] = [selected_count.replace(",", "")]

    if amount_match:
        amount = amount_match.group("amount").replace(",", "")
        unit = re.sub(r"\s+", "", amount_match.group("unit"))
        fields["execution_amount"] = [f"{amount}{unit}"]

    program_match = _PROGRAM_TITLE_RE.search(haystack)
    if program_match:
        fields["program_title"] = [re.sub(r"\s+", " ", program_match.group("title")).strip()]

    if not any(key in fields for key in ("selected_count", "execution_amount", "program_title")):
        return {}

    return fields


def _extract_dates(text: str, *, reference_date: datetime | None = None) -> list[str]:
    dates: list[str] = []
    occupied_spans: list[tuple[int, int]] = []
    for match in _YEAR_DATE_RE.finditer(text):
        parsed = _iso_date(
            int(match.group("year")), int(match.group("month")), int(match.group("day"))
        )
        if parsed:
            dates.append(parsed)
            occupied_spans.append(match.span())

    base_year = _reference_year(reference_date)
    for match in _MONTH_DATE_RE.finditer(text):
        if _overlaps(match.span(), occupied_spans):
            continue
        parsed = _iso_date(base_year, int(match.group("month")), int(match.group("day")))
        if parsed:
            dates.append(parsed)
    return _dedupe_ordered(dates)


def _first_group_match(text: str, patterns: Iterable[re.Pattern[str]], group: str) -> str:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return str(match.group(group))
    return ""


def _selection_entity_key(field_name: str) -> str:
    if field_name == "selection_result_date":
        return "SelectionResultDate"
    return f"Selection{field_name.title().replace('_', '')}"


def enrich_support_operational_fields(articles: Iterable[Article]) -> list[Article]:
    """Add parsed support-program operational hints to matched_entities."""
    enriched: list[Article] = []
    for article in articles:
        text = f"{article.title}\n{article.summary}"
        window = extract_application_window(text, reference_date=article.published)
        eligibility = extract_eligibility_fields(text)
        selection_result = extract_selection_result_fields(
            article.title,
            reference_date=article.published,
        )

        matches = dict(article.matched_entities)
        event_models: list[str] = []
        if window.start_date:
            matches["ApplicationStartDate"] = [window.start_date]
        if window.deadline:
            matches["ApplicationDeadline"] = [window.deadline]
            event_models.append("application_deadline")
        for field_name, values in eligibility.items():
            matches[f"Eligibility{field_name.title().replace('_', '')}"] = values
        if eligibility:
            event_models.append("eligibility_rule")
        for field_name, values in selection_result.items():
            matches[_selection_entity_key(field_name)] = values
        if selection_result:
            event_models.append("selection_result")
        if event_models:
            matches["OperationalEvent"] = _dedupe_ordered(event_models)

        article.matched_entities = matches
        enriched.append(article)
    return enriched
