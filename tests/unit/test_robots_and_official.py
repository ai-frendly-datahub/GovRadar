from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from radar_core.models import Source

from govradar.official_collectors import (
    articles_from_api_payload,
    collect_official_sources,
    parse_seoul_notice_html,
)
from govradar.robots import clear_robots_cache, partition_robots_disallowed, url_is_allowed

_GOV_ROBOTS = """User-agent: *
Disallow: /
Allow: /portal/main
Allow: /mw/AA020InfoCappView.do
Allow: /mw/AA210LifeSvcInfo.do
Allow: /yearendpay*
Allow: /portal/ntcItm*
Allow: /portal/orgSite*
Allow: /$
"""

_SEMAS_ROBOTS = """User-agent: *
Disallow: /
Allow : /$
"""

_SEOUL_ROBOTS = """User-agent: *
Disallow: /
Allow: /$
Allow: /main
Allow: /news
"""

_NEWS_SEOUL_ROBOTS = """User-agent: *
Allow: /
Disallow: /gov/files
Disallow: /*?s=
"""

_SEOUL_HTML = """
<table class="sib-lst-type-basic">
  <tbody>
    <tr>
      <td>12114</td>
      <td class="sib-lst-type-basic-subject">
        <a href="javascript:fnTbbsView('468519');">서울시 청년 지원사업 모집</a>
      </td>
      <td>일자리정책과</td>
      <td>2026-10-20</td>
      <td>2026-11-20</td>
    </tr>
  </tbody>
</table>
"""


def setup_function() -> None:
    clear_robots_cache()


def _fetcher(bodies: dict[str, tuple[int | None, str]]):
    seen: list[str] = []

    def fetch(url: str, timeout: int) -> tuple[int | None, str]:
        assert timeout > 0
        seen.append(url)
        assert url.endswith("/robots.txt")
        return bodies.get(url, (404, ""))

    return fetch, seen


def test_gov_and_semas_collection_urls_are_disallowed() -> None:
    fetch, seen = _fetcher(
        {
            "https://www.gov.kr/robots.txt": (200, _GOV_ROBOTS),
            "https://www.semas.or.kr/robots.txt": (200, _SEMAS_ROBOTS),
            "https://www.seoul.go.kr/robots.txt": (200, _SEOUL_ROBOTS),
            "https://news.seoul.go.kr/robots.txt": (200, _NEWS_SEOUL_ROBOTS),
        }
    )
    catalog = "https://www.gov.kr/portal/rcvfvrSvc/svcFind/svcSearchAll"
    board = "https://www.semas.or.kr/web/board/webBoardList.kmdc?bCd=1"
    notice = "https://www.seoul.go.kr/news/news_notice.do?bbsNo=277"
    feed = "https://news.seoul.go.kr/gov/feed"
    assert url_is_allowed(catalog, timeout=5, fetcher=fetch)[0] is False
    assert url_is_allowed("https://www.gov.kr/portal/main", timeout=5, fetcher=fetch)[0] is True
    assert url_is_allowed(board, timeout=5, fetcher=fetch)[0] is False
    assert url_is_allowed("https://www.semas.or.kr/", timeout=5, fetcher=fetch)[0] is True
    assert url_is_allowed(notice, timeout=5, fetcher=fetch)[0] is True
    assert url_is_allowed(feed, timeout=5, fetcher=fetch)[0] is True
    assert all(url.endswith("/robots.txt") for url in seen)


