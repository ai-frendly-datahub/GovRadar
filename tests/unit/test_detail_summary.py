from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from govradar.detail_summary import (
    EnrichStats,
    enrich_empty_summaries,
    extract_summary,
    fetch_public_page,
    format_stats,
)
from govradar.models import Article, Source

ARTICLE_HTML = """
<html><head>
<meta name="description" content="메타 설명입니다. 기사 리드 문단이 여기에 들어갑니다 &middot; 계속">
</head><body>
<div id="articletxt">
  <figure><img src="x.jpg"><figcaption>사진=로이터 캡션</figcaption></figure>
  첫 문단입니다. 정부가 지원 대상을 넓힌다고 밝혔다.<br>둘째 줄입니다.
  <p>셋째 문단입니다.</p><script>var secret = 1;</script>
</div>
</body></html>
"""

SPAN_HTML = (
    "<div class='view_contents'>"
    "<span>농림축산식품부</span><span>(장관</span> <span>송미령)는</span>"
    "<span>사업을 개정한다고</span> <span>밝혔다.</span></div>"
)

LD_HTML = """
<html><head><script type="application/ld+json">
{"@type": "NewsArticle", "headline": "제목",
 "description": "ld+json 설명입니다. 충분히 긴 문장으로 작성합니다."}
</script></head><body><p>x</p></body></html>
"""


def _source(**config: object) -> Source:
    return Source(
        name="테스트 뉴스",
        type="rss",
        url="https://news.example.kr/feed",
        config={"fetch_detail_summary": True, **config},
    )


def _article(link: str = "https://news.example.kr/a/1", summary: str = "") -> Article:
    return Article(
        title="기사 제목",
        link=link,
        summary=summary,
        published=None,
        source="테스트 뉴스",
        category="govsupport",
    )


def _allow(_url: str, _timeout: int) -> tuple[bool, str]:
    return True, "ok"


@pytest.mark.unit
def test_extract_summary_prefers_body_and_drops_captions_and_scripts() -> None:
    text = extract_summary(
        ARTICLE_HTML, selectors=["#articletxt"], prefer_meta=False, max_chars=800
    )
    assert text.startswith("첫 문단입니다.")
    assert "둘째 줄입니다." in text
    assert "셋째 문단입니다." in text
    assert "캡션" not in text
    assert "secret" not in text


@pytest.mark.unit
def test_extract_summary_prefers_meta_when_configured_and_unescapes_entities() -> None:
    text = extract_summary(ARTICLE_HTML, selectors=["#articletxt"], prefer_meta=True, max_chars=800)
    assert text.startswith("메타 설명입니다.")
    assert "·" in text
    assert "&middot;" not in text


@pytest.mark.unit
def test_extract_summary_does_not_insert_spaces_between_inline_tags() -> None:
    text = extract_summary(
        SPAN_HTML, selectors=[".view_contents"], prefer_meta=False, max_chars=800
    )
    assert text.startswith("농림축산식품부(장관 송미령)는사업을 개정한다고 밝혔다.")


@pytest.mark.unit
def test_extract_summary_falls_back_to_json_ld_and_truncates() -> None:
    text = extract_summary(LD_HTML, selectors=["#missing"], prefer_meta=False, max_chars=10)
    assert text == "ld+json 설명"
    assert extract_summary("<html></html>", selectors=[], prefer_meta=False, max_chars=50) == ""


@pytest.mark.unit
def test_enrich_fills_only_empty_summaries_of_enabled_sources() -> None:
    articles = [
        _article("https://news.example.kr/a/1"),
        _article("https://news.example.kr/a/2", summary="이미 있는 요약"),
    ]
    fetched: list[str] = []

    def fetch(url: str, _timeout: int) -> str:
        fetched.append(url)
        return ARTICLE_HTML

    result, stats = enrich_empty_summaries(
        articles,
        [_source(detail_summary_selectors=["#articletxt"])],
        timeout=5,
        fetcher=fetch,
        robots_check=_allow,
        sleep=lambda _s: None,
    )
    assert result[0].summary.startswith("첫 문단입니다.")
    assert result[1].summary == "이미 있는 요약"
    assert fetched == ["https://news.example.kr/a/1"]
    assert stats["테스트 뉴스"] == EnrichStats(attempted=1, filled=1)


@pytest.mark.unit
def test_enrich_ignores_sources_without_flag_or_disabled() -> None:
    plain = Source(name="테스트 뉴스", type="rss", url="https://news.example.kr/feed")
    disabled = _source()
    disabled.enabled = False
    for source in (plain, disabled):
        articles = [_article()]
        _result, stats = enrich_empty_summaries(
            articles,
            [source],
            timeout=5,
            fetcher=lambda *_a: pytest.fail("fetched"),
            robots_check=_allow,
        )
        assert articles[0].summary == ""
        assert stats == {}


