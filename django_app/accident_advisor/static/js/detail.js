// static/js/detail.js

// CSRF 토큰 가져오기 함수
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

// 좋아요 버튼 기능
function initializeLikeButton() {
    const likeBtn = document.getElementById('likeBtn');
    if (!likeBtn) return;

    likeBtn.addEventListener('click', function() {
        const postId = this.dataset.postId;
        const csrftoken = getCookie('csrftoken');
        
        fetch(`/posts/${postId}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('likeCount').textContent = data.like_count;
                const likeBtn = document.getElementById('likeBtn');
                const likeIcon = document.getElementById('likeIcon');
                
                if (data.liked) {
                    likeBtn.classList.add('liked');
                    likeIcon.textContent = '❤️';
                } else {
                    likeBtn.classList.remove('liked');
                    likeIcon.textContent = '🤍';
                }
            }
        })
        .catch(error => {
            console.error('좋아요 처리 중 오류:', error);
            alert('좋아요 처리 중 오류가 발생했습니다.');
        });
    });
}

// 댓글 작성 기능
function initializeCommentForm() {
    const commentForm = document.getElementById('commentForm');
    if (!commentForm) return;

    commentForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const csrftoken = getCookie('csrftoken');
        const postId = document.getElementById('likeBtn').dataset.postId;
        
        fetch(`/posts/${postId}/comments/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addCommentToList(data.comment);
                updateCommentCount(data.comment_count);
                this.reset();
            } else {
                alert('댓글 작성에 실패했습니다.');
            }
        })
        .catch(error => {
            console.error('댓글 작성 중 오류:', error);
            alert('댓글 작성 중 오류가 발생했습니다.');
        });
    });
}

// 댓글 목록에 새 댓글 추가
function addCommentToList(comment) {
    const commentsList = document.getElementById('commentsList');
    
    // 빈 댓글 메시지가 있다면 제거
    const emptyMessage = commentsList.querySelector('.comment-text[style*="text-align: center"]');
    if (emptyMessage) {
        emptyMessage.parentElement.remove();
    }
    
    const newComment = document.createElement('div');
    newComment.className = 'comment-item';
    newComment.innerHTML = `
        <div class="comment-author">
            <div class="comment-avatar">${comment.author_initial}</div>
            <span class="comment-name">${comment.author}</span>
            <span class="comment-date">${comment.created_at}</span>
        </div>
        <div class="comment-text">${comment.content.replace(/\n/g, '<br>')}</div>
    `;
    
    commentsList.appendChild(newComment);
}

// 댓글 수 업데이트
function updateCommentCount(count) {
    const commentCountElement = document.getElementById('commentCount');
    if (commentCountElement) {
        commentCountElement.textContent = count;
    }
}

// 공유 버튼 기능
function initializeShareButton() {
    const shareBtn = document.querySelector('.share-btn');
    if (!shareBtn) return;

    shareBtn.addEventListener('click', function() {
        if (navigator.share) {
            navigator.share({
                title: document.querySelector('.post-title').textContent,
                url: window.location.href
            }).catch(console.error);
        } else {
            // 클립보드에 URL 복사
            navigator.clipboard.writeText(window.location.href).then(() => {
                alert('링크가 클립보드에 복사되었습니다.');
            }).catch(() => {
                alert('링크 복사에 실패했습니다.');
            });
        }
    });
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeLikeButton();
    initializeCommentForm();
    initializeShareButton();
});
