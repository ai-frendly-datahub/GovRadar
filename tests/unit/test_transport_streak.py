from __future__ import annotations

import ssl
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from govradar.models import Article, CategoryConfig, Source
from govradar.official_collectors import collect_official_sources
from govradar.quality_report import build_quality_report
from govradar.transport_streak import (
    TransportStreakStore,
    consecutive_transport_failure_limit,
    crawl_health_db_path,
    summarize_request_exception,
    transport_error_kind,
)

_SEOUL_URL = "https://www.seoul.go.kr/news/news_notice.do?bbsNo=277"
_SEOUL_HTML = """
<table class="sib-lst-type-basic">
  <tbody>
    <tr>
      <td>12114</td>
      <td><a href="javascript:fnTbbsView('468519');">서울시 청년 지원사업 모집</a></td>
      <td>일자리정책과</td>
      <td>2026-10-20</td>
      <td>2026-11-20</td>
    </tr>
  </tbody>
</table>
"""
_SECRET = "unit-test-service-key"
_HEADER_TOKEN = "super-secret-token"


def _seoul_source(*, limit: int = 3, name: str = "서울시 지원사업") -> Source:
    return Source(
        name=name,
        type="public_page",
        url=_SEOUL_URL,
        config={
            "provider": "seoul_notice",
            "detail_url_template": "https://www.seoul.go.kr/news/news_notice.do?bbsNo=277&nttNo={id}",
            "event_model": "application_deadline",
            "consecutive_transport_failure_limit": limit,
        },
    )


def _ssl_error() -> requests.exceptions.SSLError:
    inner = ssl.SSLError(
        8, "[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol"
    )
    outer = requests.exceptions.SSLError(
        "HTTPSConnectionPool(host='www.seoul.go.kr', port=443): Max retries exceeded "
        f"serviceKey={_SECRET} Authorization: Bearer {_HEADER_TOKEN}"
    )
    outer.reason = inner
    return outer


def _response(status: int, text: str = "") -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = text.encode()
    response.url = _SEOUL_URL
    return response


def _collect(source: Source) -> tuple[list[Article], list[str]]:
    with patch("govradar.official_collectors.url_is_allowed", return_value=(True, "ok")):
        return collect_official_sources(
            [source],
            category="govsupport",
            limit_per_source=5,
            timeout=5,
        )


def test_transport_failure_limit_defaults_to_three() -> None:
    source = Source(name="plain", type="public_page", url="https://example.com/notice")
    assert consecutive_transport_failure_limit(source) == 3
    source.config["consecutive_transport_failure_limit"] = 0
    assert consecutive_transport_failure_limit(source) == 3
    source.config["consecutive_transport_failure_limit"] = "2"
    assert consecutive_transport_failure_limit(source) == 2


def test_request_summary_keeps_ssl_cause_and_drops_secrets() -> None:
    exc = _ssl_error()
    exc.request = requests.Request(headers={"Cookie": f"session={_HEADER_TOKEN}"})  # type: ignore[attr-defined]
    summary = summarize_request_exception(exc, secret=_SECRET, limit=240)

    assert summary.startswith("SSLError:")
    assert "UNEXPECTED_EOF_WHILE_READING" in summary
    assert "SSLError" in summary
    assert _SECRET not in summary
    assert _HEADER_TOKEN not in summary
    assert "Bearer [redacted]" in summary or "Authorization=[redacted]" in summary
    assert len(summary) <= 240
    assert transport_error_kind(exc) == "ssl"
    assert transport_error_kind(requests.exceptions.ConnectTimeout("timed out")) == "connection"
    assert transport_error_kind(requests.exceptions.TooManyRedirects("redirects")) is None

    long_summary = summarize_request_exception(
        requests.exceptions.SSLError("x" * 500),
        limit=240,
    )
    assert len(long_summary) <= 240
    assert long_summary.endswith("...")


def test_ssl_failure_records_detail_in_quality_errors(capsys: pytest.CaptureFixture[str]) -> None:
    source = _seoul_source()
    with patch("govradar.official_collectors.requests.get", side_effect=_ssl_error()) as get:
        articles, errors = _collect(source)

    assert articles == []
    assert get.call_count == 1
    assert get.call_args.kwargs["verify"] is True
    assert "request failed: SSLError:" in errors[0]
    assert "UNEXPECTED_EOF_WHILE_READING" in errors[0]
    assert _SECRET not in errors[0]
    assert _HEADER_TOKEN not in errors[0]
    logged = capsys.readouterr().out
    assert "UNEXPECTED_EOF_WHILE_READING" in logged
    assert _SECRET not in logged
    assert _HEADER_TOKEN not in logged

    report = build_quality_report(
        category=CategoryConfig(
            category_name="govsupport",
            display_name="Gov Support",
            sources=[source],
            entities=[],
        ),
        articles=[],
        errors=errors,
    )
    assert any("UNEXPECTED_EOF_WHILE_READING" in error for error in report["errors"])
    row = report["sources"][0]
    assert row["errors"][0] == errors[0]
    assert "Cookie" not in errors[0]


