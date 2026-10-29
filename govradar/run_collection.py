"""This-run collection counts, separate from the 7-day report window."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from govradar.models import Article, Source


def build_run_collection(
    sources: Sequence[Source],
    collected: Sequence[Article],
    errors: Sequence[str],
    *,
    last_success_at: Mapping[str, datetime | None],
) -> dict[str, object]:
    """Count what this execution fetched, which enabled sources failed, and when each last stored."""
    enabled = [source for source in sources if source.enabled]
    collected_counts = {source.name: 0 for source in enabled}
    for article in collected:
        if article.source in collected_counts:
            collected_counts[article.source] += 1

    failed_sources: list[dict[str, object]] = []
    for source in enabled:
        prefix = f"{source.name}:"
        source_errors = [error for error in errors if error.startswith(prefix)]
        if source_errors:
            failed_sources.append({"source": source.name, "errors": source_errors})

    last_success: dict[str, str | None] = {}
    for source in enabled:
        last_success[source.name] = _iso(last_success_at.get(source.name))

    return {
        "collected_counts": collected_counts,
        "failed_sources": failed_sources,
        "last_success_at": last_success,
    }


def run_collected_total(run_collection: Mapping[str, object]) -> int:
    counts = run_collection.get("collected_counts")
    if not isinstance(counts, Mapping):
        return 0
    return sum(
        value for value in counts.values() if isinstance(value, int) and not isinstance(value, bool)
    )


def run_failed_source_count(run_collection: Mapping[str, object]) -> int:
    failed = run_collection.get("failed_sources")
    if not isinstance(failed, list):
        return 0
    return len(failed)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()
