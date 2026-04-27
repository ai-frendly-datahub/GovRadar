from __future__ import annotations

from collections.abc import Iterable

from .models import Article, Source


TRACKED_EVENT_MODELS = {
    "application_deadline",
    "eligibility_rule",
    "selection_result",
    "support_program_notice",
}
SOURCE_CONTEXT_PURPOSES = {
    "application_deadline",
    "eligibility_rule",
    "selection_result",
    "support_program_notice",
    "api-ecosystem",
    "public-data",
}
OPERATIONAL_ENTITY_NAMES = {
    "ApplicationDeadline",
    "ApplicationStartDate",
    "OperationalEvent",
}
GOV_SUPPORT_ENTITY_NAMES = {
    "ApplicationInfo",
    "EligibilityBusinessStage",
    "EligibilityIndustry",
    "EligibilityRegion",
    "EligibilityTargetGroup",
    "Ministry",
    "Region",
    "SupportType",
    "TargetGroup",
}
CORE_SUPPORT_TERMS = {
    "assistance",
    "benefit",
    "grant",
    "loan",
    "public funding",
    "rebate",
    "subsidy",
    "voucher",
    "감면",
    "근로장려금",
    "대출",
    "바우처",
    "보조금",
    "세액공제",
    "융자",
    "장려금",
    "재정지원",
    "정책자금",
    "정책금융",
    "포상금",
    "지원금",
    "지원사업",
    "취약계층",
}
APPLICATION_TERMS = {
    "application deadline",
    "apply",
    "deadline",
    "공고",
    "공모",
    "마감",
    "모집",
    "선정",
    "신청",
    "접수",
}
CORE_SUPPORT_ENTITY_VALUES = {
    "grant",
    "subsidy",
    "benefit",
    "voucher",
    "rebate",
    "assistance",
    "welfare",
    "감면",
    "긴급자금",
    "긴급지원",
    "대출",
    "무상지원",
    "바우처",
    "보조금",
    "보조사업",
    "사업비",
    "세금감면",
    "세액공제",
    "소득공제",
    "수당",
    "융자",
    "이자지원",
    "장려금",
    "정책자금",
    "포상금",
    "지원금",
    "지원사업",
    "지원제도",
    "출연금",
    "특별지원",
}
GOVERNMENT_FUNDING_TERMS = {
    "government support",
    "grant",
    "policy funding",
    "public funding",
    "subsidy",
    "공공지원",
    "보조금",
    "유가보조금",
    "이차보전",
    "재정지원",
    "정책금융",
    "정책자금",
    "지원금",
    "지원사업",
    "포상금",
    "피해지원금",
}
STRONG_TARGET_ENTITY_VALUES = {
    "small business",
    "startup",
    "entrepreneur",
    "강소기업",
    "구직자",
    "농가",
    "농어민",
    "벤처",
    "벤처기업",
    "사회적기업",
    "소상공인",
    "스타트업",
    "예비창업자",
    "자영업",
    "저소득",
    "중견기업",
    "중소기업",
    "창업",
    "청년",
    "취약계층",
    "혁신기업",
}
WEAK_LOAN_VALUES = {"loan", "대출", "융자"}
PUBLIC_DATA_TERMS = {
    "data.go.kr",
    "mcp",
    "open api",
    "public api",
    "공공 api",
    "공공데이터",
    "국가법령정보",
    "법령정보",
}
GENERIC_ONLY_SUPPORT_VALUES = {
    "대책",
    "면제",
    "상환유예",
    "유예",
    "지원",
    "지원책",
    "추경",
    "특례",
}


def apply_source_context_entities(
    articles: Iterable[Article],
    sources: Iterable[Source],
) -> list[Article]:
    source_map = {source.name: source for source in sources if source.enabled}
    classified: list[Article] = []
    for article in articles:
        if article.category != "govsupport":
            classified.append(article)
            continue

        source = source_map.get(article.source)
        if source is None:
            continue

        tags = _source_context_tags(source)
        if tags:
            existing = article.matched_entities.get("SourceSignal", [])
            existing_values = existing if isinstance(existing, list) else [existing]
            article.matched_entities["SourceSignal"] = sorted(
                {str(value) for value in existing_values} | set(tags)
            )
        classified.append(article)
    return classified


def filter_relevant_articles(
    articles: Iterable[Article],
    sources: Iterable[Source],
) -> list[Article]:
    source_map = {source.name: source for source in sources if source.enabled}
    filtered: list[Article] = []
    for article in articles:
        if article.category != "govsupport":
            filtered.append(article)
            continue

        source = source_map.get(article.source)
        if source is None:
            continue
        if _is_invalid_page(article):
            continue
        if _has_govsupport_signal(article, source):
            filtered.append(article)
    return filtered


