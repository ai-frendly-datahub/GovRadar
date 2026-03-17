# GovRadar 데이터소스 분석 보고서

분석일: 2026-03-17

## 요약

| 상태 | 수 | 비율 |
|---|---|---|
| ✅ 정상 (200 OK) | 55 | 81% |
| ❌ 404/URL변경 | 6 | 9% |
| ❌ SSL 오류 | 4 | 6% |
| ❌ DNS 실패 | 1 | 1% |
| ⚠️ SPA/극소응답 | 2 | 3% |
| **전체** | **68** | **100%** |

## 전체 소스 상태

| # | 소스명 | HTTP | 응답크기 | 셀렉터 | 상태 |
|---|--------|------|----------|--------|------|
| 1 | 산업통상자원부 | 404 | — | — | ❌ URL 변경 |
| 2 | 과학기술정보통신부 | 200 | 168KB | `ul[class*=list] li:29`, `dl dt:33` | ✅ |
| 3 | 국토교통부 | 200 | — | `table tbody tr:10` | ✅ |
| 4 | 정부24 보조금 | 200 | 413KB | `[class*=item]:36`, `div.card-head a` | ✅ |
| 5 | K-Startup(구) | 404 | — | — | ❌ URL 변경 |
| 6 | 소상공인시장진흥공단 | 200 | 68KB | `table tbody tr:10` | ✅ |
| 7 | 서울시 지원사업 | 200 | 77KB | `table tbody tr:10` | ✅ |
| 8 | KIAT 한국산업기술진흥원 | 404 | — | — | ❌ URL 변경 |
| 9 | 경기기업비서 | 200 | 172KB | `ul[class*=list] li:72`, `div.card-body a` | ✅ |
| 10 | 경기도주식회사 | 200 | 26KB | `li a` (커스텀 리스트) | ✅ |
| 11 | 경기도일자리포털 | 200 | 156KB | TBD | ✅ |
| 12 | 고양스타특업 | 200 | 41KB | TBD | ✅ |
| 13 | 수원창업지원포털 | 200 | 437KB | TBD | ✅ |
| 14 | 성남산업진흥원 | 200 | 20KB | TBD | ✅ |
| 15 | 의정부 기업지원포털 | 200 | 27KB | TBD | ✅ |
| 16 | 과천시 | 200 | 352KB | TBD | ✅ |
| 17 | 시흥시산업진흥원 | 200 | 28KB | TBD | ✅ |
| 18 | 시흥시 창업센터 | 200 | 116KB | TBD | ✅ |
| 19 | 용인시 | 200 | 34KB | TBD | ✅ |
| 20 | 파주시 | 200 | 290KB | TBD | ✅ |
| 21 | 이천시 | ERR | — | — | ❌ SSL 인증서 |
| 22 | 안성시 | 200 | 364KB | TBD | ✅ |
| 23 | 김포시산업지원 | 200 | 9KB | TBD | ✅ |
| 24 | 화성시 | ERR | — | — | ❌ SSL 인증서 |
| 25 | 연천군 | 200 | 228KB | TBD | ✅ |
| 26 | 가평군 기업지원 | 200 | 279KB | TBD | ✅ |
| 27 | 가평군 소상공인 | 200 | 277KB | TBD | ✅ |
| 28 | 서울시 소상공인 종합지원 | 200 | 3KB | TBD | ⚠️ SPA |
| 29 | 인천광역시 | 200 | 42KB | TBD | ✅ |
| 30 | 부산창업포털 | 200 | 123KB | TBD | ✅ |
| 31 | 서울경제진흥원 | 200 | 378KB | TBD | ✅ |
| 32 | 서울시 R&D 지원 | 200 | 26KB | TBD | ✅ |
| 33 | 인천창업플랫폼 | 200 | 35KB | TBD | ✅ |
| 34 | 광주광역시 | ERR | — | — | ❌ SSL 인증서 |
| 35 | 대구광역시 창업플랫폼 | 200 | 78KB | TBD | ✅ |
| 36 | 대전광역시 | ERR | — | — | ❌ SSL 인증서 |
| 37 | 세종특별자치시 창업플랫폼 | 404 | — | — | ❌ URL 변경 |
| 38 | 울산정보산업진흥원 | 200 | 2KB | TBD | ⚠️ SPA |
| 39 | 여수시 | 200 | 480KB | TBD | ✅ |
| 40 | 경상북도 | 200 | 117KB | TBD | ✅ |
| 41 | 경남창업포털 | 404 | — | — | ❌ URL 변경 |
| 42 | 강원지역산업진흥원 | 200 | 70KB | TBD | ✅ |
| 43 | 강원특별자치도경제진흥원 | 200 | 67KB | TBD | ✅ |
| 44 | 충청북도 시책사업 | 200 | 31KB | TBD | ✅ |
| 45 | 충청남도경제진흥원 | 200 | 39KB | TBD | ✅ |
| 46 | 전북 중소기업종합지원 | 200 | 97KB | TBD | ✅ |
| 47 | 전남창업지원플랫폼 | 200 | 29KB | TBD | ✅ |
| 48 | 잇지제주 | 200 | 1.6MB | TBD | ✅ |
| 49 | 경남기업119 | 200 | 69KB | TBD | ✅ |
| 50 | 충청북도 도내시책사업 | 200 | 30KB | TBD | ✅ |
| 51 | 전북경제통상진흥원 | 200 | 50KB | TBD | ✅ |
| 52 | 제주경제통상진흥원 | 200 | 98KB | TBD | ✅ |
| 53 | 기업마당 지원사업 | 200 | 109KB | TBD | ✅ |
| 54 | 기업마당 행사정보 | 200 | 77KB | TBD | ✅ |
| 55 | 소상공인24 | 200 | 3KB | TBD | ⚠️ SPA |
| 56 | K-Startup 진행중 사업 | 200 | 182KB | TBD | ✅ |
| 57 | 창업진흥원 KISED | 200 | 100KB | TBD | ✅ |
| 58 | 한국산업기술진흥협회 KOITA | 200 | 157KB | TBD | ✅ |
| 59 | 중소벤처기업진흥공단 KOSME | 200 | 191KB | TBD | ✅ |
| 60 | 중소기업유통센터 | ERR | — | — | ❌ DNS 소멸 |
| 61 | 중소기업기술정보진흥원 TIPA | 200 | 2KB | TBD | ⚠️ SPA |
| 62 | 한국콘텐츠진흥원 KOCCA | 200 | 214KB | TBD | ✅ |
| 63 | 정보통신산업진흥원 NIPA | 200 | 3KB | TBD | ⚠️ SPA |
| 64 | 지역지식재산센터 RIPC | 200 | 22KB | TBD | ✅ |
| 65 | 한국특허전략개발원 KISTA | 200 | 233KB | TBD | ✅ |
| 66 | 지식재산보호원 IP-NAVI | 200 | 59KB | TBD | ✅ |
| 67 | KEIT 산업기술평가관리원 | 200 | 73KB | TBD | ✅ |
| 68 | 서울창업허브 | 200 | 123KB | TBD | ✅ |

