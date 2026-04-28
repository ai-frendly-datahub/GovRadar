from __future__ import annotations

import argparse
from datetime import UTC
from pathlib import Path
from typing import Any, cast

from radar_core.analyzer import apply_entity_rules
from radar_core.collector import collect_sources
from radar_core.config_loader import load_category_config, load_settings
from radar_core.ontology import annotate_articles_with_ontology
from radar_core.raw_logger import RawLogger
from radar_core.search_index import SearchIndex

from govradar.common.validators import validate_article
from govradar.config_loader import load_category_quality_config
from govradar.date_storage import apply_date_storage_policy
from govradar.models import Article, Source
from govradar.quality_report import build_quality_report, write_quality_report
from govradar.relevance import apply_source_context_entities, filter_relevant_articles
from govradar.reporter import generate_index_html, generate_report
from govradar.storage import RadarStorage
from govradar.support_signals import enrich_support_operational_fields


def _send_notifications(
    *,
    category_name: str,
    sources_count: int,
    collected_count: int,
    matched_count: int,
    errors_count: int,
    report_path: Path,
) -> None:
    import os
    from datetime import datetime

    email_to = os.environ.get("NOTIFICATION_EMAIL")
    webhook_url = os.environ.get("NOTIFICATION_WEBHOOK")

    if not email_to and not webhook_url:
        return

    from govradar.notifier import (
        CompositeNotifier,
        EmailNotifier,
        NotificationPayload,
        Notifier,
        WebhookNotifier,
    )

    payload = NotificationPayload(
        category_name=category_name,
        sources_count=sources_count,
        collected_count=collected_count,
        matched_count=matched_count,
        errors_count=errors_count,
        timestamp=datetime.now(UTC),
        report_url=str(report_path),
    )

    notifiers: list[Notifier] = []
    if email_to:
        notifiers.append(
            EmailNotifier(
                smtp_host=os.environ.get("SMTP_HOST", "localhost"),
                smtp_port=int(os.environ.get("SMTP_PORT", "587")),
                smtp_user=os.environ.get("SMTP_USER", ""),
                smtp_password=os.environ.get("SMTP_PASSWORD", ""),
                from_addr=os.environ.get("SMTP_FROM", ""),
                to_addrs=[email_to],
            )
        )
    if webhook_url:
        notifiers.append(WebhookNotifier(url=webhook_url))

    if notifiers:
        composite = CompositeNotifier(notifiers)
        _ = composite.send(payload)


def run(
    *,
    category: str,
    config_path: Path | None = None,
    categories_dir: Path | None = None,
    per_source_limit: int = 30,
    recent_days: int = 7,
    timeout: int = 15,
    keep_days: int = 90,
    keep_raw_days: int = 180,
    keep_report_days: int = 90,
    keep_snapshot_days: int = 30,
    snapshot_db: bool = False,
) -> Path:
    """Execute the lightweight collect -> analyze -> report pipeline."""
    settings = load_settings(config_path)
    category_cfg = load_category_config(category, categories_dir=categories_dir)
    quality_cfg = load_category_quality_config(category, categories_dir=categories_dir)

    print(
        f"[Radar] Collecting '{category_cfg.display_name}' from {len(category_cfg.sources)} sources..."
    )
    collected: list[Article]
    errors: list[str]
    collected, errors = collect_sources(
        category_cfg.sources,
        category=category_cfg.category_name,
        limit_per_source=per_source_limit,
        timeout=timeout,
    )
    collected = annotate_articles_with_ontology(
        collected,
        repo_name="GovRadar",
        sources_by_name={source.name: source for source in category_cfg.sources},
        category_name=category_cfg.category_name,
        search_from=Path(__file__),
        attach_event_model_payload=True,
    )

    raw_logger = RawLogger(settings.raw_data_dir)
    for source in category_cfg.sources:
        source_articles = [article for article in collected if article.source == source.name]
        if source_articles:
            _ = raw_logger.log(source_articles, source_name=source.name)

    analyzed = enrich_support_operational_fields(
        apply_entity_rules(collected, category_cfg.entities)
    )
    classified = apply_source_context_entities(analyzed, category_cfg.sources)
    scoped_articles = filter_relevant_articles(classified, category_cfg.sources)

    # Validate articles for data quality
    validated_articles: list[Article] = []
    validation_errors: list[str] = []
    for article in scoped_articles:
        is_valid, validation_msgs = validate_article(article)
        if is_valid:
            validated_articles.append(article)
        else:
            validation_errors.append(f"{article.link}: {', '.join(validation_msgs)}")

    if validation_errors:
        errors.extend(validation_errors)

    storage = RadarStorage(settings.database_path)
    storage.upsert_articles(validated_articles)
    _ = storage.delete_older_than(keep_days)

    with SearchIndex(settings.search_db_path) as search_idx:
        for article in validated_articles:
            search_idx.upsert(article.link, article.title, article.summary)

    recent_articles = _select_report_articles(
        storage,
        category_cfg.category_name,
        recent_days=recent_days,
        sources=category_cfg.sources,
    )
    storage.close()

    matched_count = sum(1 for article in recent_articles if article.matched_entities)
    source_count = len({article.source for article in recent_articles if article.source})
    stats: dict[str, int] = {
        "sources": len(category_cfg.sources),
        "collected": len(recent_articles),
        "matched": matched_count,
        "validated": len(validated_articles),
        "window_days": recent_days,
        "article_count": len(recent_articles),
        "source_count": source_count,
        "matched_count": matched_count,
    }

    quality_report = build_quality_report(
        category=cast(Any, category_cfg),
        articles=cast(Any, recent_articles),
        errors=errors,
        quality_config=quality_cfg,
    )
    quality_report_paths = write_quality_report(
        quality_report,
        output_dir=settings.report_dir,
        category_name=category_cfg.category_name,
    )

    output_path = settings.report_dir / f"{category_cfg.category_name}_report.html"
    _ = generate_report(
        category=cast(Any, category_cfg),
        articles=cast(Any, recent_articles),
        output_path=output_path,
        stats=stats,
        errors=errors,
        quality_report=quality_report,
    )
    _ = generate_index_html(settings.report_dir)
    print(f"[Radar] Report generated at {output_path}")
    print(f"[Radar] Quality report generated at {quality_report_paths['latest']}")
    date_storage = apply_date_storage_policy(
        database_path=settings.database_path,
        raw_data_dir=settings.raw_data_dir,
        report_dir=settings.report_dir,
        keep_raw_days=keep_raw_days,
        keep_report_days=keep_report_days,
        keep_snapshot_days=keep_snapshot_days,
        snapshot_db=snapshot_db,
    )
    snapshot_path = date_storage.get("snapshot_path")
    if isinstance(snapshot_path, str) and snapshot_path:
        print(f"[Radar] Snapshot saved at {snapshot_path}")
    if errors:
        print(f"[Radar] {len(errors)} source(s) had issues. See report for details.")

    _send_notifications(
        category_name=category_cfg.category_name,
        sources_count=len(category_cfg.sources),
        collected_count=len(collected),
        matched_count=sum(1 for a in collected if a.matched_entities),
        errors_count=len(errors),
        report_path=output_path,
    )

    return output_path


