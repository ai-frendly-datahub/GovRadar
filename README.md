# GovRadar - 한국 정부지원 레이더

**Live Report**: https://ai-frendly-datahub.github.io/GovRadar/

한국 정부지원 정책, 보조금, 지원사업 공고를 수집·분석하는 레이더입니다.

## 데이터소스

| 소스 | 수집 방식 | 분류 |
|------|----------|------|
| 정부24 보조금 | Playwright | 중앙부처 |
| 정책브리핑 | RSS | 중앙부처 |
| 고용노동부 | RSS | 중앙부처 |
| 중소벤처기업부 | RSS | 중앙부처 |
| 기획재정부 | RSS | 중앙부처 |
| 산업통상자원부 | Playwright | 중앙부처 |
| 과학기술정보통신부 | Playwright | 중앙부처 |
| 국토교통부 | Playwright | 중앙부처 |
| K-Startup | Playwright | 창업 |
| 소상공인시장진흥공단 | Playwright | 소상공인 |
| 서울시 지원사업 | Playwright | 지자체 |
| KIAT 한국산업기술진흥원 | Playwright | 기술 R&D |

## 실행

```bash
pip install -r requirements.txt
python main.py --category govsupport --recent-days 7
```

## 파이프라인

RSS/Playwright 수집 → 엔티티 태깅 (지원유형/대상/부처/지역/접수정보) → DuckDB 저장 → HTML 리포트 → GitHub Pages 배포
