"""
메인 채팅 페이지 뷰 (리더 담당)

이 파일은 메인 채팅 인터페이스와 AI 연동을 담당합니다.
메모리 시스템을 활용하여 대화 맥락을 기억하고 개인화된 응답을 제공합니다.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from core.models import User, ChatSession, ChatMessage
from .services.ai_classifier import process_user_query, process_user_query_with_memory
from .utils.memory_system import process_with_memory, record_ai_response, get_session_insights, get_context_enhanced_query
import json
import uuid
import logging

# 로거 설정
logger = logging.getLogger(__name__)


def index(request):
    """
    메인 채팅 페이지
    - 채팅 인터페이스
    - 사이드바에 채팅 히스토리 표시
    """
    # 로그인한 사용자의 최근 채팅 세션들 가져오기
    recent_sessions = []
    if request.user.is_authenticated:
        recent_sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at')[:10]
    
    context = {
        'recent_sessions': recent_sessions,
        'user': request.user,
    }
    
    return render(request, 'main/index.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    메시지 전송 API (메모리 시스템 통합)
    - 사용자 메시지 저장
    - 대화 맥락을 기억하는 AI 응답 생성
    - 개인화된 응답 반환
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', None)
        
        if not user_message:
            return JsonResponse({'error': '메시지를 입력해주세요.'}, status=400)
        
        # 세션 가져오기 또는 생성
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                session = create_new_session(request.user, user_message)
        else:
            session = create_new_session(request.user, user_message)
        
        # 사용자 메시지 저장
        user_msg = ChatMessage.objects.create(
            session=session,
            sender='user',
            content=user_message
        )
        
        # 사용자 ID 추출 (익명 사용자도 세션으로 추적)
        user_id = str(request.user.id) if request.user.is_authenticated else None
        
        # 메모리 시스템을 활용한 AI 응답 생성
        bot_response, memory_insights = generate_bot_response_with_unified_memory(
            user_message, 
            str(session.session_id), 
            user_id
        )
        
        # 봇 응답 저장
        bot_msg = ChatMessage.objects.create(
            session=session,
            sender='bot',
            content=bot_response
        )
        
        # 세션 메시지 수 업데이트
        session.message_count = session.messages.count()
        session.save()
        
        # 응답 데이터 (메모리 인사이트 포함)
        response_data = {
            'success': True,
            'session_id': str(session.session_id),
            'user_message': user_message,
            'bot_response': bot_response,
            'session_title': session.title,
            'memory_insights': memory_insights,  # 메모리 기반 인사이트
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"메시지 처리 중 오류: {str(e)}")
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


def create_new_session(user, first_message):
    """새로운 채팅 세션 생성"""
    # 첫 메시지로 제목 생성 (최대 50자)
    title = first_message[:50] + ('...' if len(first_message) > 50 else '')
    
    session = ChatSession.objects.create(
        user=user if user.is_authenticated else None,
        session_id=str(uuid.uuid4()),
        title=title,
    )
    
    return session


def generate_bot_response_with_unified_memory(user_message, session_id, user_id=None):
    """
    ✅ 개선된 통합 메모리 시스템 활용 AI 봇 응답 생성 (P0-2)
    
    메모리 이중 호출 문제 해결 및 맥락 인식 강화
    """
    try:
        # ✅ 단일 메모리 호출로 통합 처리
        result = process_user_query_with_memory(user_message, session_id, user_id)
        
        ai_response = result['response']
        memory_insights = result.get('memory_insights', {})
        category = result.get('category', 'general')
        
        # ✅ 맥락 인식 정보 추가 (메모리에서 자동 처리)
        context_info = memory_insights.get('conversation_context', {})
        if context_info.get('followup_info', {}).get('has_followup'):
            confidence = context_info['followup_info'].get('confidence', 0.0)
            if confidence > 0.5:
                context_note = f"\n\n💡 **맥락 인식**: 이전 대화와 연관된 질문으로 이해하고 답변드렸습니다. (신뢰도: {confidence:.1f})"
                ai_response = ai_response + context_note
        
        logger.info(f"통합 메모리 처리 완료: '{user_message[:50]}...' → {category}")
        
        return ai_response, memory_insights
            
    except Exception as e:
        logger.error(f"통합 메모리 응답 생성 중 오류: {str(e)}")
        fallback_response = generate_fallback_response(user_message)
        return fallback_response, {}


def generate_fallback_response(user_message):
    """폴백 응답 (AI 시스템 오류 시)"""
    return """❌ **일시적 오류 발생**

죄송합니다. 일시적으로 AI 분류 시스템에 문제가 발생했습니다.
잠시 후 다시 시도해주시거나, 구체적인 교통사고 상황을 자세히 설명해주시면 도움을 드리겠습니다.

**문의 예시**:
- "교차로에서 좌회전 중 사고가 났어요"
- "주차장에서 접촉사고가 발생했어요"
- "대법원 판례를 검색해주세요"
- "도로교통법 조문을 알려주세요"