def _select_report_articles(
    storage: RadarStorage,
    category: str,
    *,
    recent_days: int,
    sources: list[Source] | None = None,
) -> list[Article]:
    published_articles = storage.recent_articles(category, days=recent_days, limit=1000)
    collected_articles = storage.recent_articles_by_collected_at(
        category,
        days=recent_days,
        limit=1000,
    )
    articles = _dedupe_articles([*published_articles, *collected_articles])
    if sources is None:
        return articles

    scoped_articles = filter_relevant_articles(
        apply_source_context_entities(articles, sources),
        sources,
    )
    return scoped_articles or articles


def _dedupe_articles(articles: list[Article]) -> list[Article]:
    deduped: dict[str, Article] = {}
    for article in articles:
        key = article.link or f"{article.source}:{article.title}"
        if key not in deduped:
            deduped[key] = article
    return list(deduped.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lightweight Radar template runner")
    _ = parser.add_argument(
        "--category", required=True, help="Category name matching a YAML in config/categories/"
    )
    _ = parser.add_argument(
        "--config", type=Path, default=None, help="Path to config/config.yaml (optional)"
    )
    _ = parser.add_argument(
        "--categories-dir", type=Path, default=None, help="Custom directory for category YAML files"
    )
    _ = parser.add_argument(
        "--per-source-limit", type=int, default=30, help="Max items to pull from each source"
    )
    _ = parser.add_argument(
        "--recent-days", type=int, default=7, help="Window (days) to show in the report"
    )
    _ = parser.add_argument(
        "--timeout", type=int, default=15, help="HTTP timeout per request (seconds)"
    )
    _ = parser.add_argument(
        "--keep-days", type=int, default=90, help="Retention window for stored items"
    )
    _ = parser.add_argument(
        "--keep-raw-days", type=int, default=180, help="Retention window for raw JSONL directories"
    )
    _ = parser.add_argument(
        "--keep-report-days", type=int, default=90, help="Retention window for dated HTML reports"
    )
    _ = parser.add_argument(
        "--keep-snapshot-days", type=int, default=30, help="Retention window for dated DuckDB snapshots"
    )
    _ = parser.add_argument(
        "--snapshot-db",
        action="store_true",
        default=False,
        help="Create a dated DuckDB snapshot after each run",
    )
    _ = parser.add_argument(
        "--generate-report",
        action="store_true",
        default=False,
        help="Generate HTML report after collection",
    )
    return parser.parse_args()


def _to_path(value: object) -> Path | None:
    if isinstance(value, Path):
        return value
    return None


def _to_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


if __name__ == "__main__":
    _PROJECT_ROOT = Path(__file__).resolve().parent
    args = cast(dict[str, object], vars(parse_args()))
    _ = run(
        category=str(args.get("category", "")),
        config_path=_to_path(args.get("config")) or _PROJECT_ROOT / "config" / "config.yaml",
        categories_dir=_to_path(args.get("categories_dir"))
        or _PROJECT_ROOT / "config" / "categories",
        per_source_limit=_to_int(args.get("per_source_limit"), 30),
        recent_days=_to_int(args.get("recent_days"), 7),
        timeout=_to_int(args.get("timeout"), 15),
        keep_days=_to_int(args.get("keep_days"), 90),
        keep_raw_days=_to_int(args.get("keep_raw_days"), 180),
        keep_report_days=_to_int(args.get("keep_report_days"), 90),
        keep_snapshot_days=_to_int(args.get("keep_snapshot_days"), 30),
        snapshot_db=bool(args.get("snapshot_db", False)),
    )
