from __future__ import annotations

import pytest

from govradar.models import Article, Source
from govradar.title_exclusion import drop_excluded_titles


def _article(title: str, source: str = "SBS 뉴스 정치") -> Article:
    return Article(
        title=title,
        link=f"https://example.com/{abs(hash(title))}",
        summary="",
        published=None,
        source=source,
        category="govsupport",
    )


def _source(name: str = "SBS 뉴스 정치", **config: object) -> Source:
    return Source(name=name, type="rss", url="https://example.com/feed", config=dict(config))


@pytest.mark.unit
def test_drops_only_titles_that_start_with_configured_prefix() -> None:
    articles = [
        _article("[여담야담] 출연자 코너"),
        _article("  [성민종합정치] 요약"),
        _article("국회, 예산안 처리 [여담야담]"),
        _article("[단독] 정부 지원 확대"),
        _article("[여담야담] 다른 소스", source="동아일보 경제"),
    ]
    kept, dropped = drop_excluded_titles(
        articles,
        [_source(exclude_title_prefixes=["[여담야담]", "[성민종합정치]"])],
    )
    assert dropped == {"SBS 뉴스 정치": 2}
    assert [article.title for article in kept] == [
        "국회, 예산안 처리 [여담야담]",
        "[단독] 정부 지원 확대",
        "[여담야담] 다른 소스",
    ]


@pytest.mark.unit
def test_no_configuration_or_disabled_source_keeps_everything() -> None:
    articles = [_article("[여담야담] 코너")]
    kept, dropped = drop_excluded_titles(articles, [_source()])
    assert kept == articles and dropped == {}

    disabled = _source(exclude_title_prefixes=["[여담야담]"])
    disabled.enabled = False
    kept, dropped = drop_excluded_titles(articles, [disabled])
    assert kept == articles and dropped == {}

    kept, dropped = drop_excluded_titles(articles, [_source(exclude_title_prefixes="[여담야담]")])
    assert kept == articles and dropped == {}