@pytest.mark.unit
def test_enrich_respects_robots_and_leaves_summary_empty() -> None:
    articles = [_article()]
    _result, stats = enrich_empty_summaries(
        articles,
        [_source()],
        timeout=5,
        fetcher=lambda *_a: pytest.fail("fetched"),
        robots_check=lambda _u, _t: (False, "robots.txt disallows /a/1"),
    )
    assert articles[0].summary == ""
    assert stats["테스트 뉴스"].skipped_robots == 1
    assert stats["테스트 뉴스"].attempted == 0


@pytest.mark.unit
def test_enrich_never_fetches_other_hosts_or_non_http_links() -> None:
    articles = [_article("https://other.example.com/a/1"), _article("ftp://news.example.kr/a/2")]
    _result, stats = enrich_empty_summaries(
        articles,
        [_source()],
        timeout=5,
        fetcher=lambda *_a: pytest.fail("fetched"),
        robots_check=_allow,
    )
    assert all(article.summary == "" for article in articles)
    assert stats["테스트 뉴스"].failed == 2


@pytest.mark.unit
def test_enrich_upgrades_http_to_https_before_robots_and_fetch() -> None:
    articles = [_article("http://news.example.kr/a/1")]
    seen: list[str] = []

    def robots(url: str, _timeout: int) -> tuple[bool, str]:
        seen.append(url)
        return True, "ok"

    def fetch(url: str, _timeout: int) -> str:
        seen.append(url)
        return ARTICLE_HTML

    enrich_empty_summaries(
        articles,
        [_source(detail_upgrade_https=True, detail_summary_selectors=["#articletxt"])],
        timeout=5,
        fetcher=fetch,
        robots_check=robots,
    )
    assert seen == ["https://news.example.kr/a/1", "https://news.example.kr/a/1"]


@pytest.mark.unit
def test_enrich_failures_do_not_invent_text() -> None:
    articles = [_article("https://news.example.kr/a/1"), _article("https://news.example.kr/a/2")]
    pages = {"https://news.example.kr/a/1": None, "https://news.example.kr/a/2": "<html></html>"}
    _result, stats = enrich_empty_summaries(
        articles,
        [_source()],
        timeout=5,
        fetcher=lambda url, _t: pages[url],
        robots_check=_allow,
        sleep=lambda _s: None,
    )
    assert [article.summary for article in articles] == ["", ""]
    assert stats["테스트 뉴스"] == EnrichStats(attempted=2, filled=0, failed=2)


@pytest.mark.unit
def test_enrich_drops_challenge_pages() -> None:
    challenge = (
        "<html><head><meta name='description' "
        "content='Just a moment... Cloudflare security verification required'></head></html>"
    )
    articles = [_article()]
    enrich_empty_summaries(
        articles,
        [_source()],
        timeout=5,
        fetcher=lambda *_a: challenge,
        robots_check=_allow,
    )
    assert articles[0].summary == ""


@pytest.mark.unit
def test_enrich_caps_requests_per_run_and_waits_between_requests() -> None:
    articles = [_article(f"https://news.example.kr/a/{i}") for i in range(5)]
    sleeps: list[float] = []
    fetched: list[str] = []

    def fetch(url: str, _timeout: int) -> str:
        fetched.append(url)
        return ARTICLE_HTML

    enrich_empty_summaries(
        articles,
        [
            _source(
                detail_summary_max_per_run=3,
                detail_min_interval_seconds=2,
                detail_summary_selectors=["#articletxt"],
            )
        ],
        timeout=5,
        fetcher=fetch,
        robots_check=_allow,
        sleep=sleeps.append,
    )
    assert len(fetched) == 3
    assert sleeps == [2.0, 2.0]
    assert [bool(article.summary) for article in articles] == [True, True, True, False, False]


@pytest.mark.unit
def test_format_stats_lists_counts_only() -> None:
    lines = format_stats({"테스트 뉴스": EnrichStats(attempted=3, filled=2, failed=1)})
    assert lines == ["테스트 뉴스: 본문 보강 시도 3건, 성공 2건, 실패 1건, robots 제외 0건"]


@pytest.mark.unit
def test_fetch_public_page_verifies_tls_and_accepts_only_html() -> None:
    ok = MagicMock(status_code=200, headers={"content-type": "text/html; charset=UTF-8"})
    ok.content = b"<html></html>"
    with patch("govradar.detail_summary.requests.get", return_value=ok) as get:
        assert fetch_public_page("https://news.example.kr/a/1", 5) == b"<html></html>"
    assert get.call_args.kwargs["verify"] is True
    assert "GovRadar" in get.call_args.kwargs["headers"]["User-Agent"]

    not_found = MagicMock(status_code=404, headers={"content-type": "text/html"})
    pdf = MagicMock(status_code=200, headers={"content-type": "application/pdf"})
    for response in (not_found, pdf):
        with patch("govradar.detail_summary.requests.get", return_value=response):
            assert fetch_public_page("https://news.example.kr/a/1", 5) is None

    with patch(
        "govradar.detail_summary.requests.get",
        side_effect=requests.exceptions.SSLError("bad cert"),
    ):
        assert fetch_public_page("https://news.example.kr/a/1", 5) is None
