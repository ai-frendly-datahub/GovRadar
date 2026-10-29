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

## 운영 계약

Radar-Template PR #4와 같은 수집·저장 계약을 유지합니다. 시크릿 값은 코드, YAML, 로그, skip 파일에 넣지 않습니다.

1. **radar-core 핀.** `requirements.txt`, `pyproject.toml`, `setup.cfg`는 `radar-core @ git+https://github.com/ai-frendly-datahub/radar-core.git@main` 입니다.
2. **스냅샷 전에 압축.** `apply_date_storage_policy()`와 `RadarStorage.create_daily_snapshot()`은 복사 전에 `radar_core.db_compact.compact_duckdb_file`를 호출합니다. 압축이 실패해도 기존 파일을 스냅샷합니다.
3. **피드 클라이언트.** User-Agent는 `GovRadar/0.1` 입니다. RSS 타임아웃 기본값은 45초입니다. TLS 검증은 항상 켭니다. Cloudflare, "Just a moment", 쿠키 월, 403/404 페이지 제목은 저장하기 전에 버립니다.
4. **없는 시크릿.** 소스마다 GitHub `::warning`을 한 번 출력합니다. `data/raw/<날짜>/<소스>.skip.json`에는 환경 변수 이름만 기록합니다. 수집 실패는 빈 리스트이며 샘플 데이터를 만들지 않습니다.
5. **실패해야 하는 실행.** 활성 소스의 수집이 0건이면 종료 코드 1입니다. 출력이 0바이트이거나 DuckDB가 100MiB 이상이면 워크플로가 실패합니다. 데이터 auto-commit/push에는 `continue-on-error`가 없습니다.
6. **Pages는 푸시 성공 후에만.** `gh-pages` 배포는 auto-commit `outcome == success`일 때만 실행됩니다.
7. **테스트.** 날짜 단정은 `tests/reference_dates.py`(2026-03-13 12:00 UTC)와 `tests/fixtures/`를 사용합니다. 커버리지는 `relative_files = true`입니다.
8. **robots.txt.** radar-core 수집기는 robots.txt를 보지 않습니다. 실행 전에 GovRadar가 읽고, `Disallow`인 URL은 가져오지 않습니다. `www.gov.kr` 보조금 목록과 `www.semas.or.kr` 공고 목록은 `Disallow: /`라 소스가 꺼져 있습니다.

## 공식 API 키

키 값은 코드, YAML, 로그에 넣지 않습니다. 환경 변수가 없으면 해당 소스는 호출하지 않고 건너뜁니다.

| 소스 | 환경 변수 |
| --- | --- |
| K-Startup 지원사업 공고 | `DATA_GO_KR_KSTARTUP_SERVICE_KEY` |
| 보조금24 공공서비스 | `DATA_GO_KR_SUBSIDY24_SERVICE_KEY` |
| 기업마당 지원사업 공고 | `DATA_GO_KR_BIZINFO_SERVICE_KEY` |

## 소스별 선택 설정 (RSS 소스의 `config:`)

| 키 | 설명 |
| --- | --- |
| `fetch_detail_summary: true` | RSS에 본문이 없는 소스의 빈 `summary`를 공개 기사 페이지에서 채웁니다. robots.txt 허용 URL만, TLS 검증 유지, 피드와 같은 호스트만, 요청 간격 1초, 소스당 실행 1회 30건 상한. 실패하면 비워 둡니다. |
| `detail_summary_selectors` | 본문 위치 CSS 선택자 목록 |
| `detail_summary_prefer_meta: true` | meta description을 본문보다 먼저 사용 |
| `detail_upgrade_https: true` | 피드 링크가 `http://`일 때 `https://`로 올려 가져옴 |
| `detail_summary_max_chars`, `detail_summary_max_per_run`, `detail_min_interval_seconds` | 길이·건수·간격 조정 |
| `exclude_title_prefixes: [...]` | 제목이 해당 접두어로 시작하는 항목을 수집 단계에서 제외 (검증된 경우에만 사용) |

일반 뉴스 피드의 키워드 포함 게이트는 모델 분류 대비 검증에서 유용 항목을 과하게 지워 도입하지 않았습니다. 근거는 `docs/noise_gate_validation_2026-10-29.md`를 보세요.

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
