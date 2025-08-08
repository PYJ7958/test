from flask import Flask, render_template_string, jsonify
import os
import requests
from datetime import datetime
import json
import feedparser  # RSS 피드 파싱용

app = Flask(__name__)

# API 키 설정 (실제 사용시 본인의 API 키로 교체 필요)
# OpenWeatherMap API: https://openweathermap.org/api 에서 무료 키 발급
# News API: https://newsapi.org/ 에서 무료 키 발급
# 네이버 API: https://developers.naver.com 에서 발급
WEATHER_API_KEY = "3e4260445d73534a4be00145d1fd38ff"  # 여기에 OpenWeatherMap API 키 입력
NEWS_API_KEY = "154630431b054a118504acd4623be4f5"  # 여기에 News API 키 입력

# 네이버 API 사용시 (선택사항)
NAVER_CLIENT_ID = "YOUR_NAVER_CLIENT_ID"  # 네이버 Client ID
NAVER_CLIENT_SECRET = "YOUR_NAVER_CLIENT_SECRET"  # 네이버 Client Secret
USE_NAVER_API = False  # True로 변경하면 네이버 API 사용

def get_weather():
    """날씨 정보 조회 - OpenWeatherMap 또는 wttr.in 사용"""
    
    # OpenWeatherMap API 시도
    if WEATHER_API_KEY != "YOUR_OPENWEATHER_API_KEY":
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q=Seoul,kr&appid={WEATHER_API_KEY}&units=metric&lang=kr"
            
            print(f"OpenWeatherMap API 요청 중...")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"날씨 데이터 수신 성공: 온도={data['main']['temp']}°C")
                
                return {
                    'temp': round(data['main']['temp']),
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon'],
                    'city': '서울특별시'
                }
            elif response.status_code == 401:
                print("API 키가 유효하지 않거나 아직 활성화되지 않았습니다.")
                print("API 키 생성 후 10분~2시간 후에 다시 시도해주세요.")
            else:
                print(f"OpenWeatherMap API 오류: {response.status_code}")
                
        except Exception as e:
            print(f"OpenWeatherMap API 오류: {e}")
    
    # wttr.in API 사용 (API 키 불필요)
    try:
        print("wttr.in 날씨 API 사용 중...")
        # wttr.in API - 무료, API 키 불필요
        url = "http://wttr.in/Seoul?format=j1"
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            # 날씨 상태 한글 변환
            weather_desc = {
                'Clear': '맑음',
                'Sunny': '맑음',
                'Partly cloudy': '구름 조금',
                'Cloudy': '흐림',
                'Overcast': '흐림',
                'Mist': '안개',
                'Rain': '비',
                'Snow': '눈',
                'Fog': '안개'
            }
            
            desc = current.get('weatherDesc', [{}])[0].get('value', 'Unknown')
            desc_kr = weather_desc.get(desc, desc)
            
            # 아이콘 매핑
            icon_map = {
                'Clear': '01d', 'Sunny': '01d',
                'Partly cloudy': '02d', 'Cloudy': '03d',
                'Overcast': '04d', 'Mist': '50d',
                'Rain': '10d', 'Snow': '13d'
            }
            
            return {
                'temp': int(current.get('temp_C', 18)),
                'description': desc_kr,
                'icon': icon_map.get(desc, '01d'),
                'city': '서울특별시'
            }
    except Exception as e:
        print(f"wttr.in API 오류: {e}")
    
    # 모든 API 실패시 기본값
    print("모든 날씨 API 실패, 기본값 반환")
    return {
        'temp': 18,
        'description': '맑음',
        'icon': '01d',
        'city': '서울특별시'
    }

