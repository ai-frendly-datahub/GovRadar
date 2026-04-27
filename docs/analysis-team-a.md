### 11. 경기도일자리포털
- URL: https://job.gg.go.kr/entSprt/list.do
- Status: 200
- Title: 기업지원정책
- Best selector: ul[class*=list] li:121
- Samples:
  1. 러닝센터 -> https://lms.gg.go.kr/home.do (parent: li)
  2. 잡아바 어플라이 -> https://apply.jobaba.net/bsns/bsnsListView.do (parent: li)
  3. 고객센터 -> https://job.gg.go.kr/hpdsk/qna/list.do (parent: li)
- Recommended:
  - article_selector: "ul[class*=list] li"
  - link_selector: "ul[class*=list] li a[href]"
  - wait_for: "ul[class*=list] li"
- Issues: None

### 12. 고양스타특업
- URL: http://goyangstartup.kr/service/04.php
- Status: 200
- Title: 고양시원스톱창업플랫폼 고양 스타트업
- Best selector: dl dt:4
- Samples:
  1. 본문 바로가기 -> https://www.goyangstartup.kr/main/main.php#container (parent: li)
  2. 주메뉴 바로가기 -> https://www.goyangstartup.kr/main/main.php#gnbW (parent: li)
  3. MAIN -> https://www.goyangstartup.kr/main/main.php#section1 (parent: li)
- Recommended:
  - article_selector: "dl dt"
  - link_selector: "a[href]"
  - wait_for: "dl dt"
- Issues: Content links are mostly quick-navigation anchors

### 13. 수원창업지원포털
- URL: https://s-startup.or.kr/menu-1-1
- Status: 200
- Title: 수원창업지원포털
- Best selector: ul[class*=list] li:13
- Samples:
  1. 로그아웃 -> https://s-startup.or.kr/logout.cm?back_url=L21lbnUtMS0x (parent: li.profile-footer.btn-group-justified)
  2. 지원사업 -> https://s-startup.or.kr/menu-1 (parent: li.depth-01)
  3. 사업공고 -> https://s-startup.or.kr/menu-1-1 (parent: li.depth-02)
- Recommended:
  - article_selector: "ul[class*=list] li"
  - link_selector: "ul[class*=list] li a[href]"
  - wait_for: "ul[class*=list] li"
- Issues: Sampled links include menu-level nodes mixed with content

### 14. 성남산업진흥원
- URL: https://portal.snip.or.kr:8443/portal/snip/MainMenu/businessManagement.page
- Status: 200
- Title: 성남기업지원포털
- Best selector: table tr:0
- Samples:
  1. N/A -> N/A
  2. N/A -> N/A
  3. N/A -> N/A
- Recommended:
  - article_selector: "table tr"
  - link_selector: "a[href]"
  - wait_for: "body"
- Issues: No candidate selector matched; no usable content links sampled

### 15. 의정부 기업지원포털
- URL: https://www.uesc.or.kr/bbs/board.php?bo_table=bus_04
- Status: 200
- Title: 의정부시 지원사업 1 페이지 | 의정부시 기업지원센터
- Best selector: [class*=item]:39
- Samples:
  1. 센터 소개 -> https://www.uesc.or.kr/bbs/content.php?co_id=info_01 (parent: li)
  2. 센터 주요활동 -> https://www.uesc.or.kr/bbs/board.php?bo_table=info_02 (parent: li)
  3. 영상 게시판 -> https://www.uesc.or.kr/bbs/board.php?bo_table=info_youtube (parent: li)
- Recommended:
  - article_selector: "[class*=item]"
  - link_selector: "[class*=item] a[href]"
  - wait_for: "[class*=item]"
- Issues: [class*=item] may include navigation blocks; field validation needed in crawler

