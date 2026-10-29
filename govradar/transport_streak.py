"""Consecutive SSL/connection failures stored in the crawl-health DuckDB.

The counter lives in the same database as ``radar_core.crawl_health``
(``RADAR_CRAWL_HEALTH_DB_PATH``, otherwise ``data/radar_data.duckdb``).
A successful response resets the counter. This module does not change TLS
verification, send traffic through a proxy, or synthesize notices.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast
from urllib.parse import quote, unquote

from radar_core.crawl_health import CrawlHealthStore

from govradar.models import Source

_DEFAULT_HEALTH_DB_PATH = "data/radar_data.duckdb"
_DEFAULT_CONSECUTIVE_TRANSPORT_FAILURES = 3
_DETAIL_LIMIT = 240
_STREAK_TABLE = "official_transport_streak"

TRANSPORT_SKIP_REASONS: dict[str, str] = {
    "ssl": "repeated_ssl_error_from_runner",
    "connection": "repeated_connection_error_from_runner",
}
TRANSPORT_REENABLE_GATES: dict[str, str] = {
    "ssl": (
        "크롤 헬스 DB의 이 소스 연속 SSL 실패 기록을 지운 뒤에만 다시 수집한다. "
        "TLS 검증을 끄거나 프록시·Cloudflare로 우회하지 않는다."
    ),
    "connection": (
        "크롤 헬스 DB의 이 소스 연속 연결 실패 기록을 지운 뒤에만 다시 수집한다. "
        "프록시·Cloudflare로 우회하지 않는다."
    ),
}

_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(authorization|proxy-authorization|cookie|set-cookie|x-api-key|api-key|x-auth-token)\b"
    r"\s*[:=]\s*(?:bearer\s+)?(?:\"[^\"]*\"|'[^']*'|\S+)"
)
_BEARER = re.compile(r"(?i)\bbearer\s+\S+")
_QUERY_SECRET = re.compile(r"(?i)((?:service|crtfc|api)[_-]?key=)(?:\"[^\"]*\"|'[^']*'|[^&\s\"']+)")
_CONNECTION_TOKENS = (
    "timeout",
    "connection",
    "protocol",
    "disconnect",
    "reset",
    "brokenpipe",
    "proxy",
    "chunked",
)


@dataclass(frozen=True)
class TransportStreak:
    source_name: str
    error_kind: str
    streak: int
    last_detail: str


def crawl_health_db_path() -> str:
    """Path of the shared crawl-health DuckDB, including its default."""
    configured = os.environ.get("RADAR_CRAWL_HEALTH_DB_PATH", "").strip()
    return configured or _DEFAULT_HEALTH_DB_PATH


def consecutive_transport_failure_limit(source: Source) -> int:
    """Per-source streak limit. Missing or invalid values use the default of 3."""
    raw = source.config.get(
        "consecutive_transport_failure_limit",
        _DEFAULT_CONSECUTIVE_TRANSPORT_FAILURES,
    )
    parsed = _positive_int(raw)
    if parsed is None:
        return _DEFAULT_CONSECUTIVE_TRANSPORT_FAILURES
    return parsed


def summarize_request_exception(
    exc: BaseException,
    *,
    secret: str = "",
    limit: int = _DETAIL_LIMIT,
) -> str:
    """Exception class plus reason/args, with secrets and header values removed."""
    detail = _cause_detail(exc)
    text = exc.__class__.__name__ if not detail else f"{exc.__class__.__name__}: {detail}"
    text = redact_secret(_strip_sensitive(text), secret)
    capped = limit if limit >= 4 else 4
    if len(text) > capped:
        return text[: capped - 3].rstrip() + "..."
    return text


def transport_error_kind(exc: BaseException) -> str | None:
    """Return ``ssl`` or ``connection`` for transport failures, otherwise None."""
    names = [item.__class__.__name__.lower() for item in _iter_causes(exc)]
    if any("ssl" in name or "certificate" in name for name in names):
        return "ssl"
    if any(any(token in name for token in _CONNECTION_TOKENS) for name in names):
        return "connection"
    return None


def redact_secret(text: str, secret: str) -> str:
    """Replace a secret and its URL-encoded forms. Header values are not added."""
    if not secret:
        return text
    variants = {secret, quote(secret, safe=""), quote(secret, safe="%"), unquote(secret)}
    redacted = text
    for variant in sorted((item for item in variants if item), key=len, reverse=True):
        redacted = redacted.replace(variant, "[redacted]")
    return redacted


class TransportStreakStore:
    """Read and update consecutive transport failures in the crawl-health file."""

    def __init__(self, db_path: str) -> None:
        self._store = CrawlHealthStore(db_path)
        _ = self._store.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {_STREAK_TABLE} (
                source_name VARCHAR PRIMARY KEY,
                error_kind VARCHAR NOT NULL,
                streak INTEGER NOT NULL,
                last_detail VARCHAR,
                updated_at TIMESTAMP
            )
            """)

    def close(self) -> None:
        self._store.close()

    def get(self, source_name: str) -> TransportStreak | None:
        row = cast(
            tuple[object, ...] | None,
            self._store.conn.execute(
                f"""
                SELECT error_kind, streak, last_detail
                FROM {_STREAK_TABLE}
                WHERE source_name = ?
                """,
                [source_name],
            ).fetchone(),
        )
        if row is None:
            return None
        return TransportStreak(
            source_name=source_name,
            error_kind=str(row[0]),
            streak=int(str(row[1])),
            last_detail=str(row[2] or ""),
        )

    def record_failure(self, source_name: str, error_kind: str, detail: str) -> int:
        """Increment the streak when the kind matches. A new kind starts at 1."""
        current = self.get(source_name)
        streak = (
            current.streak + 1 if current is not None and current.error_kind == error_kind else 1
        )
        _ = self._store.conn.execute(
            f"""
            INSERT INTO {_STREAK_TABLE} (
                source_name, error_kind, streak, last_detail, updated_at
            )
            VALUES (?, ?, ?, ?, now())
            ON CONFLICT(source_name) DO UPDATE SET
                error_kind = excluded.error_kind,
                streak = excluded.streak,
                last_detail = excluded.last_detail,
                updated_at = now()
            """,
            [source_name, error_kind, streak, detail],
        )
        return streak

    def record_success(self, source_name: str) -> None:
        _ = self._store.conn.execute(
            f"DELETE FROM {_STREAK_TABLE} WHERE source_name = ?",
            [source_name],
        )


