# GovRadar - 한국 정부지원 레이더

**🌐 Live Report**: https://ai-frendly-datahub.github.io/GovRadar/

한국 정부지원금/보조금/지원사업 공고를 매일 수집하고 엔티티 기반으로 분류해 추적 리포트를 제공하는 Standard Tier 레이더 프로젝트입니다.

## 프로젝트 목표

- **정부지원 정보 수집**: 중앙부처/지자체/공공기관 RSS 기반 공고 자동 수집
- **엔티티 분석**: 지원유형, 대상자, 부처, 지역, 신청기간 키워드 자동 태깅
- **리포트 생성**: DuckDB 저장 + HTML 리포트로 최근 동향 시각화
- **자동화 운영**: GitHub Actions 일일 실행 + GitHub Pages 자동 배포

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
