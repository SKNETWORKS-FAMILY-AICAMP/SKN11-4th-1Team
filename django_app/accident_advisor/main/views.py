"""
메인 채팅 페이지 뷰 (리더 담당)

이 파일은 메인 채팅 인터페이스와 AI 연동을 담당합니다.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from core.models import User, ChatSession, ChatMessage, AccidentCase
from .services.ai_classifier import process_user_query
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
    메시지 전송 API
    - 사용자 메시지 저장
    - AI 응답 생성 (파인튜닝된 분류기 사용)
    - 응답 반환
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
        
        # AI 응답 생성 (현재는 임시 응답)
        bot_response = generate_bot_response(user_message)
        
        # 봇 응답 저장
        bot_msg = ChatMessage.objects.create(
            session=session,
            sender='bot',
            content=bot_response
        )
        
        # 세션 메시지 수 업데이트
        session.message_count = session.messages.count()
        session.save()
        
        # 응답 데이터
        response_data = {
            'success': True,
            'session_id': str(session.session_id),
            'user_message': user_message,
            'bot_response': bot_response,
            'session_title': session.title,
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
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


def generate_bot_response(user_message):
    """
    AI 봇 응답 생성 (RAG 시스템 사용)
    
    1. 파인튜닝된 GPT-3.5-turbo로 질문 분류
    2. 카테고리별 RAG 처리 (판례 검색 구현 완료)
    """
    try:
        # 통합 처리 함수 사용 (분류 + RAG 처리)
        category, response = process_user_query(user_message)
        logger.info(f"질문 처리 완료: '{user_message[:50]}...' → {category}")
        
        return response
            
    except Exception as e:
        logger.error(f"응답 생성 중 오류: {str(e)}")
        return generate_fallback_response(user_message)


def generate_accident_response(user_message):
    """사고 분석 응답 생성 (임시)"""
    user_message_lower = user_message.lower()
    
    if any(word in user_message_lower for word in ['교차로', '좌회전', '직진']):
        return """교차로에서의 좌회전 사고의 경우, 일반적으로 좌회전 차량(A)의 과실비율이 70%, 직진 차량(B)의 과실비율이 30%입니다.

**법적 근거**: 도로교통법 제25조 (교차로 통행방법)

**조정 요소**:
- 신호위반 시: 추가 과실 +20%
- 속도위반 시: 추가 과실 +10%
- 안전운전 의무 위반 시: 과실 조정 가능

더 정확한 분석을 위해서는 구체적인 사고 상황을 알려주시기 바랍니다."""
    
    elif any(word in user_message_lower for word in ['주차장', '주차', '접촉']):
        return """주차장 내 접촉사고의 경우, 일반적으로 움직이는 차량의 과실비율이 더 높습니다.

**기본 과실비율**:
- 후진 차량 vs 정지 차량: 후진 차량 100%
- 서로 움직이는 경우: 50% : 50%

**법적 근거**: 도로교통법 제27조 (후진의 금지)

구체적인 상황을 알려주시면 더 정확한 과실비율을 안내해드리겠습니다."""
    
    elif any(word in user_message_lower for word in ['신호위반', '신호', '적색']):
        return """신호위반 사고의 경우 위반 차량의 과실비율이 매우 높습니다.

**기본 과실비율**:
- 신호위반 차량: 90-100%
- 정상 신호 차량: 0-10%

**법적 근거**: 도로교통법 제5조 (신호 등에 따른 통행)

신호위반은 중대한 교통법규 위반으로 과실비율이 크게 증가합니다."""
    
    else:
        return """안녕하세요! 교통사고 과실비율 상담 챗봇 '노느'입니다.

구체적인 사고 상황을 알려주시면 관련 법률과 판례를 바탕으로 과실비율을 분석해드리겠습니다.

**예시 질문**:
- "교차로에서 좌회전하다가 직진차와 충돌했어요"
- "주차장에서 후진하다가 다른 차와 접촉했어요"
- "신호위반 차량과 사고가 났어요"

어떤 상황인지 자세히 설명해주세요!"""


def generate_precedent_response(user_message):
    """판례 검색 응답 생성 (임시)"""
    return """⚖️ **판례 검색 결과**

**분류**: 판례 검색 (파인튜닝 모델 분류 ✅)

현재 판례 검색 기능을 준비 중입니다. 
구체적인 사건번호나 판례 내용을 알려주시면 관련 정보를 찾아드리겠습니다.

**예시 질문**:
- "대법원 2019다12345 판례 내용은?"
- "교차로 사고 관련 판례를 알려주세요"""

def generate_law_response(user_message):
    """법률 조회 응답 생성 (임시)"""
    return """📚 **도로교통법 조회 결과**

**분류**: 법률 조회 (파인튜닝 모델 분류 ✅)

현재 도로교통법 조회 기능을 준비 중입니다.
구체적인 조문 번호나 법률 내용을 알려주시면 관련 정보를 찾아드리겠습니다.

**예시 질문**:
- "도로교통법 제25조 내용은?"
- "신호위반 관련 법률을 알려주세요"""

def generate_term_response(user_message):
    """용어 설명 응답 생성 (임시)"""
    return """📖 **용어 설명 결과**

**분류**: 용어 설명 (파인튜닝 모델 분류 ✅)

현재 용어 설명 기능을 준비 중입니다.
구체적인 용어를 알려주시면 정확한 정의를 설명해드리겠습니다.

**예시 질문**:
- "과실비율이 무엇인가요?"
- "차로변경의 정의는?"""

def generate_general_response(user_message):
    """일반 질문 응답 생성 (임시)"""
    return """👋 **일반 상담**

**분류**: 일반 질문 (파인튜닝 모델 분류 ✅)

안녕하세요! 교통사고 과실비율 상담 챗봇 '노느'입니다.

다음과 같은 도움을 드릴 수 있습니다:
- 🚗 교통사고 과실비율 분석
- ⚖️ 관련 판례 검색
- 📚 도로교통법 조회
- 📖 교통 용어 설명

어떤 도움이 필요하신지 알려주세요!"""

def generate_fallback_response(user_message):
    """폴백 응답 (오류 시)"""
    return """❌ **일시적 오류 발생**

죄송합니다. 일시적으로 AI 분류 시스템에 문제가 발생했습니다.
잠시 후 다시 시도해주시거나, 구체적인 교통사고 상황을 자세히 설명해주시면 도움을 드리겠습니다.

**문의 예시**:
- "교차로에서 좌회전 중 사고가 났어요"
- "주차장에서 접촉사고가 발생했어요"""
    



@require_http_methods(["GET"])
def get_chat_history(request, session_id):
    """특정 세션의 채팅 기록 가져오기"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        
        # 권한 확인 (로그인한 사용자만 자신의 세션 조회 가능)
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
        
        return JsonResponse({
            'success': True,
            'session_title': session.title,
            'messages': messages_data
        })
    
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': '세션을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


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
