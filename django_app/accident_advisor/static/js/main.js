// 메인 JavaScript 파일

$(document).ready(function() {
    // 페이지 로드 애니메이션
    $('body').addClass('fade-in');
    
    // 알림 메시지 자동 숨김
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
    
    // 툴팁 초기화
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 스크롤 시 네비게이션 바 효과
    $(window).scroll(function() {
        if ($(this).scrollTop() > 50) {
            $('.navbar').addClass('scrolled');
        } else {
            $('.navbar').removeClass('scrolled');
        }
    });
});

// 공통 AJAX 설정
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

// CSRF 토큰 가져오기
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

// CSRF 안전한 메소드 확인
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// 로딩 스피너 표시/숨김
function showLoading(target = 'body') {
    $(target).append(`
        <div class="loading-overlay">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
}

function hideLoading() {
    $('.loading-overlay').remove();
}

// 에러 메시지 표시
function showError(message, container = '.container') {
    const errorHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $(container).prepend(errorHtml);
    
    // 5초 후 자동 숨김
    setTimeout(function() {
        $('.alert-danger').fadeOut('slow');
    }, 5000);
}

// 성공 메시지 표시
function showSuccess(message, container = '.container') {
    const successHtml = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="bi bi-check-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $(container).prepend(successHtml);
    
    // 3초 후 자동 숨김
    setTimeout(function() {
        $('.alert-success').fadeOut('slow');
    }, 3000);
}

// 확인 대화상자
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 좋아요 토글 (커뮤니티용)
function toggleLike(postId, button) {
    $.ajax({
        url: `/community/${postId}/like/`,
        method: 'POST',
        success: function(response) {
            if (response.success) {
                const $button = $(button);
                const $icon = $button.find('i');
                const $count = $button.find('.like-count');
                
                if (response.liked) {
                    $button.addClass('liked');
                    $icon.removeClass('bi-heart').addClass('bi-heart-fill');
                    showSuccess('좋아요!');
                } else {
                    $button.removeClass('liked');
                    $icon.removeClass('bi-heart-fill').addClass('bi-heart');
                    showSuccess('좋아요 취소');
                }
                
                $count.text(response.like_count);
            }
        },
        error: function() {
            showError('좋아요 처리 중 오류가 발생했습니다.');
        }
    });
}

// 텍스트 영역 자동 크기 조절
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

// 이미지 미리보기
function previewImage(input, preview) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            $(preview).attr('src', e.target.result).show();
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// 문자 수 카운터
function updateCharCount(input, counter, maxLength) {
    const currentLength = $(input).val().length;
    $(counter).text(`${currentLength}/${maxLength}`);
    
    if (currentLength > maxLength * 0.9) {
        $(counter).addClass('text-warning');
    } else {
        $(counter).removeClass('text-warning');
    }
    
    if (currentLength > maxLength) {
        $(counter).addClass('text-danger').removeClass('text-warning');
    } else {
        $(counter).removeClass('text-danger');
    }
}

// 폼 유효성 검사
function validateForm(formId) {
    let isValid = true;
    
    $(`#${formId} [required]`).each(function() {
        const $field = $(this);
        const value = $field.val().trim();
        
        if (!value) {
            $field.addClass('is-invalid');
            isValid = false;
        } else {
            $field.removeClass('is-invalid').addClass('is-valid');
        }
    });
    
    // 이메일 형식 검사
    $(`#${formId} input[type="email"]`).each(function() {
        const $field = $(this);
        const email = $field.val().trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (email && !emailRegex.test(email)) {
            $field.addClass('is-invalid');
            isValid = false;
        }
    });
    
    return isValid;
}

// 페이지 상단으로 스크롤
function scrollToTop() {
    $('html, body').animate({scrollTop: 0}, 'slow');
}

// 부드러운 스크롤
function smoothScroll(target) {
    $('html, body').animate({
        scrollTop: $(target).offset().top - 100
    }, 'slow');
}

// 클립보드에 복사
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showSuccess('클립보드에 복사되었습니다.');
    }).catch(function() {
        showError('복사에 실패했습니다.');
    });
}

// 날짜 포맷팅
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;
    if (hours < 24) return `${hours}시간 전`;
    if (days < 7) return `${days}일 전`;
    
    return date.toLocaleDateString('ko-KR');
}

// 숫자 포맷팅 (천 단위 콤마)
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// 디바운스 함수 (검색 등에 사용)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 모바일 디바이스 감지
function isMobile() {
    return window.innerWidth <= 768;
}

// 네트워크 상태 확인
function checkNetworkStatus() {
    if (!navigator.onLine) {
        showError('네트워크 연결을 확인해주세요.');
        return false;
    }
    return true;
}

// 전역 에러 핸들러
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showError('예상치 못한 오류가 발생했습니다.');
});

// 전역 AJAX 에러 핸들러
$(document).ajaxError(function(event, xhr, settings, error) {
    if (xhr.status === 403) {
        showError('권한이 없습니다.');
    } else if (xhr.status === 404) {
        showError('요청한 페이지를 찾을 수 없습니다.');
    } else if (xhr.status === 500) {
        showError('서버 오류가 발생했습니다.');
    } else {
        showError('네트워크 오류가 발생했습니다.');
    }
});

// 페이지 언로드 시 정리
$(window).on('beforeunload', function() {
    // 필요시 정리 작업 수행
    hideLoading();
});
