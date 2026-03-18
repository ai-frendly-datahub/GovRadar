# GovRadar

GovRadar는 한국 정부지원/보조금/정책 공고를 수집해 엔티티 분석 후 리포트를 생성하는 Standard Tier 레이더입니다.

## Purpose

- 중앙부처, 공공기관, 지자체의 지원사업 공고 RSS 수집
- 지원유형/대상자/부처/지역/신청기간 엔티티 태깅
- DuckDB 기반 누적 저장 및 보존 정책 적용
- HTML 리포트 생성 후 GitHub Pages 배포

## Project Structure

```
GovRadar/
├── main.py
├── govradar/
│   ├── collector.py
│   ├── analyzer.py
│   ├── reporter.py
│   ├── storage.py
│   ├── date_storage.py
│   ├── notifier.py
│   └── common/
├── config/
│   ├── config.yaml
│   └── categories/
│       └── govsupport.yaml
├── data/
├── reports/
├── tests/
└── .github/workflows/radar-crawler.yml
```

## Runtime

- 기본 실행: `python main.py --category govsupport --recent-days 7`
- DB 파일: `data/govradar_data.duckdb`
- 리포트: `reports/govsupport_report.html`
- 스케줄: GitHub Actions cron `0 22 * * *` (KST 07:00)

## Notes

- `radar_core` 패키지는 공용 라이브러리이며 import 경로를 유지합니다.
- 카테고리/소스 정의는 `config/categories/govsupport.yaml`만 수정해 확장합니다.
