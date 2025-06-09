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