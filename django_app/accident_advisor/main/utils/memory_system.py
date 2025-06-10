"""
교통사고 챗봇 통합 메모리 시스템
각 카테고리별 전문 메모리와 사용자 개인화 기능 제공
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict, Counter

# 로거 설정
logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """✅ 대화 맥락 정보 (P0-1에서 추가)"""
    current_topic: Optional[str] = None  # 현재 주제 (accident, precedent, law, term, general)
    topic_keywords: List[str] = field(default_factory=list)  # 주제 관련 키워드
    mentioned_entities: List[str] = field(default_factory=list)  # 언급된 엔티티 (사건번호, 조문 등)
    conversation_flow: List[str] = field(default_factory=list)  # 대화 흐름 (카테고리 순서)
    followup_context: Dict[str, Any] = field(default_factory=dict)  # 연관 질문 맥락
    accident_details: Dict[str, Any] = field(default_factory=dict)  # 사고 상세 정보
    
    def update_topic(self, new_topic: str, keywords: List[str] = None):
        """주제 업데이트"""
        self.current_topic = new_topic
        if keywords:
            self.topic_keywords = list(set(self.topic_keywords + keywords))
        self.conversation_flow.append(new_topic)
        
        # 최근 10개 카테고리만 유지
        if len(self.conversation_flow) > 10:
            self.conversation_flow = self.conversation_flow[-10:]
    
    def add_entity(self, entity: str):
        """엔티티 추가"""
        if entity and entity not in self.mentioned_entities:
            self.mentioned_entities.append(entity)
            # 최근 20개만 유지
            if len(self.mentioned_entities) > 20:
                self.mentioned_entities = self.mentioned_entities[-20:]

@dataclass
class UserProfile:
    """사용자 프로필 정보"""
    user_id: Optional[str] = None
    preferred_explanation_level: str = "beginner"  # beginner, intermediate, advanced
    frequent_question_types: List[str] = field(default_factory=list)
    interaction_count: int = 0
    preferred_response_style: str = "comprehensive"  # comprehensive, concise, technical
    common_scenarios: List[str] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.now)

@dataclass
class GeneralMemory:
    """일반 대화 메모리"""
    help_topics_viewed: List[str] = field(default_factory=list)
    guide_completion_status: Dict[str, bool] = field(default_factory=dict)
    preferred_help_style: str = "comprehensive"  # comprehensive, quick, examples
    explanation_depth_preference: str = "detailed"  # brief, detailed, technical
    frequent_help_categories: List[str] = field(default_factory=list)
    repeated_questions: List[str] = field(default_factory=list)
    feedback_history: List[Dict] = field(default_factory=list)
    satisfaction_scores: List[int] = field(default_factory=list)
    learning_progress: Dict[str, float] = field(default_factory=dict)  # 카테고리별 이해도
    mastered_topics: List[str] = field(default_factory=list)
    recommended_topics: List[str] = field(default_factory=list)
    next_learning_suggestions: List[str] = field(default_factory=list)

@dataclass
class UnifiedMemory:
    """✅ 개선된 통합 대화 메모리 (P0-1에서 수정)"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    messages: List[Dict] = field(default_factory=list)
    user_profile: UserProfile = field(default_factory=UserProfile)
    general_memory: GeneralMemory = field(default_factory=GeneralMemory)
    conversation_context: ConversationContext = field(default_factory=ConversationContext)  # ✅ 추가
    total_interactions: int = 0
    category_usage_count: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

