# 교통사고 상담 챗봇 "노느" - 팀원 작업 가이드

## 🎯 프로젝트 개요
- **프로젝트명**: 노느 (교통사고 과실비율 상담 챗봇)
- **기술스택**: Django + Bootstrap + jQuery
- **목표**: 각 팀원이 독립적으로 자신의 페이지를 개발

## 📋 팀원별 작업 분담

### 👑 **리더** - 메인 채팅 페이지 + AI 연동
- **담당 파일**: `main/` 앱 전체 + AI 모델 연동
- **주요 작업**: 채팅 인터페이스, 히스토리, RAG + 파인튜닝

### 👨‍💻 **팀원 A** - 로그인/회원가입 페이지
- **담당 폴더**: `accounts/` 앱
- **주요 작업**: 
  - `templates/accounts/login.html` (로그인 페이지)
  - `templates/accounts/signup.html` (회원가입 페이지)
  - `templates/accounts/profile.html` (프로필 페이지)

### 👩‍💻 **팀원 B** - 커뮤니티 목록 페이지
- **담당 폴더**: `templates/community/list.html`
- **주요 작업**:
  - 게시글 목록 표시
  - 카테고리별 필터링
  - 검색 기능
  - 페이지네이션

### 👨‍💻 **팀원 C** - 게시글 상세 페이지
- **담당 폴더**: `templates/community/detail.html`
- **주요 작업**:
  - 게시글 상세 내용 표시
  - 댓글 목록 및 작성
  - 좋아요 버튼 (AJAX)

### 👩‍💻 **팀원 D** - 게시글 작성 페이지
- **담당 폴더**: `templates/community/write.html`
- **주요 작업**:
  - 게시글 작성 폼
  - 카테고리 선택
  - 제목/내용/태그 입력

## 🚀 시작하기

### 1. 개발 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 패키지 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python manage.py makemigrations
python manage.py migrate

# 초기 데이터 생성
python manage.py create_initial_data

# 서버 실행
python manage.py runserver
```

### 2. 관리자 페이지 접속
- URL: http://127.0.0.1:8000/admin/
- 계정: admin / admin123!

## 📁 프로젝트 구조

```
accident_advisor/
├── core/                    # 공통 모델 (리더 관리)
│   ├── models.py           # 모든 데이터베이스 모델
│   └── admin.py            # 관리자 설정
├── main/                   # 메인 채팅 (리더)
│   ├── views.py
│   └── urls.py
├── accounts/               # 로그인/회원가입 (팀원 A)
│   ├── views.py           # 이미 작성됨
│   ├── forms.py           # 이미 작성됨
│   └── urls.py            # 이미 작성됨
├── community/              # 커뮤니티 (팀원 B,C,D)
│   ├── views.py           # 이미 작성됨
│   ├── forms.py           # 이미 작성됨
│   └── urls.py            # 이미 작성됨
├── templates/              # HTML 템플릿
│   ├── base.html          # 기본 템플릿 (이미 작성됨)
│   ├── accounts/          # 팀원 A 작업 폴더
│   ├── community/         # 팀원 B,C,D 작업 폴더
│   └── main/              # 리더 작업 폴더
└── static/                 # CSS, JS 파일
    ├── css/main.css       # 기본 스타일 (이미 작성됨)
    └── js/main.js         # 기본 스크립트 (이미 작성됨)
