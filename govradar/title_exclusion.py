"""소스별 ``exclude_title_prefixes`` 설정으로 제목이 특정 접두어로 시작하는 항목을 제외한다.

사용 범위는 검증으로 확인된 접두어로 한정한다(예: SBS 라디오 요약 코너 ``[여담야담]``).
키워드 포함 게이트(include_keywords)는 일반 뉴스 피드에서 유용한 항목을 너무 많이 지워
도입하지 않았다. 근거는 docs/noise_gate_validation_2026-10-29.md 참고.
"""

from __future__ import annotations

from collections.abc import Iterable

from govradar.models import Article, Source


def drop_excluded_titles(
    articles: list[Article],
    sources: Iterable[Source],
) -> tuple[list[Article], dict[str, int]]:
    """제목 접두어가 제외 목록에 있는 항목을 뺀 목록과 소스별 제외 건수를 돌려준다."""
    prefixes_by_source: dict[str, tuple[str, ...]] = {}
    for source in sources:
        if not source.enabled:
            continue
        raw = (source.config or {}).get("exclude_title_prefixes")
        if isinstance(raw, list):
            prefixes = tuple(str(item) for item in raw if str(item).strip())
            if prefixes:
                prefixes_by_source[source.name] = prefixes
    if not prefixes_by_source:
        return articles, {}
    kept: list[Article] = []
    dropped: dict[str, int] = {}
    for article in articles:
        source_prefixes = prefixes_by_source.get(article.source)
        if source_prefixes and article.title.lstrip().startswith(source_prefixes):
            dropped[article.source] = dropped.get(article.source, 0) + 1
            continue
        kept.append(article)
    return kept, dropped
