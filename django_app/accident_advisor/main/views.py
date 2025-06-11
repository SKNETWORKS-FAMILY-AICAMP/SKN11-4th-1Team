"""
최적화된 메인 채팅 페이지 뷰
- 세션별 영속적 메모리
- 최소한의 API 호출 (3번 → 1번)
- 빠른 응답 시간
"""

import json
import uuid
import logging
from typing import Dict, Any

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
# main/views.py 상단에 추가
from typing import List, Dict, Optional, Tuple, Any
from core.models import ChatSession, ChatMessage
from .services.optimized_ai_bot import (
    process_optimized_query, 
    clear_session_memory, 
    cleanup_old_sessions,
    get_optimized_bot
)

# 로거 설정
logger = logging.getLogger(__name__)


def index(request):
    """메인 채팅 페이지"""
    recent_sessions = []
    if request.user.is_authenticated:
        recent_sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at')[:10]
    
    # 정기적으로 오래된 세션 정리 (페이지 로드 시)
    try:
        cleanup_old_sessions()
    except:
        pass
    
    context = {
        'recent_sessions': recent_sessions,
        'user': request.user,
    }
    
    return render(request, 'main/index.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """최적화된 메시지 전송 API (단일 LLM 호출)"""
    import socket
    # 소켓 타임아웃 증가 (60초)
    socket.setdefaulttimeout(60)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', None)
        
        if not user_message:
            return JsonResponse({'error': '메시지를 입력해주세요.'}, status=400)
        
        # 세션 가져오기 또는 생성
        session = _get_or_create_session(request.user, session_id, user_message)
        session_id_str = str(session.session_id)
        
        # 사용자 메시지 저장
        ChatMessage.objects.create(
            session=session,
            sender='user',
            content=user_message
        )
        
        # 🚀 최적화된 AI 응답 생성 (단일 API 호출)
        result = process_optimized_query(user_message, session_id_str)
        
        bot_response = result['response']
        ai_metadata = {
            'category': result['category'],
            'processing_time': result['processing_time'],
            'context_used': result.get('context_used', False),
            'session_stats': result.get('session_stats', {})
        }
        
        # 봇 응답 저장
        ChatMessage.objects.create(
            session=session,
            sender='bot',
            content=bot_response
        )
        
        # 세션 업데이트
        session.message_count = session.messages.count()
        session.save()
        
        # AI 처리 정보를 로그에만 기록
        performance_note = _generate_performance_note(ai_metadata)
        logger.info(f"AI 처리 완료 - 세션: {session_id_str} | {performance_note.replace(chr(10), ' ')}")
        
        return JsonResponse({
            'success': True,
            'session_id': session_id_str,
            'user_message': user_message,
            'bot_response': bot_response,
            'session_title': session.title,
            'ai_metadata': ai_metadata,
            'memory_status': '✅ 대화 맥락 유지 중'
        })
    
    except Exception as e:
        logger.error(f"메시지 처리 중 오류: {str(e)}")
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def get_chat_history_with_insights(request, session_id):
    """채팅 기록 조회 + 세션 통계"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        
        # 권한 확인
        if session.user and session.user != request.user:
            return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        messages = session.messages.all().order_by('created_at')
        messages_data = []
        
        total_processing_time = 0
        category_count = {}
        
        for msg in messages:
            message_data = {
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # AI 메타데이터 처리 (기본값 사용)
            if msg.sender == 'bot':
                # 기본 AI 메타데이터 설정
                message_data['ai_metadata'] = {
                    'category': 'general',
                    'processing_time': 2.0,
                    'context_used': False
                }
                # 기본 통계 집계
                total_processing_time += 2.0
                category_count['general'] = category_count.get('general', 0) + 1
            
            messages_data.append(message_data)
        
        # 동적 추천 생성
        recommendations = _generate_dynamic_recommendations(category_count, len(messages_data))
        
        # 세션 통계
        bot = get_optimized_bot()
        session_stats = bot.conversation_manager.get_session_stats(session_id)
        
        return JsonResponse({
            'success': True,
            'session_title': session.title,
            'messages': messages_data,
            'recommendations': recommendations,
            'session_stats': {
                'total_messages': len(messages_data),
                'total_processing_time': round(total_processing_time, 2),
                'category_usage': category_count,
                'memory_system': '✅ 최적화된 세션별 메모리',
                'conversation_chain_stats': session_stats
            }
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        logger.error(f"채팅 기록 조회 중 오류: {str(e)}")
        return JsonResponse({'error': '채팅 기록을 불러오는 중 오류가 발생했습니다.'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def new_chat(request):
    """새 채팅 시작 (이전 세션 메모리는 유지)"""
    try:
        new_session_id = str(uuid.uuid4())
        
        return JsonResponse({
            'success': True,
            'session_id': new_session_id,
            'message': '✨ 새로운 상담을 시작합니다! (이전 대화들은 각각 기억하고 있어요)',
            'memory_status': '🧠 세션별 독립 메모리 시스템'
        })
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def clear_session_memory_view(request, session_id):
    """특정 세션 메모리 초기화"""
    try:
        clear_session_memory(session_id)
        
        return JsonResponse({
            'success': True,
            'message': f'세션 {session_id}의 대화 기록이 초기화되었습니다.',
            'memory_status': '🔄 메모리 초기화 완료'
        })
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"]) 
def get_session_analytics(request, session_id):
    """세션 상세 분석 정보"""
    try:
        bot = get_optimized_bot()
        session_stats = bot.conversation_manager.get_session_stats(session_id)
        
        # DB에서 세션 정보 조회
        try:
            session = ChatSession.objects.get(session_id=session_id)
            messages = session.messages.all()
            
            # 카테고리별 분석
            category_analysis = {}
            processing_times = []
            
            for msg in messages.filter(sender='bot'):
                # 기본값으로 분석 (실제로는 로그에서 데이터 추출)
                category = 'general'
                processing_time = 2.0
                
                if category not in category_analysis:
                    category_analysis[category] = {'count': 0, 'avg_time': 0, 'total_time': 0}
                
                category_analysis[category]['count'] += 1
                category_analysis[category]['total_time'] += processing_time
                processing_times.append(processing_time)
            
            # 평균 처리 시간 계산
            for category in category_analysis:
                if category_analysis[category]['count'] > 0:
                    category_analysis[category]['avg_time'] = round(
                        category_analysis[category]['total_time'] / category_analysis[category]['count'], 2
                    )
        
        except ChatSession.DoesNotExist:
            category_analysis = {}
            processing_times = []
        
        return JsonResponse({
            'session_id': session_id,
            'conversation_chain_stats': session_stats,
            'performance_analysis': {
                'category_breakdown': category_analysis,
                'avg_processing_time': round(sum(processing_times) / len(processing_times), 2) if processing_times else 0,
                'total_optimized_calls': len(processing_times)
            },
            'memory_system_info': {
                'type': 'SessionBasedConversationManager',
                'memory_window': 8,
                'persistent': True,
                'isolation': '세션별 독립 메모리'
            }
        })

    except Exception as e:
        logger.error(f"세션 분석 조회 중 오류: {str(e)}")
        return JsonResponse({'error': '분석 정보를 불러오는 중 오류가 발생했습니다.'}, status=500)


@require_http_methods(["GET"])
def get_live_recommendations(request, session_id):
    """실시간 추천 (최적화된 버전)"""
    try:
        # 세션 기반 동적 추천
        try:
            session = ChatSession.objects.get(session_id=session_id)
            messages = session.messages.all()
            
            category_usage = {}
            for msg in messages.filter(sender='bot'):
                # 기본값으로 카테고리 집계
                category = 'general'
                category_usage[category] = category_usage.get(category, 0) + 1
            
            recommendations = _generate_dynamic_recommendations(category_usage, len(messages))
            
        except ChatSession.DoesNotExist:
            recommendations = _get_default_recommendations()
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations,
            'system': '최적화된 동적 추천 시스템'
        })
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def get_chat_sessions(request):
    """채팅 세션 목록 조회"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'sessions': []})
        
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at')[:20]
        
        sessions_data = []
        for session in sessions:
            last_message = session.messages.last()
            sessions_data.append({
                'session_id': str(session.session_id),
                'title': session.title,
                'message_count': session.message_count,
                'last_message': last_message.content[:100] if last_message else '',
                'updated_at': session.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': session.created_at.strftime('%Y-%m-%d')
            })
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_data
        })
    
    except Exception as e:
        logger.error(f"세션 목록 조회 중 오류: {str(e)}")
        return JsonResponse({'error': '세션 목록을 불러오는 중 오류가 발생했습니다.'}, status=500)


