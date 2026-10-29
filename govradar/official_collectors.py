"""Official public-page and data.go.kr collectors.

Keyed APIs are skipped when the named environment variable is unset. The key
value is never written to config, logs, or exceptions. Responses are parsed
only; this module does not invent notices.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, urlencode, urlparse
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import requests
import structlog
from bs4 import BeautifulSoup

from govradar.collection_contract import GOVRADAR_USER_AGENT, missing_required_env
from govradar.models import Article, Source
from govradar.robots import url_is_allowed
from govradar.transport_streak import (
    TRANSPORT_REENABLE_GATES,
    TRANSPORT_SKIP_REASONS,
    TransportStreakStore,
    consecutive_transport_failure_limit,
    crawl_health_db_path,
    redact_secret,
    summarize_request_exception,
    transport_error_kind,
)

logger = structlog.get_logger(__name__)

_API_HOSTS = frozenset({"apis.data.go.kr", "api.odcloud.kr"})
_SEOUL_HOST = "www.seoul.go.kr"
_DETAIL_URL = "https://www.seoul.go.kr/news/news_notice.do?bbsNo=277&nttNo={id}"
_VIEW_ID = re.compile(r"fnTbbsView\('(\d+)'\)")
_DATE = re.compile(r"(\d{4})[-./]?(\d{2})[-./]?(\d{2})")
_TAG = re.compile(r"<[^>]+>")
_OFFICIAL_TYPES = frozenset({"api", "public_page"})


class OfficialRequestError(RuntimeError):
    """HTTP transport failure. ``kind`` is ``ssl``, ``connection``, or None."""

    def __init__(self, message: str, *, kind: str | None) -> None:
        super().__init__(message)
        self.kind = kind


def is_official_source(source: Source) -> bool:
    return source.type.lower() in _OFFICIAL_TYPES


def collect_official_sources(
    sources: list[Source],
    *,
    category: str,
    limit_per_source: int,
    timeout: int,
) -> tuple[list[Article], list[str]]:
    """Collect enabled official page/API sources. Missing keys are skipped."""
    articles: list[Article] = []
    errors: list[str] = []
    streak: TransportStreakStore | None = None
    try:
        for source in sources:
            if not source.enabled or not is_official_source(source):
                continue
            try:
                missing = missing_required_env(source)
            except ValueError:
                errors.append(f"{source.name}: required_env must be an environment variable name")
                continue
            if missing:
                errors.append(f"{source.name}: skipped_missing_env {', '.join(missing)}")
                continue
            if streak is None:
                streak = _open_transport_streak_store()
            if _skip_repeated_transport_failure(source, streak, errors):
                continue
            secret = _secret_value(source)
            try:
                batch = _collect_one(
                    source,
                    category=category,
                    limit=max(1, limit_per_source),
                    timeout=timeout,
                    secret=secret,
                    streak=streak,
                )
            except OfficialRequestError as exc:
                message = _redact(str(exc), secret)
                errors.append(f"{source.name}: {message}")
                _note_transport_failure(source, streak, exc.kind, message)
                continue
            except RuntimeError as exc:
                errors.append(f"{source.name}: {_redact(str(exc), secret)}")
                continue
            articles.extend(batch)
            if not batch:
                errors.append(f"{source.name}: official source returned no notices")
    finally:
        if streak is not None:
            streak.close()
    return articles, errors


def parse_seoul_notice_html(
    html: str,
    *,
    source_name: str,
    category: str,
    limit: int,
    detail_url_template: str = _DETAIL_URL,
) -> list[Article]:
    """Parse the server-rendered 서울시 고시공고 table."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.sib-lst-type-basic")
    if table is None:
        raise RuntimeError("서울시 고시공고 목록 표를 찾지 못했다")
    articles: list[Article] = []
    for row in table.select("tbody tr"):
        if len(articles) >= limit:
            break
        anchor = row.select_one("a[href*='fnTbbsView']")
        if anchor is None:
            continue
        href = str(anchor.get("href") or "")
        matched = _VIEW_ID.search(href)
        if matched is None:
            continue
        notice_id = matched.group(1)
        title = " ".join(anchor.get_text(" ", strip=True).split())
        if not title:
            continue
        department, published_text, deadline = _seoul_row_fields(row)
        link = detail_url_template.format(id=notice_id)
        if urlparse(link).hostname != _SEOUL_HOST:
            raise RuntimeError("서울시 상세 URL이 공식 호스트가 아니다")
        summary_parts = [
            part
            for part in (
                f"담당부서: {department}" if department else "",
                f"마감일: {deadline}" if deadline else "",
            )
            if part
        ]
        articles.append(
            Article(
                title=title,
                link=link,
                summary=". ".join(summary_parts),
                published=_parse_date(published_text),
                source=source_name,
                category=category,
            )
        )
    if not articles:
        raise RuntimeError("서울시 고시공고 행에서 fnTbbsView 번호를 찾지 못했다")
    return articles


