"""
메인 앱 URL 설정 (리더 담당)
"""

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # 메인 채팅 페이지 (루트 URL)
    path('', views.index, name='index'),
    
    # API 엔드포인트들
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/chat-history/<str:session_id>/', views.get_chat_history_with_insights, name='chat_history'),
    path('api/new-chat/', views.new_chat, name='new_chat'),
    
    # 채팅 세션 목록 API (누락된 URL 추가)
    path('api/chat-sessions/', views.get_chat_sessions, name='chat_sessions'),
]