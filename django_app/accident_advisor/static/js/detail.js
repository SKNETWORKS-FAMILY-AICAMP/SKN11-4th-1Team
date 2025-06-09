// 공유하기 기능
function sharePost() {
    const postTitle = document.querySelector('.card-title').textContent.trim();
    
    if (navigator.share) {
        navigator.share({
            title: postTitle,
            text: `${postTitle} - 교통사고 상담 커뮤니티`,
            url: window.location.href
        });
    } else {
        // 클립보드에 URL 복사
        navigator.clipboard.writeText(window.location.href).then(function () {
            alert('링크가 클립보드에 복사되었습니다!');
        });
    }
}

// 댓글 등록
function submitComment(event) {
    event.preventDefault();
    const form = document.getElementById('commentForm');
    const textarea = form.querySelector('textarea');
    const content = textarea.value.trim();
    const submitBtn = document.getElementById('commentSubmitBtn');
    const url = submitBtn.getAttribute('data-create-url');
    if (!content) {
        alert('댓글 내용을 입력해주세요.');
        textarea.focus();
        return;
    }
    fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.CSRF_TOKEN || getCookie('csrftoken')
        },
        body: JSON.stringify({ content: content })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.error || "댓글 등록 중 오류가 발생했습니다.");
        }
    })
    .catch(() => {
        alert("댓글 등록 중 오류가 발생했습니다.");
    });
}

// 게시글 좋아요 버튼 동작 추가
document.addEventListener('DOMContentLoaded', function() {
    // 게시글 좋아요
    const likeBtn = document.querySelector('.like-btn[data-post-id]');
    if (likeBtn) {
        likeBtn.addEventListener('click', function() {
            const url = likeBtn.getAttribute('data-toggle-url');
            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": window.CSRF_TOKEN || getCookie('csrftoken'),
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const likeCountSpan = likeBtn.querySelector('.like-count');
                    likeCountSpan.textContent = `❤️${data.like_count}`;
                    if (data.liked) {
                        likeBtn.classList.remove('btn-outline-danger');
                        likeBtn.classList.add('btn-danger');
                    } else {
                        likeBtn.classList.remove('btn-danger');
                        likeBtn.classList.add('btn-outline-danger');
                    }
                } else {
                    alert(data.error || "좋아요 처리 중 오류가 발생했습니다.");
                }
            })
            .catch(() => {
                alert("좋아요 처리 중 오류가 발생했습니다.");
            });
        });
    }

    // 댓글 좋아요 (여러 개이므로 querySelectorAll)
    document.querySelectorAll('.comment-like-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const url = btn.getAttribute('data-toggle-url');
            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": window.CSRF_TOKEN || getCookie('csrftoken'),
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const likeCountSpan = btn.querySelector('.like-count');
                    likeCountSpan.textContent = `❤️${data.like_count}`;
                    if (data.liked) {
                        btn.classList.remove('btn-outline-danger');
                        btn.classList.add('btn-danger');
                    } else {
                        btn.classList.remove('btn-danger');
                        btn.classList.add('btn-outline-danger');
                    }
                } else {
                    alert(data.error || "댓글 좋아요 처리 중 오류가 발생했습니다.");
                }
            })
            .catch(() => {
                alert("댓글 좋아요 처리 중 오류가 발생했습니다.");
            });
        });
    });
});

// CSRF 토큰을 쿠키에서 가져오는 함수 (window.CSRF_TOKEN이 없을 때 사용)
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