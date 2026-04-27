from __future__ import annotations

import pytest

from govradar.models import Article, Source
from govradar.relevance import apply_source_context_entities, filter_relevant_articles


pytestmark = pytest.mark.unit


def _article(
    *,
    title: str,
    source: str = "정책브리핑",
    summary: str | None = None,
    matched_entities: dict[str, list[str]] | None = None,
) -> Article:
    return Article(
        title=title,
        link=f"https://example.com/{title}",
        summary=summary if summary is not None else title,
        published=None,
        source=source,
        category="govsupport",
        matched_entities=matched_entities or {},
    )


def test_apply_source_context_entities_adds_support_notice_signal() -> None:
    article = _article(
        title="청년 지원사업 신청 공고",
        matched_entities={"SupportType": ["지원사업"]},
    )
    source = Source(
        name="정책브리핑",
        type="rss",
        url="https://www.korea.kr/rss/policy.xml",
        info_purpose=["support_program_notice"],
        config={"event_model": "support_program_notice"},
    )

    classified = apply_source_context_entities([article], [source])

    assert classified[0].matched_entities["SourceSignal"] == ["support_program_notice"]


def test_filter_relevant_articles_keeps_support_rows_and_drops_generic_policy() -> None:
    sources = [
        Source(
            name="정책브리핑",
            type="rss",
            url="https://www.korea.kr/rss/policy.xml",
            config={"event_model": "support_program_notice"},
        ),
        Source(name="동아일보 경제", type="rss", url="https://rss.donga.com/economy.xml"),
        Source(
            name="Awesome MCP Korea",
            type="rss",
            url="https://github.com/darjeeling/awesome-mcp-korea/commits/main.atom",
            info_purpose=["api-ecosystem", "public-data"],
        ),
    ]
    articles = [
        _article(
            title="고유가 피해지원금 4월 27일부터 신청",
            matched_entities={
                "SupportType": ["지원금"],
                "TargetGroup": ["국민"],
                "ApplicationInfo": ["신청"],
            },
        ),
        _article(
            title="정부 국제유가 대책 발표",
            source="동아일보 경제",
            matched_entities={"GovGeneral": ["정부", "발표"]},
        ),
        _article(
            title="공공데이터 MCP 서버 추가",
            source="Awesome MCP Korea",
            matched_entities={"McpKoreaEcosystem": ["mcp", "공공데이터"]},
        ),
    ]

    filtered = filter_relevant_articles(
        apply_source_context_entities(articles, sources),
        sources,
    )

    assert [article.title for article in filtered] == [
        "고유가 피해지원금 4월 27일부터 신청",
        "공공데이터 MCP 서버 추가",
    ]


def test_filter_relevant_articles_drops_browser_index_chrome() -> None:
    source = Source(
        name="보건복지부",
        type="javascript",
        url="https://www.mohw.go.kr/",
        config={"event_model": "eligibility_rule"},
    )
    article = _article(
        title="목록 < 전체 < 보도자료 < 알림",
        source="보건복지부",
        summary="본문으로 바로가기 주메뉴 바로가기 알림 보도자료",
        matched_entities={
            "SupportType": ["지원"],
            "TargetGroup": ["청년"],
            "OperationalEvent": ["eligibility_rule"],
        },
    )

    assert filter_relevant_articles([article], [source]) == []


def test_filter_relevant_articles_does_not_drop_support_due_to_incidental_mcp_terms() -> None:
    source = Source(
        name="금융위원회",
        type="javascript",
        url="https://www.fsc.go.kr/no010101",
        config={"event_model": "eligibility_rule"},
    )
    article = _article(
        title="서민 취약계층 복합지원 신청 안내",
        source="금융위원회",
        summary="취약계층을 위한 복합지원 사업이며 API 문서도 함께 공개한다.",
        matched_entities={
            "McpKoreaEcosystem": ["api"],
            "SupportType": ["지원"],
            "TargetGroup": ["취약계층"],
            "EligibilityTargetGroup": ["취약계층"],
            "OperationalEvent": ["eligibility_rule"],
        },
    )

    assert filter_relevant_articles([article], [source]) == [article]