## 상세 분석 (Playwright 검증 완료분)

### 1. 산업통상자원부
- **URL**: https://www.motie.go.kr/motie/py/brf/motiebriefing/motiebriefingList.do
- **상태**: ❌ 404 — URL 변경됨
- **조치**: 새 URL 탐색 필요

### 2. 과학기술정보통신부
- **URL**: https://www.msit.go.kr/bbs/list.do?sCode=user&mPid=74&mId=99
- **상태**: ✅ 200
- **페이지 제목**: 통계정보 - 과학기술정보통신부
- **셀렉터**: `dl dt:33`, `ul[class*=list] li:29`
- **추천**: `article_selector: "ul[class*=list] li"`, `link_selector: "ul[class*=list] li a"`

### 3. 국토교통부
- **URL**: https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp
- **상태**: ✅ 200
- **페이지 제목**: 보도자료
- **셀렉터**: `table tbody tr:10`
- **샘플**: "'26년 공동주택 공시가격(안) 열람"
- **추천**: `article_selector: "table tbody tr"`, `link_selector: "td.bd_title a"`

### 4. 정부24 보조금
- **URL**: https://www.gov.kr/portal/rcvfvrSvc/svcFind/svcSearchAll
- **상태**: ✅ 200
- **페이지 제목**: 전체 혜택 | 보조금24 | 정부24
- **셀렉터**: `[class*=item]:36`, `div.card-head a`
- **샘플**: "국민내일배움카드", "근로·자녀장려금", "국민취업지원제도"
- **추천**: `article_selector: "[class*=item]"`, `link_selector: "div.card-head a"`
- **비고**: 10,915건 보조금 데이터, 페이지네이션 필요

