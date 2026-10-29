"""소스별 ``store_summary: false`` 설정으로 RSS 요약(summary)의 저장·공개를 막는다.

목적: 언론사 소스는 RSS가 준 summary를 저장하지 않고 제목·링크·출처명만 저장·공개한다
(설정은 README의 ``store_summary`` 항목 참고).

동작 규칙:
- 수집 직후의 메모리 객체에는 summary를 그대로 둔다. 엔티티 분류와 관련성 필터가 쓰기 때문이다.
- raw JSONL 기록과 DuckDB/검색 색인 기록 직전에만 summary를 비운 사본을 쓴다.
- 이미 DuckDB에 들어 있는 같은 소스의 summary는 실행마다 비운다(보고서에 다시 나오지 않게).
- Git 기록에 남은 과거 커밋의 데이터는 지우지 않는다.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from govradar.models import Article, Source

STORE_SUMMARY_KEY = "store_summary"


def summary_free_source_names(sources: Iterable[Source]) -> frozenset[str]:
    """``store_summary``가 불리언 False인 소스 이름. 다른 값(문자열 등)은 무시한다.

    수집을 멈춘(``enabled: false``) 소스도 포함한다. 이미 저장된 summary를 계속 비우기 위해서다.
    """
    names: set[str] = set()
    for source in sources:
        if (source.config or {}).get(STORE_SUMMARY_KEY) is False:
            names.add(source.name)
    return frozenset(names)


def redact_summaries(
    articles: Iterable[Article],
    sources: Iterable[Source],
) -> list[Article]:
    """대상 소스 항목은 summary를 비운 사본으로, 나머지는 그대로 돌려준다. 원본은 바꾸지 않는다."""
    names = summary_free_source_names(sources)
    result: list[Article] = []
    for article in articles:
        if article.source in names and article.summary:
            result.append(replace(article, summary=""))
        else:
            result.append(article)
    return result
