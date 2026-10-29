from __future__ import annotations

from govradar.config_loader import load_category_config, load_category_quality_config


def test_real_govsupport_config_exposes_data_quality_overlay() -> None:
    metadata = load_category_quality_config("govsupport")

    data_quality = metadata["data_quality"]
    assert isinstance(data_quality, dict)
    assert data_quality["priority"] == "P0"
    assert data_quality["primary_motion"] == "conversion"
    assert data_quality["quality_outputs"]["freshness_report"] == "reports/govsupport_quality.json"
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
    result_candidates = {candidate["id"] for candidate in backlog["selection_result_candidates"]}
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
    assert gov24.enabled is False
    assert "Disallow: /" in str(gov24.config["skip_reason"])
    assert gov24.producer_role == "government"
    assert "application_deadline" in gov24.info_purpose
    assert "eligibility_rule" in gov24.info_purpose
    assert gov24.config["event_model"] == "application_deadline"
    assert gov24.config["observed_date_field"] == "collected_at"
    assert gov24.config["canonical_key_fields"]

    semas = sources["소상공인시장진흥공단"]
    assert semas.enabled is False
    assert "Disallow: /" in str(semas.config["skip_reason"])
    assert semas.config["event_model"] == "eligibility_rule"
    assert "operational_event" in semas.info_purpose

    seoul_notices = sources["서울시 지원사업"]
    assert seoul_notices.enabled is True
    assert seoul_notices.type == "public_page"
    assert seoul_notices.url == "https://www.seoul.go.kr/news/news_notice.do?bbsNo=277"
    assert seoul_notices.config["consecutive_transport_failure_limit"] == 3
    assert seoul_notices.config["provider"] == "seoul_notice"

    kstartup_api = sources["K-Startup 지원사업 공고 API"]
    subsidy_api = sources["보조금24 공공서비스 API"]
    bizinfo_api = sources["기업마당 지원사업 공고 API"]
    assert kstartup_api.config["required_env"] == "DATA_GO_KR_KSTARTUP_SERVICE_KEY"
    assert subsidy_api.config["required_env"] == "DATA_GO_KR_SUBSIDY24_SERVICE_KEY"
    assert bizinfo_api.config["required_env"] == "DATA_GO_KR_BIZINFO_SERVICE_KEY"

    seoul = sources["서울시 정책뉴스"]
    assert seoul.producer_role == "local-government"
    assert seoul.type == "rss"
    assert seoul.url == "https://news.seoul.go.kr/gov/feed"
    assert seoul.config["freshness_sla_days"] == 1

    mofra = sources["농림축산식품부"]
    assert mofra.config["event_model"] == "official_notice"
    assert "industry" in mofra.config["canonical_key_fields"]

    molit = sources["국토교통부"]
    assert molit.enabled is False
    assert molit.config["event_model"] == "official_notice"
    assert "resets connections" in molit.config["skip_reason"]


def test_newspapers_disabled_and_mafra_detail_requires_kogl_type1() -> None:
    """저작권 검토: 신문 3곳은 꺼져 있고 상세 보강 설정이 없으며, 농림축산식품부만 제1유형일 때 보강한다."""
    category = load_category_config("govsupport")
    sources = {source.name: source for source in category.sources}

    for name in ("한국경제 경제", "한국경제 정치", "서울경제 경제"):
        assert sources[name].enabled is False
        assert sources[name].config["skip_reason"]
        for key in (
            "fetch_detail_summary",
            "detail_summary_selectors",
            "detail_summary_prefer_meta",
            "detail_upgrade_https",
        ):
            assert key not in sources[name].config
    assert sources["서울경제 경제"].config["bypass_crawl_health"] is True

    mafra = sources["농림축산식품부"]
    assert mafra.enabled is True
    assert mafra.config["fetch_detail_summary"] is True
    assert mafra.config["detail_require_license"] == "kogl_type1"
    assert mafra.config["detail_upgrade_https"] is True
    assert mafra.config["detail_summary_selectors"]
    enabled_detail = [
        name for name, source in sources.items() if source.config.get("fetch_detail_summary")
    ]
    assert enabled_detail == ["농림축산식품부"]

    assert sources["SBS 뉴스 정치"].config["exclude_title_prefixes"] == [
        "[여담야담]",
        "[성민종합정치]",
    ]
    for source in sources.values():
        assert "include_keywords" not in source.config