def get_rss_news():
    """RSS 피드를 사용한 한국 뉴스 조회"""
    all_news = []
    
    # 여러 RSS 피드 소스
    rss_feeds = [
        {
            'url': 'https://fs.jtbc.co.kr/RSS/newsflash.xml',
            'source': 'JTBC'
        },
        {
            'url': 'https://www.yonhapnewstv.co.kr/browse/feed/',
            'source': '연합뉴스TV'
        },
        {
            'url': 'http://www.khan.co.kr/rss/rssdata/total_news.xml',
            'source': '경향신문'
        },
        {
            'url': 'https://rss.donga.com/total.xml',
            'source': '동아일보'
        },
        {
            'url': 'http://rss.kmib.co.kr/data/kmibRssAll.xml',
            'source': '국민일보'
        },
        {
            'url': 'https://www.mk.co.kr/rss/30000001/',
            'source': '매일경제'
        }
    ]
    
    for feed_info in rss_feeds:
        try:
            print(f"{feed_info['source']} RSS 피드 읽는 중...")
            feed = feedparser.parse(feed_info['url'])
            
            # 각 피드에서 최대 3개씩만 가져오기
            for entry in feed.entries[:3]:
                # HTML 태그 제거
                import re
                clean_title = re.sub('<[^<]+?>', '', entry.get('title', ''))
                clean_desc = re.sub('<[^<]+?>', '', entry.get('summary', entry.get('description', '')))
                
                # 날짜 파싱
                published = entry.get('published', entry.get('pubDate', ''))
                
                news_item = {
                    'title': clean_title[:100] + '...' if len(clean_title) > 100 else clean_title,
                    'description': clean_desc[:150] + '...' if len(clean_desc) > 150 else clean_desc,
                    'url': entry.get('link', '#'),
                    'source': feed_info['source'],
                    'publishedAt': published,
                    'image': ''
                }
                all_news.append(news_item)
                
        except Exception as e:
            print(f"{feed_info['source']} RSS 오류: {e}")
            continue
    
    # 최신 뉴스순으로 정렬 (날짜가 있는 경우)
    # all_news.sort(key=lambda x: x['publishedAt'], reverse=True)
    
    # 최대 12개만 반환
    return all_news[:12] if all_news else get_sample_news()

def get_news():
    """뉴스 조회 - RSS 피드 우선 사용"""
    try:
        # RSS 피드로 한국 뉴스 가져오기
        print("RSS 피드로 한국 뉴스를 가져옵니다...")
        news = get_rss_news()
        if news:
            print(f"RSS에서 {len(news)}개 뉴스를 가져왔습니다.")
            return news
    except Exception as e:
        print(f"RSS 피드 오류: {e}")
    
    # RSS 실패시 News API 사용 (영어 뉴스)
    if NEWS_API_KEY != "154630431b054a118504acd4623be4f5":
        return get_news_api()
    
    # 모두 실패시 샘플 데이터
    return get_sample_news()

def get_news_api():
    """News API를 사용한 뉴스 조회 (폴백용)"""
    
    try:
        # 미국 헤드라인 뉴스 (News API 무료 플랜)
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
        
        print(f"News API 요청 중...")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            news_list = []
            for article in articles[:12]:
                title = article.get('title', '')
                if not title or title == '[Removed]':
                    continue
                    
                news_list.append({
                    'title': title[:100] + '...' if len(title) > 100 else title,
                    'description': (article.get('description') or '')[:150] + '...' if article.get('description') and len(article.get('description', '')) > 150 else article.get('description', ''),
                    'url': article.get('url', '#'),
                    'source': article.get('source', {}).get('name', 'News'),
                    'publishedAt': article.get('publishedAt', ''),
                    'image': article.get('urlToImage', '')
                })
            
            if news_list:
                return news_list
                
    except Exception as e:
        print(f"News API 오류: {e}")
    
    return get_sample_news()

def get_sample_news():
    """샘플 뉴스 데이터 반환"""
    
    return [
        {'title': '오늘의 주요 뉴스', 'source': '연합뉴스', 'description': '최신 뉴스를 확인하세요', 'url': '#'},
        {'title': '경제 동향 분석', 'source': '한국경제', 'description': '오늘의 경제 소식', 'url': '#'},
        {'title': 'IT 기술 혁신', 'source': '전자신문', 'description': '최신 기술 동향', 'url': '#'},
        {'title': '정치 뉴스', 'source': '조선일보', 'description': '오늘의 정치 이슈', 'url': '#'},
        {'title': '사회 뉴스', 'source': '한겨레', 'description': '사회 전반 소식', 'url': '#'},
        {'title': '스포츠 소식', 'source': '스포츠서울', 'description': '스포츠 경기 결과', 'url': '#'},
    ]