```

## 📋 각 팀원별 상세 가이드

### 🔥 **팀원 A - 로그인/회원가입 페이지**

#### 작업할 파일들:
- `templates/accounts/login.html`
- `templates/accounts/signup.html`
- `templates/accounts/profile.html`

#### 사용 가능한 데이터:
```python
# views.py에서 전달되는 데이터
context = {
    'form': form,           # 로그인/회원가입 폼
    'title': '페이지 제목',
    'user': request.user    # 현재 사용자 (프로필 페이지)
}
```

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

### 🔥 **팀원 B - 커뮤니티 목록 페이지**

#### 작업할 파일:
- `templates/community/list.html`

#### 사용 가능한 데이터:
```python
context = {
    'categories': categories,           # 카테고리 목록
    'posts': page_obj,                 # 게시글 목록 (페이지네이션)
    'search_query': search_query,      # 검색어
    'selected_category': category_id,  # 선택된 카테고리
}
```

#### 주요 기능:
- 카테고리별 필터링
- 검색 기능
- 게시글 목록 표시
- 페이지네이션

### 🔥 **팀원 C - 게시글 상세 페이지**

#### 작업할 파일:
- `templates/community/detail.html`

#### 사용 가능한 데이터:
```python
context = {
    'post': post,                    # 게시글 객체
    'comments': comments,            # 댓글 목록
    'comment_form': comment_form,    # 댓글 작성 폼
    'user_liked': user_liked,        # 사용자 좋아요 여부
}
```

#### 주요 기능:
- 게시글 상세 내용
- 댓글 목록 및 작성
- 좋아요 버튼 (AJAX)

### 🔥 **팀원 D - 게시글 작성 페이지**

#### 작업할 파일:
- `templates/community/write.html`

#### 사용 가능한 데이터:
```python
context = {
    'form': form,              # 게시글 작성 폼
    'categories': categories,  # 카테고리 목록
}
```

#### 주요 기능:
- 제목/내용 입력
- 카테고리 선택
- 태그 입력
- 게시글 유형 선택

## 🎨 사용 가능한 CSS 클래스

프로젝트에 이미 정의된 CSS 클래스들을 활용하세요:

```css
/* 컨테이너 */
.auth-container          /* 로그인/회원가입 컨테이너 */
.post-item              /* 게시글 아이템 */
.category-filter        /* 카테고리 필터 영역 */

/* 버튼 */
.btn-primary            /* 기본 버튼 */
.category-btn           /* 카테고리 버튼 */
.like-btn              /* 좋아요 버튼 */

/* 폼 */
.form-control           /* 입력 필드 */
.auth-form             /* 인증 폼 */

/* 기타 */
.text-gradient         /* 그라데이션 텍스트 */
.shadow-custom         /* 커스텀 그림자 */
```

## 📚 유용한 JavaScript 함수들

이미 정의된 함수들을 활용하세요:

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

## ⚠️ 주의사항

### 절대 수정하지 말 것:
- `core/models.py` (모든 모델)
- `settings.py` (Django 설정)
- 다른 팀원의 템플릿 파일
- `base.html` (기본 템플릿)

### 자유롭게 수정 가능:
- 자신이 담당하는 템플릿 파일
- `static/css/` 폴더에 개인 CSS 파일 추가
- `static/js/` 폴더에 개인 JS 파일 추가

## 🆘 도움이 필요할 때

1. **Django 모델 사용법**: `core/models.py` 파일 참고
2. **기존 뷰 함수 로직**: 각 앱의 `views.py` 파일 참고
3. **Bootstrap 사용법**: https://getbootstrap.com/docs/5.1/
4. **jQuery 사용법**: https://api.jquery.com/
5. **팀 내 질문**: 팀원 A 또는 리더에게 문의

## ✅ 완성 체크리스트

### 팀원 A (accounts):
- [ ] 로그인 페이지 디자인
- [ ] 회원가입 페이지 디자인
- [ ] 프로필 페이지 디자인
- [ ] 폼 유효성 검사 JavaScript
- [ ] 반응형 디자인

### 팀원 B (community/list):
- [ ] 게시글 목록 표시
- [ ] 카테고리 필터링
- [ ] 검색 기능
- [ ] 페이지네이션
- [ ] 반응형 디자인

### 팀원 C (community/detail):
- [ ] 게시글 상세 표시
- [ ] 댓글 목록 표시
- [ ] 댓글 작성 폼
- [ ] 좋아요 버튼 (AJAX)
- [ ] 반응형 디자인

### 팀원 D (community/write):
- [ ] 게시글 작성 폼
- [ ] 카테고리 선택 UI
- [ ] 제목/내용 입력
- [ ] 태그 입력
- [ ] 반응형 디자인

행운을 빕니다! 🚀