### 5. K-Startup (구URL)
- **URL**: https://www.k-startup.go.kr/unifyinfo/info/openinfo/notice.do
- **상태**: ❌ 404 — URL 변경
- **조치**: 신규 URL 별도 등록됨 (#56)

### 6. 소상공인시장진흥공단
- **URL**: https://www.semas.or.kr/web/board/webBoardList.kmdc?bCd=1
- **상태**: ✅ 200
- **셀렉터**: `table tbody tr:10`
- **샘플**: "소상공인 재난지원금 환수 결정통지 반송에 따른 공시송달 공고"
- **추천**: `article_selector: "table tbody tr"`, `link_selector: "td.left a"`
- **비고**: javascript:fncGoDetail() 패턴 — href 추출 시 JS 호출 처리 필요

### 7. 서울시 지원사업
- **URL**: https://www.seoul.go.kr/news/news_notice.do
- **상태**: ✅ 200
- **셀렉터**: `table tbody tr:10`
- **추천**: `article_selector: "table tbody tr"`, `link_selector: "td a"`

### 8. KIAT 한국산업기술진흥원
- **URL**: https://www.kiat.or.kr/front/board/boardContents.do?board_id=21
- **상태**: ❌ 404 — CSS/폰트 모두 404, 사이트 리뉴얼
- **조치**: 새 URL 탐색 필요

### 9. 경기기업비서
- **URL**: https://www.egbiz.or.kr/sp/supportPrjAreaList.do
- **상태**: ✅ 200
- **셀렉터**: `ul[class*=list] li:72`, `div.card-body a`
- **샘플**: "[경기] 성남시 베트남 국제 프리미엄 소비재전 참가기업 모집", "[경기] 로봇 실증 지원 사업"
- **추천**: `article_selector: "div.card-body"`, `link_selector: "div.card-body a"`
- **비고**: 카드형 레이아웃, href는 모두 # (JS 이벤트) — 클릭 기반 추출 필요

### 10. 경기도주식회사
- **URL**: https://www.kgcbrand.com/KGCBrand/businessNoticeList.do
- **상태**: ✅ 200
- **셀렉터**: 표준 셀렉터 매칭 안됨, `li a` 커스텀
- **샘플**: "진행중 2026-03-12..." → businessNoticeDetail.do?BoardID=2361
- **추천**: `article_selector: "li"`, `link_selector: "li a[href*=businessNoticeDetail]"`

## 문제 소스 분류

### ❌ URL 변경 (6개) — 새 URL 탐색 필요
1. 산업통상자원부
2. K-Startup (구URL) — #56에 신규 URL 존재
3. KIAT 한국산업기술진흥원
4. 세종특별자치시 창업플랫폼
5. 경남창업포털
6. 중소기업유통센터 (DNS 소멸)

### ❌ SSL 인증서 오류 (4개) — verify=False 또는 대체 URL 필요
1. 이천시
2. 화성시
3. 광주광역시
4. 대전광역시

### ⚠️ SPA/극소응답 (5개) — Playwright 렌더링 대기 시간 증가 필요
1. 서울시 소상공인 종합지원 (3KB)
2. 울산정보산업진흥원 (2KB)
3. 소상공인24 (3KB)
4. 중소기업기술정보진흥원 TIPA (2KB)
5. 정보통신산업진흥원 NIPA (3KB)
