### 41. 경남창업포털
- URL: https://www.gnstartup.kr/business/8339db24-725a-45bc-baf9-d778adc7b0d8
- Status: 200
- Title: 경남창업포털
- Best selector: table tbody tr:0
- Samples: 1. N/A → N/A; 2. N/A → N/A; 3. N/A → N/A
- Recommended: article_selector=`a[href]`, link_selector=`a[href]`, wait_for=`domcontentloaded`
- Issues: Expected 404 but got 200; no candidate selector matched; fewer than 3 content links found

### 42. 강원지역산업진흥원
- URL: https://gw.riia.or.kr/board/businessAnnouncement
- Status: 200
- Title: (empty)
- Best selector: [class*=item]:27
- Samples: 1. 2026년도 지역혁신클러스터육성(R&D) 사업 시행계획 공고 → https://gw.riia.or.kr/board/businessAnnouncement/view/6d74fc41-0e03-11f1-9f99-0b7e505423f0; 2. 2026년 지역혁신선도기업육성(R&D) 시행계획 공고 → https://gw.riia.or.kr/board/businessAnnouncement/view/d229ee08-0d6f-11f1-9f99-b58d3b281997; 3. 2026년 메가시티협력 첨단산업 육성지원(R&D) 사업 신규지원 공고 → https://gw.riia.or.kr/board/businessAnnouncement/view/2ad697b2-0d2a-11f1-9f99-efbcc21a4ce6
- Recommended: article_selector=`[class*=item]`, link_selector=`[class*=item] a`, wait_for=`[class*=item]`
- Issues: Empty title

### 43. 강원특별자치도경제진흥원
- URL: https://www.gwep.or.kr/bbs/board.php?bo_table=gw_sub21
- Status: 200
- Title: 강원특별자치도경제진흥원
- Best selector: table tbody tr:16
- Samples: 1. 일자리부 → https://www.gwep.or.kr/bbs/board.php?bo_table=gw_sub21&sca=%EC%9D%BC%EC%9E%90%EB%A6%AC%EB%B6%80; 2. 제8회 강원특별자치도 일자리대상 시행 변경 공고(~3. 31.) → https://www.gwep.or.kr/bbs/board.php?bo_table=gw_sub21&wr_id=3405; 3. 전략사업부 → https://www.gwep.or.kr/bbs/board.php?bo_table=gw_sub21&sca=%EC%A0%84%EB%9E%B5%EC%82%AC%EC%97%85%EB%B6%80
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a`, wait_for=`table tbody tr`
- Issues: None

### 44. 충청북도 시책사업
- URL: https://cbgms.chungbuk.go.kr/export/joinBusinessList.jsp?busi_section=1
- Status: 200
- Title: 충북 글로벌 마케팅 시스템
- Best selector: table tbody tr:15
- Samples: 1. 로그인 → https://cbgms.chungbuk.go.kr/login/login.jsp; 2. 회원가입 → https://cbgms.chungbuk.go.kr/login/join.jsp; 3. 시스템소개 → https://cbgms.chungbuk.go.kr/help/systemGuide.jsp
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a`, wait_for=`table tbody tr`
- Issues: None

### 45. 충청남도경제진흥원
- URL: https://www.cnsp.or.kr/project/list.do
- Status: 200
- Title: 충청남도 중소기업 통합지원시스템
- Best selector: [class*=item]:14
- Samples: 1. 이용안내 → https://www.cnsp.or.kr/introduce/introduce.do; 2. 사업공고 → https://www.cnsp.or.kr/project/list.do; 3. 알림마당 → https://www.cnsp.or.kr/community/list.do?menuSeq=13
- Recommended: article_selector=`[class*=item]`, link_selector=`[class*=item] a`, wait_for=`[class*=item]`
- Issues: None

### 46. 전북 중소기업종합지원
- URL: https://www.jbok.kr/spWork/supportBusinessList.do?menuId=60
- Status: 200
- Title: 전북특별자치도 중소기업종합지원시스템
- Best selector: [class*=item]:1
- Samples: 1. 기업애로 → https://www.jbok.kr/content/contentView.do?contentMenuId=10&menuId=10; 2. 기업애로신청 → https://www.jbok.kr/compDiff/compDifficultReg.do?menuId=11; 3. 컨설턴트 POOL → https://www.jbok.kr/compDiff/consttPoolList.do?menuId=13
- Recommended: article_selector=`[class*=item]`, link_selector=`[class*=item] a`, wait_for=`[class*=item]`
- Issues: None

