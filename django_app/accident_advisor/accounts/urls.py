"""
사용자 인증 URL 설정 (팀원 A 담당)
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # 로그인/로그아웃
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 회원가입
    path('signup/', views.signup_view, name='signup'),
    
    # 프로필 (선택사항)
    path('profile/', views.profile_view, name='profile'),

    # 프로필 수정 (선택사항)
    path('profile/update/', views.profile_update_view, name='profile_update'),
    
    # 비밀번호 변경 (선택사항)
    path('password-reset/', views.password_reset_view, name='password_reset'),

    # 탈퇴 비밀번호 입력 페이지
    path('confirm_delete/', views.confirm_delete_view, name='confirm_delete'),

    # 실제 회원 탈퇴 처리 (POST만 허용)
    path('delete/', views.delete_account_view, name='delete_account'),
    
]
