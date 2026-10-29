"""RSS 항목의 본문(summary)이 비어 있을 때 공개 기사 페이지에서 요약을 보강한다.

배경: 농림축산식품부 RSS는 항목마다 ``title``/``link``/``author``/``pubDate``만 내려주고
``description``/``content:encoded``가 없다. radar-core 수집기는 그 두 필드만 읽기 때문에
``summary``가 빈 문자열이 된다. 이 모듈은 소스 설정에서 ``fetch_detail_summary: true``로 켠
소스에 한해, 이미 수집한 상세 페이지의 공개 HTML을 읽어 ``summary``를 채운다.

저작권 검토(2026-10-29)에 따라 신문 소스(한국경제·서울경제)는 약관상 자동 수집이 제한되어
비활성화했고, 이 모듈은 신문 페이지를 가져오지 않는다. 농림축산식품부는 ``detail_require_license:
kogl_type1``이 설정된 경우 공공누리 제1유형 표시가 있는 페이지에서만 본문을 쓴다.

지키는 규칙:
- robots.txt를 확인한다(``govradar.robots.url_is_allowed``). Disallow이거나 읽을 수 없으면 가져오지 않는다.
- TLS 검증을 끄지 않는다. 챌린지/차단 페이지는 우회하지 않고 건너뛴다.
- 피드와 같은 호스트의 URL만 가져온다. 요청 사이 간격을 두고, 실행당 소스별 상한이 있다.
- 가져오지 못하면 ``summary``는 빈 채로 둔다. 만들어 낸 내용은 넣지 않는다.
"""

from __future__ import annotations

import html
import re
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from govradar.collection_contract import GOVRADAR_USER_AGENT
from govradar.common.validators import is_challenge_or_error_page
from govradar.models import Article, Source
from govradar.robots import url_is_allowed

DEFAULT_MAX_CHARS = 800
DEFAULT_MAX_PER_RUN = 30
DEFAULT_MIN_INTERVAL_SECONDS = 1.0
_MIN_USEFUL_CHARS = 20
KOGL_TYPE1 = "kogl_type1"
_WS = re.compile(r"\s+")
_BLOCK_TAGS = ["p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section"]

PageFetcher = Callable[[str, int], bytes | str | None]
RobotsCheck = Callable[[str, int], tuple[bool, str]]


@dataclass
class EnrichStats:
    """소스별 보강 결과. 출력용이며 오류 목록에는 넣지 않는다."""

    attempted: int = 0
    filled: int = 0
    skipped_robots: int = 0
    failed: int = 0
    skipped_license: int = 0


def fetch_public_page(url: str, timeout: int) -> bytes | None:
    """공개 HTML을 TLS 검증을 켠 채로 가져온다. 실패하면 None."""
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": GOVRADAR_USER_AGENT,
                "Accept": "text/html, application/xhtml+xml;q=0.9, */*;q=0.5",
            },
            timeout=timeout,
            verify=True,
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    content_type = response.headers.get("content-type", "").lower()
    if content_type and "html" not in content_type:
        return None
    # 인코딩 판별은 BeautifulSoup(meta charset)에 맡기기 위해 바이트로 돌려준다.
    return response.content


def _normalize(text: str) -> str:
    return _WS.sub(" ", html.unescape(text)).strip()


_KOGL_TYPE1_HREF = re.compile(r"kogl\.or\.kr/info/licenseType1\.do", re.IGNORECASE)
_KOGL_TYPE1_IMG = re.compile(r"opentype01(?!\d)", re.IGNORECASE)
# 제2~4유형(변경금지·영리금지 조건이 붙음)이 함께 보이면 제1유형으로 보지 않는다.
_KOGL_OTHER_HREF = re.compile(r"kogl\.or\.kr/info/licenseType[2-9]\.do", re.IGNORECASE)
_KOGL_OTHER_IMG = re.compile(r"opentype0[2-9]", re.IGNORECASE)


def _has_kogl_type1(page_html: bytes | str) -> bool:
    """페이지에 공공누리 제1유형(출처표시) 마크가 있고 제2~4유형 마크는 없으면 True."""
    soup = BeautifulSoup(page_html, "html.parser")
    type1 = False
    for tag in soup.find_all(["a", "img"]):
        attr = tag.get("href") if tag.name == "a" else tag.get("src")
        if not isinstance(attr, str):
            continue
        if _KOGL_OTHER_HREF.search(attr) or _KOGL_OTHER_IMG.search(attr):
            return False
        if _KOGL_TYPE1_HREF.search(attr) or _KOGL_TYPE1_IMG.search(attr):
            type1 = True
    return type1


