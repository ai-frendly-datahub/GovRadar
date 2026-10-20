"""robots.txt guard for GovRadar collection.

radar-core's collector does not read robots.txt. This module applies RFC 9309
longest-match rules before any source URL is fetched. urllib.robotparser is not
used: it keeps the first matching rule, so a leading ``Disallow: /`` hides later
``Allow`` lines.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

import requests

from govradar.collection_contract import GOVRADAR_USER_AGENT
from govradar.models import Source

RobotsFetcher = Callable[[str, int], tuple[int | None, str]]

_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, tuple[list[_Rule], str]] = {}


@dataclass(frozen=True)
class _Rule:
    allow: bool
    path: str


@dataclass(frozen=True)
class _Group:
    agents: tuple[str, ...]
    rules: tuple[_Rule, ...]


def partition_robots_disallowed(
    sources: list[Source],
    *,
    timeout: int,
    user_agent: str = GOVRADAR_USER_AGENT,
    fetcher: RobotsFetcher | None = None,
) -> tuple[list[Source], list[str]]:
    """Drop enabled sources whose URL is disallowed. Disabled sources stay."""
    runnable: list[Source] = []
    errors: list[str] = []
    fetch = fetcher or fetch_robots_txt
    for source in sources:
        if not source.enabled:
            runnable.append(source)
            continue
        allowed, reason = url_is_allowed(
            source.url,
            timeout=timeout,
            user_agent=user_agent,
            fetcher=fetch,
        )
        if allowed:
            runnable.append(source)
            continue
        message = f"{source.name} skipped; {reason}"
        print(f"::warning title=GovRadar robots::{message}", flush=True)
        errors.append(f"{source.name}: skipped_robots {reason}")
    return runnable, errors


def url_is_allowed(
    url: str,
    *,
    timeout: int,
    user_agent: str = GOVRADAR_USER_AGENT,
    fetcher: RobotsFetcher | None = None,
) -> tuple[bool, str]:
    """Return whether ``url`` may be fetched under that host's robots.txt."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "URL is not an http(s) source"
    origin = f"{parsed.scheme}://{parsed.netloc}"
    path = unquote(parsed.path or "/") or "/"
    rules, status_reason = _rules_for_origin(
        origin,
        timeout=timeout,
        user_agent=user_agent,
        fetcher=fetcher or fetch_robots_txt,
    )
    if status_reason:
        return False, status_reason
    if _path_allowed(rules, path, user_agent):
        return True, "robots.txt allows this URL"
    return False, f"robots.txt disallows {path}"


def fetch_robots_txt(robots_url: str, timeout: int) -> tuple[int | None, str]:
    """GET robots.txt with TLS verification. Never raises."""
    try:
        response = requests.get(
            robots_url,
            headers={
                "User-Agent": GOVRADAR_USER_AGENT,
                "Accept": "text/plain, */*",
            },
            timeout=timeout,
            verify=True,
        )
    except requests.RequestException:
        return None, ""
    return response.status_code, response.text or ""


def _rules_for_origin(
    origin: str,
    *,
    timeout: int,
    user_agent: str,
    fetcher: RobotsFetcher,
) -> tuple[list[_Rule], str]:
    cache_key = f"{user_agent}\n{origin}"
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key) if fetcher is fetch_robots_txt else None
    if cached is not None:
        return cached

    status, body = fetcher(f"{origin}/robots.txt", timeout)
    rules, reason = _rules_from_response(status, body, user_agent)
    if fetcher is fetch_robots_txt and not reason.startswith("robots.txt unavailable"):
        with _CACHE_LOCK:
            _CACHE[cache_key] = (rules, reason)
    return rules, reason


def _rules_from_response(
    status: int | None,
    body: str,
    user_agent: str,
) -> tuple[list[_Rule], str]:
    """Map an HTTP result to rules. A non-empty reason means do not fetch."""
    if status is None or 500 <= status <= 599:
        return [], "robots.txt unavailable; not fetching until it can be read"
    if status in {401, 403, 429}:
        return [], f"robots.txt HTTP {status}; not fetching"
    if status == 404 or 400 <= status <= 499:
        return [], ""
    if status < 200 or status >= 300:
        return [], f"robots.txt HTTP {status}; not fetching"
    groups = _parse_groups(body)
    return _merged_rules(groups, user_agent), ""


def _parse_groups(text: str) -> list[_Group]:
    groups: list[_Group] = []
    agents: list[str] = []
    rules: list[_Rule] = []
    started_rules = False

    def flush() -> None:
        nonlocal agents, rules, started_rules
        if agents or rules:
            groups.append(_Group(tuple(agents or ["*"]), tuple(rules)))
        agents = []
        rules = []
        started_rules = False

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = line.split(":", 1)
        field_name = field.strip().lower()
        field_value = value.strip()
        if field_name == "user-agent":
            if started_rules:
                flush()
            agents.append(field_value.lower())
            continue
        if field_name not in {"allow", "disallow"}:
            continue
        if not agents:
            agents.append("*")
        rules.append(_Rule(allow=field_name == "allow", path=field_value))
        started_rules = True
    flush()
    return groups


def _merged_rules(groups: list[_Group], user_agent: str) -> list[_Rule]:
    token = user_agent.split("/", 1)[0].strip().lower()
    specific: list[_Group] = []
    wildcard: list[_Group] = []
    for group in groups:
        if any(_agent_matches(agent, token, user_agent) for agent in group.agents):
            specific.append(group)
        elif any(agent.strip() == "*" for agent in group.agents):
            wildcard.append(group)
    chosen = specific or wildcard
    merged: list[_Rule] = []
    for group in chosen:
        merged.extend(group.rules)
    return merged


def _agent_matches(agent: str, token: str, user_agent: str) -> bool:
    normalized = agent.strip().lower()
    if not normalized or normalized == "*":
        return False
    ua = user_agent.lower()
    return normalized == token or token.startswith(normalized) or ua.startswith(normalized)


def _path_allowed(rules: list[_Rule], path: str, user_agent: str) -> bool:
    del user_agent  # rules are already selected for this user agent
    best_length = -1
    best_allow = True
    matched = False
    for rule in rules:
        if not rule.path:
            continue
        if not _rule_matches(rule.path, path):
            continue
        length = len(rule.path)
        if not matched or length > best_length or (length == best_length and rule.allow):
            matched = True
            best_length = length
            best_allow = rule.allow
    return best_allow


def _rule_matches(pattern: str, path: str) -> bool:
    end_anchor = pattern.endswith("$")
    body = pattern[:-1] if end_anchor else pattern
    if body == "" and end_anchor:
        return False
    regex = "^" + ".*".join(re.escape(part) for part in body.split("*"))
    if end_anchor:
        regex += "$"
    return re.match(regex, path) is not None


def clear_robots_cache() -> None:
    """Drop cached robots.txt documents. Tests call this between cases."""
    with _CACHE_LOCK:
        _CACHE.clear()