def articles_from_api_payload(
    payload: object,
    *,
    provider: str,
    source_name: str,
    category: str,
    limit: int,
) -> list[Article]:
    """Map one official API document to articles. Unknown shapes yield nothing."""
    error = _payload_error(payload)
    if error:
        raise RuntimeError(error)
    rows = _item_rows(payload)
    articles: list[Article] = []
    for row in rows:
        if len(articles) >= limit:
            break
        article = _article_from_row(
            row,
            provider=provider,
            source_name=source_name,
            category=category,
        )
        if article is not None:
            articles.append(article)
    return articles


def _collect_one(
    source: Source,
    *,
    category: str,
    limit: int,
    timeout: int,
    secret: str,
    streak: TransportStreakStore | None,
) -> list[Article]:
    allowed, reason = url_is_allowed(source.url, timeout=timeout)
    if not allowed:
        raise RuntimeError(reason)
    provider = str(source.config.get("provider") or "").strip().lower()
    if source.type.lower() == "public_page" or provider == "seoul_notice":
        body = _fetch_official_text(
            source,
            source.url,
            timeout=timeout,
            secret="",
            streak=streak,
        )
        template = str(source.config.get("detail_url_template") or _DETAIL_URL)
        return parse_seoul_notice_html(
            body,
            source_name=source.name,
            category=category,
            limit=limit,
            detail_url_template=template,
        )
    if provider not in {"kstartup", "subsidy24", "bizinfo"}:
        raise RuntimeError(f"unsupported official provider '{provider}'")
    if not secret:
        raise RuntimeError("required service key is empty")
    _require_official_host(source.url)
    params = _query_params(provider, limit)
    url = _url_with_service_key(source.url, secret, params)
    body = _fetch_official_text(
        source,
        url,
        timeout=timeout,
        secret=secret,
        streak=streak,
    )
    payload = _decode_payload(body, secret)
    return articles_from_api_payload(
        payload,
        provider=provider,
        source_name=source.name,
        category=category,
        limit=limit,
    )


def _query_params(provider: str, limit: int) -> dict[str, str]:
    size = str(min(max(limit, 1), 100))
    if provider == "kstartup":
        return {"page": "1", "perPage": size, "returnType": "json"}
    if provider == "subsidy24":
        return {"page": "1", "perPage": size, "returnType": "json"}
    return {"pageNo": "1", "numOfRows": size, "dataType": "json"}


def _url_with_service_key(base: str, secret: str, params: Mapping[str, str]) -> str:
    encoded_key = quote(secret, safe="%")
    query = urlencode(list(params.items()))
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}serviceKey={encoded_key}&{query}"


def _require_official_host(url: str) -> None:
    host = urlparse(url).hostname or ""
    if host not in _API_HOSTS:
        raise RuntimeError(f"refusing non-official API host {host}")


def _fetch_official_text(
    source: Source,
    url: str,
    *,
    timeout: int,
    secret: str,
    streak: TransportStreakStore | None,
) -> str:
    try:
        body = _http_get_text(url, timeout=timeout, secret=secret, source_name=source.name)
    except OfficialRequestError:
        raise
    except RuntimeError as exc:
        if str(exc).startswith("HTTP "):
            _remember_transport_success(source, streak)
        raise
    _remember_transport_success(source, streak)
    return body


def _http_get_text(url: str, *, timeout: int, secret: str, source_name: str = "") -> str:
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": GOVRADAR_USER_AGENT,
                "Accept": "application/json, application/xml, text/xml, text/html, */*",
            },
            timeout=timeout,
            verify=True,
        )
    except requests.RequestException as exc:
        summary = summarize_request_exception(exc, secret=secret)
        message = f"request failed: {summary}"
        kind = transport_error_kind(exc)
        logger.warning(
            "official_request_failed",
            source=source_name,
            error=message,
            error_kind=kind,
        )
        print(f"[GovRadar] {source_name}: {message}", flush=True)
        raise OfficialRequestError(message, kind=kind) from None
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}")
    return response.text or ""