def _body_text(soup: BeautifulSoup, selectors: Iterable[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue
        for junk in node.find_all(["script", "style", "noscript", "figcaption"]):
            junk.decompose()
        # 인라인 태그(단어마다 span인 한글 문서 등) 사이에는 공백을 넣지 않고,
        # 줄 바꿈 성격의 태그 뒤에만 공백을 넣는다.
        for br in node.find_all("br"):
            br.replace_with(" ")
        for block in node.find_all(_BLOCK_TAGS):
            block.append(" ")
        text = _normalize(node.get_text())
        if len(text) >= _MIN_USEFUL_CHARS:
            return text
    return ""


def extract_summary(
    page_html: bytes | str,
    *,
    selectors: list[str],
    max_chars: int,
) -> str:
    """상세 페이지 HTML의 본문 앞부분을 뽑는다. 못 찾으면 빈 문자열."""
    soup = BeautifulSoup(page_html, "html.parser")
    return _body_text(soup, selectors)[:max_chars].rstrip()


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _int_setting(value: object, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return default
    return value


def _float_setting(value: object, default: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return default
    return float(value)


def _detail_url(link: str, feed_url: str, *, upgrade_https: bool) -> str | None:
    """피드와 같은 호스트일 때만 상세 URL을 돌려준다. 필요하면 https로 올린다."""
    parsed = urlparse(link)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    feed_host = (urlparse(feed_url).hostname or "").lower()
    if parsed.hostname.lower() != feed_host:
        return None
    if upgrade_https and parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")
    return urlunparse(parsed)


def enrich_empty_summaries(
    articles: list[Article],
    sources: Iterable[Source],
    *,
    timeout: int,
    fetcher: PageFetcher | None = None,
    robots_check: RobotsCheck | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[list[Article], dict[str, EnrichStats]]:
    """``fetch_detail_summary``가 켜진 소스의 빈 summary를 공개 기사 페이지로 채운다.

    ``articles``를 제자리에서 바꾸고 같은 리스트를 돌려준다. 오류는 던지지 않는다.
    """
    fetch = fetcher or fetch_public_page
    check = robots_check or (lambda url, secs: url_is_allowed(url, timeout=secs))
    stats: dict[str, EnrichStats] = {}
    for source in sources:
        config = source.config or {}
        if not source.enabled or config.get("fetch_detail_summary") is not True:
            continue
        selectors = _string_list(config.get("detail_summary_selectors"))
        require_license = config.get("detail_require_license")
        upgrade_https = config.get("detail_upgrade_https") is True
        max_chars = _int_setting(config.get("detail_summary_max_chars"), DEFAULT_MAX_CHARS)
        max_per_run = _int_setting(config.get("detail_summary_max_per_run"), DEFAULT_MAX_PER_RUN)
        interval = _float_setting(
            config.get("detail_min_interval_seconds"), DEFAULT_MIN_INTERVAL_SECONDS
        )
        source_stats = stats.setdefault(source.name, EnrichStats())
        for article in articles:
            if article.source != source.name or article.summary.strip():
                continue
            if source_stats.attempted >= max_per_run:
                break
            url = _detail_url(article.link, source.url, upgrade_https=upgrade_https)
            if url is None:
                source_stats.failed += 1
                continue
            allowed, _reason = check(url, timeout)
            if not allowed:
                source_stats.skipped_robots += 1
                continue
            if source_stats.attempted:
                sleep(interval)
            source_stats.attempted += 1
            page = fetch(url, timeout)
            if page is None:
                source_stats.failed += 1
                continue
            if require_license == KOGL_TYPE1 and not _has_kogl_type1(page):
                source_stats.skipped_license += 1
                continue
            summary = extract_summary(page, selectors=selectors, max_chars=max_chars)
            if not summary or is_challenge_or_error_page(article.title, summary):
                source_stats.failed += 1
                continue
            article.summary = summary
            source_stats.filled += 1
    return articles, stats


def format_stats(stats: dict[str, EnrichStats]) -> list[str]:
    """실행 로그용 한 줄 요약. 시크릿이나 본문은 포함하지 않는다."""
    lines: list[str] = []
    for name, item in stats.items():
        lines.append(
            f"{name}: 본문 보강 시도 {item.attempted}건, 성공 {item.filled}건, "
            f"실패 {item.failed}건, robots 제외 {item.skipped_robots}건, "
            f"라이선스 제외 {item.skipped_license}건"
        )
    return lines