def test_repeated_ssl_failure_skips_without_another_request(
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _seoul_source(limit=3)
    with patch("govradar.official_collectors.requests.get", side_effect=_ssl_error()) as get:
        for _ in range(3):
            _articles, errors = _collect(source)
            assert "UNEXPECTED_EOF_WHILE_READING" in errors[0]
        assert get.call_count == 3
        assert source.config["skip_reason"] == "repeated_ssl_error_from_runner"
        assert "TLS" in str(source.config["reenable_gate"])

        allowed = patch("govradar.official_collectors.url_is_allowed", return_value=(True, "ok"))
        with allowed as robots:
            articles, skipped = collect_official_sources(
                [source],
                category="govsupport",
                limit_per_source=5,
                timeout=5,
            )

    assert articles == []
    assert get.call_count == 3
    assert robots.call_count == 0
    assert skipped == ["서울시 지원사업: skipped_transport repeated_ssl_error_from_runner"]
    assert source.config["skip_reason"] == "repeated_ssl_error_from_runner"
    warning = capsys.readouterr().out
    assert "::warning title=GovRadar transport::" in warning
    assert _SECRET not in warning

    persisted = TransportStreakStore(crawl_health_db_path())
    try:
        state = persisted.get(source.name)
        assert persisted.record_failure("다른 소스", "ssl", "SSLError") == 1
        assert persisted.record_failure("다른 소스", "ssl", "SSLError") == 2
        assert persisted.record_failure("다른 소스", "connection", "ConnectionError") == 1
        persisted.record_success("다른 소스")
        assert persisted.get("다른 소스") is None
    finally:
        persisted.close()
    assert state is not None
    assert state.error_kind == "ssl"
    assert state.streak == 3
    assert _SECRET not in state.last_detail

    report = build_quality_report(
        category=CategoryConfig(
            category_name="govsupport",
            display_name="Gov Support",
            sources=[source],
            entities=[],
        ),
        articles=[],
        errors=skipped,
    )
    row = report["sources"][0]
    assert row["skip_reason"] == "repeated_ssl_error_from_runner"
    assert "프록시" in str(row["reenable_gate"])
    assert report["errors"] == skipped


def test_success_resets_ssl_streak_and_connection_kind_is_separate() -> None:
    source = _seoul_source(limit=3)
    with patch("govradar.official_collectors.requests.get", side_effect=_ssl_error()):
        _collect(source)
        _collect(source)
    with patch(
        "govradar.official_collectors.requests.get",
        return_value=_response(200, _SEOUL_HTML),
    ) as get:
        articles, errors = _collect(source)
    assert get.call_args.kwargs["verify"] is True
    assert articles and articles[0].title == "서울시 청년 지원사업 모집"
    assert errors == []
    assert "skip_reason" not in source.config

    with patch("govradar.official_collectors.requests.get", side_effect=_ssl_error()) as get:
        _collect(source)
        _collect(source)
        articles, errors = _collect(source)
    assert get.call_count == 3
    assert "UNEXPECTED_EOF_WHILE_READING" in errors[0]
    assert articles == []

    connection_source = _seoul_source(limit=2, name="연결 실패 소스")
    connection = requests.exceptions.ConnectionError("Remote end closed connection")
    with patch("govradar.official_collectors.requests.get", side_effect=connection) as get:
        _articles, errors = _collect(connection_source)
        assert "ConnectionError" in errors[0]
        assert "request failed:" in errors[0]
        _articles, errors = _collect(connection_source)
        assert get.call_count == 2
        assert "skipped_transport" not in errors[0]
        _articles, skipped = _collect(connection_source)
    assert get.call_count == 2
    assert skipped == ["연결 실패 소스: skipped_transport repeated_connection_error_from_runner"]
    assert connection_source.config["skip_reason"] == "repeated_connection_error_from_runner"


def test_http_response_resets_streak_and_store_outage_still_reports_detail() -> None:
    source = _seoul_source(limit=2)
    with patch("govradar.official_collectors.requests.get", side_effect=_ssl_error()):
        _collect(source)
    with patch(
        "govradar.official_collectors.requests.get",
        return_value=_response(503, "unavailable"),
    ):
        _articles, errors = _collect(source)
    assert errors == ["서울시 지원사업: HTTP 503"]
    with patch("govradar.official_collectors.requests.get", side_effect=_ssl_error()) as get:
        _collect(source)
        articles, errors = _collect(source)
    assert get.call_count == 2
    assert articles == []
    assert "skipped_transport" not in errors[0]

    with (
        patch(
            "govradar.official_collectors.TransportStreakStore",
            side_effect=OSError("crawl health unavailable"),
        ),
        patch("govradar.official_collectors.requests.get", side_effect=_ssl_error()) as get,
    ):
        articles, errors = _collect(source)
    assert articles == []
    assert get.call_count == 1
    assert "UNEXPECTED_EOF_WHILE_READING" in errors[0]


def test_collectors_keep_tls_verification_enabled() -> None:
    official = Path("govradar/official_collectors.py").read_text(encoding="utf-8")
    streak = Path("govradar/transport_streak.py").read_text(encoding="utf-8")
    robots = Path("govradar/robots.py").read_text(encoding="utf-8")
    policy = Path("config/categories/govsupport.yaml").read_text(encoding="utf-8")
    assert "verify=False" not in official
    assert "verify=False" not in streak
    assert "verify=False" not in robots
    assert "verify=True" in official
    assert "https://news.seoul.go.kr/gov/feed" in policy
    seoul_policy = policy.split("- name: 서울시 정책뉴스", 1)[1].split("- name:", 1)[0]
    assert "type: rss" in seoul_policy
    assert "repeated_ssl_error_from_runner" not in seoul_policy
