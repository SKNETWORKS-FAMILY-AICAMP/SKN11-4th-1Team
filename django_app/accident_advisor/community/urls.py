"""
커뮤니티 URL 설정 (팀원 B, C, D 공용)
"""

from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # 게시글 목록 (팀원 B)
    path('', views.post_list, name='list'),
    
    # 게시글 상세 (팀원 C)
    path('<int:post_id>/', views.post_detail, name='detail'),
    
    # 게시글 작성 (팀원 D)
    path('write/', views.post_create, name='create'),
    
    # 좋아요 기능 (팀원 C가 AJAX로 사용)
    path('<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    
    # 게시글 수정/삭제 (선택사항)
    path('<int:post_id>/edit/', views.post_edit, name='edit'),
    path('<int:post_id>/delete/', views.post_delete, name='delete'),
]
