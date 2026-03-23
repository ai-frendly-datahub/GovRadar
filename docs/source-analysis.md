# GovRadar Browser Source Analysis (govsupport)

Analysis timestamp: 2026-03-19 (Playwright MCP, 2.5s JS wait per source).

Note: `GovRadar/config/categories/govsupport.yaml` currently contains **8** `collection_method: browser` sources (not 68). This document covers all browser sources present in that file.

| # | Source | Status | Selector | Items | Verdict |
|---|--------|--------|----------|-------|---------|
| 1 | 정부24 보조금 | 200 | ul[class*=list] li | 61 | FIX |
| 2 | K-Startup | 404 | table tbody tr | 2 | DEAD |
| 3 | 소상공인시장진흥공단 | 200 | table tbody tr | 10 | OK |
| 4 | 산업통상자원부 | 404 | none | 0 | DEAD |
| 5 | 과학기술정보통신부 | 200 | ul[class*=list] li | 29 | FIX |
| 6 | 보조금24 | 200 | article | 3 | FIX |
| 7 | 서울시 지원사업 | 200 | table tbody tr | 10 | FIX |
| 8 | 경기도 지원사업 | 404 | none | 0 | DEAD |

## 1. 정부24 보조금

| Field | Value |
|---|---|
| URL | https://www.gov.kr/portal/rcvfvrSvc/svcFind/svcSearchAll |
| HTTP Status | 200 |
| Page Title | 전체 혜택 \| 보조금24 \| 정부24 |
| Body Size | 2708ch |
| Best Selector | ul[class*=list] li:61 |
| Article Selector | ul[class*=list] li |
| Link Selector | a[href*='rcvfvrSvc/dtlEx'] |

### Sample Data
1. 내집마련 디딤돌 대출 → https://www.gov.kr/portal/rcvfvrSvc/dtlEx/B55140800003?administOrgCd=ALL
2. 장기전세 주택공급 → https://www.gov.kr/portal/rcvfvrSvc/dtlEx/999000000024?administOrgCd=ALL
3. 혜택 조회하기(보조금24) → https://www.gov.kr/portal/rcvfvrSvc/main

### Issues
- Anti-bot scripts and repeated telemetry calls observed in console.
- Some links inside list blocks are hash/navigation links, not article detail links.

### Recommended Config
```yaml
article_selector: "ul[class*=list] li"
link_selector: "a[href*='rcvfvrSvc/dtlEx']"
wait_for: "ul[class*=list] li"
```

## 6. K-Startup

| Field | Value |
|---|---|
| URL | https://www.k-startup.go.kr/unifyinfo/info/openinfo/notice.do |
| HTTP Status | 404 |
| Page Title | 알림 |
| Body Size | 25ch |
| Best Selector | table tbody tr:2 |
| Article Selector | table tbody tr |
| Link Selector | td a[href] |

### Sample Data
1. (no usable article rows found) → -
2. - → -

### Issues
- URL returns HTTP 404.
- Page body is too small for crawling; only error/alert-type content detected.

### Recommended Config
```yaml
article_selector: "table tbody tr"
link_selector: "td a[href]"
wait_for: "table tbody tr"
```

## 7. 소상공인시장진흥공단

| Field | Value |
|---|---|
| URL | https://www.semas.or.kr/web/board/webBoardList.kmdc?bCd=1 |
| HTTP Status | 200 |
| Page Title | 알림마당 〉 공지사항 |
| Body Size | 1026ch |
| Best Selector | table tbody tr:10 |
| Article Selector | table tbody tr |
| Link Selector | td a[href] |

### Sample Data
1. 기업가형 소상공인 발굴 육성 → https://www.semas.or.kr/web/SUP01/SUP0122/SUP012201.kmdc
2. 소상공인 맞춤형 성장 지원 → https://www.semas.or.kr/web/SUP01/SUP0123/SUP012304.kmdc
3. 소상공인 재기 경영안정망 강화 → https://www.semas.or.kr/web/SUP01/SUP0117/SUP011702.kmdc

### Issues
- Main table structure is stable, but first-link extraction can pull service-navigation links depending on crawl context.
- Several webfont decode warnings in console (non-fatal).

### Recommended Config
```yaml
article_selector: "table tbody tr"
link_selector: "td a[href]"
wait_for: "table tbody tr"
```

## 8. 산업통상자원부

