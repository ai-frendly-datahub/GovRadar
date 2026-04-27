# Data Quality Plan

- 생성 시각: `2026-04-11T16:05:37.910248+00:00`
- 우선순위: `P0`
- 데이터 품질 점수: `96`
- 가장 약한 축: `추적성`
- Governance: `high`
- Primary Motion: `conversion`

## 현재 이슈

- 현재 설정상 즉시 차단 이슈 없음. 운영 지표와 freshness SLA만 명시하면 됨

## 필수 신호

- 지원사업 공고 원문과 신청 마감일
- 대상자·업종·지역 eligibility 조건
- 선정 결과와 집행 실적

## 품질 게이트

- 접수 시작/마감/선정 발표일을 별도 필드로 유지
- 지원금 규모와 신청 자격은 원문 기준으로 trace 가능해야 함
- 마감일 파싱 실패 시 경고를 남기고 임의 추정하지 않음

## 다음 구현 순서

- application_deadline과 eligibility_rule freshness/stale 리포트를 검증 산출물에 추가
- 선정 결과/집행 실적 후보는 source_backlog에서 parser·program id mapping·evidence URL 검증 후 단계적 활성화
- 지원사업별 신청 가능성 점수와 근거 URL을 결과 리포트에 함께 출력

## 운영 규칙

- 원문 URL, 수집일, 이벤트 발생일은 별도 필드로 유지한다.
- 공식 source와 커뮤니티/시장 source를 같은 신뢰 등급으로 병합하지 않는다.
- collector가 인증키나 네트워크 제한으로 skip되면 실패를 숨기지 말고 skip 사유를 기록한다.
- 이 문서는 `scripts/build_data_quality_review.py --write-repo-plans`로 재생성한다.