def _positive_int(raw: object) -> int | None:
    if isinstance(raw, bool) or isinstance(raw, float):
        return None
    if isinstance(raw, int):
        parsed = raw
    elif isinstance(raw, str) and raw.strip().isdigit():
        parsed = int(raw.strip())
    else:
        return None
    if parsed < 1:
        return None
    return parsed


def _strip_sensitive(text: str) -> str:
    stripped = _SENSITIVE_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[redacted]", text)
    stripped = _BEARER.sub("Bearer [redacted]", stripped)
    return _QUERY_SECRET.sub(r"\1[redacted]", stripped)


def _cause_detail(exc: BaseException) -> str:
    parts: list[str] = []
    for item in _iter_causes(exc):
        if item is exc:
            continue
        arg_text = _plain_args(item.args)
        piece = (
            f"{item.__class__.__name__} {arg_text}".strip() if arg_text else item.__class__.__name__
        )
        if piece not in parts:
            parts.append(piece)
    outer = _plain_args(exc.args)
    if outer and outer not in " ".join(parts):
        parts.append(outer)
    return " | ".join(parts)


def _iter_causes(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen and len(chain) < 6:
        seen.add(id(current))
        chain.append(current)
        reason = getattr(current, "reason", None)
        if isinstance(reason, BaseException) and id(reason) not in seen:
            current = reason
            continue
        cause = current.__cause__
        if isinstance(cause, BaseException) and id(cause) not in seen:
            current = cause
            continue
        context = current.__context__
        if (
            isinstance(context, BaseException)
            and not current.__suppress_context__
            and id(context) not in seen
        ):
            current = context
            continue
        break
    return chain


def _plain_args(args: tuple[object, ...] | object) -> str:
    if not isinstance(args, tuple):
        return ""
    bits: list[str] = []
    for arg in args:
        if isinstance(arg, bool):
            continue
        if isinstance(arg, str):
            cleaned = " ".join(arg.split())
            if cleaned:
                bits.append(cleaned)
            continue
        if isinstance(arg, int):
            bits.append(str(arg))
            continue
        if isinstance(arg, BaseException):
            nested = _plain_args(arg.args)
            bits.append(f"{arg.__class__.__name__} {nested}".strip())
            continue
        if isinstance(arg, Mapping):
            continue
    return " ".join(bits).strip()
