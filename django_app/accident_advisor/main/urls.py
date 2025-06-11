"""
최적화된 메인 앱 URL 패턴
- 세션별 메모리 관리 API 추가
- 성능 분석 엔드포인트 추가
- 최적화된 AI 시스템 연동 (단일 LLM 호출)
"""

from django.urls import path
from . import views  # 최적화된 views.py 사용

app_name = 'main'

urlpatterns = [
    # 메인 페이지
    path('', views.index, name='index'),
    
    # 채팅 관련 API (최적화된 단일 LLM 호출)
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/new-chat/', views.new_chat, name='new_chat'),
    
    # 세션 관리 API (세션별 독립 메모리)
    path('api/chat-history/<str:session_id>/', views.get_chat_history_with_insights, name='chat_history'),
    path('api/session-analytics/<str:session_id>/', views.get_session_analytics, name='session_analytics'),
    path('api/clear-session-memory/<str:session_id>/', views.clear_session_memory_view, name='clear_session_memory'),
    
    # 추천 및 세션 목록 (스마트 추천 시스템)
    path('api/recommendations/<str:session_id>/', views.get_live_recommendations, name='live_recommendations'),
    path('api/chat-sessions/', views.get_chat_sessions, name='chat_sessions'),
    
    # 개발/테스트 엔드포인트
    path('api/test-precedent/', views.test_precedent_extraction, name='test_precedent'),
    path('api/test-hybrid-rag/', views.test_hybrid_rag, name='test_hybrid_rag'),
]
