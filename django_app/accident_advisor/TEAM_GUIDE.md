# 🚨 노느 - 교통사고 과실비율 산정 AI 챗봇 Django 프로젝트

## 🎯 프로젝트 개요
- **프로젝트명**: 노느 (교통사고 과실비율 상담 챗봇)
- **기술스택**: Django 5.2.1 + Bootstrap 5.1.3 + jQuery 3.6.0 + AI/ML (RAG + 파인튜닝)
- **목표**: 교통사고 발생 시 법률 기준과 판례를 기반으로 과실비율을 신속하게 산정해주는 AI 챗봇

## 🏠 프로젝트 구조

```
accident_advisor/
├── 🛠️ manage.py
├── 📜 requirements.txt
├── 🗺️ TEAM_GUIDE.md
├── 📁 accident_advisor/ (프로젝트 설정)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── 📁 core/ (공통 모델)
│   ├── models.py (모든 데이터베이스 모델)
│   ├── admin.py
│   └── management/commands/create_initial_data.py
├── 📁 main/ (메인 챗봇 - 리더)
│   ├── views.py
│   └── urls.py
├── 📁 accounts/ (로그인/회원가입 - 팀원 A)
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── 📁 community/ (커뮤니티 - 팀원 B,C,D)
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── 📁 templates/ (HTML 템플릿)
│   ├── base.html
│   ├── main/index.html
│   ├── accounts/ (팀원 A 작업 폴더)
│   └── community/ (팀원 B,C,D 작업 폴더)
└── 📁 static/ (CSS, JS)
    ├── css/main.css
    └── js/main.js
```

## 🚀 실행법

### 1. 가상환경 설정
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 초기화
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py create_initial_data
```

### 4. 서버 실행
```bash
python manage.py runserver
```

## 📊 데이터베이스 모델 구조

### 👤 User 모델 (확장된 사용자 모델)
- `nickname`: 닉네임
- `profile_image`: 프로필 이미지
- `total_chats`: 총 챗팅 수 (자동 업데이트)
- `total_posts`: 총 게시글 수 (자동 업데이트)

### 🤖 AI/데이터 모델들 (리더만 사용)

#### ⚙️ AccidentCase: 교통사고 사례 데이터베이스 (AI 학습용)
- `case_id`: 사례 ID
- `title`: 사례 제목
- `description`: 사고 상황 설명
- `fault_ratio_a/b`: A/B차량 과실비율(%)
- `case_type`: 사고 유형 (교차로, 주차장, 차로변경 등)
- `legal_basis`: 법적 근거 (도로교통법 조문, 판례 등)

### 💬 채팅 모델들 (리더만 사용)

#### 📝 ChatSession: 채팅 세션 관리
- `user`: 사용자 연결 (null 가능 = 익명 사용자)
- `session_id`: 고유 세션 ID (UUID)
- `title`: 상담 제목 (첫 메시지로 자동 생성)
- `message_count`: 메시지 수 (자동 업데이트)
- `is_active`: 활성 상태

#### 💬 ChatMessage: 채팅 메시지
- `session`: 채팅 세션 연결
- `sender`: 발신자 ('user' 또는 'bot')
- `content`: 메시지 내용
- `ai_confidence`: AI 신뢰도 (선택사항, 나중에 AI 모델 평가용)

### 📝 커뮤니티 모델들 (팀원들이 사용)

#### 📎 Category: 게시글 카테고리
- `name`: 카테고리명
- `description`: 카테고리 설명
- `icon`: 아이콘 (이모지 하나)
- `post_count`: 게시글 수 (자동 업데이트)

#### 📝 Post: 커뮤니티 게시글
- `author`: 작성자 (User 모델과 연결)
- `category`: 카테고리
- `title`: 제목
- `content`: 내용
- `post_type`: 게시글 유형 ('question', 'experience', 'tip')
- `is_resolved`: 해결됨 (질문이 해결되었는지 여부)
- `view_count`: 조회수 (자동 업데이트)
- `like_count`: 좋아요 수 (자동 업데이트)
- `comment_count`: 댓글 수 (자동 업데이트)
- `tags`: 태그 (쉼표로 구분해서 입력, 예: '교차로,사고,과실비율')

#### 💬 Comment: 댓글
- `post`: 게시글 연결
- `author`: 작성자
- `content`: 댓글 내용
- `like_count`: 좋아요 수 (자동 업데이트)
- `is_active`: 활성 상태

## 👥 팀원별 작업 분담 및 가이드

### 👑 **리더 - 메인 챗봇 페이지 + AI 연동**
- **담당 파일**: `main/` 앱 전체 + AI 모델 연동
- **주요 작업**: 채팅 인터페이스, 히스토리, RAG + 파인튜닝
- **현재 상태**: 기본 채팅 인터페이스 완료, 임시 응답 시스템 구현됨
- **다음 단계**: OpenAI API 연동, RAG 시스템 구축, 파인튜닝 모델 적용

### 👨‍💻 **팀원 A - 로그인/회원가입 페이지**
- **담당 폴더**: `accounts/` 앱
- **주요 작업**:
  - `templates/accounts/login.html` (로그인 페이지)
  - `templates/accounts/signup.html` (회원가입 페이지)
  - `templates/accounts/profile.html` (프로필 페이지)
- **현재 상태**: views.py, forms.py, urls.py 이미 작성됨. HTML 템플릿만 작업 필요
- **사용 가능한 데이터**: form, title, user 객체

#### 예시 템플릿 구조:
```html
{% extends 'base.html' %}

