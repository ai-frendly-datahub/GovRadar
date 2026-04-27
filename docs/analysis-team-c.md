### 31. 서울경제진흥원
- URL: https://www.sba.seoul.kr/Pages/BusinessApply/Posting.aspx  
- Status: 200
- Title: 전체사업 > 사업신청 > 서울경제진흥원
- Best selector: table tbody tr:62
- Samples: 1. 신청현황조회 -> https://www.sba.seoul.kr/Pages/MyPage/ApplyStatus.aspx; 2. 카카오톡 알림신청 -> https://www.sba.seoul.kr/Pages/MyPage/KakaoAlarm.aspx; 3. 찜목록 -> https://www.sba.seoul.kr/Pages/MyPage/WishList.aspx
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a[href]`, wait_for=`table tbody tr`
- Issues: None

### 32. 서울시 R&D 지원
- URL: https://seoul.rnbd.kr/client/c030100/c030100_00.jsp  
- Status: 200
- Title: 사업공고
- Best selector: table tbody tr:10
- Samples: 1. 사업안내 -> https://seoul.rnbd.kr/client/c020500/c020500_00.jsp; 2. 주요사업 소개 -> https://seoul.rnbd.kr/client/c020500/c020500_00.jsp; 3. 사업추진절차 -> https://seoul.rnbd.kr/client/c020100/c020101_00.jsp
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a[href]`, wait_for=`table tbody tr`
- Issues: None

### 33. 인천창업플랫폼
- URL: https://incheon-startup.kr/04_suport/suport_1_1  
- Status: 200
- Title: 인천창업플랫폼
- Best selector: N/A:0
- Samples: 1. 지원사업 -> https://incheon-startup.kr/04_suport/suport_1_1; 2. 2026년 사이즈코리아 데이터 활용 컨설팅 지원사업 수요기업 모집 (2026.03.11 ~ 2026.06.30) -> https://incheon-startup.kr/04_suport/suport_1_1_view?idx=6664; 3. 2026년「부천시 지원」 AI숏폼 & 라이브커머스 창업가 양성과정 훈련생 모집 -> https://incheon-startup.kr/04_suport/suport_1_1_view?idx=6663
- Recommended: article_selector=`a[href]`, link_selector=`a[href]`, wait_for=`a[href]`
- Issues: Candidate list selectors did not match; use link-level extraction on this page.

### 34. 광주광역시
- URL: https://www.gjbizinfo.or.kr/online.do?pageId=www48  
- Status: 200
- Title: 전체 지원사업 | 광주광역시 기업지원시스템
- Best selector: N/A:0
- Samples: 1. 지원사업정보 -> https://www.gjbizinfo.or.kr/online.do?pageId=www48; 2. 전체 지원사업 -> https://www.gjbizinfo.or.kr/online.do?pageId=www48; 3. 기업지원 -> https://www.gjbizinfo.or.kr/online.do?pageId=www72
- Recommended: article_selector=`a[href]`, link_selector=`a[href]`, wait_for=`a[href]`
- Issues: SSL issue reported for this target (intermittent TLS/certificate validation).

### 35. 대구광역시 창업플랫폼
- URL: https://startup.daegu.go.kr/index.do?menu_id=00002552  
- Status: 200
- Title: 지원사업공고 | DASH - 대구창업허브
- Best selector: table tbody tr:10
- Samples: 1. 지원프로그램 -> https://startup.daegu.go.kr/index.do?menu_id=00002211; 2. 지원사업공고 -> https://startup.daegu.go.kr/index.do?menu_id=00002552; 3. 창업행사 -> https://startup.daegu.go.kr/index.do?menu_id=00003122
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a[href]`, wait_for=`table tbody tr`
- Issues: None

### 36. 대전광역시
- URL: https://www.djbea.or.kr/pms/an/an_0101/list?  
- Status: 200
- Title: 대전일자리경제진흥원 사업관리시스템
- Best selector: article:2
- Samples: 1. 주메뉴 -> https://www.djbea.or.kr/pms/an/an_0101/list?#main-gnb; 2. 주메뉴 건너뛰기 -> https://www.djbea.or.kr/pms/an/an_0101/list?#container; 3. 기업지원사업 -> https://www.djbea.or.kr/pms/an/an_0101/list?#this
- Recommended: article_selector=`article`, link_selector=`article a[href]`, wait_for=`article`
- Issues: SSL issue reported for this target (intermittent TLS/certificate validation).

### 37. 세종특별자치시 창업플랫폼
- URL: https://www.sjstarton.or.kr/startupSupport/support/index.do?menu_gubun=mid&menu_no=1  
- Status: 404
- Title: 기업마당>정책정보>지원사업 공고
- Best selector: table tbody tr:15
- Samples: 1. 본문 바로가기 -> https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do?null#container; 2. 주메뉴 바로가기 -> https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do?null#gnb; 3. 정책정보 -> https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a[href]`, wait_for=`table tbody tr`
- Issues: 404 page returned; URL resolves to bizinfo.go.kr error/fallback page.

### 38. 울산정보산업진흥원
- URL: https://uipa.or.kr/  
- Status: 200
- Title: 울산정보산업진흥원
- Best selector: N/A:0
- Samples: 1. N/A -> N/A; 2. N/A -> N/A; 3. N/A -> N/A
- Recommended: article_selector=`a[href]`, link_selector=`a[href]`, wait_for=`a[href]`
- Issues: Anchor extraction returned no usable links in the rendered DOM snapshot (likely frame/script-rendered navigation).

### 39. 여수시
- URL: https://yjss.or.kr/62  
- Status: 200
- Title: 정부 및 경기도 지원사업
- Best selector: main a:54
- Samples: 1. 지원사업 -> https://yjss.or.kr/business; 2. 경기도시장상권진흥원 및 소상공인시장진흥공단 지원사업 -> https://yjss.or.kr/61; 3. 센터 지원사업 -> https://yjss.or.kr/62
- Recommended: article_selector=`main a`, link_selector=`main a`, wait_for=`main a`
- Issues: None

### 40. 경상북도
- URL: https://www.gb.go.kr/Main/open_contents/section/economy2020/page.do?LARGE_CODE=690&MEDIUM_CODE=10&mnu_uid=6177  
- Status: 200
- Title: 목록 | 중소기업지원 소식<중소기업지원<경제
- Best selector: N/A:0
- Samples: 1. 본문 바로가기 -> https://www.gb.go.kr/Main/finace/page.do?mnu_uid=15256#container; 2. 경북의 힘으로! 새로운 대한민국 -> https://www.gb.go.kr/Main/index.html; 3. 예산/재정/계약/세금 -> https://www.gb.go.kr/Main/finace/index.html
- Recommended: article_selector=`a[href]`, link_selector=`a[href]`, wait_for=`a[href]`
- Issues: Requested URL redirected to /Main/finace/page.do?mnu_uid=15256 during crawl.
