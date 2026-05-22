from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import duckdb
import yaml

from govradar.models import Article
from main import run


class _FakeResponse:
    status_code: int
    content: bytes

    def __init__(self, content: bytes) -> None:
        self.status_code = 200
        self.content = content

    def raise_for_status(self) -> None:
        return None


def test_full_pipeline_creates_all_outputs(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    categories_dir = tmp_path / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)

    db_path = tmp_path / "data" / "radar_data.duckdb"
    report_dir = tmp_path / "reports"
    raw_dir = tmp_path / "data" / "raw"
    search_db_path = tmp_path / "data" / "search_index.db"

    _ = config_path.write_text(
        yaml.safe_dump(
            {
                "database_path": str(db_path),
                "report_dir": str(report_dir),
                "raw_data_dir": str(raw_dir),
                "search_db_path": str(search_db_path),
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    category_file = categories_dir / "test_cat.yaml"
    _ = category_file.write_text(
        yaml.safe_dump(
            {
                "category_name": "test_cat",
                "display_name": "Test Category",
                "sources": [
                    {
                        "name": "Mock RSS",
                        "type": "rss",
                        "url": "https://example.com/feed.xml",
                    }
                ],
                "entities": [
                    {
                        "name": "Bean",
                        "display_name": "Bean",
                        "keywords": ["arabica"],
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    rss_payload = b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\"><channel><title>Mock</title>
<item>
  <title>Arabica market update</title>
  <link>https://example.com/article-1</link>
  <description>arabica demand is up</description>
  <pubDate>Wed, 04 Mar 2026 10:00:00 GMT</pubDate>
</item>
</channel></rss>
"""

    with patch("radar.collector.requests.Session.get", return_value=_FakeResponse(rss_payload)):
        output_path = run(
            category="test_cat",
            config_path=config_path,
            categories_dir=categories_dir,
            per_source_limit=5,
            recent_days=7,
            timeout=5,
            keep_days=30,
        )

    assert db_path.exists()
    assert raw_dir.exists()
    assert list(raw_dir.rglob("*.jsonl"))
    assert search_db_path.exists()
    assert output_path.exists()
    assert output_path.suffix == ".html"


def test_pipeline_quality_report_uses_validated_stored_scope(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    categories_dir = tmp_path / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)

    db_path = tmp_path / "data" / "govradar.duckdb"
    report_dir = tmp_path / "reports"
    raw_dir = tmp_path / "data" / "raw"
    search_db_path = tmp_path / "data" / "search_index.db"

    _ = config_path.write_text(
        yaml.safe_dump(
            {
                "database_path": str(db_path),
                "report_dir": str(report_dir),
                "raw_data_dir": str(raw_dir),
                "search_db_path": str(search_db_path),
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    _ = (categories_dir / "govsupport.yaml").write_text(
        yaml.safe_dump(
            {
                "category_name": "govsupport",
                "display_name": "Gov Support",
                "data_quality": {
                    "quality_outputs": {
                        "tracked_event_models": ["eligibility_rule"],
                    },
                },
                "sources": [
                    {
                        "name": "Tracked Feed",
                        "type": "rss",
                        "url": "https://example.com/support.xml",
                        "trust_tier": "T1_authoritative",
                        "enabled": True,
                        "config": {
                            "event_model": "eligibility_rule",
                            "freshness_sla_days": 2,
                        },
                    }
                ],
                "entities": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    now = datetime(2026, 5, 21, 12, 0, tzinfo=UTC)
    relevant = Article(
        title="청년 지원사업 신청 공고",
        link="https://example.com/support",
        summary="청년 대상 지원사업 신청 공고",
        published=now,
        collected_at=now,
        source="Tracked Feed",
        category="govsupport",
        matched_entities={
            "SupportType": ["지원사업"],
            "TargetGroup": ["청년"],
            "OperationalEvent": ["eligibility_rule"],
        },
    )
    irrelevant_with_event_tag = Article(
        title="General operations update",
        link="https://example.com/general",
        summary="Internal operations update without support program signal.",
        published=now,
        collected_at=now,
        source="Tracked Feed",
        category="govsupport",
        matched_entities={"OperationalEvent": ["eligibility_rule"]},
    )

    with (
        patch("main.collect_sources", return_value=([relevant, irrelevant_with_event_tag], [])),
        patch("main.annotate_articles_with_ontology", side_effect=lambda articles, **_: articles),
    ):
        _ = run(
            category="govsupport",
            config_path=config_path,
            categories_dir=categories_dir,
            per_source_limit=5,
            recent_days=7,
            timeout=5,
            keep_days=30,
        )

    report = json.loads((report_dir / "govsupport_quality.json").read_text(encoding="utf-8"))
    assert report["summary"]["eligibility_rule_events"] == 1
    assert len(report["events"]) == 1
    assert report["events"][0]["title"] == "청년 지원사업 신청 공고"

    with duckdb.connect(str(db_path), read_only=True) as con:
        assert con.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 1
        assert con.execute("SELECT title FROM articles").fetchone()[0] == "청년 지원사업 신청 공고"