class GeneralMemoryProcessor:
    """일반 카테고리 전문 메모리 처리기"""
    
    def __init__(self):
        # 도움말 컨텐츠 정의
        self.help_content = {
            'features': {
                'content': '''**🔧 현재 이용 가능한 기능**:

**✅ 판례 검색**
• 구체적인 사건번호로 검색 (예: "대법원 92도2077")
• 사고 유형별 판례 검색 (예: "교차로 좌회전 사고 판례")

**✅ 도로교통법 조회**
• 조문번호로 검색 (예: "도로교통법 제5조")
• 키워드로 검색 (예: "신호위반 처벌 규정")

**✅ 용어 설명**
• 법률 용어 설명 (예: "과실비율이란?")
• 교통사고 용어 (예: "차로변경 정의")

**🔧 개발 중인 기능**:
• 🚗 교통사고 과실비율 분석
• 🤖 개인 맞춤형 상담
• 🎯 실시간 법률 업데이트'''
            },
            'usage_guide': {
                'content': '''**🎯 효과적인 질문 방법**:

**1. 구체적으로 질문하기**
❌ "사고 관련 법률"
✅ "교차로 좌회전 시 적용되는 도로교통법"

**2. 사건번호 정확히 입력**
❌ "대법원 사건"
✅ "대법원 92도2077 판례"

**3. 키워드 활용하기**
• 판례: "판례", "대법원", "사건번호"
• 법률: "도로교통법", "제○조", "규정"
• 용어: "정의", "의미", "설명"

**4. 단계적 질문하기**
복잡한 상황은 여러 번 나누어 질문하시면 더 정확한 답변을 받으실 수 있습니다.'''
            },
            'examples': {
                'content': '''**🔍 판례 검색 예시**:
• "대법원 92도2077 판례 내용은?"
• "교차로 좌회전 사고 관련 판례 찾아줘"
• "신호위반 사고 판례 검색"

**📚 법률 조회 예시**:
• "도로교통법 제5조 내용은?"
• "신호위반 시 처벌 규정"
• "교차로 통행 관련 법률"

**📖 용어 설명 예시**:
• "과실비율이란 무엇인가요?"
• "차로변경의 정의는?"
• "보호의무위반이 뭔가요?"'''
            },
            'contact': {
                'content': '''**🆘 도움이 필요할 때**:

**1. 시스템 오류 시**
• 잠시 후 다시 시도해보세요
• 다른 키워드로 질문해보세요
• "도움말"을 입력해보세요

**2. 찾는 정보가 없을 때**
• 더 구체적인 키워드 사용
• 다른 방식으로 질문 시도
• 관련 용어부터 검색

**⚠️ 주의사항**:
• 본 시스템은 참고용 정보만 제공합니다
• 정확한 법률 판단은 전문가와 상의하세요
• 실제 사고 시에는 반드시 전문가 상담을 받으시기 바랍니다'''
            }
        }
        
        # 질문 패턴 분석을 위한 키워드
        self.question_patterns = {
            'help_request': ['도움', '도움말', '사용법', '어떻게', '가이드', '설명', '방법', '안내'],
            'feature_inquiry': ['기능', '무엇', '뭐', '할 수 있', '가능', '지원', '제공'],
            'usage_guide': ['사용', '이용', '질문', '검색', '찾기', '방법'],
            'examples': ['예시', '예제', '샘플', '예', '사례'],
            'contact': ['문의', '연락', '도움', '오류', '문제', '신고'],
            'feedback': ['만족', '불만', '좋다', '나쁘다', '개선', '건의', '의견'],
            'greeting': ['안녕', '처음', '시작', '반가', '소개', '인사'],
            'goodbye': ['안녕', '끝', '종료', '그만', '나가기', '마침']
        }

    def process_with_memory(self, user_input: str, general_memory: GeneralMemory, user_profile: UserProfile) -> str:
        """메모리를 활용한 일반 질문 처리"""
        try:
            # 1. 질문 패턴 분석
            question_type = self._analyze_question_pattern(user_input)
            
            # 2. 사용자 프로필 업데이트
            self._update_user_profile(user_profile, question_type, user_input)
            
            # 3. 메모리 업데이트
            self._update_general_memory(general_memory, question_type, user_input)
            
            # 4. 개인화된 응답 생성
            response = self._generate_personalized_response(
                user_input, question_type, general_memory, user_profile
            )
            
            # 5. 학습 진행도 업데이트
            self._update_learning_progress(general_memory, question_type)
            
            # 6. 추천 콘텐츠 생성
            self._generate_recommendations(general_memory, user_profile)
            
            return response
            
        except Exception as e:
            logger.error(f"일반 질문 처리 중 오류: {str(e)}")
            return self._generate_fallback_response(user_input)

    def _analyze_question_pattern(self, user_input: str) -> str:
        """질문 패턴 분석"""
        user_input_lower = user_input.lower()
        
        pattern_scores = {}
        for pattern, keywords in self.question_patterns.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                pattern_scores[pattern] = score
        
        if pattern_scores:
            return max(pattern_scores.items(), key=lambda x: x[1])[0]
        
        return 'general_inquiry'

    def _update_user_profile(self, user_profile: UserProfile, question_type: str, user_input: str):
        """사용자 프로필 업데이트"""
        # 상호작용 횟수 증가
        user_profile.interaction_count += 1
        user_profile.last_active = datetime.now()
        
        # 자주 묻는 질문 유형 업데이트
        user_profile.frequent_question_types.append(question_type)
        
        # 최근 10개만 유지
        if len(user_profile.frequent_question_types) > 10:
            user_profile.frequent_question_types = user_profile.frequent_question_types[-10:]
        
        # 설명 수준 조정 (패턴 기반)
        technical_keywords = ['조문', '판례', '법령', '규정', '위반', '사건번호', '판결']
        if any(keyword in user_input.lower() for keyword in technical_keywords):
            if user_profile.preferred_explanation_level == "beginner":
                user_profile.preferred_explanation_level = "intermediate"
        
        # 간단한 질문이 많으면 간결한 스타일 선호로 조정
        simple_keywords = ['뭐', '무엇', '설명', '알려줘']
        if any(keyword in user_input.lower() for keyword in simple_keywords):
            if user_profile.preferred_response_style == "comprehensive":
                user_profile.preferred_response_style = "concise"

    def _update_general_memory(self, general_memory: GeneralMemory, question_type: str, user_input: str):
        """일반 메모리 업데이트"""
        # 도움말 주제 기록
        if question_type in ['help_request', 'feature_inquiry', 'usage_guide']:
            if question_type not in general_memory.help_topics_viewed:
                general_memory.help_topics_viewed.append(question_type)
        
        # 자주 묻는 카테고리 업데이트
        general_memory.frequent_help_categories.append(question_type)
        
        # 최근 20개만 유지
        if len(general_memory.frequent_help_categories) > 20:
            general_memory.frequent_help_categories = general_memory.frequent_help_categories[-20:]
        
        # 반복 질문 감지
        similar_questions = [q for q in general_memory.repeated_questions 
                           if self._calculate_similarity(user_input, q) > 0.7]
        if not similar_questions:
            general_memory.repeated_questions.append(user_input)
            if len(general_memory.repeated_questions) > 10:
                general_memory.repeated_questions = general_memory.repeated_questions[-10:]

    def _generate_personalized_response(self, user_input: str, question_type: str, 
                                      general_memory: GeneralMemory, user_profile: UserProfile) -> str:
        """개인화된 응답 생성"""
        
        # 기본 응답 생성
        base_response = self._get_base_response(question_type, user_input, user_profile)
        
        # 개인화 요소 추가
        personalization = self._generate_personalization_elements(general_memory, user_profile, question_type)
        
        # 최종 응답 구성
        if personalization:
            final_response = f"{base_response}\n\n{personalization}"
        else:
            final_response = base_response
        
        return final_response

    def _get_base_response(self, question_type: str, user_input: str, user_profile: UserProfile) -> str:
        """기본 응답 생성 (사용자 레벨에 맞춤)"""
        
        if question_type == 'greeting':
            return self._generate_greeting_response(user_profile)
        elif question_type == 'goodbye':
            return self._generate_goodbye_response(user_profile)
        elif question_type == 'feature_inquiry':
            return self._adapt_content_to_level(self.help_content['features']['content'], user_profile)
        elif question_type == 'usage_guide':
            return self._adapt_content_to_level(self.help_content['usage_guide']['content'], user_profile)
        elif question_type == 'examples':
            return self._adapt_content_to_level(self.help_content['examples']['content'], user_profile)
        elif question_type == 'contact':
            return self.help_content['contact']['content']
        elif question_type == 'help_request':
            # 종합 도움말
            return f"""👋 **노느 상담 챗봇 종합 도움말**

{self._adapt_content_to_level(self.help_content['features']['content'], user_profile)}

{self._adapt_content_to_level(self.help_content['usage_guide']['content'], user_profile)}"""
        else:
            # 일반적인 인사 및 안내
            return self._generate_welcome_response(user_profile)

    def _generate_greeting_response(self, user_profile: UserProfile) -> str:
        """인사 응답 생성"""
        if user_profile.interaction_count == 1:
            return """👋 **처음 방문해주셔서 환영합니다!**

🚗 **교통사고 과실비율 상담 전문 AI 챗봇 노느**입니다!

**🎯 무엇을 도와드릴까요?**
• 판례 검색 및 분석
• 도로교통법 조회
• 법률 용어 설명

**💡 사용법이 궁금하시면 "도움말"이라고 입력해주세요!**"""
        else:
            return f"""👋 **다시 찾아주셔서 감사합니다!**

지금까지 **{user_profile.interaction_count}번째** 상담입니다.

**어떤 도움이 필요하신가요?** 😊"""

    def _generate_goodbye_response(self, user_profile: UserProfile) -> str:
        """작별 인사 응답 생성"""
        return f"""👋 **상담을 마치시는군요!**

오늘 총 **{user_profile.interaction_count}번** 대화했습니다.

**📚 유용한 정보를 얻으셨기를 바랍니다!**
언제든 다시 찾아와 주세요. 

**노느와 함께해서 감사했습니다!** 🙏"""

    def _generate_welcome_response(self, user_profile: UserProfile) -> str:
        """환영 메시지 생성"""
        level_msg = {
            "beginner": "법률 초보자도 쉽게 이해할 수 있도록 도와드릴게요!",
            "intermediate": "법률에 어느 정도 익숙하시니 상세한 정보를 제공해드릴게요!",
            "advanced": "법률 전문 지식을 원하시는군요! 심화 내용까지 안내해드릴게요!"
        }
        
        return f"""👋 **노느 상담 챗봇에 오신 것을 환영합니다!**

교통사고 과실비율 상담 전문 AI 챗봇 **노느**입니다! 🚗

**🎯 무엇을 도와드릴까요?**

**✅ 가능한 상담 분야**:
• **판례 검색**: 교통사고 관련 판례 및 판결 내용
• **법률 조회**: 도로교통법 조문 및 규정 설명  
• **용어 설명**: 법률 및 교통사고 관련 용어 해설

{level_msg.get(user_profile.preferred_explanation_level, level_msg["beginner"])}

**💡 효과적인 질문 방법**:
• 구체적인 사건번호나 상황을 알려주세요
• 궁금한 법률 조문이나 용어를 명시해주세요
• "도움말"이라고 입력하시면 더 자세한 사용법을 확인할 수 있습니다

**어떤 도움이 필요하신가요?** 😊"""

    def _adapt_content_to_level(self, content: str, user_profile: UserProfile) -> str:
        """사용자 레벨에 맞춰 콘텐츠 조정"""
        if user_profile.preferred_explanation_level == "beginner":
            # 초보자용: 더 친근하고 간단하게
            adapted = content.replace("조회", "찾기").replace("검색", "찾기")
            return f"🔰 **초보자 가이드**\n\n{adapted}"
        elif user_profile.preferred_explanation_level == "advanced":
            # 고급자용: 더 전문적으로
            return f"⚡ **전문가 모드**\n\n{content}\n\n*💡 고급 기능: 복합 검색, 판례 분석, 법리 해석 등도 가능합니다.*"
        else:
            # 중급자용: 기본 콘텐츠
            return content

    def _generate_personalization_elements(self, general_memory: GeneralMemory, 
                                         user_profile: UserProfile, question_type: str) -> str:
        """개인화 요소 생성"""
        elements = []
        
        # 방문 횟수에 따른 메시지
        if user_profile.interaction_count == 1:
            elements.append("🆕 **처음 방문하신 것을 환영합니다!** 궁금한 점이 있으시면 언제든 문의해주세요.")
        elif user_profile.interaction_count < 5:
            elements.append("👋 **다시 찾아주셔서 감사합니다!** 더 궁금한 점이 있으시면 말씀해주세요.")
        elif user_profile.interaction_count >= 10:
            elements.append("⭐ **단골 사용자시네요!** 항상 이용해주셔서 감사합니다.")
        
        # 자주 묻는 질문 패턴 기반 추천
        frequent_types = Counter(user_profile.frequent_question_types)
        if frequent_types and len(frequent_types) > 2:
            most_common = frequent_types.most_common(1)[0][0]
            if most_common == 'feature_inquiry':
                elements.append("💡 **기능에 관심이 많으시네요!** 실제 기능을 사용해보시면 더 도움이 될 것 같아요.")
            elif most_common == 'examples':
                elements.append("📚 **예시를 선호하시는군요!** 구체적인 사례로 질문하시면 더 정확한 답변을 드릴 수 있어요.")
            elif most_common == 'help_request':
                elements.append("🎓 **학습 의욕이 높으시네요!** 실제 기능을 하나씩 시도해보시는 것을 추천드려요.")
        
        # 추천 질문
        recommendations = general_memory.next_learning_suggestions
        if recommendations:
            elements.append(f"🎯 **추천 기능**: {', '.join(recommendations[:2])}")
        
        # 학습 진행도
        if general_memory.mastered_topics:
            mastered_display = ', '.join(general_memory.mastered_topics[-3:])
            elements.append(f"🎓 **숙련 분야**: {mastered_display}")
        
        # 반복 질문 감지
        if len(general_memory.repeated_questions) > 3:
            elements.append("🔄 **비슷한 질문을 여러 번 하셨네요.** 다른 방식으로 질문해보시면 새로운 정보를 얻을 수 있어요!")
        
        return "\n".join(elements) if elements else ""

    def _update_learning_progress(self, general_memory: GeneralMemory, question_type: str):
        """학습 진행도 업데이트"""
        if question_type not in general_memory.learning_progress:
            general_memory.learning_progress[question_type] = 0.1
        else:
            general_memory.learning_progress[question_type] = min(1.0, 
                general_memory.learning_progress[question_type] + 0.1)
        
        # 숙련도가 0.8 이상이면 마스터한 것으로 간주
        if general_memory.learning_progress[question_type] >= 0.8:
            topic_names = {
                'help_request': '도움말 활용',
                'feature_inquiry': '기능 이해',
                'usage_guide': '사용법 숙지',
                'examples': '예시 학습',
                'contact': '문의 방법'
            }
            topic_name = topic_names.get(question_type, question_type)
            if topic_name not in general_memory.mastered_topics:
                general_memory.mastered_topics.append(topic_name)

    def _generate_recommendations(self, general_memory: GeneralMemory, user_profile: UserProfile):
        """추천 콘텐츠 생성"""
        recommendations = []
        
        # 아직 시도하지 않은 기능 추천
        viewed_topics = set(general_memory.help_topics_viewed)
        all_topics = set(self.help_content.keys())
        unviewed_topics = all_topics - viewed_topics
        
        if unviewed_topics:
            topic_descriptions = {
                'features': '기능 소개 확인하기',
                'usage_guide': '사용법 가이드 보기',
                'examples': '질문 예시 참고하기',
                'contact': '문의 방법 확인하기'
            }
            
            for topic in list(unviewed_topics)[:2]:
                if topic in topic_descriptions:
                    recommendations.append(topic_descriptions[topic])
        
        # 사용자 패턴 기반 추천
        frequent_types = Counter(user_profile.frequent_question_types)
        if frequent_types:
            most_common = frequent_types.most_common(1)[0][0]
            if most_common == 'help_request':
                recommendations.append('구체적인 판례나 법률 조회를 시도해보세요')
            elif most_common == 'feature_inquiry':
                recommendations.append('실제 기능을 사용해보세요')
            elif most_common == 'examples':
                recommendations.append('직접 질문을 시도해보세요')
        
        # 레벨에 따른 추천
        if user_profile.preferred_explanation_level == "beginner":
            recommendations.append('용어 설명부터 시작해보세요')
        elif user_profile.preferred_explanation_level == "advanced":
            recommendations.append('복합 검색 기능을 활용해보세요')
        
        general_memory.next_learning_suggestions = recommendations[:3]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """단순한 텍스트 유사도 계산"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

    def _generate_fallback_response(self, user_input: str) -> str:
        """폴백 응답 생성"""
        return f"""❌ **일시적 오류 발생**

