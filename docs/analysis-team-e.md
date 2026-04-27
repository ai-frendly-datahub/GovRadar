# GovRadar Source Analysis (Team E)

Analysis timestamp: 2026-03-19 (Playwright MCP `browser_run_code`, dialog handler applied: `page.on('dialog', async d => { await d.accept(); });`).

Target set: National portal sources #53-#60.

| # | Source | Status | Selector | Items | Verdict |
|---|--------|--------|----------|-------|---------|
| 53 | 기업마당 지원사업 | 200 | table tbody tr | 15 | OK |
| 54 | 기업마당 행사정보 | 200 | table tbody tr | 15 | OK |
| 55 | 소상공인24 | 200 | table tbody tr | 10 | FIX |
| 56 | K-Startup 진행중 사업 | 200 | [class*=list] li | 60 | FIX |
| 57 | 창업진흥원 KISED | 200 | .item | 19 | FIX |
| 58 | 한국산업기술진흥협회 KOITA | 200 | table tbody tr | 10 | OK |
| 59 | 중소벤처기업진흥공단 KOSME | 200 | [class*=list] li | 198 | FIX |
| 60 | 중소기업유통센터 | ERR_NAME_NOT_RESOLVED | none | 0 | DEAD |

## 53. 기업마당 지원사업

| Field | Value |
|---|---|
| URL | https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do |
| HTTP Status | 200 |
| Page Title | 기업마당>정책정보>지원사업 공고 |
| Final URL | https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do?null |
| Best Selector | table tbody tr:15 |
| DOM Selectors | table tbody tr:15, tbody tr:15, [class*=list] li:32, ul li:75 |

### Sample Data
1. 2026년 해외진출 맞춤형 수출 지원(수출GO) 참가기업 모집 공고 -> https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?hashCode=&rowsSel=&rows=15&cpage=&cat=&schPblancDiv=&schJrsdCodeTy=&schWntyAt=&schAreaDetailCodes=&schEndAt=N&orderGb=&sort=&preKeywords=&condition=&condition1=&keyword=&pblancId=PBLN_000000000119678
2. 2026년 일터혁신상생컨설팅 참여기업 모집 공고 -> https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?hashCode=&rowsSel=&rows=15&cpage=&cat=&schPblancDiv=&schJrsdCodeTy=&schWntyAt=&schAreaDetailCodes=&schEndAt=N&orderGb=&sort=&preKeywords=&condition=&condition1=&keyword=&pblancId=PBLN_000000000119677
3. 2026년 AI 기반 소형선박 충돌 예방 시스템 개발 실증 참여 모집 공고 -> https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?hashCode=&rowsSel=&rows=15&cpage=&cat=&schPblancDiv=&schJrsdCodeTy=&schWntyAt=&schAreaDetailCodes=&schEndAt=N&orderGb=&sort=&preKeywords=&condition=&condition1=&keyword=&pblancId=PBLN_000000000119676

### Issues
- Legacy path redirects to active board path.

### Recommended Config
```yaml
article_selector: "table tbody tr"
link_selector: "table tbody tr td a[href]"
wait_for: "table tbody tr"
```

## 54. 기업마당 행사정보

| Field | Value |
|---|---|
| URL | https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C127/AX/210/list.do |
| HTTP Status | 200 |
| Page Title | 기업마당>정책정보>행사정보 |
| Final URL | https://www.bizinfo.go.kr/sie/siea/selectSIEA430View.do?null |
| Best Selector | table tbody tr:15 |
| DOM Selectors | table tbody tr:15, tbody tr:15, [class*=list] li:10, ul li:53 |

### Sample Data
1. [인천] 기업 홍보 마케팅 콘텐츠 제작 실무 교육생 모집 -> https://www.bizinfo.go.kr/sie/siea/selectSIEA430Detail.do?condition=&schJrsdCodeTy=&schEndAt=&orderGb=&sort=&keyword=&area=all&rows=15&cpage=1&eventInfoId=EVEN_000000000068278
2. [경북] FTA 원산지증명서 서류작성 실습교육 안내 -> https://www.bizinfo.go.kr/sie/siea/selectSIEA430Detail.do?condition=&schJrsdCodeTy=&schEndAt=&orderGb=&sort=&keyword=&area=all&rows=15&cpage=1&eventInfoId=EVEN_000000000068277
3. [경북] 2026년 찾아가는 FTA 활용 교육 개최 안내 -> https://www.bizinfo.go.kr/sie/siea/selectSIEA430Detail.do?condition=&schJrsdCodeTy=&schEndAt=&orderGb=&sort=&keyword=&area=all&rows=15&cpage=1&eventInfoId=EVEN_000000000068276

### Issues
- Legacy path redirects to active board path.

### Recommended Config
```yaml
article_selector: "table tbody tr"
link_selector: "table tbody tr td a[href]"
wait_for: "table tbody tr"
```

## 55. 소상공인24

| Field | Value |
|---|---|
| URL | https://www.sbiz24.kr/#/pbanc |
| HTTP Status | 200 |
| Page Title | 소상공인24 소진공 공고조회 및 신청 |
| Final URL | https://www.sbiz24.kr/#/pbanc |
| Best Selector | table tbody tr:10 |
| DOM Selectors | table tbody tr:10, tbody tr:10, [class*=list] li:85, ul li:287 |

### Sample Data
1. 고용보험 미적용자 출산(유산·사산) 급여 지원 사업 공고 -> https://www.sbiz24.kr/#/pbanc/607
2. 2026년 소상공인 고용보험료 지원사업 공고 -> https://www.sbiz24.kr/#/pbanc/559
3. 2026년 중소기업 수출지원사업 통합공고 -> https://www.sbiz24.kr/#/pbanc/553

