### 21. 이천시
- URL: https://www.icheon.go.kr/biz/board/post/list.do?bcIdx=698&mid=0502010000
- Status: ERR
- Title: 강원특별자치도경제진흥원
- Best selector: ul li:144
- Samples:
  1. 일자리부 → https://www.gwep.or.kr/bbs/board.php?bo_table=gw_sub21&sca=%EC%9D%BC%EC%9E%90%EB%A6%AC%EB%B6%80
  2. 제8회 강원특별자치도 일자리대상 시행 변경 공고(~3. 31.) → https://www.gwep.or.kr/bbs/board.php?bo_table=gw_sub21&wr_id=3405
  3. 전략사업부 → https://www.gwep.or.kr/bbs/board.php?bo_table=gw_sub21&sca=%EC%A0%84%EB%9E%B5%EC%82%AC%EC%97%85%EB%B6%80
- Recommended: article_selector=table tbody tr, link_selector=table tbody tr a[href], wait_for=table tbody tr
- Issues: Alert dialog("잘못된 접근입니다.") and navigation mismatch (landed on https://www.icheon.go.kr/main.do); SSL/certificate issue expected for this target.

### 22. 안성시
- URL: https://www.anseong.go.kr/depart/bbs/list.do?ptIdx=16&mId=0102040000
- Status: 200
- Title: 기업지원사업안내 목록 | 기업지원 | 기업/경제 | 안성시청 분야별 홈페이지
- Best selector: ul li:813
- Samples:
  1. 2026년 중소벤처기업 지원사업 설명회 발표자료 - 지방세법령개정안내 → #
  2. 2026년 안성시 기업 지원사업 → #
  3. 2026년 중소벤처기업 지원시책 설명회 발표자료 → #
- Recommended: article_selector=table tbody tr, link_selector=table tbody tr a[href], wait_for=table tbody tr
- Issues: None.

### 23. 김포시산업지원
- URL: https://gopa.or.kr/sub/apply01/list.html?curpage=1&
- Status: 200
- Title: 김포시 지원사업 | 기업지원사업 | 지원사업 | 김포산업진흥원
- Best selector: ul li:123
- Samples:
  1. 로그인 → https://gopa.or.kr/sub/member/login.html
  2. 회원가입 → https://gopa.or.kr/sub/member/join.html
  3. 지원사업 → https://gopa.or.kr/sub/apply01/list.html?curpage=1&
- Recommended: article_selector=ul li, link_selector=ul li a[href], wait_for=ul li
- Issues: Initial attempt triggered repeated alert popups on a redirected page; clean-tab retry succeeded.

### 24. 화성시
- URL: https://platform.hsbiz.or.kr/business/list
- Status: 200
- Title: 화성시 지원사업-화성시 기업지원 플랫폼
- Best selector: ul li:100
- Samples:
  1. 블로그 → https://blog.naver.com/hipa_manager
  2. 인스타그램 → https://www.instagram.com/hi_hipa/
  3. 페이스북 → https://www.facebook.com/%ED%99%94%EC%84%B1%EC%82%B0%EC%97%85%EC%A7%84%ED%9D%A5%EC%9B%90-108695784864118/
- Recommended: article_selector=ul li, link_selector=ul li a[href], wait_for=ul li
- Issues: SSL/certificate issue was expected for this target but was not reproduced in this run.

### 25. 연천군
- URL: https://yeoncheon.go.kr/www/selectBbsNttList.do?bbsNo=260&key=3524
- Status: 200
- Title: 기업지원사업 정보안내 목록 - 연천군청
- Best selector: ul li:710
- Samples:
  1. 2026년 중소기업 마케팅-여성기업 마케팅 지원사업 안내 새글 → ./selectBbsNttView.do?key=3524&id=&bbsNo=260&nttNo=104117&searchCtgry=&searchCnd=all&searchKrwd=&pageIndex=1&&frstRegisterPnttmSdt=&frstRegisterPnttmEdt=&searchDeleteAt=N&integrDeptCode=&searchDeptCode=
  2. 2026년 경기 스타트업 지원센터 상담기업 모집 안내 → ./selectBbsNttView.do?key=3524&id=&bbsNo=260&nttNo=103896&searchCtgry=&searchCnd=all&searchKrwd=&pageIndex=1&&frstRegisterPnttmSdt=&frstRegisterPnttmEdt=&searchDeleteAt=N&integrDeptCode=&searchDeptCode=
  3. 연천군 농어촌 기본소득 Q&A → ./selectBbsNttView.do?key=3524&id=&bbsNo=260&nttNo=103613&searchCtgry=&searchCnd=all&searchKrwd=&pageIndex=1&&frstRegisterPnttmSdt=&frstRegisterPnttmEdt=&searchDeleteAt=N&integrDeptCode=&searchDeptCode=
- Recommended: article_selector=table tbody tr, link_selector=table tbody tr a[href], wait_for=table tbody tr
- Issues: None.

### 26. 가평군 기업지원
- URL: https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=550&key=735&scheduleZoneNo=4
- Status: 200
- Title: 소상공인24 소진공 공고조회 및 신청
- Best selector: ul li:287
- Samples:
  1. 고용보험 미적용자 출산(유산·사산) 급여 지원 사업 공고 → #/pbanc/607
  2. 2026년 소상공인 고용보험료 지원사업 공고 → #/pbanc/559
  3. 2026년 중소기업 수출지원사업 통합공고 → #/pbanc/553
- Recommended: article_selector=table tbody tr, link_selector=table tbody tr a[href], wait_for=table tbody tr
- Issues: Redirected to https://www.sbiz24.kr/#/pbanc.

### 27. 가평군 소상공인
- URL: https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=533&key=2370
- Status: 200
- Title: 가평군 지원사업 게시물 목록 -가평군청
- Best selector: ul li:957
- Samples:
  1. 2026년「소상공인 홍보마케팅 지원사업」 안내(공고문 및 신청서식 첨부) → ./selectBbsNttView.do?key=2370&bbsNo=533&nttNo=271457&searchCtgry=&searchCnd=all&searchKrwd=&pageIndex=1&integrDeptCode=
  2. 2026년「첫 출발 응원 창업 소상공인 지원사업」 안내(공고문 및 신청서식 첨부) → ./selectBbsNttView.do?key=2370&bbsNo=533&nttNo=271242&searchCtgry=&searchCnd=all&searchKrwd=&pageIndex=1&integrDeptCode=
  3. 『2026년 가평군 소상공인 경영환경개선사업』안내(공고문 및 신청서식 첨부) → ./selectBbsNttView.do?key=2370&bbsNo=533&nttNo=270841&searchCtgry=&searchCnd=all&searchKrwd=&pageIndex=1&integrDeptCode=
- Recommended: article_selector=table tbody tr, link_selector=table tbody tr a[href], wait_for=table tbody tr
- Issues: None.

### 28. 서울시 소상공인 종합지원
- URL: https://www.seoulsbdc.or.kr/sb/main.do
- Status: 200
- Title: 서울시 소상공인 종합지원 포털 - 지원사업
- Best selector: ul li:107
- Samples:
  1. 주택 → http://news.seoul.go.kr/citybuild/
  2. 경제 → http://news.seoul.go.kr/economy/
  3. 교통 → http://news.seoul.go.kr/traffic/
- Recommended: article_selector=ul li, link_selector=ul li a[href], wait_for=ul li
- Issues: None.

### 29. 인천광역시
- URL: https://bizok.incheon.go.kr/open_content/support.do?act=list&pgno=1
- Status: 200
- Title: 온라인 기업지원사업신청 | 비즈OK>기업지원
- Best selector: ul li:133
- Samples:
  1. 기업지원 → #
  2. 온라인 기업지원사업신청 → /open_content/support/application.jsp
  3. 기업마당 지원사업 → /open_content/support/business_bizinfo.jsp
- Recommended: article_selector=ul li, link_selector=ul li a[href], wait_for=ul li
- Issues: None.

### 30. 부산창업포털
- URL: https://busanstartup.kr/biz_sup?deadline=N&mcode=biz02
- Status: 200
- Title: 접수중 < 지원사업 < 창업지원 < 부산창업포털
- Best selector: ul li:162
- Samples:
  1. 본문 바로가기 → #container-wrap
  2. 주 메뉴 바로가기 → #mainNavi
  3. 서브 메뉴 바로가기 → #subMenu
- Recommended: article_selector=ul li, link_selector=ul li a[href], wait_for=ul li
- Issues: None.
