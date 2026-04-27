from __future__ import annotations

from govradar.config_loader import load_category_config, load_category_quality_config


def test_real_govsupport_config_exposes_data_quality_overlay() -> None:
    metadata = load_category_quality_config("govsupport")

    data_quality = metadata["data_quality"]
    assert isinstance(data_quality, dict)
    assert data_quality["priority"] == "P0"
    assert data_quality["primary_motion"] == "conversion"
    assert (
        data_quality["quality_outputs"]["freshness_report"]
        == "reports/govsupport_quality.json"
    )
    assert set(data_quality["quality_outputs"]["tracked_event_models"]) == {
        "support_program_notice",
        "application_deadline",
        "eligibility_rule",
        "selection_result",
    }
    assert "support_program_notice" in data_quality["event_models"]
    assert "application_deadline" in data_quality["event_models"]
    assert "eligibility_rule" in data_quality["event_models"]
    assert "selection_result" in data_quality["event_models"]
    assert data_quality["canonical_keys"]["program"]["fields"]

    backlog = metadata["source_backlog"]
    assert isinstance(backlog, dict)
    result_candidates = {
        candidate["id"] for candidate in backlog["selection_result_candidates"]
    }
    eligibility_candidates = {
        candidate["id"] for candidate in backlog["eligibility_capability_candidates"]
    }
    assert result_candidates >= {
        "kstartup_selection_results",
        "subsidy24_execution_results",
    }
    assert eligibility_candidates >= {"nps_business_enrollment_mcp"}


def test_real_govsupport_sources_preserve_operational_metadata() -> None:
    config = load_category_config("govsupport")
    sources = {source.name: source for source in config.sources}

    gov24 = sources["정부24 보조금"]
    assert gov24.producer_role == "government"
    assert "application_deadline" in gov24.info_purpose
    assert "eligibility_rule" in gov24.info_purpose
    assert gov24.config["event_model"] == "application_deadline"
    assert gov24.config["observed_date_field"] == "collected_at"
    assert gov24.config["canonical_key_fields"]

    semas = sources["소상공인시장진흥공단"]
    assert semas.config["event_model"] == "eligibility_rule"
    assert "operational_event" in semas.info_purpose

    seoul = sources["서울시 지원사업"]
    assert seoul.producer_role == "local-government"
    assert seoul.config["freshness_sla_days"] == 1

    mofra = sources["농림축산식품부"]
    assert mofra.config["event_model"] == "official_notice"
    assert "industry" in mofra.config["canonical_key_fields"]

    molit = sources["국토교통부"]
    assert molit.config["event_model"] == "official_notice"