### Issues
- SPA hash-routing page; static HTML is minimal and reliable extraction requires JS-render wait.
- Anonymous session produced 401 refresh-token errors in console, but board rows still rendered.

### Recommended Config
```yaml
article_selector: "table tbody tr"
link_selector: "table tbody tr td a[href^='#/pbanc/']"
wait_for: "table tbody tr"
```

## 56. K-Startup 진행중 사업

| Field | Value |
|---|---|
| URL | https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do |
| HTTP Status | 200 |
| Page Title | K-Startup 창업지원포털>사업공고>모집중 |
| Final URL | https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do |
| Best Selector | [class*=list] li:60 |
| DOM Selectors | [class*=list] li:60, ul li:215, .item:2 |

### Sample Data
1. 2026 창업지원사업통합공고 -> https://www.k-startup.go.kr/web/contents/webFSBIPBANC.do
2. 사업신청관리 -> https://www.k-startup.go.kr/passni/kstartup/tokenInfoRelay.jsp?flag=biz
3. 회원가입 -> https://www.k-startup.go.kr/web/contents/webMEMB_JOIN.do

### Issues
- Current static DOM mostly exposes portal/service links, not clean per-notice detail rows.
- Recommend tighter selector after confirming live-rendered notice block in production crawl run.

### Recommended Config
```yaml
article_selector: "[class*=list] li"
link_selector: "[class*=list] li a[href*='web/contents/'], [class*=list] li a[href*='biz']"
wait_for: "[class*=list] li"
```

## 57. 창업진흥원 KISED

| Field | Value |
|---|---|
| URL | https://www.kised.or.kr/index.es?sid=a1 |
| HTTP Status | 200 |
| Page Title | 창업진흥원 |
| Final URL | https://www.kised.or.kr/index.es?sid=a1 |
| Best Selector | .item:19 |
| DOM Selectors | .item:19, [class*=list] li:4, ul li:234 |

### Sample Data
1. 첨단제조 스타트업 스케일업 지원사업 -> https://www.kised.or.kr/menu.es?mid=a10205200000
2. 글로벌 창업허브 사업 -> https://www.kised.or.kr/menu.es?mid=a10211040000
3. 1인 창조기업 활성화 지원사업 -> https://www.kised.or.kr/menu.es?mid=a10211050000

### Issues
- Home page mixes policy menus, banners, and notice blocks; `.item` is broad and should be narrowed for production collector.

### Recommended Config
```yaml
article_selector: ".item"
link_selector: ".item a[href*='menu.es?mid=']"
wait_for: ".item"
```

## 58. 한국산업기술진흥협회 KOITA

| Field | Value |
|---|---|
| URL | https://www.koita.or.kr/board/commBoardNotice003List.do |
| HTTP Status | 200 |
| Page Title | 사업공고 | KOITA 한국산업기술진흥협회 |
| Final URL | https://www.koita.or.kr/board/commBoardNotice003List.do |
| Best Selector | table tbody tr:10 |
| DOM Selectors | table tbody tr:10, tbody tr:10, [class*=list] li:281, ul li:291 |

### Sample Data
1. 사업공고 -> https://www.koita.or.kr/board/commBoardNotice003List.do
2. 정부 및 지자체 R&D사업 공고 -> https://www.koita.or.kr/board/commBoardGovRnDList.do
3. 교류회 설립운영 및 지원 -> https://www.koita.or.kr/conts/105003001000000.do

### Issues
- Board table is stable, but site-wide list elements are numerous; crawler should avoid generic `[class*=list] li`.

### Recommended Config
```yaml
article_selector: "table tbody tr"
link_selector: "table tbody tr td a[href]"
wait_for: "table tbody tr"
```

## 59. 중소벤처기업진흥공단 KOSME

| Field | Value |
|---|---|
| URL | https://www.kosmes.or.kr/nsh/map/main.do |
| HTTP Status | 200 |
| Page Title | 중소벤처기업진흥공단 홈페이지 |
| Final URL | https://www.kosmes.or.kr/nsh/map/main.do |
| Best Selector | [class*=list] li:198 |
| DOM Selectors | [class*=list] li:198, ul li:268 |

### Sample Data
1. 국민신문고 -> https://www.epeople.go.kr/
2. 기술사관 육성사업 -> https://www.smes.go.kr/sanhakin/?w2xPath=/wqxml/usr/10intd/intdBizTecho.xml
3. 중소기업 계약학과 -> https://www.smes.go.kr/sanhakin/?w2xPath=/wqxml/usr/10intd/intdBizCndept.xml

### Issues
- Main page is portal-style; list selector captures many navigation/service links.
- Dedicated notice endpoint is preferable for high-precision policy crawling.

### Recommended Config
```yaml
article_selector: "[class*=list] li"
link_selector: "[class*=list] li a[href]"
wait_for: "[class*=list] li"
```

## 60. 중소기업유통센터

| Field | Value |
|---|---|
| URL | http://www.smemall.or.kr/ |
| HTTP Status | ERR_NAME_NOT_RESOLVED |
| Page Title | (unavailable) |
| Final URL | (unavailable) |
| Best Selector | none:0 |
| DOM Selectors | none |

### Sample Data
1. (DNS resolution failure; no content links extracted) -> -
2. - -> -
3. - -> -

### Issues
- DNS lookup failed (`getaddrinfo ENOTFOUND www.smemall.or.kr`).

### Recommended Config
```yaml
article_selector: ""
link_selector: "a[href]"
wait_for: "body"
```