{% block title %}로그인 - 노느{% endblock %}

{% block content %}
<div class="container">
    <div class="auth-container">
        <div class="auth-header">
            <h2>{{ title }}</h2>
        </div>
        
        <form method="post" class="auth-form">
            {% csrf_token %}
            <!-- 폼 필드들 -->
        </form>
        
        <div class="auth-links">
            <!-- 링크들 -->
        </div>
    </div>
</div>
{% endblock %}
```

### 👩‍💻 **팀원 B - 커뮤니티 목록 페이지**
- **담당 파일**: `templates/community/list.html`
- **주요 작업**:
  - 게시글 목록 표시
  - 카테고리별 필터링
  - 검색 기능
  - 페이지네이션
- **사용 가능한 데이터**: categories, posts, search_query, selected_category

### 👨‍💻 **팀원 C - 게시글 상세 페이지**
- **담당 파일**: `templates/community/detail.html`
- **주요 작업**:
  - 게시글 상세 내용 표시
  - 댓글 목록 및 작성
  - 좋아요 버튼 (AJAX)
- **사용 가능한 데이터**: post, comments, comment_form, user_liked

### 👩‍💻 **팀원 D - 게시글 작성 페이지**
- **담당 파일**: `templates/community/write.html`
- **주요 작업**:
  - 게시글 작성 폼
  - 카테고리 선택
  - 제목/내용/태그 입력
  - 게시글 유형 선택
- **사용 가능한 데이터**: form, categories

## ⚠️ 주의사항 및 가이드라인

### 🚫 절대 수정하지 말 것:
- `core/models.py` (모든 모델)
- `settings.py` (Django 설정)
- 다른 팀원의 템플릿 파일
- `base.html` (기본 템플릿)

### ✅ 자유롭게 수정 가능:
- 자신이 담당하는 템플릿 파일
- `static/css/` 폴더에 개인 CSS 파일 추가
- `static/js/` 폴더에 개인 JS 파일 추가

## 🎨 사용 가능한 CSS 클래스 및 JavaScript 함수

### Bootstrap 5.1.3 + Custom CSS 포함
프로젝트에 이미 정의된 CSS 클래스들을 활용하세요:

- `.auth-container`: 로그인/회원가입 컨테이너
- `.post-item`: 게시글 아이템
- `.category-filter`: 카테고리 필터 영역
- `.btn-primary`: 기본 버튼
- `.category-btn`: 카테고리 버튼
- `.like-btn`: 좋아요 버튼
- `.form-control`: 입력 필드
- `.auth-form`: 인증 폼

### 유용한 JavaScript 함수들 (jQuery 3.6.0 포함)
```javascript
// 메시지 표시
showSuccess('성공 메시지');
showError('에러 메시지');

// 폼 유효성 검사
validateForm('formId');

// 좋아요 토글
toggleLike(postId, buttonElement);

// 문자 수 카운터
updateCharCount(input, counter, maxLength);

// 확인 대화상자
confirmAction('정말 삭제하시겠습니까?', callback);
```

## 🔍 개발 환경 접속 URL

- **메인 사이트**: http://127.0.0.1:8000/
- **관리자 페이지**: http://127.0.0.1:8000/admin/
- **관리자 계정**: admin / admin123!
- **커뮤니티 목록**: http://127.0.0.1:8000/community/
- **로그인**: http://127.0.0.1:8000/accounts/login/
- **회원가입**: http://127.0.0.1:8000/accounts/signup/

## 🔧 개발 도구 및 참고 자료

- **Django 모델 사용법**: core/models.py 파일 참고
- **기존 뷰 함수 로직**: 각 앱의 views.py 파일 참고
- **Bootstrap 사용법**: https://getbootstrap.com/docs/5.1/
- **jQuery 사용법**: https://api.jquery.com/
- **Django 공식 매뉴얼**: https://docs.djangoproject.com/


## 🛠️ 기술적 특징

### 이미 준비된 것들:
✅ **Django 5.2.1** - 최신 버전 사용
✅ **Bootstrap 5.1.3** - 현대적 UI 컴포넌트
✅ **jQuery 3.6.0** - DOM 조작 및 AJAX
✅ **SQLite 데이터베이스** - 개발용으로 설정
✅ **한국어/한국 시간대** - 로컬라이제이션 완료
✅ **커스텀 User 모델** - 확장 가능한 사용자 시스템
✅ **관리자 패널** - 데이터 관리 편의성

### 확장 예정:
🔜 **OpenAI API 연동** - GPT 모델 활용
🔜 **RAG 시스템** - 벡터 데이터베이스와 연동
🔜 **파인튜닝 모델** - 교통사고 전문 AI 모델
🔜 **실시간 채팅** - WebSocket 연동 검토

## 🆘 도움이 필요할 때

1. **Django 모델 사용법**: `core/models.py` 파일 참고
2. **기존 뷰 함수 로직**: 각 앱의 `views.py` 파일 참고
3. **Bootstrap 사용법**: https://getbootstrap.com/docs/5.1/
4. **jQuery 사용법**: https://api.jquery.com/
5. **팀 내 질문**: 리더 또는 다른 팀원에게 문의


