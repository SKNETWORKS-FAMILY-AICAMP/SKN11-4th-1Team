// 전역 변수
let selectedCategory = '';
let tags = [];
let isPreviewMode = false;

// 태그 추천 목록
const tagSuggestions = [
    // 교통사고 관련
    '교차로', '사고', '과실비율', '보험', '합의', '치료비', '위자료',
    '블랙박스', '목격자', '경찰서', '사고처리', '차량손상',

    // 법률 관련  
    '법률상담', '소송', '변호사', '법원', '판례', '민사', '형사',
    '손해배상', '합의서', '진술서',

    // 차량 관련
    '자동차', '오토바이', '자전거', '보행자', '버스', '택시', '트럭',

    // 기타
    '질문', '경험담', '팁', '도움요청', '정보공유'
];

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function () {
    initializeCategoryButtons();
    initializeCharCounters();
    initializeTagInput();
    checkForDraft();
});

// 카테고리 버튼 초기화
function initializeCategoryButtons() {
    const categoryBtns = document.querySelectorAll('.category-btn');
    categoryBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            categoryBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedCategory = this.dataset.category;
            document.getElementById('selectedCategory').value = selectedCategory;
            showNotification(`"${this.textContent}" 카테고리를 선택했습니다.`);
        });
    });
}

// 글자수 카운터 초기화
function initializeCharCounters() {
    const titleInput = document.getElementById('postTitle');
    const titleCounter = document.getElementById('titleCounter');
    const contentInput = document.getElementById('postContent');
    const contentCounter = document.getElementById('contentCounter');

    titleInput.addEventListener('input', function () {
        const length = this.value.length;
        titleCounter.textContent = `${length} / 100`;
        titleCounter.className = 'char-counter';
        if (length > 80) titleCounter.classList.add('warning');
        if (length > 95) titleCounter.classList.add('danger');
    });

    contentInput.addEventListener('input', function () {
        contentCounter.textContent = `${this.value.length}자`;
    });
}

// 태그 입력 초기화
function initializeTagInput() {
    const tagInput = document.getElementById('tagInput');
    tagInput.addEventListener('keydown', handleTagInput);
    tagInput.addEventListener('input', showTagSuggestions);

    // 태그 영역 외부 클릭 시 suggestions 숨기기
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.tags-input-container')) {
            hideTagSuggestions();
        }
    });
}

// 태그 입력 처리
function handleTagInput(event) {
    if (event.key === 'Enter' || event.key === '#') {
        event.preventDefault();
        addTag(event.target.value.trim());
        event.target.value = '';
        hideTagSuggestions();
    } else if (event.key === 'Backspace' && event.target.value === '' && tags.length > 0) {
        removeTag(tags.length - 1);
    }
}

// 태그 추가
function addTag(tagText) {
    if (!tagText || tags.length >= 5 || tags.includes(tagText)) {
        if (tags.length >= 5) showNotification('태그는 최대 5개까지만 추가할 수 있습니다.', 'error');
        if (tags.includes(tagText)) showNotification('이미 추가된 태그입니다.', 'error');
        return;
    }

    tags.push(tagText);
    renderTags();
    showNotification(`"${tagText}" 태그가 추가되었습니다.`);
}

// 태그 제거
function removeTag(index) {
    const removedTag = tags[index];
    tags.splice(index, 1);
    renderTags();
    showNotification(`"${removedTag}" 태그가 제거되었습니다.`);
}

// 태그 렌더링
function renderTags() {
    const tagsDisplay = document.querySelector('.tags-display');
    const tagInput = document.getElementById('tagInput');

    // 기존 태그 아이템들 제거
    const existingTags = tagsDisplay.querySelectorAll('.tag-item');
    existingTags.forEach(tag => tag.remove());

    // 새 태그들 추가
    tags.forEach((tag, index) => {
        const tagElement = document.createElement('div');
        tagElement.className = 'tag-item';
        tagElement.innerHTML = `
                ${tag}
                <button type="button" class="tag-remove" onclick="removeTag(${index})">×</button>
            `;
        tagsDisplay.insertBefore(tagElement, tagInput);
    });
}

// 태그 제안 표시
function showTagSuggestions(event) {
    const input = event.target.value.toLowerCase();
    const suggestions = document.getElementById('tagSuggestions');

    if (!input) {
        hideTagSuggestions();
        return;
    }

    const filtered = tagSuggestions.filter(tag =>
        tag.toLowerCase().includes(input) && !tags.includes(tag)
    );

    if (filtered.length > 0) {
        suggestions.innerHTML = filtered.map(tag =>
            `<div class="tag-suggestion" onclick="selectTag('${tag}')">${tag}</div>`
        ).join('');
        suggestions.style.display = 'block';
    } else {
        hideTagSuggestions();
    }
}

// 태그 제안 숨기기
function hideTagSuggestions() {
    document.getElementById('tagSuggestions').style.display = 'none';
}

// 태그 선택
function selectTag(tag) {
    addTag(tag);
    document.getElementById('tagInput').value = '';
    hideTagSuggestions();
}

// 태그 입력 포커스
function focusTagInput() {
    document.getElementById('tagInput').focus();
}

// 미리보기 토글
function togglePreview() {
    const content = document.getElementById('postContent');
    const toolbar = document.querySelector('.toolbar');
    const btn = toolbar.querySelector('button');

    if (!isPreviewMode) {
        // 미리보기 모드로 전환
        const previewDiv = document.createElement('div');
        previewDiv.className = 'preview-mode';
        previewDiv.innerHTML = content.value.replace(/\n/g, '<br>') || '<em>내용을 입력해주세요...</em>';
        content.style.display = 'none';
        content.parentNode.insertBefore(previewDiv, content);
        isPreviewMode = true;
        btn.textContent = '✏️ 편집';
    } else {
        // 편집 모드로 전환
        const previewDiv = content.parentNode.querySelector('.preview-mode');
        if (previewDiv) {
            previewDiv.remove();
        }
        content.style.display = 'block';
        isPreviewMode = false;
        btn.textContent = '👁️ 미리보기';
    }
}