def test_partition_skips_disallowed_source_without_fetching_the_page(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fetch, seen = _fetcher({"https://www.gov.kr/robots.txt": (200, _GOV_ROBOTS)})
    source = Source(
        name="정부24 보조금",
        type="javascript",
        url="https://www.gov.kr/portal/rcvfvrSvc/svcFind/svcSearchAll",
    )
    runnable, errors = partition_robots_disallowed([source], timeout=5, fetcher=fetch)
    assert runnable == []
    assert errors and "skipped_robots" in errors[0]
    assert "Disallow" not in errors[0] or "disallows" in errors[0]
    warning = capsys.readouterr().out
    assert warning.count("::warning title=GovRadar robots::") == 1
    assert seen == ["https://www.gov.kr/robots.txt"]


def test_robots_status_fail_closed_or_open() -> None:
    blocked, _ = url_is_allowed(
        "https://blocked.example/list",
        timeout=5,
        fetcher=lambda _url, _timeout: (403, ""),
    )
    missing, _ = url_is_allowed(
        "https://open.example/list",
        timeout=5,
        fetcher=lambda _url, _timeout: (404, ""),
    )
    down, reason = url_is_allowed(
        "https://down.example/list",
        timeout=5,
        fetcher=lambda _url, _timeout: (None, ""),
    )
    assert blocked is False
    assert missing is True
    assert down is False
    assert "unavailable" in reason


def test_seoul_notice_html_builds_official_detail_url() -> None:
    articles = parse_seoul_notice_html(
        _SEOUL_HTML,
        source_name="서울시 지원사업",
        category="govsupport",
        limit=5,
    )
    assert len(articles) == 1
    article = articles[0]
    assert article.title == "서울시 청년 지원사업 모집"
    assert article.link == "https://www.seoul.go.kr/news/news_notice.do?bbsNo=277&nttNo=468519"
    assert "일자리정책과" in article.summary
    assert "2026-11-20" in article.summary
    assert article.published is not None
    assert article.published.date().isoformat() == "2026-10-20"


def test_api_payloads_map_official_fields_and_reject_errors() -> None:
    kstartup = articles_from_api_payload(
        {
            "data": [
                {
                    "biz_pbanc_nm": "2026 창업지원",
                    "detl_pg_url": "https://www.k-startup.go.kr/web/contents/view.do?pbancSn=1",
                    "pbanc_ntrp_nm": "창업진흥원",
                    "pbanc_rcpt_bgng_dt": "20261001",
                    "aply_trgt_ctnt": "예비창업자",
                }
            ]
        },
        provider="kstartup",
        source_name="K-Startup 지원사업 공고 API",
        category="govsupport",
        limit=5,
    )
    assert kstartup[0].title == "2026 창업지원"
    assert kstartup[0].link.startswith("https://www.k-startup.go.kr/")
    assert kstartup[0].published is not None
    assert kstartup[0].published.date().isoformat() == "2026-10-01"

    bizinfo = articles_from_api_payload(
        {
            "response": {
                "header": {"resultCode": "00"},
                "body": {
                    "items": {
                        "item": {
                            "pblancNm": "소상공인 공고",
                            "pblancUrl": "https://www.bizinfo.go.kr/view.do?pblancId=1",
                            "trgetNm": "소상공인",
                            "creatPnttm": "2026-10-20 09:00:00",
                        }
                    }
                },
            }
        },
        provider="bizinfo",
        source_name="기업마당 지원사업 공고 API",
        category="govsupport",
        limit=5,
    )
    assert bizinfo[0].title == "소상공인 공고"
    assert "소상공인" in bizinfo[0].summary

    subsidy = articles_from_api_payload(
        {
            "data": [
                {
                    "서비스명": "소상공인 정책자금",
                    "상세조회URL": "https://www.gov.kr/portal/rcvfvrSvc/dtlEx/ABC",
                    "지원대상": "소상공인",
                    "소관기관명": "중소벤처기업부",
                }
            ]
        },
        provider="subsidy24",
        source_name="보조금24 공공서비스 API",
        category="govsupport",
        limit=5,
    )
    assert subsidy[0].link.startswith("https://www.gov.kr/")

    with pytest.raises(RuntimeError, match="resultCode 30"):
        articles_from_api_payload(
            {"response": {"header": {"resultCode": "30", "resultMsg": "SERVICE KEY"}}},
            provider="bizinfo",
            source_name="기업마당 지원사업 공고 API",
            category="govsupport",
            limit=5,
        )


def test_missing_api_key_skips_without_request() -> None:
    source = Source(
        name="K-Startup 지원사업 공고 API",
        type="api",
        url="https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01",
        config={"provider": "kstartup", "required_env": "DATA_GO_KR_KSTARTUP_SERVICE_KEY"},
    )
    with (
        patch.dict(os.environ, {"DATA_GO_KR_KSTARTUP_SERVICE_KEY": ""}, clear=False),
        patch(
            "govradar.official_collectors._http_get_text",
            side_effect=AssertionError("fetched"),
        ),
    ):
        articles, errors = collect_official_sources(
            [source],
            category="govsupport",
            limit_per_source=5,
            timeout=5,
        )
    assert articles == []
    assert "skipped_missing_env DATA_GO_KR_KSTARTUP_SERVICE_KEY" in errors[0]


def test_api_error_redacts_service_key() -> None:
    secret = "unit-test-service-key"
    source = Source(
        name="기업마당 지원사업 공고 API",
        type="api",
        url="https://apis.data.go.kr/1421000/bizinfo/pblancBsnsService",
        config={"provider": "bizinfo", "required_env": "DATA_GO_KR_BIZINFO_SERVICE_KEY"},
    )

    def boom(_url: str, *, timeout: int, secret: str, **_kwargs: object) -> str:
        del timeout
        raise RuntimeError(f"request failed serviceKey={secret}")

    with (
        patch.dict(os.environ, {"DATA_GO_KR_BIZINFO_SERVICE_KEY": secret}, clear=False),
        patch("govradar.official_collectors.url_is_allowed", return_value=(True, "ok")),
        patch("govradar.official_collectors._http_get_text", side_effect=boom),
    ):
        articles, errors = collect_official_sources(
            [source],
            category="govsupport",
            limit_per_source=5,
            timeout=5,
        )
    assert articles == []
    assert secret not in errors[0]
    assert "[redacted]" in errors[0]


def test_non_official_api_host_is_refused() -> None:
    source = Source(
        name="elsewhere",
        type="api",
        url="https://evil.example/collect",
        config={"provider": "bizinfo", "required_env": "DATA_GO_KR_BIZINFO_SERVICE_KEY"},
    )
    with (
        patch.dict(os.environ, {"DATA_GO_KR_BIZINFO_SERVICE_KEY": "present"}, clear=False),
        patch("govradar.official_collectors.url_is_allowed", return_value=(True, "ok")),
        patch(
            "govradar.official_collectors._http_get_text",
            side_effect=AssertionError("fetched"),
        ),
    ):
        _articles, errors = collect_official_sources(
            [source],
            category="govsupport",
            limit_per_source=5,
            timeout=5,
        )
    assert "non-official API host" in errors[0]


def test_readme_lists_key_names_only() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    for name in (
        "DATA_GO_KR_KSTARTUP_SERVICE_KEY",
        "DATA_GO_KR_SUBSIDY24_SERVICE_KEY",
        "DATA_GO_KR_BIZINFO_SERVICE_KEY",
    ):
        assert name in readme
    assert "serviceKey=" not in readme
    assert "crtfcKey=" not in readme