def _get_or_create_session(user, session_id, first_message):
    """세션 가져오기 또는 생성"""
    if session_id:
        try:
            return ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            pass
    
    # 새 세션 생성
    title = first_message[:50] + ('...' if len(first_message) > 50 else '')
    return ChatSession.objects.create(
        user=user if user.is_authenticated else None,
        session_id=str(uuid.uuid4()),
        title=title,
    )


def _generate_performance_note(ai_metadata: Dict[str, Any]) -> str:
    """성능 정보 노트 생성"""
    category = ai_metadata.get('category', 'unknown')
    processing_time = ai_metadata.get('processing_time', 0)
    context_used = ai_metadata.get('context_used', False)
    
    notes = []
    
    # 카테고리 정보
    category_emojis = {
        'accident': '🚗',
        'precedent': '⚖️', 
        'law': '📚',
        'term': '📖',
        'general': '💬'
    }
    
    category_emoji = category_emojis.get(category, '❓')
    notes.append(f"{category_emoji} **{category}** 분류")
    
    # 처리 시간 (빠르면 강조)
    if processing_time < 2:
        notes.append(f"⚡ 빠른 응답 ({processing_time:.1f}초)")
    else:
        notes.append(f"⏱️ 처리시간 {processing_time:.1f}초")
    
    # RAG 사용 여부
    if context_used:
        notes.append("🔍 전문자료 활용")
    
    # 메모리 상태
    notes.append("🧠 대화맥락 유지")
    
    return f"\n\n💡 **AI 처리 정보**: {' | '.join(notes)}"