**다시 시도해주시면 정상적인 AI 응답을 받으실 수 있습니다.**"""


@require_http_methods(["GET"])
def get_chat_history_with_insights(request, session_id):
    """✅ 개선된 채팅 기록 조회 (상세 메모리 인사이트 포함)"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        
        # 권한 확인
        if session.user and session.user != request.user:
            return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        messages = session.messages.all().order_by('created_at')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # ✅ 상세 메모리 인사이트 조회
        memory_insights = get_session_insights(session_id) or {}
        
        # ✅ 사용자 맞춤 추천 생성
        recommendations = []
        context_info = memory_insights.get('conversation_context', {})
        usage_pattern = memory_insights.get('usage_pattern', {})
        
        # 미사용 카테고리 추천
        if usage_pattern:
            used_categories = set(usage_pattern.get('category_distribution', {}).keys())
            all_categories = {'accident', 'precedent', 'law', 'term', 'general'}
            unused_categories = all_categories - used_categories
            
            category_suggestions = {
                'accident': '교통사고 상황을 입력해서 과실비율을 분석해보세요',
                'precedent': '구체적인 사건번호로 판례를 검색해보세요',
                'law': '도로교통법 조문을 조회해보세요',
                'term': '궁금한 법률 용어를 질문해보세요'
            }
            
            for category in list(unused_categories)[:2]:  # 최대 2개
                if category in category_suggestions:
                    recommendations.append(category_suggestions[category])
        
        # 맥락 기반 추천
        current_topic = context_info.get('current_topic')
        if current_topic == 'accident' and context_info.get('accident_details'):
            recommendations.append('관련 판례나 법률 조문도 함께 확인해보세요')
        elif current_topic == 'precedent':
            recommendations.append('유사한 사고 상황으로 과실비율도 분석해보세요')
        
        return JsonResponse({
            'success': True,
            'session_title': session.title,
            'messages': messages_data,
            'memory_insights': memory_insights,
            'recommendations': recommendations[:3],  # 최대 3개
            'session_stats': {
                'total_messages': len(messages_data),
                'session_duration': str(memory_insights.get('activity_pattern', {}).get('session_duration', '0')),
                'user_expertise': memory_insights.get('user_level', {}).get('user_expertise', 'newcomer')
            }
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        logger.error(f"채팅 기록 조회 중 오류: {str(e)}")
        return JsonResponse({'error': '채팅 기록을 불러오는 중 오류가 발생했습니다.'}, status=500)


@require_http_methods(["GET"])  
def get_session_analytics(request, session_id):
    """✅ 새로운 세션 분석 정보 조회"""
    try:
        # 메모리 시스템에서 상세 분석 정보 조회
        analytics = get_user_session_insights(session_id)
        
        if not analytics:
            return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
        
        # 분석 정보 구성
        response_data = {
            'session_id': session_id,
            'basic_info': {
                'total_interactions': analytics.get('total_interactions', 0),
                'session_age': analytics.get('session_age', '0'),
                'last_activity': analytics.get('last_activity', 'Unknown')
            },
            'usage_patterns': analytics.get('usage_pattern', {}),
            'conversation_context': analytics.get('conversation_context', {}),
            'learning_progress': analytics.get('learning_progress', {}),
            'user_level': analytics.get('user_level', {}),
            'recommendations': analytics.get('recommendations', [])
        }
        
        return JsonResponse({
            'success': True,
            'analytics': response_data
        })
        
    except Exception as e:
        logger.error(f"세션 분석 조회 중 오류: {str(e)}")
        return JsonResponse({'error': '분석 정보를 불러오는 중 오류가 발생했습니다.'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def new_chat(request):
    """새 채팅 시작"""
    try:
        # 새 세션 ID 생성
        new_session_id = str(uuid.uuid4())
        
        return JsonResponse({
            'success': True,
            'session_id': new_session_id,
            'message': '새로운 상담을 시작합니다!'
        })
    
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"])  
def get_session_statistics(request, session_id):
    """세션 통계 및 메모리 인사이트 조회 (디버깅용)"""
    try:
        memory_insights = get_session_insights(session_id)
        
        if not memory_insights:
            return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'insights': memory_insights
        })
    
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def get_chat_sessions(request):
    """사용자의 채팅 세션 목록 가져오기 (사이드바용)"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'sessions': []})
        
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at')[:10]
        
        sessions_data = []
        for session in sessions:
            # 마지막 메시지 가져오기
            last_message = session.messages.order_by('-created_at').first()
            
            sessions_data.append({
                'session_id': str(session.session_id),
                'title': session.title,
                'message_count': session.message_count,
                'last_message': last_message.content[:50] + '...' if last_message and len(last_message.content) > 50 else (last_message.content if last_message else ''),
                'updated_at': session.updated_at.strftime('%m/%d %H:%M'),
                'created_at': session.created_at.strftime('%Y-%m-%d')
            })
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_data
        })
    
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)