**🔍 요청 내용**: "{user_input}"

죄송합니다. 일시적인 시스템 오류가 발생했습니다.

**💡 해결 방법**:
• 잠시 후 다시 시도해주세요
• "도움말"이라고 입력해보세요
• 구체적인 질문으로 다시 시도해주세요

**도움이 필요하시면 언제든 말씀해주세요!** 🙏"""


class UnifiedMemoryManager:
    """통합 메모리 관리자"""
    
    def __init__(self):
        self._sessions: Dict[str, UnifiedMemory] = {}
        self._session_timeout = timedelta(hours=24)  # 24시간 후 세션 만료
        
        # 카테고리별 전문 처리기 초기화
        self.general_processor = GeneralMemoryProcessor()
        
        logger.info("통합 메모리 관리자 초기화 완료")

    def get_or_create_session(self, session_id: str = None, user_id: str = None) -> UnifiedMemory:
        """세션 가져오기 또는 생성"""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            # 세션 만료 체크
            if datetime.now() - session.last_updated > self._session_timeout:
                logger.info(f"세션 만료: {session_id}")
                del self._sessions[session_id]
                return self._create_new_session(user_id)
            
            session.last_updated = datetime.now()
            return session
        else:
            return self._create_new_session(user_id)

    def _create_new_session(self, user_id: str = None) -> UnifiedMemory:
        """새 세션 생성"""
        session = UnifiedMemory()
        if user_id:
            session.user_profile.user_id = user_id
        
        self._sessions[session.session_id] = session
        logger.info(f"새 세션 생성: {session.session_id}")
        return session

    def process_general_query(self, user_input: str, session_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """일반 질문 처리 (메모리 적용)"""
        try:
            # 세션 가져오기/생성
            session = self.get_or_create_session(session_id, user_id)
            
            # 메시지 기록
            session.messages.append({
                'timestamp': datetime.now(),
                'sender': 'user',
                'content': user_input,
                'category': 'general'
            })
            
            # 통계 업데이트
            session.total_interactions += 1
            session.category_usage_count['general'] += 1
            
            # 일반 카테고리 전문 처리
            response = self.general_processor.process_with_memory(
                user_input, 
                session.general_memory, 
                session.user_profile
            )
            
            # 응답 기록
            session.messages.append({
                'timestamp': datetime.now(),
                'sender': 'bot',
                'content': response,
                'category': 'general'
            })
            
            # 메모리 업데이트 시간 갱신
            session.last_updated = datetime.now()
            
            return {
                'session_id': session.session_id,
                'category': 'general',
                'response': response,
                'memory_insights': self._generate_memory_insights(session),
                'recommendations': session.general_memory.next_learning_suggestions,
                'user_stats': self._generate_user_stats(session)
            }
            
        except Exception as e:
            logger.error(f"일반 질문 처리 중 오류: {str(e)}")
            return {
                'session_id': session_id or 'error',
                'category': 'general',
                'response': self.general_processor._generate_fallback_response(user_input),
                'memory_insights': {},
                'recommendations': [],
                'user_stats': {}
            }

    def process_any_category(self, user_input: str, category: str, session_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """모든 카테고리 처리 (메모리 적용) - 외부 AI 처리 함수와 연동용"""
        try:
            # 세션 가져오기/생성
            session = self.get_or_create_session(session_id, user_id)
            
            # 메시지 기록
            session.messages.append({
                'timestamp': datetime.now(),
                'sender': 'user',
                'content': user_input,
                'category': category
            })
            
            # 통계 업데이트
            session.total_interactions += 1
            session.category_usage_count[category] += 1
            
            # 사용자 프로필 업데이트 (모든 카테고리 공통)
            self._update_common_user_profile(session.user_profile, category, user_input)
            
            # 메모리 업데이트 시간 갱신
            session.last_updated = datetime.now()
            
            return {
                'session_id': session.session_id,
                'category': category,
                'session': session,  # 외부에서 응답 기록용
                'memory_insights': self._generate_memory_insights(session),
                'user_stats': self._generate_user_stats(session)
            }
            
        except Exception as e:
            logger.error(f"{category} 카테고리 처리 중 오류: {str(e)}")
            return {
                'session_id': session_id or 'error',
                'category': category,
                'session': None,
                'memory_insights': {},
                'user_stats': {}
            }

    def record_response(self, session_id: str, response: str, category: str):
        """외부 AI 처리 결과를 메모리에 기록"""
        try:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.messages.append({
                    'timestamp': datetime.now(),
                    'sender': 'bot',
                    'content': response,
                    'category': category
                })
                session.last_updated = datetime.now()
                logger.info(f"응답 기록 완료: {session_id}, 카테고리: {category}")
            else:
                logger.warning(f"세션 찾을 수 없음: {session_id}")
        except Exception as e:
            logger.error(f"응답 기록 중 오류: {str(e)}")

    def _update_common_user_profile(self, user_profile: UserProfile, category: str, user_input: str):
        """모든 카테고리에 공통으로 적용되는 사용자 프로필 업데이트"""
        # 상호작용 횟수 증가
        user_profile.interaction_count += 1
        user_profile.last_active = datetime.now()
        
        # 자주 묻는 질문 유형 업데이트
        user_profile.frequent_question_types.append(category)
        
        # 최근 10개만 유지
        if len(user_profile.frequent_question_types) > 10:
            user_profile.frequent_question_types = user_profile.frequent_question_types[-10:]
        
        # 카테고리별 시나리오 추가
        if category == 'accident':
            # 사고 시나리오 추출 (간단한 키워드 기반)
            accident_keywords = ['교차로', '좌회전', '직진', '후진', '주차', '신호', '차로변경']
            found_scenarios = [kw for kw in accident_keywords if kw in user_input]
            if found_scenarios:
                for scenario in found_scenarios:
                    if scenario not in user_profile.common_scenarios:
                        user_profile.common_scenarios.append(scenario)
        
        # 설명 수준 자동 조정
        technical_keywords = ['조문', '판례', '법령', '규정', '위반', '사건번호', '판결', '과실비율']
        beginner_keywords = ['뭐', '무엇', '설명', '알려줘', '간단히', '쉽게']
        
        if any(keyword in user_input.lower() for keyword in technical_keywords):
            if user_profile.preferred_explanation_level == "beginner":
                user_profile.preferred_explanation_level = "intermediate"
            elif user_profile.preferred_explanation_level == "intermediate":
                # 전문 용어를 자주 사용하면 고급으로 승급
                tech_count = sum(1 for kw in technical_keywords if kw in user_input.lower())
                if tech_count >= 2:
                    user_profile.preferred_explanation_level = "advanced"
        
        elif any(keyword in user_input.lower() for keyword in beginner_keywords):
            if user_profile.preferred_explanation_level == "advanced":
                user_profile.preferred_explanation_level = "intermediate"

    def _update_conversation_context(self, context: ConversationContext, user_input: str, category: str):
        """대화 맥락 업데이트"""
        try:
            # 이전 카테고리 기록
            context.last_category = category
            context.conversation_flow.append(category)
            
            # 최근 10개 카테고리만 유지
            if len(context.conversation_flow) > 10:
                context.conversation_flow = context.conversation_flow[-10:]
            
            # 카테고리별 맥락 정보 추출
            if category == 'accident':
                self._extract_accident_context(context, user_input)
            elif category == 'precedent':
                self._extract_precedent_context(context, user_input)
            elif category == 'law':
                self._extract_law_context(context, user_input)
            
            # 연관 질문 패턴 감지
            self._detect_followup_patterns(context, user_input)
            
        except Exception as e:
            logger.error(f"대화 맥락 업데이트 중 오류: {str(e)}")

    def _extract_accident_context(self, context: ConversationContext, user_input: str):
        """교통사고 맥락 정보 추출"""
        # 현재 주제를 사고로 설정
        context.current_topic = 'accident'
        
        # 사고 관련 키워드 추출
        accident_keywords = {
            'location': ['교차로', '횡단보도', '주차장', '고속도로', '일반도로', '골목'],
            'action': ['좌회전', '우회전', '직진', '후진', '주차', '출차', '차로변경', 'U턴'],
            'situation': ['신호등', '무신호', '적색신호', '황색신호', '녹색신호', '일시정지'],
            'vehicle_type': ['승용차', '트럭', '오토바이', '자전거', '보행자']
        }
        
        extracted_keywords = []
        for category_name, keywords in accident_keywords.items():
            found = [kw for kw in keywords if kw in user_input]
            if found:
                extracted_keywords.extend(found)
                context.accident_details[category_name] = found
        
        context.topic_keywords = list(set(context.topic_keywords + extracted_keywords))
        
        # 연관 질문을 위한 맥락 설정
        context.followup_context['accident_scenario'] = {
            'keywords': extracted_keywords,
            'details': dict(context.accident_details)
        }

    def _extract_precedent_context(self, context: ConversationContext, user_input: str):
        """판례 맥락 정보 추출"""
        import re
        
        # 사건번호 패턴 감지
        case_patterns = [
            r'\d{4}[가-힣]\d+',  # 2019다12345
            r'\d{2}[가-힣]\d+',   # 92도2077
            r'대법원\s*\d+[가-힣]\d+',  # 대법원 2019다12345
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, user_input)
            if matches:
                context.mentioned_entities.extend(matches)
                context.followup_context['case_numbers'] = matches

    def _extract_law_context(self, context: ConversationContext, user_input: str):
        """법률 맥락 정보 추출"""
        import re
        
        # 법령 조문 패턴 감지
        law_patterns = [
            r'제\s*\d+조',  # 제5조
            r'도로교통법\s*제\s*\d+조',  # 도로교통법 제5조
            r'제\s*\d+조\s*제\s*\d+항',  # 제5조 제1항
        ]
        
        for pattern in law_patterns:
            matches = re.findall(pattern, user_input)
            if matches:
                context.mentioned_entities.extend(matches)
                context.followup_context['law_articles'] = matches

    def _detect_followup_patterns(self, context: ConversationContext, user_input: str):
        """✅ 개선된 연관 질문 패턴 감지 (P1-1)"""
        # 기본 연관 질문 지시어
        followup_indicators = [
            '관련', '관련된', '이와 관련', '이것과 관련', '그것', '그거', '이거', 
            '그런', '이런', '판례', '법률', '조문', '어떤', '무엇', '뭐', 
            '그럼', '그러면', '추가로', '더', '또', '그리고', '또한',
            '비슷한', '유사한', '같은', '다른', '반대로', '오히려', '그런데'
        ]
        
        # 강한 연관성 지시어 (가중치 높음)
        strong_indicators = [
            '이 경우', '그 경우', '이런 상황', '그런 상황', '앞서', '위에서', 
            '방금', '이전', '해당', '동일한', '똑같은', '비슷한', '유사한'
        ]
        
        # 약한 연관성 (질문형)
        weak_indicators = ['그런가요', '맞나요', '어떤가요', '어떨까요']
        
        is_followup = False
        confidence = 0.0
        
        # 강한 지시어 체크 (신뢰도 높음)
        for indicator in strong_indicators:
            if indicator in user_input:
                is_followup = True
                confidence = 0.8
                logger.info(f"강한 연관 지시어 감지: '{indicator}'")
                break
        
        # 기본 지시어 체크
        if not is_followup:
            basic_count = sum(1 for indicator in followup_indicators if indicator in user_input)
            if basic_count > 0:
                is_followup = True
                confidence = min(basic_count * 0.3, 0.7)
                logger.info(f"기본 연관 지시어 {basic_count}개 감지")
        
        # 약한 지시어 추가 체크
        if not is_followup:
            weak_count = sum(1 for indicator in weak_indicators if indicator in user_input)
            if weak_count > 0 and context.current_topic:
                is_followup = True
                confidence = 0.4
                logger.info(f"약한 연관 지시어 감지 (기존 주제 있음)")
        
        # 맥락 업데이트
        if is_followup and context.current_topic:
            context.followup_context['is_followup'] = True
            context.followup_context['confidence'] = confidence
            context.followup_context['previous_topic'] = context.current_topic
            context.followup_context['keywords_from_previous'] = context.topic_keywords.copy()
            logger.info(f"연관 질문 감지 완료 - 신뢰도: {confidence:.2f}")

    def get_context_enhanced_query(self, session_id: str, user_input: str) -> str:
        """✅ 개선된 맥락 강화 질문 반환 (P1-1)"""
        try:
            if session_id not in self._sessions:
                logger.info(f"세션 없음, 원본 질문 반환: {session_id}")
                return user_input
                
            session = self._sessions[session_id]
            context = session.conversation_context
            
            # ✅ 개선된 연관 질문 감지 로직
            is_followup = self._is_enhanced_followup_question(user_input, context)
            
            if not is_followup:
                logger.info(f"연관 질문 아님, 원본 반환: '{user_input[:30]}...'")
                return user_input
            
            # ✅ 맥락별 정교한 질문 강화
            enhanced_query = self._apply_context_enhancement(user_input, context)
            
            if enhanced_query != user_input:
                logger.info(f"맥락 강화 완료: '{user_input[:30]}...' → '{enhanced_query[:50]}...'")
            
            return enhanced_query
            
        except Exception as e:
            logger.error(f"맥락 강화 중 오류: {str(e)}")
            return user_input
    
    def _is_enhanced_followup_question(self, user_input: str, context: ConversationContext) -> bool:
        """✅ 정교한 연관 질문 판별 (P1-1)"""
        # 1. 명시적 연관 지시어 체크
        strong_indicators = [
            '이 경우', '그 경우', '이런 상황', '그런 상황', '앞서', '위에서', 
            '방금', '이전', '해당', '동일한', '똑같은', '비슷한', '유사한'
        ]
        
        # 2. 강한 지시어가 있으면 확실한 연관 질문
        for indicator in strong_indicators:
            if indicator in user_input:
                return True
        
        return False
    
    def _apply_context_enhancement(self, user_input: str, context: ConversationContext) -> str:
        """✅ 맥락별 정교한 질문 강화 (P1-1)"""
        enhanced_query = user_input
        
        try:
            # 1. 교통사고 카테고리 맥락 활용
            if context.current_topic == 'accident':
                enhanced_query = self._enhance_accident_context(user_input, context)
            
            # 2. 판례 카테고리 맥락 활용
            elif context.current_topic == 'precedent':
                enhanced_query = self._enhance_precedent_context(user_input, context)
            
            # 3. 법률 카테고리 맥락 활용
            elif context.current_topic == 'law':
                enhanced_query = self._enhance_law_context(user_input, context)
            
            # 4. 용어 카테고리 맥락 활용
            elif context.current_topic == 'term':
                enhanced_query = self._enhance_term_context(user_input, context)
            
            # 5. 일반적인 엔티티 맥락 활용
            if enhanced_query == user_input and context.mentioned_entities:
                enhanced_query = self._enhance_entity_context(user_input, context)
            
            return enhanced_query
            
        except Exception as e:
            logger.error(f"맥락 강화 적용 중 오류: {str(e)}")
            return user_input
    
    def _enhance_accident_context(self, user_input: str, context: ConversationContext) -> str:
        """교통사고 맥락 기반 질문 강화"""
        accident_details = context.accident_details
        
        # 판례 요청 시 사고 정보 포함
        if '판례' in user_input and accident_details:
            keywords = []
            if 'location' in accident_details:
                keywords.append(accident_details['location'])
            if 'scenario' in accident_details:
                keywords.extend(accident_details['scenario'][:2])  # 주요 시나리오 2개
            
            if keywords:
                keyword_str = ' '.join(keywords)
                return f"{keyword_str} 관련 {user_input}"
        
        # 법률 요청 시 위반 유형 포함
        elif '법률' in user_input or '조문' in user_input:
            if 'violations' in accident_details:
                violations = accident_details['violations'][:2]  # 주요 위반 2개
                if violations:
                    violation_str = ' '.join(violations)
                    return f"{violation_str} 관련 {user_input}"
        
        return user_input
    
    def _enhance_precedent_context(self, user_input: str, context: ConversationContext) -> str:
        """판례 맥락 기반 질문 강화"""
        # 최근 언급된 판례 정보 활용
        recent_cases = [entity for entity in context.mentioned_entities[-3:] 
                       if '법원' in entity or '판례' in entity or any(char.isdigit() for char in entity)]
        
        if recent_cases and ('관련' in user_input or '유사' in user_input):
            case_info = recent_cases[-1]  # 가장 최근 판례
            return f"{case_info}와 {user_input}"
        
        return user_input
    
    def _enhance_law_context(self, user_input: str, context: ConversationContext) -> str:
        """법률 맥락 기반 질문 강화"""
        # 최근 언급된 조문 활용
        recent_laws = [entity for entity in context.mentioned_entities[-3:] 
                      if '제' in entity and '조' in entity]
        
        if recent_laws and ('다른' in user_input or '추가' in user_input):
            law_info = recent_laws[-1]  # 가장 최근 조문
            return f"{law_info} 외 {user_input}"
        
        return user_input
    
    def _enhance_term_context(self, user_input: str, context: ConversationContext) -> str:
        """용어 맥락 기반 질문 강화"""
        # 토픽 키워드 활용
        if context.topic_keywords and ('관련' in user_input or '다른' in user_input):
            keywords = context.topic_keywords[:2]  # 주요 키워드 2개
            keyword_str = ' '.join(keywords)
            return f"{keyword_str} 분야 {user_input}"
        
        return user_input
    
    def _enhance_entity_context(self, user_input: str, context: ConversationContext) -> str:
        """일반 엔티티 맥락 기반 질문 강화"""
        # 최근 2개 엔티티 활용
        recent_entities = context.mentioned_entities[-2:]
        
        if recent_entities and len(user_input.strip()) < 20:
            entity_str = ' '.join(recent_entities)
            return f"{entity_str}와 관련된 {user_input}"
        
        return user_input

    def _generate_memory_insights(self, session: UnifiedMemory) -> Dict[str, Any]:
        """✅ 개선된 메모리 기반 인사이트 생성 (맥락 정보 포함)"""
        insights = {}
        
        # 사용 패턴 분석
        category_counts = dict(session.category_usage_count)
        total_interactions = session.total_interactions
        
        if total_interactions > 0:
            insights['usage_pattern'] = {
                'total_interactions': total_interactions,
                'category_distribution': {
                    cat: round((count / total_interactions) * 100, 1) 
                    for cat, count in category_counts.items()
                },
                'most_used_category': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None,
                'category_variety': len(category_counts)
            }
        
        # ✅ 대화 맥락 정보 추가 (상세)
        context = session.conversation_context
        insights['conversation_context'] = {
            'current_topic': context.current_topic,
            'topic_keywords': context.topic_keywords,
            'mentioned_entities': context.mentioned_entities,
            'conversation_flow': context.conversation_flow,
            'followup_info': {
                'has_followup': context.followup_context.get('is_followup', False),
                'confidence': context.followup_context.get('confidence', 0.0),
                'previous_topic': context.followup_context.get('previous_topic'),
            },
            'accident_details': dict(context.accident_details) if context.accident_details else {},
            'context_richness': len(context.mentioned_entities) + len(context.topic_keywords)
        }
        
        # 학습 진행도
        if hasattr(session, 'general_memory') and session.general_memory.learning_progress:
            insights['learning_progress'] = dict(session.general_memory.learning_progress)
            insights['mastered_topics'] = session.general_memory.mastered_topics.copy()
            insights['learning_effectiveness'] = {
                'topics_mastered': len(session.general_memory.mastered_topics),
                'avg_progress': sum(session.general_memory.learning_progress.values()) / len(session.general_memory.learning_progress) if session.general_memory.learning_progress else 0
            }
        
        # 사용자 레벨 및 선호도
        insights['user_level'] = {
            'explanation_level': session.user_profile.preferred_explanation_level,
            'response_style': session.user_profile.preferred_response_style,
            'interaction_count': session.user_profile.interaction_count,
            'user_expertise': self._assess_user_expertise(session)
        }
        
        # 시간 패턴 분석
        if len(session.messages) > 1:
            recent_activity = [msg['timestamp'] for msg in session.messages[-10:]]
            insights['activity_pattern'] = {
                'session_duration': str(datetime.now() - session.created_at),
                'last_activity': str(datetime.now() - session.last_updated),
                'recent_activity_count': len(recent_activity),
                'conversation_pace': self._calculate_conversation_pace(session.messages)
            }
        
        return insights
    
    def _assess_user_expertise(self, session: UnifiedMemory) -> str:
        """사용자 전문성 수준 평가"""
        total_interactions = session.total_interactions
        category_variety = len(session.category_usage_count)
        
        if total_interactions >= 20 and category_variety >= 4:
            return 'expert'
        elif total_interactions >= 10 and category_variety >= 3:
            return 'intermediate'
        elif total_interactions >= 5:
            return 'beginner'
        else:
            return 'newcomer'
    
    def _calculate_conversation_pace(self, messages: List[Dict]) -> str:
        """대화 속도 계산"""
        if len(messages) < 2:
            return 'insufficient_data'
        
        time_intervals = []
        for i in range(1, len(messages)):
            interval = (messages[i]['timestamp'] - messages[i-1]['timestamp']).total_seconds()
            time_intervals.append(interval)
        
        avg_interval = sum(time_intervals) / len(time_intervals)
        
        if avg_interval < 30:
            return 'fast'
        elif avg_interval < 120:
            return 'moderate'
        else:
            return 'slow'

    def _generate_user_stats(self, session: UnifiedMemory) -> Dict[str, Any]:
        """사용자 통계 생성"""
        stats = {
            'session_info': {
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'total_interactions': session.total_interactions,
                'session_age': str(datetime.now() - session.created_at)
            },
            'category_usage': dict(session.category_usage_count),
            'user_profile': {
                'level': session.user_profile.preferred_explanation_level,
                'style': session.user_profile.preferred_response_style,
                'interaction_count': session.user_profile.interaction_count,
                'common_scenarios': session.user_profile.common_scenarios.copy()
            }
        }
        
        # 최근 메시지 수
        recent_messages = [msg for msg in session.messages 
                          if datetime.now() - msg['timestamp'] < timedelta(hours=1)]
        stats['recent_activity'] = {
            'messages_last_hour': len(recent_messages),
            'categories_used_recently': list(set(msg['category'] for msg in recent_messages))
        }
        
        return stats

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 요약 정보 반환"""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        return {
            'session_id': session_id,
            'created_at': session.created_at.isoformat(),
            'last_updated': session.last_updated.isoformat(),
            'total_interactions': session.total_interactions,
            'category_usage': dict(session.category_usage_count),
            'user_level': session.user_profile.preferred_explanation_level,
            'message_count': len(session.messages),
            'memory_insights': self._generate_memory_insights(session),
            'recommendations': getattr(session.general_memory, 'next_learning_suggestions', [])
        }

    def get_all_sessions_summary(self) -> List[Dict[str, Any]]:
        """모든 세션의 요약 정보 반환"""
        summaries = []
        for session_id in self._sessions:
            summary = self.get_session_summary(session_id)
            if summary:
                summaries.append(summary)
        
        return sorted(summaries, key=lambda x: x['last_updated'], reverse=True)

    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if current_time - session.last_updated > self._session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
            logger.info(f"만료된 세션 삭제: {session_id}")
        
        return len(expired_sessions)

    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 내보내기 (JSON 직렬화 가능한 형태)"""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        try:
            # dataclass를 dict로 변환
            session_dict = asdict(session)
            
            # datetime 객체들을 문자열로 변환
            def convert_datetimes(obj):
                if isinstance(obj, dict):
                    return {k: convert_datetimes(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetimes(item) for item in obj]
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj
            
            return convert_datetimes(session_dict)
            
        except Exception as e:
            logger.error(f"세션 데이터 내보내기 오류: {str(e)}")
            return None

    def import_session_data(self, session_data: Dict[str, Any]) -> bool:
        """세션 데이터 가져오기"""
        try:
            # datetime 문자열을 datetime 객체로 변환
            def convert_to_datetime(obj):
                if isinstance(obj, dict):
                    return {k: convert_to_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_datetime(item) for item in obj]
                elif isinstance(obj, str):
                    # ISO format datetime 문자열 감지 및 변환
                    try:
                        if 'T' in obj and (':' in obj or '+' in obj):
                            return datetime.fromisoformat(obj.replace('Z', '+00:00'))
                    except:
                        pass
                    return obj
                else:
                    return obj
            
            converted_data = convert_to_datetime(session_data)
            
            # UnifiedMemory 객체 재구성
            session = UnifiedMemory(
                session_id=converted_data['session_id'],
                created_at=converted_data['created_at'],
                last_updated=converted_data['last_updated'],
                messages=converted_data['messages'],
                user_profile=UserProfile(**converted_data['user_profile']),
                general_memory=GeneralMemory(**converted_data['general_memory']),
                total_interactions=converted_data['total_interactions'],
                category_usage_count=defaultdict(int, converted_data['category_usage_count'])
            )
            
            self._sessions[session.session_id] = session
            logger.info(f"세션 데이터 가져오기 완료: {session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"세션 데이터 가져오기 오류: {str(e)}")
            return False


# 전역 메모리 매니저 인스턴스
_memory_manager = None

def get_memory_manager() -> UnifiedMemoryManager:
    """메모리 매니저 싱글톤 인스턴스 반환"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = UnifiedMemoryManager()
    return _memory_manager