def _decode_payload(body: str, secret: str) -> object:
    stripped = body.lstrip()
    if stripped.startswith("<"):
        return _xml_to_payload(stripped, secret)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise RuntimeError(_redact(f"invalid JSON: {exc.msg}", secret)) from None


def _xml_to_payload(body: str, secret: str) -> dict[str, object]:
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError as exc:
        raise RuntimeError(_redact(f"invalid XML: {exc}", secret)) from None
    items: list[dict[str, str]] = []
    header: dict[str, str] = {}
    for element in root.iter():
        tag = _local_name(element)
        if tag == "item":
            row = {_local_name(child): (child.text or "").strip() for child in list(element)}
            if row:
                items.append(row)
        elif tag in {"resultCode", "resultMsg", "returnReasonCode", "returnAuthMsg"}:
            header[tag] = (element.text or "").strip()
    return {"header": header, "items": items}


def _payload_error(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    header = payload.get("header")
    response = payload.get("response")
    if isinstance(response, dict) and isinstance(response.get("header"), dict):
        header = response.get("header")
    if isinstance(header, dict):
        code = str(header.get("resultCode") or header.get("returnReasonCode") or "").strip()
        if code and code not in {"00", "0"}:
            message = str(header.get("resultMsg") or header.get("returnAuthMsg") or "api error")
            return f"resultCode {code} {message}"[:200]
    return ""


def _item_rows(payload: object) -> list[Mapping[str, object]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if isinstance(data, list):
        return [row for row in data if isinstance(row, Mapping)]
    items = payload.get("items")
    if isinstance(items, list):
        return [row for row in items if isinstance(row, Mapping)]
    if isinstance(items, dict) and "item" in items:
        return _mapping_list(items.get("item"))
    response = payload.get("response")
    body = response.get("body") if isinstance(response, dict) else None
    if isinstance(body, dict):
        nested = body.get("items")
        if isinstance(nested, dict) and "item" in nested:
            return _mapping_list(nested.get("item"))
        if isinstance(nested, list):
            return [row for row in nested if isinstance(row, Mapping)]
    return []


def _mapping_list(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _article_from_row(
    row: Mapping[str, object],
    *,
    provider: str,
    source_name: str,
    category: str,
) -> Article | None:
    if provider == "kstartup":
        title = _field(row, "biz_pbanc_nm")
        link = _field(row, "detl_pg_url", "biz_aply_url", "biz_gdnc_url")
        summary = _join_summary(
            [
                _labeled("기관", _field(row, "pbanc_ntrp_nm", "sprv_inst")),
                _labeled("지역", _field(row, "supt_regin")),
                _labeled("대상", _field(row, "aply_trgt_ctnt", "aply_trgt")),
                _labeled(
                    "접수",
                    _period(_field(row, "pbanc_rcpt_bgng_dt"), _field(row, "pbanc_rcpt_end_dt")),
                ),
            ]
        )
        published = _parse_date(_field(row, "pbanc_rcpt_bgng_dt"))
    elif provider == "subsidy24":
        title = _field(row, "서비스명")
        link = _field(row, "상세조회URL", "온라인신청사이트URL")
        summary = _join_summary(
            [
                _field(row, "서비스목적요약"),
                _labeled("대상", _field(row, "지원대상")),
                _labeled("내용", _field(row, "지원내용")),
                _labeled("기한", _field(row, "신청기한")),
                _labeled("기관", _field(row, "소관기관명")),
            ]
        )
        published = _parse_date(_field(row, "수정일시", "등록일시"))
    else:
        title = _field(row, "pblancNm", "title")
        link = _field(row, "pblancUrl", "link")
        summary = _join_summary(
            [
                _plain(_field(row, "bsnsSumryCn", "description")),
                _labeled("대상", _field(row, "trgetNm")),
                _labeled("기간", _field(row, "reqstBeginEndDe", "reqstDt")),
                _labeled("기관", _field(row, "jrsdInsttNm", "author")),
            ]
        )
        published = _parse_date(_field(row, "creatPnttm", "pubDate"))
    if not title or not link or urlparse(link).scheme not in {"http", "https"}:
        return None
    return Article(
        title=title,
        link=link,
        summary=summary[:800],
        published=published,
        source=source_name,
        category=category,
    )


def _seoul_row_fields(row: Any) -> tuple[str, str, str]:
    department = ""
    dates: list[str] = []
    cells = row.find_all("td") if hasattr(row, "find_all") else []
    for cell in cells:
        text = " ".join(cell.get_text(" ", strip=True).split())
        if not text or cell.find("a") is not None:
            continue
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            dates.append(text)
            continue
        if re.fullmatch(r"\d+", text):
            continue
        if not department:
            department = text
    published = dates[0] if dates else ""
    deadline = dates[1] if len(dates) > 1 else ""
    return department, published, deadline


def _secret_value(source: Source) -> str:
    configured = source.config.get("required_env", source.config.get("required_env_vars"))
    names: list[str] = []
    if isinstance(configured, str):
        names = [configured]
    elif isinstance(configured, list):
        names = [str(item) for item in configured]
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _field(row: Mapping[str, object], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return _plain(value)
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
    return ""


def _plain(value: str) -> str:
    text = _TAG.sub(" ", value)
    return " ".join(text.split())


def _labeled(label: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    return f"{label}: {cleaned}"


def _period(start: str, end: str) -> str:
    if start and end:
        return f"{start} ~ {end}"
    return start or end


def _join_summary(parts: list[str]) -> str:
    return ". ".join(part for part in parts if part)


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    matched = _DATE.search(value)
    if matched is None:
        return None
    year, month, day = (int(matched.group(index)) for index in range(1, 4))
    try:
        return datetime(year, month, day, tzinfo=UTC)
    except ValueError:
        return None


def _local_name(element: Element) -> str:
    return element.tag.split("}", 1)[-1]


def _redact(text: str, secret: str) -> str:
    return redact_secret(text, secret)


def _open_transport_streak_store() -> TransportStreakStore | None:
    try:
        return TransportStreakStore(crawl_health_db_path())
    except Exception as exc:
        logger.warning("transport_streak_unavailable", error_type=type(exc).__name__)
        return None


def _skip_repeated_transport_failure(
    source: Source,
    streak: TransportStreakStore | None,
    errors: list[str],
) -> bool:
    if streak is None:
        return False
    try:
        state = streak.get(source.name)
    except Exception as exc:
        logger.warning(
            "transport_streak_read_failed", source=source.name, error_type=type(exc).__name__
        )
        return False
    if state is None or state.error_kind not in TRANSPORT_SKIP_REASONS:
        return False
    if state.streak < consecutive_transport_failure_limit(source):
        return False
    reason = _assign_transport_gate(source, state.error_kind)
    logger.warning(
        "official_transport_skipped",
        source=source.name,
        skip_reason=reason,
        reenable_gate=source.config.get("reenable_gate"),
        consecutive_failures=state.streak,
        last_error=state.last_detail,
    )
    print(
        f"[GovRadar] {source.name}: skipped_transport {reason} "
        f"consecutive={state.streak} last={state.last_detail}",
        flush=True,
    )
    print(f"::warning title=GovRadar transport::{source.name} skipped; {reason}", flush=True)
    errors.append(f"{source.name}: skipped_transport {reason}")
    return True


def _note_transport_failure(
    source: Source,
    streak: TransportStreakStore | None,
    kind: str | None,
    message: str,
) -> None:
    if streak is None or kind is None or kind not in TRANSPORT_SKIP_REASONS:
        return
    try:
        count = streak.record_failure(source.name, kind, message)
    except Exception as exc:
        logger.warning(
            "transport_streak_update_failed",
            source=source.name,
            error_type=type(exc).__name__,
        )
        return
    if count >= consecutive_transport_failure_limit(source):
        reason = _assign_transport_gate(source, kind)
        logger.warning(
            "official_transport_threshold_reached",
            source=source.name,
            skip_reason=reason,
            reenable_gate=source.config.get("reenable_gate"),
            consecutive_failures=count,
            last_error=message,
        )


def _remember_transport_success(source: Source, streak: TransportStreakStore | None) -> None:
    if streak is not None:
        try:
            streak.record_success(source.name)
        except Exception as exc:
            logger.warning(
                "transport_streak_update_failed",
                source=source.name,
                error_type=type(exc).__name__,
            )
    _clear_transport_skip(source)


def _assign_transport_gate(source: Source, kind: str) -> str:
    reason = TRANSPORT_SKIP_REASONS[kind]
    source.config["skip_reason"] = reason
    source.config["reenable_gate"] = TRANSPORT_REENABLE_GATES[kind]
    return reason


def _clear_transport_skip(source: Source) -> None:
    reason = source.config.get("skip_reason")
    if reason not in TRANSPORT_SKIP_REASONS.values():
        return
    source.config.pop("skip_reason", None)
    if source.config.get("reenable_gate") in TRANSPORT_REENABLE_GATES.values():
        source.config.pop("reenable_gate", None)