### 47. 전남창업지원플랫폼
- URL: https://www.jnstartup.co.kr/business.cs?m=14&pageIndex=1
- Status: 200
- Title: 지원사업공고 : 전남으뜸창업
- Best selector: table tbody tr:10
- Samples: 1. 2026년 전남 농수산식품 세계 일류 상품화 지원사업 참여기업 모집공고 → https://www.jnstartup.co.kr/business.cs?act=view&bsinId=1807&pageIndex=1&searchCondition=&searchKeyword=; 2. 「2026년 오픈이노베이션 플랫폼 지원사업」 참여기업 모집 공고 1차 → https://www.jnstartup.co.kr/business.cs?act=view&bsinId=1806&pageIndex=1&searchCondition=&searchKeyword=; 3. 2026 한중(웨이하이) 의료기기 산업 협력 기회 매칭회 참가기업 모집 공고 → https://www.jnstartup.co.kr/business.cs?act=view&bsinId=1805&pageIndex=1&searchCondition=&searchKeyword=
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a`, wait_for=`table tbody tr`
- Issues: None

### 48. 잇지제주
- URL: https://www.idge.co.kr/all_programs
- Status: 200
- Title: 잇지제주ㅣ제주 지역 소식
- Best selector: [class*=item]:298
- Samples: 1. 광고 문의 → https://www.idge.co.kr/ad; 2. 로그인 → https://www.idge.co.kr/login?back_url=L2FsbF9wcm9ncmFtcw%3D%3D&used_login_btn=Y; 3. 1:1 문의 → http://idge.channel.io/
- Recommended: article_selector=`[class*=item]`, link_selector=`[class*=item] a`, wait_for=`[class*=item]`
- Issues: None

### 49. 경남기업119
- URL: https://www.gyeongnam.go.kr/giup/index.gyeong?menuCd=DOM_000004603001000000
- Status: 200
- Title: 경남기업119 > 경상남도 지원사업 > 경상남도 지원사업
- Best selector: article:12
- Samples: 1. 접수중 2026년 양산시 1분기 중소기업육성자금 융자지원 변경 금융 '26.3.18.~예산소진시까지 → https://www.gyeongnam.go.kr/giup/index.gyeong?&menuCd=DOM_000004603001001000&menuType=U&pageNo=1&keyword=&sangSi=&busiCateAll=&busiCate1=&busiCate2=&busiCate3=&busiCate4=&busiCate5=&busiCate6=&busiCate7=&busiCate8=&busiYearAll=&sigun1=&sigun2=&sigun3=&sigun4=&sigun5=&sigun6=&sigun7=&sigun8=&sigun9=&sigun10=&sigun11=&sigun12=&sigun13=&sigun14=&sigun15=&sigun16=&sigun17=&sigun18=&sigunAll=&busiSupportCd=2885; 2. 접수중 경남콘텐츠기업지원센터 융복합 콘텐츠 제작 지원사업 모집 내수 '26. 3. 18. ~ 4. 7. → https://www.gyeongnam.go.kr/giup/index.gyeong?&menuCd=DOM_000004603001001000&menuType=U&pageNo=1&keyword=&sangSi=&busiCateAll=&busiCate1=&busiCate2=&busiCate3=&busiCate4=&busiCate5=&busiCate6=&busiCate7=&busiCate8=&busiYearAll=&sigun1=&sigun2=&sigun3=&sigun4=&sigun5=&sigun6=&sigun7=&sigun8=&sigun9=&sigun10=&sigun11=&sigun12=&sigun13=&sigun14=&sigun15=&sigun16=&sigun17=&sigun18=&sigunAll=&busiSupportCd=3061; 3. 접수중 경남 방산 강소기업 육성지원사업 수혜기업 모집(김해, 진주, 사천, 함안) 경영 '26. 3. 18. ~ 4. 17. → https://www.gyeongnam.go.kr/giup/index.gyeong?&menuCd=DOM_000004603001001000&menuType=U&pageNo=1&keyword=&sangSi=&busiCateAll=&busiCate1=&busiCate2=&busiCate3=&busiCate4=&busiCate5=&busiCate6=&busiCate7=&busiCate8=&busiYearAll=&sigun1=&sigun2=&sigun3=&sigun4=&sigun5=&sigun6=&sigun7=&sigun8=&sigun9=&sigun10=&sigun11=&sigun12=&sigun13=&sigun14=&sigun15=&sigun16=&sigun17=&sigun18=&sigunAll=&busiSupportCd=3063
- Recommended: article_selector=`article`, link_selector=`article a`, wait_for=`article`
- Issues: None

### 50. 충청북도 도내시책사업
- URL: https://cbgms.chungbuk.go.kr/export/joinBusinessList.jsp?busi_section=3
- Status: 200
- Title: 충북 글로벌 마케팅 시스템
- Best selector: table tbody tr:15
- Samples: 1. 로그인 → https://cbgms.chungbuk.go.kr/login/login.jsp; 2. 회원가입 → https://cbgms.chungbuk.go.kr/login/join.jsp; 3. 시스템소개 → https://cbgms.chungbuk.go.kr/help/systemGuide.jsp
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a`, wait_for=`table tbody tr`
- Issues: None

### 51. 전북경제통상진흥원
- URL: https://www.jbba.kr/bbs/board.php?bo_table=sub01_09
- Status: 200
- Title: 지원사업 1 페이지 | 전북특별자치도경제통상진흥원
- Best selector: table tbody tr:20
- Samples: 1. 2026년 새출발 재기지원 (휴·폐업 사업주형) 재기 지원(사업정리비 및 교육비) 모집 공고 → https://www.jbba.kr/bbs/board.php?bo_table=sub01_09&wr_id=1702; 2. 2026년 새출발 재기지원 (가동 사업주형) 사업장 환경개선 지원 모집 공고 → https://www.jbba.kr/bbs/board.php?bo_table=sub01_09&wr_id=1701; 3. [돋움기업] 디지털기술 BM 고도화 지원사업 → https://www.jbba.kr/bbs/board.php?bo_table=sub01_09&wr_id=1700
- Recommended: article_selector=`table tbody tr`, link_selector=`table tbody tr a`, wait_for=`table tbody tr`
- Issues: None

### 52. 제주경제통상진흥원
- URL: https://www.jba.or.kr/bbs/board.php?bo_table=2_1_1_1
- Status: 403
- Title: 403 Forbidden
- Best selector: table tbody tr:0
- Samples: 1. N/A → N/A; 2. N/A → N/A; 3. N/A → N/A
- Recommended: article_selector=`a[href]`, link_selector=`a[href]`, wait_for=`domcontentloaded`
- Issues: HTTP 403 blocked access; no candidate selector matched; fewer than 3 content links found
