document.addEventListener('DOMContentLoaded', function () {
    // 좋아요 버튼 이벤트
    const likeBtn = document.querySelector('.like-btn');
    if (likeBtn) {
        likeBtn.addEventListener('click', function () {
            const postId = this.dataset.postId;
            const isLiked = this.dataset.liked === 'true';

            // Django URL을 동적으로 생성하기 위해 data 속성 사용
            const toggleLikeUrl = this.dataset.toggleUrl || `/community/post/${postId}/toggle-like/`;

            fetch(toggleLikeUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 좋아요 상태 업데이트
                        this.dataset.liked = data.liked;
                        const heartIcon = this.querySelector('i');
                        const likeCount = this.querySelector('.like-count');

                        if (data.liked) {
                            heartIcon.className = 'fas fa-heart me-1';
                            this.classList.remove('btn-outline-danger');
                            this.classList.add('btn-danger');
                        } else {
                            heartIcon.className = 'fas fa-heart-o me-1';
                            this.classList.remove('btn-danger');
                            this.classList.add('btn-outline-danger');
                        }

                        likeCount.textContent = `❤️${data.like_count}`;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('오류가 발생했습니다.');
                });
        });
    }
});

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