# HTML 템플릿
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NAVER</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", helvetica, sans-serif;
            background: #f5f6f7;
        }
        
        /* 헤더 영역 */
        .header-wrapper {
            background: white;
            border-bottom: 1px solid #e4e8eb;
        }
        
        .header {
            max-width: 1130px;
            margin: 0 auto;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 32px;
            font-weight: bold;
            color: #03c75a;
            text-decoration: none;
        }
        
        .header-right {
            display: flex;
            gap: 15px;
            align-items: center;
            font-size: 13px;
        }
        
        .header-right a {
            color: #404040;
            text-decoration: none;
        }
        
        .header-right a:hover {
            text-decoration: underline;
        }
        
        /* 검색 영역 */
        .search-wrapper {
            background: white;
            padding: 20px 0 30px;
        }
        
        .search-container {
            max-width: 586px;
            margin: 0 auto;
        }
        
        .search-box {
            position: relative;
            width: 100%;
            height: 56px;
            border: 2px solid #03c75a;
            border-radius: 33px;
            display: flex;
            align-items: center;
            padding: 0 20px;
        }
        
        .search-input {
            width: 100%;
            height: 100%;
            border: none;
            outline: none;
            font-size: 18px;
            padding: 0 10px;
        }
        
        .search-btn {
            position: absolute;
            right: 8px;
            width: 56px;
            height: 40px;
            background: #03c75a;
            border: none;
            border-radius: 20px;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }
        
        /* 네비게이션 메뉴 */
        .nav-wrapper {
            background: white;
            border-top: 1px solid #e4e8eb;
            border-bottom: 1px solid #e4e8eb;
        }
        
        .nav-menu {
            max-width: 1130px;
            margin: 0 auto;
            padding: 0 30px;
            display: flex;
            gap: 20px;
            height: 52px;
            align-items: center;
        }
        
        .nav-item {
            color: #03c75a;
            text-decoration: none;
            font-size: 15px;
            font-weight: bold;
            padding: 5px 8px;
        }
        
        .nav-item:hover {
            background: #f5f6f7;
            border-radius: 4px;
        }
        
        /* 메인 컨텐츠 */
        .main-container {
            max-width: 1130px;
            margin: 30px auto;
            padding: 0 30px;
            display: grid;
            grid-template-columns: 750px 350px;
            gap: 30px;
        }
        
        /* 왼쪽 메인 섹션 */
        .main-left {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        /* 실시간 뉴스 */
        .news-section {
            background: white;
            border: 1px solid #dae1e6;
            padding: 20px;
            border-radius: 8px;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e4e8eb;
        }
        
        .section-title {
            font-size: 14px;
            font-weight: bold;
            color: #000;
        }
        
        .news-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .news-item {
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.2s;
        }
        
        .news-item:hover {
            background: #f8f9fa;
        }
        
        .news-item:last-child {
            border-bottom: none;
        }
        
        .news-source {
            font-size: 11px;
            color: #03c75a;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .news-title {
            font-size: 14px;
            color: #000;
            text-decoration: none;
            font-weight: 500;
            display: block;
            margin-bottom: 5px;
        }
        
        .news-title:hover {
            text-decoration: underline;
        }
        
        .news-desc {
            font-size: 12px;
            color: #666;
            line-height: 1.4;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        .news-time {
            font-size: 11px;
            color: #999;
            margin-top: 5px;
        }
        
        /* 쇼핑 섹션 */
        .shopping {
            background: white;
            border: 1px solid #dae1e6;
            padding: 20px;
            border-radius: 8px;
        }
        
        .shopping-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        
        .shopping-item {
            text-align: center;
        }
        
        .shopping-item-img {
            width: 100%;
            height: 140px;
            background: #f8f9fa;
            border: 1px solid #e4e8eb;
            margin-bottom: 8px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 12px;
        }
        
        .shopping-item-title {
            font-size: 13px;
            color: #333;
            margin-bottom: 4px;
        }
        
        .shopping-item-price {
            font-size: 14px;
            font-weight: bold;
            color: #000;
        }
        
        /* 오른쪽 사이드바 */
        .main-right {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        /* 로그인 박스 */
        .login-box {
            background: white;
            border: 1px solid #dae1e6;
            padding: 20px;
            border-radius: 8px;
        }
        
        .login-msg {
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
            line-height: 1.5;
        }
        
        .login-btn {
            width: 100%;
            height: 48px;
            background: #03c75a;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .login-links {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 15px;
            font-size: 13px;
        }
        
        .login-links a {
            color: #666;
            text-decoration: none;
        }
        
        /* 날씨 위젯 */
        .weather-widget {
            background: white;
            border: 1px solid #dae1e6;
            padding: 20px;
            border-radius: 8px;
        }
        
        .weather-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .weather-icon {
            width: 50px;
            height: 50px;
        }
        
        .weather-details {
            flex: 1;
        }
        
        .weather-temp {
            font-size: 28px;
            font-weight: bold;
            color: #000;
        }
        
        .weather-desc {
            font-size: 14px;
            color: #666;
            margin-top: 3px;
        }
        
        .weather-location {
            font-size: 13px;
            color: #999;
            margin-top: 10px;
        }
        
        .weather-update {
            font-size: 11px;
            color: #999;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #f0f0f0;
        }
        
        /* 광고 박스 */
        .ad-box {
            background: white;
            border: 1px solid #dae1e6;
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 14px;
            border-radius: 8px;
        }
        
        /* API 정보 박스 */
        .api-info {
            background: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .api-info h4 {
            margin-bottom: 10px;
        }
        
        .api-info a {
            color: #0066cc;
        }
        
        /* 푸터 */
        .footer {
            background: #f5f6f7;
            padding: 30px 0;
            margin-top: 50px;
            border-top: 1px solid #e4e8eb;
        }
        
        .footer-content {
            max-width: 1130px;
            margin: 0 auto;
            padding: 0 30px;
            text-align: center;
            font-size: 12px;
            color: #888;
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 15px;
        }
        
        .footer-links a {
            color: #666;
            text-decoration: none;
        }
        
        /* 로딩 애니메이션 */
        .loading {
            text-align: center;
            padding: 20px;
            color: #999;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #03c75a;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- 헤더 -->
    <div class="header-wrapper">
        <div class="header">
            <a href="/" class="logo">NAVER</a>
            <div class="header-right">
                <a href="#">네이버페이</a>
                <a href="#">네이버쇼핑</a>
                <a href="#">네이버플러스</a>
                <a href="#">네이버TV</a>
                <a href="#">사전</a>
                <a href="#">뉴스</a>
                <a href="#">증권</a>
                <a href="#">부동산</a>
                <a href="#">지도</a>
                <a href="#">더보기</a>
            </div>
        </div>
    </div>
    
    <!-- 검색 영역 -->
    <div class="search-wrapper">
        <div class="search-container">
            <div class="search-box">
                <input type="text" class="search-input" placeholder="검색어를 입력하세요">
                <button class="search-btn">검색</button>
            </div>
        </div>
    </div>
    
    <!-- 네비게이션 메뉴 -->
    <div class="nav-wrapper">
        <div class="nav-menu">
            <a href="#" class="nav-item">메일</a>
            <a href="#" class="nav-item">카페</a>
            <a href="#" class="nav-item">블로그</a>
            <a href="#" class="nav-item">쇼핑</a>
            <a href="#" class="nav-item">뉴스</a>
            <a href="#" class="nav-item">증권</a>
            <a href="#" class="nav-item">부동산</a>
            <a href="#" class="nav-item">지도</a>
            <a href="#" class="nav-item">웹툰</a>
            <a href="#" class="nav-item">영화</a>
        </div>
    </div>
    
    <!-- 메인 컨텐츠 -->
    <div class="main-container">
        <!-- 왼쪽 메인 섹션 -->
        <div class="main-left">
            <!-- API 설정 안내 -->
            {% if not has_api_keys %}
            <div class="api-info">
                <h4>⚠️ API 키 설정 필요</h4>
                <p>실시간 뉴스와 날씨 정보를 보려면 API 키를 설정해주세요:</p>
                <ol style="margin: 10px 0; padding-left: 20px;">
                    <li>날씨 API: <a href="https://openweathermap.org/api" target="_blank">OpenWeatherMap</a>에서 무료 키 발급</li>
                    <li>뉴스 API: <a href="https://newsapi.org/" target="_blank">News API</a>에서 무료 키 발급</li>
                    <li>app.py 파일의 상단에 있는 API 키 변수에 발급받은 키 입력</li>
                </ol>
                <p style="margin-top: 10px;">현재는 샘플 데이터가 표시됩니다.</p>
            </div>
            {% endif %}
            
            <!-- 실시간 뉴스 -->
            <div class="news-section">
                <div class="section-header">
                    <span class="section-title">📰 실시간 뉴스</span>
                    <span style="font-size: 13px; color: #666;">
                        <span id="update-time">{{ current_time }}</span> 
                        <button onclick="refreshNews()" style="margin-left: 10px; padding: 2px 8px; background: #03c75a; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">새로고침</button>
                    </span>
                </div>
                <div class="news-list" id="news-container">
                    {% for article in news %}
                    <div class="news-item">
                        <div class="news-source">{{ article.source }}</div>
                        <a href="{{ article.url }}" class="news-title" target="_blank">{{ article.title }}</a>
                        {% if article.description %}
                        <div class="news-desc">{{ article.description }}</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- 쇼핑 섹션 -->
            <div class="shopping">
                <div class="section-header">
                    <span class="section-title">쇼핑</span>
                    <span style="font-size: 13px; color: #666;">더보기</span>
                </div>
                <div class="shopping-grid">
                    <div class="shopping-item">
                        <div class="shopping-item-img">상품 이미지</div>
                        <div class="shopping-item-title">인기 상품</div>
                        <div class="shopping-item-price">29,900원</div>
                    </div>
                    <div class="shopping-item">
                        <div class="shopping-item-img">상품 이미지</div>
                        <div class="shopping-item-title">추천 상품</div>
                        <div class="shopping-item-price">39,900원</div>
                    </div>
                    <div class="shopping-item">
                        <div class="shopping-item-img">상품 이미지</div>
                        <div class="shopping-item-title">베스트 상품</div>
                        <div class="shopping-item-price">49,900원</div>
                    </div>
                    <div class="shopping-item">
                        <div class="shopping-item-img">상품 이미지</div>
                        <div class="shopping-item-title">특가 상품</div>
                        <div class="shopping-item-price">19,900원</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 오른쪽 사이드바 -->
        <div class="main-right">
            <!-- 로그인 박스 -->
            <div class="login-box">
                <div class="login-msg">
                    네이버를 더 안전하고 편리하게 이용하세요
                </div>
                <button class="login-btn">NAVER 로그인</button>
                <div class="login-links">
                    <a href="#">아이디 찾기</a>
                    <a href="#">비밀번호 찾기</a>
                    <a href="#">회원가입</a>
                </div>
            </div>
            
            <!-- 날씨 위젯 -->
            <div class="weather-widget">
                <div class="section-header">
                    <span class="section-title">🌤️ 오늘의 날씨</span>
                </div>
                <div class="weather-info" id="weather-container">
                    {% if weather.icon %}
                    <img src="http://openweathermap.org/img/wn/{{ weather.icon }}@2x.png" alt="날씨 아이콘" class="weather-icon">
                    {% endif %}
                    <div class="weather-details">
                        <div class="weather-temp">{{ weather.temp }}°C</div>
                        <div class="weather-desc">{{ weather.description }}</div>
                    </div>
                </div>
                <div class="weather-location">📍 {{ weather.city }}</div>
                <div class="weather-update">
                    <button onclick="refreshWeather()" style="width: 100%; padding: 5px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 3px; cursor: pointer; font-size: 12px;">날씨 새로고침</button>
                </div>
            </div>
            
            <!-- 광고 박스 -->
            <div class="ad-box">
                광고 영역
            </div>
        </div>
    </div>
    
    <!-- 푸터 -->
    <div class="footer">
        <div class="footer-content">
            <div class="footer-links">
                <a href="#">회사소개</a>
                <a href="#">인재채용</a>
                <a href="#">제휴제안</a>
                <a href="#">이용약관</a>
                <a href="#">개인정보처리방침</a>
                <a href="#">청소년보호정책</a>
                <a href="#">네이버 정책</a>
                <a href="#">고객센터</a>
            </div>
            <div>© NAVER Corp.</div>
        </div>
    </div>
    
    <script>
        // 뉴스 새로고침 함수
        function refreshNews() {
            const newsContainer = document.getElementById('news-container');
            newsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>뉴스를 불러오는 중...</p></div>';
            
            fetch('/api/news')
                .then(response => response.json())
                .then(data => {
                    let newsHTML = '';
                    data.news.forEach(article => {
                        newsHTML += `
                            <div class="news-item">
                                <div class="news-source">${article.source}</div>
                                <a href="${article.url}" class="news-title" target="_blank">${article.title}</a>
                                ${article.description ? `<div class="news-desc">${article.description}</div>` : ''}
                            </div>
                        `;
                    });
                    newsContainer.innerHTML = newsHTML;
                    document.getElementById('update-time').textContent = data.current_time;
                })
                .catch(error => {
                    newsContainer.innerHTML = '<div class="loading">뉴스를 불러올 수 없습니다.</div>';
                });
        }
        
        // 날씨 새로고침 함수
        function refreshWeather() {
            const weatherContainer = document.getElementById('weather-container');
            weatherContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            fetch('/api/weather')
                .then(response => response.json())
                .then(data => {
                    weatherContainer.innerHTML = `
                        ${data.icon ? `<img src="http://openweathermap.org/img/wn/${data.icon}@2x.png" alt="날씨 아이콘" class="weather-icon">` : ''}
                        <div class="weather-details">
                            <div class="weather-temp">${data.temp}°C</div>
                            <div class="weather-desc">${data.description}</div>
                        </div>
                    `;
                })
                .catch(error => {
                    weatherContainer.innerHTML = '<div class="loading">날씨 정보를 불러올 수 없습니다.</div>';
                });
        }
        
        // 10분마다 자동 새로고침
        setInterval(() => {
            refreshNews();
            refreshWeather();
        }, 600000); // 10분 = 600000ms
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    # API 키 확인 (날씨 API만 체크)
    has_weather_api = WEATHER_API_KEY != "YOUR_OPENWEATHER_API_KEY"
    
    # 날씨 정보 가져오기
    weather = get_weather()
    
    # 뉴스 가져오기
    news = get_news()
    
    # 현재 시간
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return render_template_string(HTML_TEMPLATE, 
                                 weather=weather, 
                                 news=news,
                                 current_time=current_time,
                                 has_api_keys=True)  # 항상 True로 설정하여 안내 메시지 숨김

@app.route('/api/news')
def api_news():
    """AJAX 요청용 뉴스 API 엔드포인트"""
    news = get_news()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return jsonify({'news': news, 'current_time': current_time})

@app.route('/api/weather')
def api_weather():
    """AJAX 요청용 날씨 API 엔드포인트"""
    weather = get_weather()
    return jsonify(weather)

if __name__ == '__main__':
    # 필요한 패키지 설치 안내
    print("="*50)
    print("필요한 패키지를 설치하세요:")
    print("pip install flask requests feedparser")
    print("="*50)
    print("\nRSS 피드로 한국 뉴스를 가져옵니다!")
    print("API 키 설정 (선택사항):")
    print("1. OpenWeatherMap API 키: https://openweathermap.org/api")
    print("   (날씨 정보를 위해 필요)")
    print("="*50)
    
    # 포트 설정 (기본: 5000)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n서버가 http://localhost:{port} 에서 실행 중입니다.")
    print("종료하려면 Ctrl+C를 누르세요.\n")
    
    # 디버그 모드로 실행 (개발 환경)
    app.run(host='0.0.0.0', port=port, debug=True)