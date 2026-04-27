# GovRadar Integration Candidates

`GovRadar`는 공고/뉴스형 source와 자격검증형 capability 후보를 분리해서 관리한다.

## 원칙

- `sources`: 신청 공고, 정책 브리핑, 실행 시그널처럼 시계열 리포트에 들어가는 source
- `integration_candidates`: 에이전트가 필요할 때 직접 질의하는 capability 후보

## 현재 후보

- `국민연금 사업장 MCP`
  - 역할: 사업장 가입 여부 및 기초 자격 검증
  - 이유: 공공데이터 기반의 고가치 source지만 시계열 공고 피드가 아니라 lookup capability에 가깝다
  - 현재 위치: `config/categories/govsupport.yaml`의 `integration_candidates`
  - 향후 쓰임새: 신청 대상 검증, 기업 기본정보 확인, eligibility workflow 보강

## 데이터 품질 backlog

- `source_backlog.selection_result_candidates`는 선정 결과와 집행 실적을 공고 원문과 별도 후행 이벤트로 붙이기 위한 후보 큐다.
- `source_backlog.eligibility_capability_candidates`는 신청 가능성 점수 계산에 필요한 lookup capability 후보이며, 기본 `sources`로 올리기 전에 API key 범위와 tool contract를 검증한다.
- 활성화 기준은 `program_id_mapping`, `selection_result_parser`, `evidence_url_check`를 통과하는 것이다. 이 기준을 통과하지 않으면 지원사업 공고와 선정 결과를 같은 신뢰 등급으로 병합하지 않는다.