| Field | Value |
|---|---|
| URL | https://www.motie.go.kr/motie/py/brf/motiebriefing/motiebriefingList.do |
| HTTP Status | 404 |
| Page Title | ERROR |
| Body Size | 91ch |
| Best Selector | none:0 |
| Article Selector | (none) |
| Link Selector | a[href] |

### Sample Data
1. 이전 페이지로 이동 → https://www.motie.go.kr/motie/py/brf/motiebriefing/motiebriefingList.do#
2. - → -

### Issues
- URL returns HTTP 404.
- No candidate article container matched in DOM.

### Recommended Config
```yaml
article_selector: ""
link_selector: "a[href]"
wait_for: "body"
```

## 9. 과학기술정보통신부

| Field | Value |
|---|---|
| URL | https://www.msit.go.kr/bbs/list.do?sCode=user&mPid=74&mId=99 |
| HTTP Status | 200 |
| Page Title | 통계정보 - 과학기술정보통신부 |
| Body Size | 1399ch |
| Best Selector | ul[class*=list] li:29 |
| Article Selector | ul[class*=list] li |
| Link Selector | ul[class*=list] li a[href] |

### Sample Data
1. 과학기술정보통신부 → https://www.msit.go.kr/index.do
2. 적극행정 국민추천 → https://www.mpm.go.kr/proactivePublicService/recommand/intro/
3. 청탁금지법 위반신고 → https://www.clean.go.kr/index.es?sid=a1

### Issues
- Current URL appears to be statistics/info page, not a clean announcement board.
- Extracted links are mostly portal/service links, not post detail links.

### Recommended Config
```yaml
article_selector: "ul[class*=list] li"
link_selector: "ul[class*=list] li a[href]"
wait_for: "ul[class*=list] li"
```

## 10. 보조금24

| Field | Value |
|---|---|
| URL | https://www.gosims.go.kr/hg/hg001/retrieveSubsSrch.do |
| HTTP Status | 200 |
| Page Title | 홈 \| 보조금통합포털 |
| Body Size | 1826ch |
| Best Selector | article:3 |
| Article Selector | article |
| Link Selector | article a[href] |

### Sample Data
1. 보조금 통합포털 AI서비스에 문의하세요. → https://bojo-ai.clabi.co.kr/
2. 크롬 브라우저 다운로드 → https://www.google.com/intl/ko_kr/chrome/
3. 엣지 브라우저 다운로드 → https://www.microsoft.com/ko-kr/edge/download?form=MA13FJ

### Issues
- Landing page content is mostly portal/help/browser-compat links, not direct subsidy announcements.
- Crawling announcement items likely requires additional navigation or form interaction.

### Recommended Config
```yaml
article_selector: "article"
link_selector: "article a[href]"
wait_for: "article"
```

## 11. 서울시 지원사업

| Field | Value |
|---|---|
| URL | https://www.seoul.go.kr/news/news_notice.do |
| HTTP Status | 200 |
| Page Title | 고시공고 \| 서울특별시 |
| Body Size | 1282ch |
| Best Selector | table tbody tr:10 |
| Article Selector | table tbody tr |
| Link Selector | td a[href] |

### Sample Data
1. 시정소식 문자알림서비스 → https://www.seoul.go.kr/seoul/smsAlarm/overView.do
2. 서울시 정책 뉴스 → https://www.seoul.go.kr/seoul/mediahub.do
3. 도시관리계획안 열람공고 → https://urban.seoul.go.kr/view/html/PMNU4010000000

### Issues
- Table row selector is valid, but first-link extraction can include related-service links.
- Needs stricter link filter for post detail URLs only.

### Recommended Config
```yaml
article_selector: "table tbody tr"
link_selector: "td a[href*='/news/news_report.do'], td a[href*='/news/news_notice.do']"
wait_for: "table tbody tr"
```

## 12. 경기도 지원사업

| Field | Value |
|---|---|
| URL | https://www.gg.go.kr/bbs/boardList.do?bbsId=BBS_0000022&menuId=1535 |
| HTTP Status | 404 |
| Page Title | 경기도청 \| 페이지를 찾을 수 없습니다 |
| Body Size | 60ch |
| Best Selector | none:0 |
| Article Selector | (none) |
| Link Selector | a[href] |

### Sample Data
1. (no usable article rows found) → -
2. - → -

### Issues
- URL returns HTTP 404.
- No article containers matched from tested selector set.

### Recommended Config
```yaml
article_selector: ""
link_selector: "a[href]"
wait_for: "body"
```