// 임시저장
function saveDraft() {
    const formData = new FormData(document.getElementById('postForm'));
    const draftData = {
        type: document.querySelector('input[name="post_type"]:checked').value,
        category: selectedCategory,
        title: document.getElementById('postTitle').value,
        content: document.getElementById('postContent').value,
        tags: tags,
        timestamp: new Date().toISOString()
    };

    localStorage.setItem('postDraft', JSON.stringify(draftData));
    showNotification('임시저장되었습니다!');
}

// 임시저장 불러오기
function loadDraft() {
    const draft = localStorage.getItem('postDraft');
    if (draft) {
        const data = JSON.parse(draft);

        // 게시글 유형 설정
        if (data.type) {
            document.querySelector(`input[value="${data.type}"]`).checked = true;
        }

        // 제목과 내용 설정
        document.getElementById('postTitle').value = data.title || '';
        document.getElementById('postContent').value = data.content || '';

        // 태그 설정
        tags = data.tags || [];
        renderTags();

        // 카테고리 설정
        if (data.category) {
            const categoryBtn = document.querySelector(`[data-category="${data.category}"]`);
            if (categoryBtn) {
                categoryBtn.click();
            }
        }

        // 글자수 카운터 업데이트
        const titleEvent = new Event('input');
        const contentEvent = new Event('input');
        document.getElementById('postTitle').dispatchEvent(titleEvent);
        document.getElementById('postContent').dispatchEvent(contentEvent);

        showNotification('임시저장된 내용을 불러왔습니다.');
    }
}

// 임시저장 확인
function checkForDraft() {
    if (localStorage.getItem('postDraft')) {
        if (confirm('임시저장된 게시글이 있습니다. 불러오시겠습니까?')) {
            loadDraft();
        }
    }
}

// 게시글 제출
function submitPost(event) {
    event.preventDefault();

    // 유효성 검사
    if (!selectedCategory) {
        showNotification('카테고리를 선택해주세요!', 'error');
        return;
    }

    const title = document.getElementById('postTitle').value.trim();
    const content = document.getElementById('postContent').value.trim();

    if (!title) {
        showNotification('제목을 입력해주세요!', 'error');
        document.getElementById('postTitle').focus();
        return;
    }

    if (!content) {
        showNotification('내용을 입력해주세요!', 'error');
        document.getElementById('postContent').focus();
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    const originalText = submitBtn.textContent;

    // 버튼 비활성화
    submitBtn.disabled = true;
    submitBtn.textContent = '등록 중...';

    // 폼 데이터 준비
    const postData = {
        type: document.querySelector('input[name="post_type"]:checked').value,
        category: selectedCategory,
        title: title,
        content: content,
        tags: tags
    };

    // 서버로 전송
    fetch(window.location.pathname, {  // 현재 URL로 전송
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(postData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 임시저장 데이터 삭제
                localStorage.removeItem('postDraft');
                showNotification(data.message);

                // 게시글 상세 페이지로 이동
                setTimeout(() => {
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.href = `/community/detail/${data.post_id}/`;
                    }
                }, 1500);
            } else {
                showNotification(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('게시글 등록 중 오류가 발생했습니다.', 'error');
        })
        .finally(() => {
            // 버튼 복원
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
}

// 임시저장 데이터 구조도 마이그레이션에 맞게 수정
function saveDraft() {
    const formData = new FormData(document.getElementById('postForm'));
    const draftData = {
        type: document.querySelector('input[name="post_type"]:checked').value,
        category: selectedCategory,
        title: document.getElementById('postTitle').value,
        content: document.getElementById('postContent').value,
        tags: tags,
        timestamp: new Date().toISOString()
    };

    localStorage.setItem('postDraft', JSON.stringify(draftData));
    showNotification('임시저장되었습니다!');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
// 취소
function goBack() {
    const hasContent = document.getElementById('postTitle').value.trim() ||
        document.getElementById('postContent').value.trim() ||
        tags.length > 0;

    if (hasContent && confirm('작성 중인 내용이 있습니다. 정말 나가시겠습니까?')) {
        showNotification('이전 페이지로 이동합니다...');
        // 실제 환경에서는: window.history.back();
    } else if (!hasContent) {
        showNotification('이전 페이지로 이동합니다...');
        // 실제 환경에서는: window.history.back();
    }
}

// 알림 메시지 표시
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type === 'error' ? 'error' : ''}`;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// 페이지 이탈 시 경고
window.addEventListener('beforeunload', function (event) {
    const title = document.getElementById('postTitle').value.trim();
    const content = document.getElementById('postContent').value.trim();

    if (title || content || tags.length > 0) {
        event.preventDefault();
        event.returnValue = '작성 중인 내용이 있습니다. 정말 나가시겠습니까?';
    }
});

// 자동 저장 (5분마다)
setInterval(() => {
    const title = document.getElementById('postTitle').value.trim();
    const content = document.getElementById('postContent').value.trim();

    if (title || content || tags.length > 0) {
        saveDraft();
    }
}, 300000); // 5분

// 키보드 단축키
document.addEventListener('keydown', function (event) {
    // Ctrl+S: 임시저장
    if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        saveDraft();
    }

    // Ctrl+Enter: 게시글 등록
    if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        document.getElementById('postForm').dispatchEvent(new Event('submit'));
    }
});