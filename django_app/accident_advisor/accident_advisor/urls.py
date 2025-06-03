"""
URL configuration for accident_advisor project.

메인 프로젝트의 URL 설정입니다.
각 앱의 URL을 포함시켜 연결합니다.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 관리자 페이지
    path("admin/", admin.site.urls),
    
    # 메인 페이지 (채팅) - 루트 URL
    path('', include('main.urls')),
    
    # 로그인/회원가입 페이지
    path('accounts/', include('accounts.urls')),
    
    # 커뮤니티 페이지
    path('community/', include('community.urls')),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