def _has_govsupport_signal(article: Article, source: Source) -> bool:
    entity_names = set(article.matched_entities)
    text = f"{article.title} {article.summary}".lower()
    support_entities = entity_names & GOV_SUPPORT_ENTITY_NAMES
    has_core_support_text = _contains_any(text, CORE_SUPPORT_TERMS)
    has_core_support_entity = _has_core_support_entity(article)
    has_application_context = _contains_any(text, APPLICATION_TERMS)
    source_event_model = _source_event_model(source)

    if "McpKoreaEcosystem" in entity_names and (
        _contains_any(text, PUBLIC_DATA_TERMS) or source_event_model == "public_data_api"
    ):
        return True

    if _is_broad_source(source):
        return _has_broad_govsupport_signal(
            article=article,
            entity_names=entity_names,
            has_core_support_text=has_core_support_text,
            has_core_support_entity=has_core_support_entity,
            text=text,
        )

    if entity_names & OPERATIONAL_ENTITY_NAMES:
        return bool(support_entities) and (has_core_support_text or has_core_support_entity)

    if not support_entities:
        return False

    if has_core_support_text or has_core_support_entity:
        if {"ApplicationInfo", "TargetGroup", "Ministry", "Region"} & entity_names:
            return True
        if _source_event_model(source) in TRACKED_EVENT_MODELS:
            return True

    if source_event_model in {"application_deadline", "eligibility_rule"}:
        return (
            len(support_entities) >= 3
            and has_application_context
            and not _support_values_are_generic_only(article)
        )

    if source_event_model == "support_program_notice":
        return _has_support_notice_signal(
            article=article,
            entity_names=entity_names,
            has_application_context=has_application_context,
            has_core_support_entity=has_core_support_entity,
        )

    return False


def _has_support_notice_signal(
    *,
    article: Article,
    entity_names: set[str],
    has_application_context: bool,
    has_core_support_entity: bool,
) -> bool:
    title = article.title.lower()
    if _contains_any(title, CORE_SUPPORT_TERMS | GOVERNMENT_FUNDING_TERMS):
        return True
    if _support_values_are_generic_only(article):
        return False
    return has_core_support_entity and has_application_context and bool(
        {"TargetGroup", "Ministry"} & entity_names
    )


def _has_broad_govsupport_signal(
    *,
    article: Article,
    entity_names: set[str],
    has_core_support_text: bool,
    has_core_support_entity: bool,
    text: str,
) -> bool:
    if not (has_core_support_text or has_core_support_entity):
        return False
    if not {"ApplicationInfo", "TargetGroup", "Ministry"} & entity_names:
        return False
    if _support_values_are_weak_loan_only(article):
        return _has_strong_target_entity(article) or _contains_any(
            text,
            GOVERNMENT_FUNDING_TERMS,
        )
    if _has_strong_target_entity(article):
        return True
    if "ApplicationInfo" in entity_names and {"TargetGroup", "Ministry"} & entity_names:
        return True
    return "Ministry" in entity_names and _contains_any(text, GOVERNMENT_FUNDING_TERMS)


def _source_context_tags(source: Source) -> list[str]:
    tags = {purpose for purpose in source.info_purpose if purpose in SOURCE_CONTEXT_PURPOSES}
    event_model = _source_event_model(source)
    if event_model:
        tags.add(event_model)
    return sorted(tags)


def _source_event_model(source: Source) -> str:
    raw = source.config.get("event_model")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    purposes = {purpose.strip() for purpose in source.info_purpose if purpose.strip()}
    if {"api-ecosystem", "public-data"} & purposes:
        return "public_data_api"
    return ""


def _is_broad_source(source: Source) -> bool:
    return not _source_event_model(source) and source.trust_tier != "T1_authoritative"


def _has_core_support_entity(article: Article) -> bool:
    values = article.matched_entities.get("SupportType", [])
    if not isinstance(values, list):
        return False
    normalized = {str(value).strip().lower() for value in values}
    return bool(normalized & CORE_SUPPORT_ENTITY_VALUES)


def _has_strong_target_entity(article: Article) -> bool:
    values = article.matched_entities.get("TargetGroup", [])
    if not isinstance(values, list):
        return False
    normalized = {str(value).strip().lower() for value in values}
    return bool(normalized & STRONG_TARGET_ENTITY_VALUES)


def _support_values_are_generic_only(article: Article) -> bool:
    values = article.matched_entities.get("SupportType", [])
    if not isinstance(values, list):
        return False
    normalized = {str(value).strip() for value in values if str(value).strip()}
    return bool(normalized) and normalized <= GENERIC_ONLY_SUPPORT_VALUES


def _support_values_are_weak_loan_only(article: Article) -> bool:
    values = article.matched_entities.get("SupportType", [])
    if not isinstance(values, list):
        return False
    normalized = {str(value).strip().lower() for value in values if str(value).strip()}
    return bool(normalized) and normalized <= WEAK_LOAN_VALUES


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term.lower() in text for term in terms)


def _is_invalid_page(article: Article) -> bool:
    haystack = f"{article.title} {article.summary}".lower()
    if any(
        marker in haystack
        for marker in (
            "404",
            "access denied",
            "not found",
            "page not found",
            "request blocked",
            "service unavailable",
            "페이지를 찾을 수 없습니다",
        )
    ):
        return True
    return "목록 < 전체" in haystack or (
        "본문으로 바로가기" in haystack and "주메뉴 바로가기" in haystack
    )
