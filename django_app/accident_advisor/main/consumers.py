"""
교통사고 챗봇 WebSocket Consumer (리더 담당)
실시간 채팅 기능 제공
"""

import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from core.models import ChatSession, ChatMessage
from .services.ai_classifier import process_user_query_with_memory

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """
    ✅ 비동기 WebSocket Consumer
    - 실시간 양방향 통신
    - 스트리밍 응답 지원  
    - 세션 기반 대화 관리
    """
    
    async def connect(self):
        """WebSocket 연결 시"""
        try:
            # URL에서 session_id 추출
            self.session_id = self.scope['url_route']['kwargs']['session_id']
            self.room_group_name = f'chat_{self.session_id}'
            
            # 그룹에 추가
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # 연결 승인
            await self.accept()
            
            # 연결 확인 메시지 전송
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': f'세션 {self.session_id}에 연결되었습니다.',
                'session_id': self.session_id
            }))
            
            logger.info(f"WebSocket 연결 성공: {self.session_id}")
            
        except Exception as e:
            logger.error(f"WebSocket 연결 실패: {e}")
            await self.close()

    async def disconnect(self, close_code):
        """WebSocket 연결 해제 시"""
        try:
            # 그룹에서 제거
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket 연결 해제: {self.session_id}")
        except Exception as e:
            logger.error(f"WebSocket 연결 해제 오류: {e}")

    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            # JSON 파싱
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'ping':
                await self.handle_ping()
            else:
                logger.warning(f"알 수 없는 메시지 타입: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            await self.send_error("잘못된 메시지 형식입니다.")
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            await self.send_error("메시지 처리 중 오류가 발생했습니다.")

    async def handle_chat_message(self, data):
        """채팅 메시지 처리"""
        try:
            user_message = data.get('message', '').strip()
            if not user_message:
                await self.send_error("빈 메시지는 전송할 수 없습니다.")
                return
            
            # 즉시 사용자 메시지 에코 (확인용)
            await self.send(text_data=json.dumps({
                'type': 'user_message_received',
                'message': user_message,
                'timestamp': str(asyncio.get_event_loop().time())
            }))
            
            # 처리 시작 알림
            await self.send(text_data=json.dumps({
                'type': 'processing_started',
                'message': '🤖 AI가 답변을 준비하고 있습니다...',
                'show_loading': True
            }))
            
            # 비동기 AI 처리 시작
            asyncio.create_task(self.process_ai_response(user_message))
            
        except Exception as e:
            logger.error(f"채팅 메시지 처리 오류: {e}")
            await self.send_error("채팅 메시지 처리 중 오류가 발생했습니다.")

    async def process_ai_response(self, user_message):
        """AI 응답 비동기 처리"""
        try:
            # 1. 사용자 메시지 저장
            user_msg = await self.save_user_message(user_message)
            
            # 2. AI 처리 (동기 함수를 비동기로 실행)
            ai_result = await self.run_ai_processing(user_message)
            
            # 3. AI 응답 저장
            bot_msg = await self.save_bot_message(
                ai_result['response'], 
                ai_result.get('category', 'general')
            )
            
            # 4. 최종 응답 전송
            await self.send(text_data=json.dumps({
                'type': 'bot_response_complete',
                'message': ai_result['response'],
                'category': ai_result.get('category', 'general'),
                'memory_insights': ai_result.get('memory_insights', {}),
                'show_loading': False,
                'timestamp': str(asyncio.get_event_loop().time())
            }))
            
            logger.info(f"AI 응답 완료: {self.session_id}")
            
        except Exception as e:
            logger.error(f"AI 처리 오류: {e}")
            await self.send_error("AI 응답 생성 중 오류가 발생했습니다.")

    @database_sync_to_async
    def run_ai_processing(self, user_message):
        """AI 처리 함수 (동기→비동기 변환)"""
        try:
            # 기존 ai_classifier 함수 호출
            result = process_user_query_with_memory(
                user_message,
                session_id=self.session_id,
                user_id=None
            )
            return result
        except Exception as e:
            logger.error(f"AI 처리 함수 오류: {e}")
            raise

    @database_sync_to_async
    def save_user_message(self, message):
        """사용자 메시지 DB 저장"""
        try:
            session, created = ChatSession.objects.get_or_create(
                session_id=self.session_id
            )
            
            user_msg = ChatMessage.objects.create(
                session=session,
                content=message,
                sender='user'
            )
            return user_msg
        except Exception as e:
            logger.error(f"사용자 메시지 저장 오류: {e}")
            raise

    @database_sync_to_async
    def save_bot_message(self, message, category='general'):
        """봇 메시지 DB 저장"""
        try:
            session = ChatSession.objects.get(session_id=self.session_id)
            
            bot_msg = ChatMessage.objects.create(
                session=session,
                content=message,
                sender='bot'
            )
            return bot_msg
        except Exception as e:
            logger.error(f"봇 메시지 저장 오류: {e}")
            raise

    async def handle_ping(self):
        """연결 상태 확인"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': str(asyncio.get_event_loop().time())
        }))

    async def send_error(self, error_message):
        """오류 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'show_loading': False
        }))

    # 그룹 메시지 핸들러들
    async def chat_message(self, event):
        """그룹에서 전송된 채팅 메시지 처리"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        })) 