### 16. 과천시
- URL: https://www.gccity.go.kr/dept/bbs/list.do?ptIdx=241&mId=0102010000
- Status: 200
- Title: 중소기업 및 소상공인 지원 게시판 목록 | 중소기업 및 소상공인 지원 | 일자리/기업/경제 | 홈페이지
- Best selector: table tbody tr:24
- Samples:
  1. 본문 바로가기 -> https://www.gccity.go.kr/dept/bbs/list.do?ptIdx=241&mId=0102010000#conts (parent: div)
  2. 주메뉴 바로가기 -> https://www.gccity.go.kr/dept/bbs/list.do?ptIdx=241&mId=0102010000#lnbWrap (parent: div)
  3. 대표포털 -> https://www.gccity.go.kr/main.do (parent: li)
- Recommended:
  - article_selector: "table tbody tr"
  - link_selector: "table tbody tr a[href]"
  - wait_for: "table tbody tr"
- Issues: ul[class*=list] li count is inflated by layout menus; table rows are cleaner target

### 17. 시흥시산업진흥원
- URL: https://www.sida.kr/notification/notice.html
- Status: 200
- Title: 시흥산업진흥원 | 지원사업공고
- Best selector: table tbody tr:20
- Samples:
  1. 회원가입 -> https://www.sida.kr/join/step1.html (parent: li)
  2. 로그인 -> https://www.sida.kr/join/login.html (parent: li)
  3. 산업현황 대시보드 -> https://www.sida.kr/notification/notice.html#void (parent: li)
- Recommended:
  - article_selector: "table tbody tr"
  - link_selector: "table tbody tr a[href]"
  - wait_for: "table tbody tr"
- Issues: Sample links include global header items; content extraction should scope to table

### 18. 시흥시 창업센터
- URL: https://startup.sida.kr/business/support/list
- Status: 200
- Title: 시흥시 창업지원사업 공고 | 시흥창업센터
- Best selector: [class*=item]:45
- Samples:
  1. 시흥산업진흥원 -> https://sida.kr/main/main.html (parent: div.link-list.f-gmak)
  2. 시흥 기업거래 장터 -> https://www.siheungb2b.com/main/main.html (parent: div.link-list.f-gmak)
  3. 시흥시맞춤입찰정보 -> http://g2b.sida.kr/ (parent: div.link-list.f-gmak)
- Recommended:
  - article_selector: "[class*=item]"
  - link_selector: "[class*=item] a[href]"
  - wait_for: "[class*=item]"
- Issues: [class*=item] is broad; narrow to board container in implementation

### 19. 용인시
- URL: https://ybs.ypa.or.kr/application.do?site=&id=
- Status: 200
- Title: 용인기업지원시스템
- Best selector: [class*=item]:28
- Samples:
  1. 용인기업지원시스템 -> https://ybs.ypa.or.kr/ (parent: h1)
  2. 로그인 -> https://ybs.ypa.or.kr/login.do (parent: li.login)
  3. 회원가입 -> https://ybs.ypa.or.kr/memberRegisterBefore.do (parent: li.join)
- Recommended:
  - article_selector: "[class*=item]"
  - link_selector: "[class*=item] a[href]"
  - wait_for: "[class*=item]"
- Issues: Sampled anchors are header links; crawler should exclude auth/menu sections

### 20. 파주시
- URL: https://www.paju.go.kr/user/board/BD_board.list.do?bbsCd=9052
- Status: 200
- Title: 기업지원 사업공고(목록) : HOME > 분야별정보 > 기업/경제/일자리 > 기업 > 기업지원 사업공고
- Best selector: table tbody tr:10
- Samples:
  1. 본문 바로가기 -> https://www.paju.go.kr/user/board/BD_board.list.do?bbsCd=9052#content (parent: li)
  2. 주메뉴 바로가기 -> https://www.paju.go.kr/user/board/BD_board.list.do?bbsCd=9052#gnb (parent: li)
  3. 푸터 바로가기 -> https://www.paju.go.kr/user/board/BD_board.list.do?bbsCd=9052#footer (parent: li)
- Recommended:
  - article_selector: "table tbody tr"
  - link_selector: "table tbody tr a[href]"
  - wait_for: "table tbody tr"
- Issues: ul[class*=list] li is heavily polluted by site-wide navigation
