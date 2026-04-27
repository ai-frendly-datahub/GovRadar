# GovRadar - 한국 정부지원 레이더

**🌐 Live Report**: https://ai-frendly-datahub.github.io/GovRadar/

한국 정부지원금/보조금/지원사업 공고를 매일 수집하고 엔티티 기반으로 분류해 추적 리포트를 제공하는 Standard Tier 레이더 프로젝트입니다. 현재 표준 실행 경로는 `radar-core`의 공용 collector/config loader를 사용하며 RSS, JavaScript 브라우저 수집, Reddit 커뮤니티 신호를 함께 처리합니다.

## 프로젝트 목표

- **정부지원 정보 수집**: 중앙부처/지자체/공공기관 RSS + 브라우저 기반 공고 자동 수집
- **엔티티 분석**: 지원유형, 대상자, 부처, 지역, 신청기간 키워드 자동 태깅
- **리포트 생성**: DuckDB 저장 + HTML 리포트로 최근 동향 시각화
- **자동화 운영**: GitHub Actions 일일 실행 + GitHub Pages 자동 배포
- **운영 메모**: 공공데이터/MCP 서버는 `sources`가 아니라 `integration_candidates`로 관리합니다. capability 후보이며 표준 공고 수집 파이프라인에는 포함되지 않습니다.

## 빠른 시작

1. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

2. 실행:
   ```bash
   python main.py --category govsupport --recent-days 7
   # 리포트: reports/govsupport_report.html
   ```

## 핵심 설정

- 카테고리: `config/categories/govsupport.yaml`
- DB 경로: `data/govradar_data.duckdb`
- 리포트 출력: `reports/`
- 워크플로: `.github/workflows/radar-crawler.yml`
- 실행 파이프라인: `radar_core.collector`, `radar_core.config_loader`

## 데이터 품질 운영

- `config/categories/govsupport.yaml`에는 `data_quality`와 `source_backlog`가 있어 지원사업 공고를 `support_program_notice`, `application_deadline`, `eligibility_rule`, `selection_result` 이벤트로 분리합니다.
- `정부24 보조금`, `소상공인시장진흥공단`, `서울시 지원사업`, 주요 중앙부처 source는 `event_model`, `canonical_key_fields`, `freshness_sla_days`를 갖고 신청 마감·자격요건 extractor의 primary evidence로 쓰입니다.
- `govradar.support_signals`는 공고 텍스트에서 보수적으로 신청 시작일/마감일과 대상자·업종·지역 eligibility 힌트를 추출해 `matched_entities`에 `ApplicationDeadline`, `EligibilityRegion` 같은 운영 신호를 추가합니다.
- 선정 결과와 집행 실적은 아직 기본 수집 source가 아니라 `source_backlog.selection_result_candidates`에서 parser, evidence URL, program id mapping 검증 후 단계적으로 활성화합니다.
- 사업장 가입 여부 같은 자격검증 capability는 시계열 공고가 아니므로 `integration_candidates`에 유지하고, 신청 가능성 점수 계산 단계에서 별도 lookup으로 연결합니다.

## 한국 MCP 생태계 추적

- `GovRadar`는 `Awesome MCP Korea`와 `K-GAPI 공공API 현황분석` 같은 소스를 통해 한국 공공 API/MCP 생태계 변화를 함께 추적합니다.
- 관련 분석 메모: [awesome-mcp-korea-analysis.md](/home/kjs/projects/ai-frendly-datahub/GovRadar/docs/awesome-mcp-korea-analysis.md)
- `config/categories/govsupport.yaml`에는 `McpKoreaEcosystem` 엔티티가 추가되어 공공 API, 한국형 MCP, AI 도구화 신호를 별도 태깅합니다.
- `국민연금 사업장 MCP` 같은 capability 후보는 `config/categories/govsupport.yaml`의 `integration_candidates`에서 관리합니다.
- capability 후보 메모: [integration-candidates.md](/home/kjs/projects/ai-frendly-datahub/GovRadar/docs/integration-candidates.md)

## 디렉터리 구성

```
GovRadar/
  main.py
  govradar/
  config/
    config.yaml
    categories/
      govsupport.yaml
  data/
  reports/
  tests/
  .github/workflows/radar-crawler.yml
```

<!-- DATAHUB-OPS-AUDIT:START -->
## DataHub Operations

- CI/CD workflows: `deploy-pages.yml`, `health-check.yml`, `pr-checks.yml`, `radar-crawler.yml`, `release.yml`.
- GitHub Pages visualization: `reports/index.html` (valid HTML); https://ai-frendly-datahub.github.io/GovRadar/.
- Latest remote Pages check: HTTP 200, HTML.
- Local workspace audit: 45 Python files parsed, 0 syntax errors.
- Re-run audit from the workspace root: `python scripts/audit_ci_pages_readme.py --syntax-check --write`.
- Latest audit report: `_workspace/2026-04-14_github_ci_pages_readme_audit.md`.
- Latest Pages URL report: `_workspace/2026-04-14_github_pages_url_check.md`.
<!-- DATAHUB-OPS-AUDIT:END -->
