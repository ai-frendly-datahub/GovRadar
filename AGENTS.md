# GovRadar

GovRadar는 한국 정부지원 정책/보조금 공고를 수집, 분석, 리포팅하는 Standard Tier 레이더입니다.

## Purpose

- 중앙부처/공공기관/지자체 지원사업 공고를 수집합니다.
- 지원유형, 대상군, 부처, 지역, 신청정보 엔티티를 태깅합니다.
- 결과를 DuckDB에 누적 저장하고 HTML 리포트로 배포합니다.

## Structure

- `main.py`: 수집 -> 분석 -> 저장 -> 리포트 파이프라인 실행
- `govradar/`: 도메인 모듈(collector, reporter, date_storage, validators, notifier)
- `config/categories/govsupport.yaml`: GovRadar 전용 소스/엔티티 정의
- `.github/workflows/radar-crawler.yml`: 일일 크롤링 + Pages 배포

## Sources

- RSS + 브라우저 수집 혼합 구성
- 주요 사이트: 정부24, 정책브리핑, 고용노동부, 중소벤처기업부, 기획재정부, K-Startup, 보조금24, 서울시, 경기도
- JS 렌더링 페이지는 `collection_method: browser`(Playwright Chromium) 사용

## Deviations from Template

- 패키지명은 `radar`가 아닌 `govradar`를 사용합니다.
- 기본 카테고리는 `template`가 아닌 `govsupport`입니다.
- DB 기본 경로는 `data/govradar_data.duckdb`입니다.
- `radar_core`는 외부 공용 의존성으로 유지하며 import 경로를 변경하지 않습니다.
