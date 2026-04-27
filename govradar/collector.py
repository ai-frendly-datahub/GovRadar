from __future__ import annotations

import html
import os
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import requests
import structlog
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import Article, Source


logger = structlog.get_logger()


_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (compatible; RadarTemplateBot/1.0; +https://github.com/zzragida/ai-frendly-datahub)",
}
_COLLECTION_CONTROL_LOCK = threading.Lock()


class RateLimiter:
    def __init__(self, min_interval: float = 0.5):
        self._min_interval: float = min_interval
        self._last_request: float = 0.0
        self._lock: threading.Lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()


def _resolve_max_workers(max_workers: int | None = None) -> int:
    if max_workers is None:
        raw_value = "5"
        try:
            parsed = int(raw_value)
        except ValueError:
            parsed = 5
    else:
        parsed = max_workers

    return max(1, min(parsed, 10))


def _create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504, 522, 524],
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def _fetch_url_with_retry(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> requests.Response:
    session = _create_session()
    merged_headers = _DEFAULT_HEADERS.copy()
    if headers:
        merged_headers.update(headers)
    response = session.get(url, headers=merged_headers, timeout=timeout)
    response.raise_for_status()
    return response


def _parse_rss_feed(
    url: str, headers: dict[str, str] | None = None, timeout: float = 30.0
) -> list[Article]:
    try:
        response = _fetch_url_with_retry(url, headers, timeout)
        feed = feedparser.parse(response.content)

        articles: list[Article] = []
        for entry in feed.entries:
            published_dt: datetime | None = None
            # Try published_parsed first (time.struct_time)
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    if isinstance(entry.published_parsed, tuple):
                        # time.struct_time is a tuple-like object
                        from time import struct_time

                        if isinstance(entry.published_parsed, struct_time):
                            published_dt = datetime(
                                entry.published_parsed.tm_year,
                                entry.published_parsed.tm_mon,
                                entry.published_parsed.tm_mday,
                                entry.published_parsed.tm_hour,
                                entry.published_parsed.tm_min,
                                entry.published_parsed.tm_sec,
                                tzinfo=UTC,
                            )
                        else:
                            published_dt = parsedate_to_datetime(entry.published_parsed)
                    else:
                        published_dt = parsedate_to_datetime(entry.published_parsed)
                    if published_dt.tzinfo:
                        published_dt = published_dt.astimezone(UTC).replace(tzinfo=None)
                except (ValueError, TypeError, AttributeError):
                    pass
            # Fallback to published string
            elif hasattr(entry, "published") and entry.published:
                try:
                    published_dt = parsedate_to_datetime(entry.published)
                    if published_dt.tzinfo:
                        published_dt = published_dt.astimezone(UTC).replace(tzinfo=None)
                except (ValueError, TypeError):
                    pass

            article = Article(
                title=html.unescape(entry.title) if hasattr(entry, "title") else "",
                link=entry.link if hasattr(entry, "link") else url,
                summary=(
                    html.unescape(entry.summary)
                    if hasattr(entry, "summary") and entry.summary
                    else ""
                ),
                published=published_dt,
                source=urlparse(url).netloc,
            )
            articles.append(article)

        return articles
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch RSS: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to parse RSS: {e}") from e


def collect_sources(
    sources: list[Source],
    category: str = "",
    limit_per_source: int = 30,
    timeout: int = 30,
    min_interval_per_host: float = 0.5,
    max_workers: int | None = None,
) -> tuple[list[Article], list[str]]:
    """Collect articles from multiple sources concurrently.

    Uses a 2-pass hybrid collection pattern:

    * **Pass 1** — RSS/feed sources collected in parallel via
      :class:`~concurrent.futures.ThreadPoolExecutor`.
    * **Pass 2** — JavaScript/browser sources collected sequentially via
      Playwright (see :mod:`radar.browser_collector`).

    If Playwright is not installed, JS sources are silently skipped with a
    warning log entry so that RSS-only mode keeps working.
    """
    # --- Source splitting ---------------------------------------------------
    enabled_sources = [source for source in sources if source.enabled]
    rss_sources = [s for s in enabled_sources if s.type.lower() == "rss"]
    js_sources = [
        s
        for s in enabled_sources
        if s.type.lower() in ("javascript", "browser", "html", "js", "web")
    ]
    reddit_sources = [s for s in enabled_sources if s.type.lower() == "reddit"]
    unsupported_sources = [
        source
        for source in enabled_sources
        if source.type.lower() not in {"rss", "javascript", "browser", "html", "js", "web", "reddit"}
    ]

    # --- Pass 1: RSS sources via ThreadPoolExecutor (parallel) --------------
    resolved_workers = _resolve_max_workers(max_workers)
    rate_limiter = RateLimiter(min_interval=min_interval_per_host)

    all_articles: list[Article] = []
    errors: list[str] = []

    def fetch_source(source: Source) -> list[Article]:
        try:
            rate_limiter.acquire()
            articles = _parse_rss_feed(source.url, timeout=float(timeout))
            for article in articles:
                article.category = category
                article.source = source.name
            return articles
        except Exception as e:
            errors.append(f"{source.name}: {e}")
            return []

    if resolved_workers == 1:
        for source in rss_sources:
            all_articles.extend(fetch_source(source))
    elif rss_sources:
        with ThreadPoolExecutor(max_workers=resolved_workers) as executor:
            futures: list[Future[list[Article]]] = [
                executor.submit(fetch_source, source) for source in rss_sources
            ]
            for future in futures:
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as e:
                    errors.append(f"unknown: {e}")

    if errors:
        logger.warning("collection_errors", errors=errors)

    # --- Pass 2: JavaScript/browser sources via Playwright (sequential) -----
    if js_sources:
        try:
            from .browser_collector import collect_browser_sources

            js_articles, js_errors = collect_browser_sources(
                js_sources,
                category,
                timeout=max(1_000, timeout * 1_000),
            )
            all_articles.extend(js_articles)
            if js_errors:
                errors.extend(js_errors)
                logger.warning("browser_collection_errors", errors=js_errors)
        except ImportError:
            errors.append(
                f"Browser collection unavailable for {len(js_sources)} source(s). Install radar-core[browser]."
            )
            logger.warning(
                "playwright_unavailable",
                js_source_count=len(js_sources),
                hint="pip install 'radar-core[browser]'",
            )

    if reddit_sources:
        try:
            from radar_core import collect_reddit_sources

            reddit_articles, reddit_errors = collect_reddit_sources(
                reddit_sources,
                category=category,
                limit=limit_per_source,
                timeout=timeout,
                health_db_path=os.environ.get("RADAR_CRAWL_HEALTH_DB_PATH"),
            )
            all_articles.extend(reddit_articles)
            if reddit_errors:
                logger.warning("reddit_collection_errors", errors=reddit_errors)
                errors.extend(reddit_errors)
        except ImportError:
            errors.append(
                f"Reddit collection unavailable for {len(reddit_sources)} source(s). Ensure radar-core reddit support is installed."
            )
            logger.warning(
                "reddit_collector_unavailable",
                reddit_source_count=len(reddit_sources),
                hint="Ensure radar-core is installed with reddit support",
            )

    for source in unsupported_sources:
        errors.append(
            f"{source.name}: Source type '{source.type}' is cataloged but not collected by the standard pipeline"
        )

    return all_articles, errors