def _generate_dynamic_recommendations(category_usage: Dict[str, int], total_messages: int) -> List[str]:
    """세션 사용 패턴 기반 동적 추천 생성"""
    recommendations = []
    
    # 카테고리별 추천
    all_categories = {'accident', 'precedent', 'law', 'term'}
    used_categories = set(category_usage.keys())
    unused_categories = all_categories - used_categories
    
    # 미사용 카테고리 추천
    category_suggestions = {
        'accident': '📋 실제 교통사고 상황을 입력해서 과실비율을 분석해보세요',
        'precedent': '⚖️ 구체적인 사건번호로 판례를 검색해보세요 (예: 대법원 2019다12345)',
        'law': '📚 궁금한 도로교통법 조문을 조회해보세요 (예: 제5조)',
        'term': '📖 모르는 법률 용어를 질문해보세요 (예: 과실비율이란?)'
    }
    
    for category in list(unused_categories)[:2]:
        if category in category_suggestions:
            recommendations.append(category_suggestions[category])
    
    # 사용 패턴 기반 추천
    if category_usage:
        most_used = max(category_usage, key=category_usage.get)
        
        if most_used == 'accident':
            recommendations.append('🔍 방금 분석한 사고와 관련된 판례도 검색해보세요')
        elif most_used == 'precedent':
            recommendations.append('📚 해당 판례에 적용된 법률 조문도 확인해보세요')
        elif most_used == 'law':
            recommendations.append('🚗 이 법률이 적용된 실제 사고 사례도 분석해보세요')
    
    # 메시지 수에 따른 추천
    if total_messages > 10:
        recommendations.append('🎯 복합적인 상황을 종합해서 질문해보세요')
    elif total_messages < 3:
        recommendations.append('🔰 기본적인 교통사고 용어부터 학습해보세요')
    
    return recommendations[:4]  # 최대 4개


@require_http_methods(["GET"])
def test_precedent_extraction(request):
    """판례번호 추출 및 검색 테스트 API (개발용)"""
    try:
        case_number = request.GET.get('case_number', '')
        if not case_number:
            return JsonResponse({
                'error': 'case_number 파라미터가 필요합니다.',
                'example': '/test-precedent/?case_number=대법원 2019다12345'
            }, status=400)
        
        from .services.optimized_ai_bot import test_precedent_search
        
        # 판례 검색 테스트 실행
        test_result = test_precedent_search(case_number)
        
        return JsonResponse({
            'success': True,
            'test_input': case_number,
            'extraction_result': test_result,
            'explanation': {
                'input': '사용자가 입력한 문자열',
                'extracted_case_number': '추출된 판례번호 (정규표현식 사용)',
                'exact_match_found': 'VectorDB에서 정확한 매칭 발견 여부',
                'result': '최종 결과 메시지'
            }
        })
        
    except Exception as e:
        logger.error(f"판례 검색 테스트 오류: {str(e)}")
        return JsonResponse({'error': f'테스트 실행 중 오류: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def test_hybrid_rag(request):
    """하이브리드 RAG 검색 테스트 API (개발용)"""
    try:
        query = request.GET.get('query', '')
        category = request.GET.get('category', 'accident')
        
        if not query:
            return JsonResponse({
                'error': 'query 파라미터가 필요합니다.',
                'example': '/test-hybrid-rag/?query=대법원 2019다12345&category=precedent',
                'categories': ['accident', 'precedent', 'law', 'term']
            }, status=400)
        
        from .services.optimized_ai_bot import test_hybrid_rag_search
        
        # 하이브리드 RAG 검색 테스트 실행
        test_result = test_hybrid_rag_search(query, category)
        
        return JsonResponse({
            'success': True,
            'test_input': {
                'query': query,
                'category': category
            },
            'hybrid_rag_result': test_result,
            'explanation': {
                'direct_search': '기본 VectorDB 검색 (100% 사용)',
                'self_query_search': '메타데이터 필터링 검색 (조건부 사용)',
                'hybrid_logic': '트리거 키워드 2개+ 또는 쿠리 길이 30자+ 시 Self-Query 사용',
                'result_combination': 'Self-Query 결과 우선 + Direct 결과 병합, 중복 제거'
            }
        })
        
    except Exception as e:
        logger.error(f"하이브리드 RAG 테스트 오류: {str(e)}")
        return JsonResponse({'error': f'테스트 실행 중 오류: {str(e)}'}, status=500)


def _get_default_recommendations() -> List[str]:
    """기본 추천 목록"""
    return [
        '🚗 교통사고 상황을 입력해서 과실비율을 분석해보세요',
        '⚖️ 판례 검색으로 비슷한 사례를 찾아보세요',
        '📚 도로교통법 조문을 학습해보세요',
        '📖 법률 용어의 정의를 물어보세요'
    ]