# Django views.py에서 사용할 편의 함수들
def process_with_memory(user_input: str, category: str, session_id: str = None, user_id: str = None) -> Dict[str, Any]:
    """메모리를 활용한 질문 처리 (Django views.py 연동용)"""
    memory_manager = get_memory_manager()
    
    if category == 'general':
        return memory_manager.process_general_query(user_input, session_id, user_id)
    else:
        # 다른 카테고리는 기본 메모리 업데이트만 수행하고 외부 AI 처리 대기
        return memory_manager.process_any_category(user_input, category, session_id, user_id)

def get_context_enhanced_query(session_id: str, user_input: str) -> str:
    """맥락이 강화된 질문 반환 (Django views.py 연동용)"""
    memory_manager = get_memory_manager()
    return memory_manager.get_context_enhanced_query(session_id, user_input)

def record_ai_response(session_id: str, response: str, category: str):
    """AI 응답을 메모리에 기록 (Django views.py 연동용)"""
    memory_manager = get_memory_manager()
    memory_manager.record_response(session_id, response, category)

def get_session_insights(session_id: str) -> Optional[Dict[str, Any]]:
    """세션 인사이트 조회 (Django views.py 연동용)"""
    memory_manager = get_memory_manager()
    return memory_manager.get_session_summary(session_id)

def cleanup_old_sessions() -> int:
    """오래된 세션 정리 (Django 관리 명령어용)"""
    memory_manager = get_memory_manager()
    return memory_manager.cleanup_expired_sessions()


# 사용 예시 (Django views.py에서 활용)
"""
사용 방법:

1. 일반 질문 처리:
result = process_with_memory("도움말", "general", session_id="abc123")
response = result['response']

2. 다른 카테고리 질문 처리:
memory_info = process_with_memory("교차로 사고", "accident", session_id="abc123")
session = memory_info['session']
# 외부 AI 처리 후
ai_response = your_ai_function(user_input)
record_ai_response(memory_info['session_id'], ai_response, "accident")

3. 세션 정보 조회:
insights = get_session_insights("abc123")
"""