# Business Quality Upgrade

- Generated: `2026-04-14T04:48:11.525239+00:00`
- Portfolio verdict: `충분`
- Business value score: `89.3`
- Upgrade phase: P0 후행 검증 이벤트 추적
- Primary motion: `conversion`
- Weakest dimension: `traceability`

## Current Evidence

- Primary rows: `1682`
- Today raw rows: `52`
- Latest report items: `66`
- Match rate: `100.0%`
- Collection errors: `0`
- Freshness gap: `6`

## Upgrade Actions

- selection_result를 tracked_event_models에 포함해 선정 결과와 집행 실적을 품질 리포트에서 감시한다.
- application_deadline과 eligibility_rule의 stale/missing 현황을 지원사업별 근거 URL과 함께 노출한다.
- K-Startup/보조금24 후행 결과 후보는 parser, program_id mapping, evidence_url 검증 후 활성화한다.

## Quality Contracts

- `config/categories/govsupport.yaml`: output `reports/govsupport_quality.json`, tracked `support_program_notice, application_deadline, eligibility_rule, selection_result`, backlog items `3`

## Contract Gaps

- None.
