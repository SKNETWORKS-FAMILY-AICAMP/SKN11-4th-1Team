"""
최적화된 교통사고 상담 AI 시스템
- 세션별 영속적 메모리 관리 
- 최소한의 모델 호출 (3번 → 1번)
- 통합 RAG + 대화 체인
- 95% 키워드 기반 빠른 분류
"""

import openai
import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
import time

# 로거 설정
logger = logging.getLogger(__name__)

class FastClassifier:
    """빠른 질문 분류기 - 95% 키워드 기반, 5% API 호출"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model_id = os.getenv('FINETUNED_MODEL_ID')
        
        # 키워드 기반 빠른 분류 패턴 (가중치 적용)
        self.keyword_patterns = {
            'accident': {
                'high': ['사고', '충돌', '접촉', '과실비율', '과실', '비율'],
                'medium': ['교차로', '신호', '좌회전', '우회전', '직진', '후진', '주차'],
                'low': ['차량', '자동차', '운전', '도로', 'A차량', 'B차량']
            },
            'precedent': {
                'high': ['판례', '대법원', '고등법원', '지방법원', '사건번호'],
                'medium': ['법원', '재판', '소송', '결정', '고법', '지방법원', '고등법원', '관련된', '관련', '찾아', '검색'],
                'low': ['사건', '결과', '20', '19', '수원', '서울', '부산', '이와', '해당']
            },
            'law': {
                'high': ['도로교통법', '법률', '조문', '법령'],
                'medium': ['제', '조', '항', '규정', '위반'],
                'low': ['법', '규칙', '처벌']
            },
            'term': {
                'high': ['정의', '의미', '뜻', '설명', '무엇'],
                'medium': ['용어', '개념', '말'],
                'low': ['이란', '라는']
            }
        }
        
        logger.info("FastClassifier 초기화 완료 - 키워드 기반 분류기")
    
    def classify(self, user_input: str) -> str:
        """
        1차: 키워드 기반 빠른 분류 (95% 케이스, API 호출 없음)
        2차: 모호한 경우만 파인튜닝 모델 사용 (5% 케이스)
        """
        start_time = time.time()
        
        # 1차: 가중치 기반 키워드 분류
        category_scores = self._calculate_keyword_scores(user_input.lower())
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[best_category]
            total_scores = sum(category_scores.values())
            confidence = max_score / total_scores if total_scores > 0 else 0
            
            # 📊 신뢰도 기반 스마트 분류 로직 (사고 관련 감지 강화)
            confidence_threshold = 0.65  # 신뢰도 임계값
            min_score_threshold = 4       # 최소 점수 임계값
            
            # 고신뢰도 분류 (단일 카테고리 확실)
            if confidence >= confidence_threshold and max_score >= min_score_threshold:
                predicted_category = max(category_scores, key=category_scores.get)
                logger.info(f"고신뢰도 분류: {predicted_category} (신뢰도: {confidence:.2f}, 점수: {max_score})")
                return predicted_category
            
            # 저신뢰도 또는 애매한 경우 - 일반 상담으로 분류
            if confidence < confidence_threshold or max_score < min_score_threshold:
                logger.info(f"저신뢰도 분류 - 일반상담 적용 (신뢰도: {confidence:.2f}, 최고점수: {max_score})")
                return 'general'
        
        # 2차: 모호한 경우만 파인튜닝 모델 사용 (완전히 애매한 경우)
        try:
            if self.model_id and len(user_input.strip()) > 10:  # 너무 짧은 입력은 파인튜닝 모델 사용 안함
                logger.info(f"파인튜닝 분류 사용: '{user_input[:30]}...'")
                category = self._classify_with_finetuned_model(user_input)
                classification_time = time.time() - start_time
                logger.info(f"파인튜닝 분류 완료: {category} ({classification_time:.2f}초)")
                return category
        except Exception as e:
            logger.warning(f"파인튜닝 모델 분류 실패: {str(e)}")
        
        # 폴백: general (더 구체적인 정보 요청)
        fallback_category = 'general'
        logger.info(f"폴백 분류: {fallback_category} - 사용자 정보 수집 모드")
        return fallback_category
    
    def _calculate_keyword_scores(self, user_input: str) -> Dict[str, float]:
        """가중치 기반 키워드 점수 계산"""
        scores = {}
        
        for category, patterns in self.keyword_patterns.items():
            score = 0
            
            # 높은 가중치 키워드 (3점)
            for keyword in patterns['high']:
                if keyword in user_input:
                    score += 3
            
            # 중간 가중치 키워드 (2점)
            for keyword in patterns['medium']:
                if keyword in user_input:
                    score += 2
            
            # 낮은 가중치 키워드 (1점)
            for keyword in patterns['low']:
                if keyword in user_input:
                    score += 1
            
            if score > 0:
                scores[category] = score
        
        return scores
    
    def _detect_accident_related_hints(self, user_input: str) -> Dict[str, Any]:
        """사고 관련 징후 감지 (분류 신뢰도가 낮을 때 사용) - 다양한 사고 유형 포함"""
        
        # 사고 관련 기본 징후 키워드 - 확장
        accident_hints = [
            # 직접적 사고 표현
            '사고', '충돌', '부딪혔', '접촉', '박았', '받았어',
            # 차대보행자 관련
            '보행자', '사람', '치었', '건드렸', '건너다', '횡단보도', '무단횡단',
            '녹색불', '빨간불', '신호등', '인도', '걷다', '산책', '아이', '학생',
            # 차대자전거 관련
            '자전거', '바이크', '따릉이', '킥보드', '전동킥보드', '자전거도로',
            '페달', '헬멧', '타고', '달리다',
            # 차대농기구 관련
            '농기구', '트랙터', '농로', '경운기', '농번기', '농사', '농촌', 
            '농기계', '농어촌', '갑자기', '나와서', '저속', '밭', '논', '농민',
            # 자연스러운 언급
            '나셨어요', '나셨네요', '맞았어요', '당했어요',
            # 상황 설명
            '드라이브', '운전', '차량', '자동차',
            # 감정 표현
            '놀랐', '당황', '대박', '무서운', '깜짝',
            # 질문/대화 유도 표현
            '어떻게', '뭐해야', '어쩌게', '도움',
            # 위치/상황 언급
            '교차로', '도로', '주차장', '신호등', '길', '시골길'
        ]
        
        detected_hints = []
        for hint in accident_hints:
            if hint in user_input:
                detected_hints.append(hint)
        
        # 최소 1개 이상의 징후가 있으면 사고 관련으로 간주
        is_accident_related = len(detected_hints) >= 1
        
        return {
            'is_accident_related': is_accident_related,
            'hints': detected_hints,
            'hint_count': len(detected_hints)
        }
    
    def _classify_with_finetuned_model(self, user_input: str) -> str:
        """파인튜닝 모델 분류 (필요시만)"""
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": user_input}],
            max_tokens=10,
            temperature=0,
            timeout=45  # OpenAI API 타임아웃 45초
        )
        category = response.choices[0].message.content.strip().lower()
        
        # 유효한 카테고리인지 확인
        valid_categories = {'accident', 'precedent', 'law', 'term', 'general'}
        return category if category in valid_categories else 'general'
    
    def classify_with_context(self, user_input: str, previous_category: str = None) -> str:
        """문맥을 고려한 분류"""
        primary_result = self.classify(user_input)
        
        # 저신뢰도일 때 이전 카테고리 고려
        if primary_result == 'general' and previous_category:
            category_scores = self._calculate_keyword_scores(user_input.lower())
            
            # 이전 카테고리와 관련된 키워드가 있으면 가중치 부여
            context_keywords = {
                'accident': ['관련', '이것', '이거', '해당', '위'],
                'precedent': ['관련', '이것', '이거', '해당', '위', '찾아', '검색'],
                'law': ['관련', '이것', '이거', '해당', '위'],
                'term': ['관련', '이것', '이거', '해당', '위']
            }
            
            if previous_category in context_keywords:
                context_score = sum(2 for keyword in context_keywords[previous_category] 
                                  if keyword in user_input.lower())
                
                if context_score >= 2:  # 문맥 키워드가 2개 이상
                    logger.info(f"문맥 고려 분류: {user_input} → {previous_category} (문맥점수: {context_score})")
                    return previous_category
        
        return primary_result


class HybridRAGSystem:
    """하이브리드 RAG 시스템 - Direct Search + Self-Query Retriever 조합"""
    
    def __init__(self):
        from ..utils.vector_db import get_vector_db_manager
        self.vector_db_manager = get_vector_db_manager()
        
        # 카테고리별 컬렉션 매핑
        self.collection_mapping = {
            'accident': 'car_case',
            'precedent': 'precedent', 
            'law': 'law',
            'term': 'term'
        }
        
        # Self-Query용 LLM (가벼운 모델 사용)
        self.self_query_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=os.getenv('OPENAI_API_KEY'),
            max_tokens=100,  # Self-Query는 짧은 응답만 필요
            request_timeout=10
        )
        
        # 카테고리별 Self-Query Retriever 설정
        self.self_query_retrievers = {}
        self.metadata_field_info = self._initialize_metadata_info()
        
        # 검색 결과 캐시 (동일 질문 반복 시 성능 향상)
        self._search_cache = {}
        
        # 성능 통계
        self.search_stats = {
            'direct_searches': 0,
            'self_query_searches': 0,
            'cache_hits': 0,
            'hybrid_searches': 0
        }
        
        logger.info("HybridRAGSystem 초기화 완료 - Direct + Self-Query 조합")
    
    def _initialize_metadata_info(self) -> Dict[str, List[AttributeInfo]]:
        """카테고리별 메타데이터 필드 정보 정의"""
        return {
            'accident': [
                AttributeInfo(
                    name="사건 ID",
                    description="교통사고 사례의 고유 식별자 (예: 차01-1, 차02-3)",
                    type="string"
                ),
                AttributeInfo(
                    name="기본 과실비율",
                    description="A차량과 B차량의 기본 과실비율 정보",
                    type="string"
                ),
                AttributeInfo(
                    name="관련 법규",
                    description="적용되는 도로교통법 조문 (예: 도로교통법 제25조)",
                    type="string"
                ),
                AttributeInfo(
                    name="참고 판례",
                    description="관련 법원 판례 (예: 대법원 2011다3250)",
                    type="string"
                )
            ],
            'precedent': [
                AttributeInfo(
                    name="court",
                    description="판결을 내린 법원명 (예: 대법원, 서울고등법원)",
                    type="string"
                ),
                AttributeInfo(
                    name="case_id",
                    description="사건번호 (예: 2019다12345, 92도2077)",
                    type="string"
                ),
                AttributeInfo(
                    name="year",
                    description="판결 연도 (4자리 숫자)",
                    type="integer"
                )
            ],
            'law': [
                AttributeInfo(
                    name="title",
                    description="조문 제목 (예: 제5조(신호 또는 지시에 따를 의무))",
                    type="string"
                ),
                AttributeInfo(
                    name="article_number",
                    description="조문 번호 (예: 제5조, 제25조)",
                    type="string"
                ),
                AttributeInfo(
                    name="category",
                    description="법률 카테고리 (예: 신호준수, 교차로통행, 안전운전)",
                    type="string"
                )
            ],
            'term': [
                AttributeInfo(
                    name="term",
                    description="법률 용어명 (예: 과실, 도로, 차로)",
                    type="string"
                ),
                AttributeInfo(
                    name="category",
                    description="용어 분류 (예: 교통법규, 사고처리, 도로시설)",
                    type="string"
                )
            ]
        }
        
    def search_context(self, query: str, category: str, max_docs: int = 2) -> str:
        """하이브리드 검색: Direct Search + Self-Query Retriever 조합"""
        start_time = time.time()
        
        try:
            # 판례 카테고리의 경우 판례번호 검증 로직 적용
            if category == 'precedent':
                case_number = self._extract_case_number(query)
                if case_number:
                    # 판례번호가 감지된 경우 정확한 매칭 검색
                    exact_match_result = self._search_exact_precedent(case_number, query)
                    if exact_match_result:
                        return exact_match_result
                    else:
                        # 정확히 일치하는 판례번호가 없음 - 일반 검색도 차단
                        return f"EXACT_PRECEDENT_NOT_FOUND: {case_number}"
                else:
                    # 판례번호가 감지되지 않으면 일반 검색 허용하지만 경고 포함
                    logger.warning(f"판례번호 미감지: {query}")
            
            # 캐시 확인
            cache_key = f"{category}_{hash(query)}"
            if cache_key in self._search_cache:
                self.search_stats['cache_hits'] += 1
                logger.info(f"RAG 캐시 히트: {category} ({time.time() - start_time:.3f}초)")
                return self._search_cache[cache_key]
            
            # 하이브리드 검색 수행
            hybrid_result = self._hybrid_search(query, category, max_docs)
            
            if not hybrid_result:
                logger.info(f"RAG 검색 결과 없음: {category}")
                return ""
            
            # 캐시 저장 (메모리 절약을 위해 최대 100개까지만)
            if len(self._search_cache) < 100:
                self._search_cache[cache_key] = hybrid_result
            
            search_time = time.time() - start_time
            logger.info(f"RAG 검색 완료: {category} ({search_time:.3f}초)")
            return hybrid_result
            
        except Exception as e:
            logger.warning(f"RAG 검색 실패 ({category}): {str(e)}")
            return ""
    
    def _hybrid_search(self, query: str, category: str, max_docs: int) -> str:
        """하이브리드 검색: Direct + Self-Query 조합"""
        self.search_stats['hybrid_searches'] += 1
        
        # 1단계: 빠른 Direct Search (기본 검색)
        direct_results = self._direct_search(query, category, max_docs)
        self.search_stats['direct_searches'] += 1
        
        # 2단계: 자연어 쿠리에 필터 키워드가 있는지 확인
        needs_self_query = self._should_use_self_query(query, category)
        
        if needs_self_query:
            # Self-Query Retriever 사용 (메타데이터 필터링)
            try:
                self_query_results = self._self_query_search(query, category, max_docs)
                self.search_stats['self_query_searches'] += 1
                
                # 결과 병합 및 중복 제거
                combined_results = self._combine_search_results(direct_results, self_query_results)
                
                if combined_results:
                    logger.info(f"하이브리드 검색 성공: Direct({len(direct_results)}) + Self-Query({len(self_query_results)}) = {len(combined_results)}")
                    return self._format_search_results(combined_results, category)
                    
            except Exception as e:
                logger.warning(f"Self-Query 검색 실패, Direct 결과 사용: {str(e)}")
        
        # Self-Query 실패 또는 불필요 시 Direct 결과만 사용
        if direct_results:
            return self._format_search_results(direct_results, category)
        
        return ""
    
    def _direct_search(self, query: str, category: str, max_docs: int) -> List[Document]:
        """빠른 Direct VectorDB 검색"""
        try:
            collection_key = self.collection_mapping.get(category)
            if not collection_key:
                return []
            
            collection_name = self.vector_db_manager.COLLECTIONS.get(collection_key, collection_key)
            docs = self.vector_db_manager.search_similar_documents(
                query=query,
                collection_name=collection_name,
                k=max_docs * 2  # Self-Query와 병합을 위해 더 많이 가져오기
            )
            
            return docs or []
            
        except Exception as e:
            logger.warning(f"Direct 검색 실패: {str(e)}")
            return []
    
    def _should_use_self_query(self, query: str, category: str) -> bool:
        """자연어 쿠리에 메타데이터 필터링이 도움이 될지 판단"""
        
        # 카테고리별 Self-Query 필요 조건
        self_query_triggers = {
            'precedent': [
                '대법원', '고등법원', '지방법원', '법원',
                '20', '19', '연도', '년도'
            ],
            'law': [
                '제', '조', '항', '번호',
                '신호', '교차로', '안전', '운전'
            ],
            'accident': [
                'A차량', 'B차량', '비율', '과실',
                '좌회전', '직진', '교차로', '신호'
            ],
            'term': [
                '정의', '의미', '개념', '용어'
            ]
        }
        
        triggers = self_query_triggers.get(category, [])
        
        # 트리거 키워드가 2개 이상 있으면 Self-Query 사용
        trigger_count = sum(1 for trigger in triggers if trigger in query)
        
        should_use = trigger_count >= 2 or len(query) > 30  # 긴 쿠리는 더 정교한 검색 필요
        
        if should_use:
            logger.info(f"Self-Query 사용 결정: {category}, 트리거={trigger_count}, 쿠리길이={len(query)}")
        
        return should_use
    
    def _self_query_search(self, query: str, category: str, max_docs: int) -> List[Document]:
        """메타데이터 필터링이 가능한 Self-Query Retriever 검색"""
        try:
            # 카테고리별 Self-Query Retriever 가져오기 또는 생성
            retriever = self._get_or_create_self_query_retriever(category)
            if not retriever:
                return []
            
            # Self-Query 검색 수행
            docs = retriever.get_relevant_documents(query)
            
            # 최대 문서 수 제한
            return docs[:max_docs] if docs else []
            
        except Exception as e:
            logger.warning(f"Self-Query 검색 실패 ({category}): {str(e)}")
            return []
    
    def _get_or_create_self_query_retriever(self, category: str) -> Optional[SelfQueryRetriever]:
        """카테고리별 Self-Query Retriever 가져오기 또는 생성"""
        
        # 이미 생성된 경우 반환
        if category in self.self_query_retrievers:
            return self.self_query_retrievers[category]
        
        try:
            # VectorStore 가져오기
            collection_key = self.collection_mapping.get(category)
            if not collection_key:
                return None
            
            collection_name = self.vector_db_manager.COLLECTIONS.get(collection_key, collection_key)
            vectorstore = self.vector_db_manager.get_collection_as_vectorstore(collection_name)
            
            if not vectorstore:
                logger.warning(f"VectorStore를 찾을 수 없음: {collection_name}")
                return None
            
            # 메타데이터 필드 정보 가져오기
            metadata_info = self.metadata_field_info.get(category, [])
            if not metadata_info:
                logger.warning(f"메타데이터 정보 없음: {category}")
                return None
            
            # 문서 내용 설명
            document_content_description = self._get_document_content_description(category)
            
            # Self-Query Retriever 생성
            retriever = SelfQueryRetriever.from_llm(
                llm=self.self_query_llm,
                vectorstore=vectorstore,
                document_contents=document_content_description,
                metadata_field_info=metadata_info,
                enable_limit=True,
                verbose=False
            )
            
            # 캐시에 저장
            self.self_query_retrievers[category] = retriever
            logger.info(f"Self-Query Retriever 생성 완료: {category}")
            
            return retriever
            
        except Exception as e:
            logger.error(f"Self-Query Retriever 생성 실패 ({category}): {str(e)}")
            return None
    
    def _get_document_content_description(self, category: str) -> str:
        """카테고리별 문서 내용 설명"""
        descriptions = {
            'accident': "교통사고 사례, 과실비율, 법적 근거 및 판례 정보",
            'precedent': "법원 판례, 사건번호, 판결 내용 및 법적 판단",
            'law': "도로교통법 조문, 법률 내용 및 처벌 규정",
            'term': "법률 용어 정의, 교통사고 관련 용어 설명"
        }
        
        return descriptions.get(category, "교통사고 관련 법률 정보")
    
    def _combine_search_results(self, direct_results: List[Document], self_query_results: List[Document]) -> List[Document]:
        """두 검색 결과를 병합하고 중복 제거"""
        
        # 중복 제거를 위한 유니크 식별자 집합
        seen_content = set()
        combined_results = []
        
        # Self-Query 결과를 우선 (더 정확한 결과)
        for doc in self_query_results:
            content_hash = hash(doc.page_content[:100])  # 처음 100자로 중복 판단
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                combined_results.append(doc)
        
        # Direct 결과 추가 (중복 제외)
        for doc in direct_results:
            content_hash = hash(doc.page_content[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                combined_results.append(doc)
        
        return combined_results
    
    def _format_search_results(self, docs: List[Document], category: str) -> str:
        """검색 결과를 포맷팅하여 문자열로 리턴"""
        if not docs:
            return ""
        
        context_parts = []
        for i, doc in enumerate(docs[:3], 1):  # 최대 3개만 사용
            content = doc.page_content[:200]  # 200자로 제한
            metadata = self._format_metadata(doc.metadata, category)
            context_parts.append(f"[{i}] {content}\n{metadata}")
        
        return "\n".join(context_parts)
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """검색 통계 정보 반환"""
        total_searches = self.search_stats['hybrid_searches']
        
        stats = {
            'total_hybrid_searches': total_searches,
            'direct_searches': self.search_stats['direct_searches'],
            'self_query_searches': self.search_stats['self_query_searches'],
            'cache_hits': self.search_stats['cache_hits'],
            'cache_hit_ratio': round(self.search_stats['cache_hits'] / max(total_searches, 1) * 100, 1),
            'self_query_usage_ratio': round(self.search_stats['self_query_searches'] / max(total_searches, 1) * 100, 1),
            'active_self_query_retrievers': len(self.self_query_retrievers)
        }
        
        return stats
    
    def clear_cache(self):
        """검색 캐시 초기화"""
        self._search_cache.clear()
        logger.info("RAG 검색 캐시 초기화")
    
    def clear_self_query_retrievers(self):
        """생성된 Self-Query Retriever들 초기화 (메모리 절약)"""
        self.self_query_retrievers.clear()
        logger.info("Self-Query Retrievers 초기화")
    
    def _extract_case_number(self, query: str) -> Optional[str]:
        """판례번호 추출 - 다양한 형식 지원"""
        # 판례번호 패턴 (대법원, 고등법원, 지방법원 등)
        patterns = [
            r'(대법원\s*\d{4}[다가나도마바사아자차카타파하]\d+)',  # 대법원 2019다12345, 92도2077
            r'(서울고법\s*\d{4}[다가나도마바사아자차카타파하]\d+)',  # 서울고법 2020나56789
            r'(서울고등법원\s*\d{4}[다가나도마바사아자차카타파하]\d+)',  # 서울고등법원 2020나56789
            r'(서울중앙지방법원\s*\d{4}[다가나도마바사아자차카타파하]\d+)',  # 지방법원
            r'(서울지방법원\s*\d{4}[다가나도마바사아자차카타파하]\d+)',  # 지방법원 축약
            r'(\d{2,4}[다가나도마바사아자차카타파하]\d+)',  # 2019다12345, 92도2077 (법원명 없이)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                case_number = match.group(1).strip()
                logger.info(f"판례번호 감지: '{case_number}' from '{query}'")
                return case_number
        
        return None
    
    def _search_exact_precedent(self, case_number: str, original_query: str) -> Optional[str]:
        """정확한 판례번호 매칭 검색"""
        try:
            collection_name = self.vector_db_manager.COLLECTIONS.get('precedent', 'precedent')
            
            # 1차: 전체 문서 검색 (더 많은 결과 가져오기)
            docs = self.vector_db_manager.search_similar_documents(
                query=case_number,
                collection_name=collection_name,
                k=10  # 더 많은 결과 검색
            )
            
            if not docs:
                return None
            
            # 2차: 메타데이터에서 정확한 매칭 찾기
            exact_matches = []
            partial_matches = []
            
            for doc in docs:
                metadata = doc.metadata
                doc_case_id = metadata.get('case_id', '').strip()
                
                # 정확한 일치 검사
                if self._is_exact_case_match(case_number, doc_case_id):
                    exact_matches.append(doc)
                    logger.info(f"정확한 판례 매칭 발견: '{case_number}' == '{doc_case_id}'")
                # 부분 일치 (예: 년도와 사건번호만 매칭)
                elif self._is_partial_case_match(case_number, doc_case_id):
                    partial_matches.append(doc)
            
            # 3차: 결과 선택 및 포맷팅
            if exact_matches:
                # 정확한 매칭이 있으면 최고 1개만 반환
                best_match = exact_matches[0]
                return self._format_exact_precedent_result(best_match, case_number, True)
            
            elif partial_matches:
                # 부분 매칭이 있으면 최고 1개 반환
                best_match = partial_matches[0]
                return self._format_exact_precedent_result(best_match, case_number, False)
            
            # 전혀 매칭되지 않음
            return None
            
        except Exception as e:
            logger.warning(f"정확한 판례 검색 실패: {str(e)}")
            return None
    
    def _is_exact_case_match(self, input_case: str, db_case: str) -> bool:
        """정확한 판례번호 일치 검사"""
        if not input_case or not db_case:
            return False
        
        # 공백 제거 및 소문자 변환
        input_clean = re.sub(r'\s+', '', input_case.lower())
        db_clean = re.sub(r'\s+', '', db_case.lower())
        
        # 완전 일치
        if input_clean == db_clean:
            return True
        
        # 전반된 순서도 검사 (db의 경우 입력을 포함하는 경우)
        if input_clean in db_clean or db_clean in input_clean:
            return True
        
        return False
    
    def _is_partial_case_match(self, input_case: str, db_case: str) -> bool:
        """부분 판례번호 일치 검사 (년도 + 사건번호)"""
        if not input_case or not db_case:
            return False
        
        # 년도와 사건번호 추출 (도 추가)
        input_pattern = re.search(r'(\d{2,4}[다가나도마바사아자차카타파하]\d+)', input_case)
        db_pattern = re.search(r'(\d{2,4}[다가나도마바사아자차카타파하]\d+)', db_case)
        
        if input_pattern and db_pattern:
            input_core = input_pattern.group(1)
            db_core = db_pattern.group(1)
            return input_core.lower() == db_core.lower()
        
        return False
    
    def _format_exact_precedent_result(self, doc: Document, searched_case: str, is_exact: bool) -> str:
        """정확한 판례 검색 결과 포맷팅"""
        metadata = doc.metadata
        content = doc.page_content[:500]  # 더 자세한 내용
        
        case_id = metadata.get('case_id', searched_case)
        court = metadata.get('court', '미상')
        
        match_type = "정확한 매칭" if is_exact else "부분 매칭"
        
        result = f"✅ **판례 검색 성공** ({match_type})\n\n"
        result += f"📝 **판례 정보:**\n"
        result += f"- 사건번호: {case_id}\n"
        result += f"- 법원: {court}\n\n"
        result += f"📜 **판례 내용:**\n{content}\n\n"
        
        if not is_exact:
            result += f"📝 **매칭 안내:** 입력하신 '{searched_case}'와 유사한 판례입니다.\n"
        
        return result
    
    def _format_metadata(self, metadata: Dict, category: str) -> str:
        """카테고리별 메타데이터 포맷팅"""
        if category == 'accident':
            case_id = metadata.get('사건 ID', '')
            ratio = metadata.get('기본 과실비율', '')
            return f"사건: {case_id}, 비율: {ratio}" if case_id else ""
        
        elif category == 'precedent':
            case_id = metadata.get('case_id', '')
            court = metadata.get('court', '')
            return f"판례: {case_id}, 법원: {court}" if case_id else ""
        
        elif category == 'law':
            article = metadata.get('title', '')
            return f"조문: {article}" if article else ""
        
        elif category == 'term':
            term = metadata.get('term', '')
            return f"용어: {term}" if term else ""
        
        return ""
    
    def clear_cache(self):
        """검색 캐시 초기화"""
        self._search_cache.clear()
        logger.info("RAG 검색 캐시 초기화")


class SessionBasedConversationManager:
    """세션별 대화 관리자 - 영속적 메모리 + 세션 격리"""
    
    def __init__(self, main_llm):
        self.main_llm = main_llm
        self.session_chains = {}  # session_id -> ConversationChain
        self.session_metadata = {}  # session_id -> 메타데이터
        
        # 카테고리별 전용 프롬프트 템플릿들
        self.category_prompts = self._initialize_category_prompts()
        
        # 기본 통합 프롬프트 (카테고리 구분 없을 때)
        self.unified_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""당신은 교통사고 전문 상담사 '노느'입니다. 사용자와의 이전 대화를 기억하면서 연속성 있는 답변을 제공하세요.

**이전 대화**:
{history}

**답변 가이드라인**:
- 이전 대화 내용을 자연스럽게 참조하세요
- 교통사고 전문적 답변을 제공하세요
- 법적 근거와 실무 적용 사례를 포함하세요
- 친근하고 이해하기 쉽게 설명하세요

사용자: {input}
노느:"""
        )
        
        logger.info("SessionBasedConversationManager 초기화 완료")
    
    def _initialize_category_prompts(self) -> Dict[str, PromptTemplate]:
        """카테고리별 전용 프롬프트 템플릿 초기화"""
        
        # 🚗 교통사고 분석 전용 프롬프트 (다양한 사고 유형 지원 + 법규/판례 강화)
        accident_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""당신은 교통사고 과실비율 분석 전문가 '노느'입니다. 

**중요: 반드시 마크다운 형식으로 답변하세요.**

**이전 대화**:
{history}

**1단계: 사고 유형 파악**
사용자 상황을 분석하여 다음 중 해당하는 사고 유형을 파악하세요:
- **차대차 사고**: 자동차와 자동차 간 충돌
- **차대보행자 사고**: 자동차와 보행자 간 충돌  
- **차대자전거 사고**: 자동차와 자전거 간 충돌
- **차대농기구 사고**: 자동차와 농기구/기타 이동장치 간 충돌

**2단계: 사고 유형별 분석 원칙**
### 🚗 차대차 사고
- 신호 위반 > 신호 준수
- 비보호 회전 > 보호 회전
- 좌회전 > 직진 (같은 신호)
- 후진입 > 선진입

### 👨‍🦯 차대보행자 사고  
- 보행자 보호 우선 원칙
- 신호 위반 보행자도 차량에 10% 기본 과실
- 횡단보도 외 무단횡단 시 보행자 과실 증가
- 야간/악천후 시 차량 주의의무 강화

### 🚴 차대자전거 사고
- 자전거 교통약자 보호 원칙  
- 차량 대비 자전거 과실 경감
- 자전거도로 미이용 시 자전거 과실 가산
- 어린이/노인/장애인 자전거 운전자 과실 감경

### 🚜 차대농기구 사고
- 농기구 저속 운행 특성 고려
- 농로 진출입 시 특별 주의의무
- 농번기 등 특수 상황 고려
- 농기구 운전자 연령대 고려

**3단계: 최소 분석 조건 확인**
다음 정보가 있으면 바로 분석하세요:
- 각 당사자의 신호 상태/행동
- 사고 지점 및 상황
- 정말 중요한 정보만 빠진 경우에만 간단히 질문

**마크다운 답변 형식**:

## 🎯 **사고 유형 및 상황**
- **사고 유형**: [차대차/차대보행자/차대자전거/차대농기구]
- **A당사자**: [차량/보행자/자전거/농기구] - [신호상태 + 행동]
- **B당사자**: [차량/보행자/자전거/농기구] - [신호상태 + 행동]
- **사고 지점**: [교차로/횡단보도/농로/일반도로 등]

## ⚖️ **과실비율 분석**
### 기본 과실비율
- **A당사자**: X% 
- **B당사자**: Y%
- **분석 근거**: [사고 유형별 특성 및 교통법리 적용]

## 🔧 **조정요소**
### [차량] 관련 수정요소
- 현저한 과실 (+10%): [해당사항 있을 때만]
- 중대한 과실 (+20%): [해당사항 있을 때만]

### [보행자/자전거/농기구] 관련 수정요소 (해당 사고일 때만)
- 야간/시야장애 (+5%)
- 교통약자 보호 (-10%)  
- 전용도로 미이용 (+5%)
- 기타 특수상황

## 📊 **예상 과실비율**
- **A당사자**: X% (기본 ± 조정)
- **B당사자**: Y% (기본 ± 조정)

## 📝 **참고자료 정보** (관련 자료가 있는 경우만)
- **참고 케이스**: [사건 ID 및 상황]
- **적용 가능성**: [사용자 상황과의 일치도 평가]

## 📋 **관련 법규 및 근거**
### 🏛️ **적용 법률**
**사고 유형별 관련 조문을 구체적으로 명시하세요:**

#### 차대차 사고 관련
- **도로교통법 제5조 (신호 또는 지시에 따를 의무)**
  - 모든 차량과 보행자는 신호기의 신호에 따라야 함
- **도로교통법 제25조 (교차로 통행방법)**  
  - 교차로에서의 우선순위 및 통행방법
- **도로교통법 제27조 (횡단·유턴·후진의 금지)**
  - 위험한 장소에서의 운전 금지

#### 차대보행자 사고 관련
- **도로교통법 제12조 (보행자의 도로횡단)**
  - 보행자의 횡단보도 이용 의무
- **도로교통법 제27조 (보행자 보호의무)**
  - 운전자의 보행자 보호 의무
- **도로교통법 제49조 (어린이 보호구역)**
  - 어린이 보호구역에서의 특별 주의의무

#### 차대자전거 사고 관련  
- **도로교통법 제13조의2 (자전거의 통행방법)**
  - 자전거 통행 관련 특례 규정
- **자전거 이용 활성화에 관한 법률 제3조**
  - 자전거도로의 구분 및 이용 의무

#### 차대농기구 사고 관련
- **도로교통법 제2조 (정의)**
  - 농기구의 차량 분류 및 정의
- **농어촌도로 정비법**
  - 농어촌 도로에서의 특별 규정

### ⚖️ **관련 판례** 
**중요: 사용자 입력의 [참고자료] 섹션에 실제 판례가 있을 때만 이 섹션을 표시하세요. 참고자료에 판례가 없으면 이 섹션을 생략하거나 "관련 판례 없음"으로 표시하세요.**

**참고자료에 실제 판례가 있는 경우만:**
- **[참고자료의 실제 법원명] [실제 사건번호]**
  - 판례 요지: [참고자료에서 직접 인용한 내용만]
  - 적용 가능성: [현재 상황과의 유사성만 분석]

**참고자료에 판례가 없는 경우:**
현재 상황과 직접 관련된 구체적인 판례는 참고자료에서 찾을 수 없습니다. 일반적인 교통사고 법리를 적용하여 분석하였습니다.

## 💡 **법리적 근거 및 해석**
### 🔍 **과실비율 산정 원칙**
- **신호 위반의 경우**: 도로교통법 제5조 위반으로 일방과실 또는 중과실 인정
- **보행자 보호의무**: 도로교통법 제27조에 따른 운전자의 절대적 주의의무
- **교통약자 보호**: 자전거, 보행자 등 교통약자에 대한 특별 보호 원칙
- **농로 특수성**: 농어촌 지역의 교통 특성 및 상황 고려

### 📖 **일반적인 법리 원칙**
- **신호 위반 사고**: 신호를 준수한 차량도 상대방 차량을 발견할 수 있었다면 경미한 과실 인정
- **보행자 사고**: 무단횡단 보행자라도 운전자에게 10% 이상의 기본 과실 부담
- **자전거 사고**: 자전거는 교통약자로서 차량 대비 과실 경감 원칙 적용
- **농기구 사고**: 농기구의 저속 특성 및 농로 진출입의 불가피성 고려

## ❓ **추가 확인사항** (꼭 필요한 경우만)
[정말 중요한 정보 부족 시에만 간단히 질문]

## 💡 **특별 참고사항**
### [해당 사고 유형별 특이사항]
- **차대차**: 과속, 음주 등 중대과실 엄중 적용
- **차대보행자**: 보행자 보호 의무, 무단횡단 시에도 차량 과실 존재
- **차대자전거**: 자전거 교통약자 보호, 저속 특성 고려
- **차대농기구**: 농기구 저속 운행, 농로 특수성, 계절적 요인 고려

## 🚨 **주의사항**
- 실제 사건은 개별 상황에 따라 과실비율이 달라질 수 있습니다
- 본 분석은 일반적인 법리와 참고자료를 기준으로 한 예상 과실비율입니다
- 정확한 과실비율 판정은 보험회사 또는 법원의 최종 판단에 따릅니다
- **절대로 참고자료에 없는 판례를 만들어내지 마세요**

사용자 질문: {input}"""
        )
        
        # ⚖️ 판례 검색 전용 프롬프트 (참고자료만 사용)
        precedent_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""당신은 교통사고 판례 검색 전문가 '노느'입니다. 

**중요: 반드시 마크다운 형식으로 답변하세요.**

**핵심 원칙 - 반드시 준수**:
- 사용자 입력의 [참고자료] 섹션에 있는 판례 내용만 사용하세요
- 참고자료에 없는 판례 정보는 절대 지어내지 마세요
- 정확한 판례가 없으면 "해당 판례를 찾을 수 없습니다"라고 명시하세요
- 다른 판례나 일반적인 법리로 보완하지 마세요

**이전 대화**:
{history}

**마크다운 답변 형식 (참고자료에 정확한 판례가 있을 때만)**:

## ⚖️ **판례 정보**
- **법원**: [참고자료의 court 정보]
- **사건번호**: [참고자료의 case_id 정보]

## 📝 **판례 내용**
[참고자료의 content를 그대로 인용]

## 🔍 **판례 분석**
[해당 판례의 주요 쟁점과 과실비율 산정 근거]

## 💡 **참고사항**
- 실제 사건은 개별적 상황을 고려하여 과실비율이 달라질 수 있습니다
- 정확한 판단은 전문가와 상담하시기 바랍니다

**참고자료에 해당 판례가 없는 경우**:
죄송합니다. 요청하신 판례를 정확히 찾을 수 없습니다. 
정확한 사건번호(예: 대법원 2019다12345)를 입력해주시거나, 다른 검색어로 시도해 주세요.

사용자 질문: {input}"""
        )
        
        # 📚 법률 검색 전용 프롬프트 (참고자료만 사용)
        law_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""당신은 교통법규 전문가 '노느'입니다. 

**중요: 반드시 마크다운 형식으로 답변하세요.**

**핵심 원칙 - 반드시 준수**:
- 사용자 입력의 [참고자료] 섹션에 있는 법조문만 사용하세요
- 참고자료에 없는 법률 내용은 절대 지어내지 마세요
- 정보가 부족하면 "참고자료에서 해당 법조문을 찾을 수 없습니다"라고 명시하세요
- 일반적인 법률 지식으로 보완하지 마세요

**이전 대화**:
{history}

**마크다운 답변 형식 (참고자료에 법조문이 있을 때만)**:

## 📖 **관련 법률**
### [참고자료의 법률명 및 조항]

## 📝 **조문 내용**
[참고자료에서 직접 인용한 법조문 전문]

## 🔍 **조문 구조** (참고자료에 subsections가 있는 경우)
- **제X조 제1항**: [해당 항목의 content]
- **제X조 제2항**: [해당 항목의 content]
[subsections 정보를 구조화하여 표시]

## 📚 **세부 조항** (참고자료에 items가 있는 경우)
[각 항목의 items 리스트를 정리하여 표시]

## 🔑 **핵심 키워드** (참고자료에 keywords가 있는 경우)
[참고자료의 keywords를 정리하여 표시]

## 💡 **해석 및 적용**
[참고자료에 명시된 해석과 적용 방법만]

## 🚨 **위반 시 처벌**
[참고자료에 명시된 처벌 내용만]

**참고자료에 해당 법조문이 없는 경우**:
죄송합니다. 요청하신 법조문에 대한 정확한 참고자료를 찾을 수 없습니다. 
구체적인 조문 번호(예: 도로교통법 제25조)를 입력해주시거나, 다른 검색어로 시도해 주세요.

사용자 질문: {input}"""
        )
        
        # 📖 용어 검색 전용 프롬프트 (참고자료만 사용)
        term_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""당신은 교통 관련 용어 전문가 '노느'입니다. 

**중요: 반드시 마크다운 형식으로 답변하세요.**

**핵심 원칙 - 반드시 준수**:
- 사용자 입력의 [참고자료] 섹션에 있는 용어 정의만 사용하세요
- 참고자료에 없는 용어 설명은 절대 지어내지 마세요
- 정보가 부족하면 "참고자료에서 해당 용어를 찾을 수 없습니다"라고 명시하세요
- 일반적인 상식으로 보완하지 마세요

**이전 대화**:
{history}

**마크다운 답변 형식 (참고자료에 용어가 있을 때만)**:

## 📝 **용어 정의**
### **[참고자료의 term]**

## 🔍 **정의 내용**
[참고자료의 desc 내용을 구조화하여 표시]

예시:
- 정의 1: [desc 배열의 첫 번째 항목]
- 정의 2: [desc 배열의 두 번째 항목]
- ...

## 📚 **상세 설명**
[참고자료의 desc에 있는 구체적인 설명들을 정리]

## 💡 **실제 적용**
[해당 용어가 교통상황에서 어떻게 적용되는지 참고자료 기반으로 설명]

## 🔗 **관련 용어**
[같은 카테고리의 관련 용어들이 있다면 함께 언급]

**참고자료에 해당 용어가 없는 경우**:
죄송합니다. 요청하신 용어에 대한 정확한 정의를 참고자료에서 찾을 수 없습니다. 
다른 용어로 검색해보시거나, 더 구체적인 용어를 입력해 주세요.

사용자 질문: {input}"""
        )
        
        # 💬 일반 상담 전용 프롬프트 (참고자료 기반)
        general_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""당신은 친근한 교통사고 상담 챗봇 '노느'입니다. 

**중요: 반드시 마크다운 형식으로 답변하세요.**

**핵심 원칙**:
- 참고자료가 있다면 그 내용만 사용하세요
- 참고자료가 없다면 일반적인 안내와 질문 유도를 하세요
- 추측이나 불확실한 정보는 제공하지 마세요

**이전 대화**:
{history}

**답변 원칙**:
- 간결하고 이해하기 쉬운 설명
- 실용적이고 도움이 되는 정보 제공
- 마크다운 형식으로 구조화된 답변

**마크다운 답변 형식**:

## 💬 **상담 내용**
[사용자 질문에 대한 답변 - 참고자료 기반 또는 일반적인 안내]

## 📊 **참고자료 정보** (참고자료가 있는 경우)
[참고자료의 종류에 따라 다음 중 해당하는 정보 표시]

### 사고 케이스 정보 (car_to_car, car_to_mobility, car_to_pedestrian 자료)
- **사건 ID**: [사건 ID]
- **사건 제목**: [사건 제목]
- **기본 과실비율**: [기본 과실비율]

### 판례 정보 (precedent 자료)
- **법원**: [court]
- **사건번호**: [case_id]
- **내용**: [content 요약]

### 법규 정보 (traffic_law_rag 자료)
- **법조문**: [title]
- **주요 내용**: [content 요약]

### 용어 정보 (term 자료)
- **용어**: [term]
- **정의**: [desc 요약]

## 💡 **참고사항**
- [추가 정보나 주의사항]
- [관련 도움말이나 다음 단계 안내]

## 🔍 **더 정확한 상담을 위한 정보**
구체적인 분석을 원하신다면 다음 정보를 알려주세요:
- 사고 상황 (교차로, 직진로 등)
- 신호 상태 (빨간불, 초록불 등)
- 각 차량의 행동 (좌회전, 직진, 정지 등)
- 기타 특이사항 (과속, 신호위반 등)

사용자 질문: {input}"""
        )
        
        return {
            'accident': accident_prompt,
            'precedent': precedent_prompt,
            'law': law_prompt,
            'term': term_prompt,
            'general': general_prompt
        }
    
    def get_or_create_chain(self, session_id: str, category: str = 'general') -> ConversationChain:
        """세션별 ConversationChain 가져오기/생성 (카테고리별 프롬프트 적용)"""
        if session_id not in self.session_chains:
            # 새 세션용 메모리 생성 (순수 대화만 저장)
            memory = ConversationBufferWindowMemory(
                k=8,  # 최근 8개 대화쌍 기억 (16개 메시지)
                return_messages=False,
                memory_key="history",
                input_key="input",
                output_key="response"
            )
            
            # 카테고리별 프롬프트 선택
            prompt_template = self.category_prompts.get(category, self.unified_prompt)
            
            # 새 ConversationChain 생성
            chain = ConversationChain(
                llm=self.main_llm,
                memory=memory,
                prompt=prompt_template,
                verbose=False,
                output_key="response"
            )
            
            self.session_chains[session_id] = chain
            self.session_metadata[session_id] = {
                'created_at': time.time(),
                'last_activity': time.time(),
                'total_interactions': 0,
                'categories_used': {},
                'total_processing_time': 0,
                'primary_category': category  # 주요 카테고리 추가
            }
            
            logger.info(f"새 세션 체인 생성: {session_id} (카테고리: {category})")
        else:
            # 기존 세션이 있으면 항상 최신 프롬프트로 업데이트 (프롬프트 변경 반영)
            current_category = self.session_metadata[session_id].get('primary_category', 'general')
            
            # 항상 최신 프롬프트 템플릿으로 업데이트
            prompt_template = self.category_prompts.get(category, self.unified_prompt)
            self.session_chains[session_id].prompt = prompt_template
            self.session_metadata[session_id]['primary_category'] = category
            
            if current_category != category:
                logger.info(f"세션 {session_id} 프롬프트 업데이트: {current_category} → {category}")
            else:
                logger.info(f"세션 {session_id} 프롬프트 새로고침: {category}")
        
        # 활동 시간 업데이트
        self.session_metadata[session_id]['last_activity'] = time.time()
        return self.session_chains[session_id]
    
    def get_category_prompt_info(self, category: str) -> Dict[str, str]:
        """카테고리별 프롬프트 정보 조회"""
        category_info = {
            'accident': {
                'name': '교통사고 분석',
                'focus': '과실비율 분석 + 법적 근거 + 조정 요소',
                'format': '상황분석 → 과실비율 → 법적근거 → 조정요소 → 실무조언'
            },
            'precedent': {
                'name': '판례 검색',
                'focus': '판례 정보 + 핵심 판단 + 쟁점 분석',
                'format': '판례정보 → 사건개요 → 법원판단 → 판례요지 → 적용지침'
            },
            'law': {
                'name': '도로교통법 조회',
                'focus': '조문 내용 + 입법 취지 + 처벌 규정',
                'format': '조문내용 → 핵심내용 → 위반유형 → 처벌기준 → 실무적용'
            },
            'term': {
                'name': '용어 설명',
                'focus': '정확한 정의 + 쉬운 설명 + 실무 예시',
                'format': '정의 → 쉬운설명 → 사용상황 → 관련용어 → 실무예시'
            },
            'general': {
                'name': '일반 상담',
                'focus': '친근한 응답 + 종합 안내 + 단계별 가이드',
                'format': '친근한인사 → 도움방법 → 제안사항 → 추가질문 → 관련기능'
            }
        }
        
        return category_info.get(category, category_info['general'])
    
    def update_session_stats(self, session_id: str, category: str, processing_time: float):
        """세션 통계 업데이트"""
        if session_id in self.session_metadata:
            metadata = self.session_metadata[session_id]
            metadata['total_interactions'] += 1
            metadata['total_processing_time'] += processing_time
            
            # 카테고리별 사용 횟수
            if category not in metadata['categories_used']:
                metadata['categories_used'][category] = 0
            metadata['categories_used'][category] += 1
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """오래된 세션 정리 (메모리 최적화)"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        expired_sessions = []
        for session_id, metadata in self.session_metadata.items():
            if current_time - metadata['last_activity'] > max_age_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            if session_id in self.session_chains:
                del self.session_chains[session_id]
            if session_id in self.session_metadata:
                del self.session_metadata[session_id]
            logger.info(f"만료된 세션 정리: {session_id}")
        
        if expired_sessions:
            logger.info(f"총 {len(expired_sessions)}개 세션 정리 완료")
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """세션 통계 조회"""
        if session_id not in self.session_metadata:
            return {'exists': False}
        
        metadata = self.session_metadata[session_id]
        chain = self.session_chains.get(session_id)
        
        history_length = 0
        if chain and hasattr(chain.memory, 'chat_memory'):
            history_length = len(chain.memory.chat_memory.messages)
        
        avg_processing_time = 0
        if metadata['total_interactions'] > 0:
            avg_processing_time = metadata['total_processing_time'] / metadata['total_interactions']
        
        return {
            'exists': True,
            'total_interactions': metadata['total_interactions'],
            'session_age_hours': round((time.time() - metadata['created_at']) / 3600, 2),
            'memory_length': history_length,
            'last_activity': metadata['last_activity'],
            'categories_used': metadata['categories_used'],
            'avg_processing_time': round(avg_processing_time, 2),
            'total_processing_time': round(metadata['total_processing_time'], 2)
        }
    
    def clear_session_memory(self, session_id: str):
        """특정 세션 메모리 초기화"""
        if session_id in self.session_chains:
            self.session_chains[session_id].memory.clear()
            
            # 통계도 리셋
            if session_id in self.session_metadata:
                self.session_metadata[session_id].update({
                    'total_interactions': 0,
                    'categories_used': {},
                    'total_processing_time': 0
                })
            
            logger.info(f"세션 {session_id} 메모리 초기화 완료")
    
    def get_active_sessions(self) -> List[str]:
        """활성 세션 목록 조회"""
        return list(self.session_chains.keys())


class OptimizedTrafficAccidentBot:
    """최적화된 교통사고 상담 봇 - 통합 시스템"""
    
    def __init__(self):
        # 핵심 컴포넌트들
        self.classifier = FastClassifier()
        self.rag_system = HybridRAGSystem()  # 하이브리드 RAG 시스템 사용
        
        # 메인 LLM (단일 인스턴스로 비용 최적화)
        self.main_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv('OPENAI_API_KEY'),
            max_tokens=800,  # 응답 길이 늘림 (600 → 800)
            request_timeout=45  # 타임아웃 대폭 증가 (10초 → 45초)
        )
        
        # 세션별 대화 관리자
        self.conversation_manager = SessionBasedConversationManager(self.main_llm)
        
        # 성능 통계
        self.total_requests = 0
        self.total_processing_time = 0
        
        logger.info("OptimizedTrafficAccidentBot 초기화 완료 - 통합 AI 시스템 (Hybrid RAG)")
    
    def process_query(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """통합 쿼리 처리 - 단일 LLM 호출로 최적화"""
        start_time = time.time()
        
        try:
            # 1. 빠른 분류 (95% 키워드 기반, API 호출 없음)
            classification_start = time.time()
            category = self.classifier.classify(user_input)
            classification_time = time.time() - classification_start
            
            # 2. RAG 컨텍스트 검색 (API 호출 없음, VectorDB 직접 검색)
            rag_start = time.time()
            context = self.rag_system.search_context(user_input, category)
            rag_time = time.time() - rag_start
            
            # 3. 세션별 ConversationChain 가져오기 (카테고리별 전용 프롬프트 적용)
            chain = self.conversation_manager.get_or_create_chain(session_id, category)
            
            # 4. 단일 LLM 호출로 응답 생성 (핵심 최적화!)
            llm_start = time.time()
            
            try:
                # 컨텍스트를 프롬프트에 자연스럽게 통합하되, 원본 사용자 입력은 유지
                if context:
                    # RAG 컨텍스트가 있는 경우, 사용자 입력에 간단히 추가
                    enhanced_input = f"{user_input}\n\n[참고자료: {context[:200]}]"
                else:
                    # 컨텍스트가 없으면 원본 그대로 사용
                    enhanced_input = user_input
                
                response = chain.predict(input=enhanced_input)
                
            except Exception as llm_error:
                logger.warning(f"LLM 호출 실패, 폴백 사용: {str(llm_error)}")
                response = self._generate_quick_fallback_response(user_input, category, context)
            
            llm_time = time.time() - llm_start
            
            # 5. 통계 업데이트
            total_time = time.time() - start_time
            self.conversation_manager.update_session_stats(session_id, category, total_time)
            self.total_requests += 1
            self.total_processing_time += total_time
            
            # 성능 로깅
            logger.info(f"쿼리 처리 완료 - 분류: {classification_time:.3f}초, RAG: {rag_time:.3f}초, LLM: {llm_time:.3f}초, 총: {total_time:.2f}초")
            
            return {
                'category': category,
                'response': response.strip() if hasattr(response, 'strip') else str(response),
                'context_used': bool(context),
                'processing_time': round(total_time, 2),
                'performance_breakdown': {
                    'classification_time': round(classification_time, 3),
                    'rag_time': round(rag_time, 3),
                    'llm_time': round(llm_time, 3)
                },
                'session_stats': self.conversation_manager.get_session_stats(session_id)
            }
            
        except Exception as e:
            logger.error(f"쿼리 처리 실패: {str(e)}")
            return self._generate_error_response(user_input, str(e), time.time() - start_time)
    
    def _generate_quick_fallback_response(self, user_input: str, category: str, context: str) -> str:
        """빠른 폴백 응답 생성 (API 호출 없음)"""
        
        category_responses = {
            'accident': f"""사고 상황: "{user_input[:50]}..."

현재 일시적으로 AI 응답 생성에 문제가 있습니다.

기본 안내:
- 교차로 사고의 경우 좌회전 차량의 과실비율이 높습니다
- 신호위반, 과속 등에 따라 비율이 조정됩니다
- 정확한 분석을 위해 상황을 더 자세히 말씀해 주세요

잠시 후 다시 시도해주세요.""",
            
            'precedent': f"""판례 검색: "{user_input[:50]}..."

현재 일시적으로 AI 응답 생성에 문제가 있습니다.

기본 안내:
- 사건번호를 정확하게 입력해주세요 (예: 대법원 2019다12345)
- 교통사고 관련 판례는 대법원, 고등법원에서 확인 가능합니다
- 판례는 비슷한 사안의 참고 자료로 활용합니다

잠시 후 다시 시도해주세요.""",
            
            'law': f"""법률 조회: "{user_input[:50]}..."

현재 일시적으로 AI 응답 생성에 문제가 있습니다.

기본 안내:
- 도로교통법은 교통안전을 위한 기본 법률입니다
- 조문 번호를 정확하게 입력해주세요 (예: 제5조, 제25조)
- 신호위반, 과속, 음주운전 등에 대한 처벌 규정이 있습니다

잠시 후 다시 시도해주세요.""",
            
            'term': f"""용어 설명: "{user_input[:50]}..."

현재 일시적으로 AI 응답 생성에 문제가 있습니다.

기본 안내:
- 과실비율: 사고 책임의 비율(퍼센트)
- 도로: 차량이 다니는 모든 길
- 차도: 도로에서 차량이 다니는 부분
- 획단보도: 보행자가 도로를 건너는 곳

잠시 후 다시 시도해주세요."""
        }
        
        return category_responses.get(category, f"""일반 상담: "{user_input[:50]}..."

현재 일시적으로 AI 응답 생성에 문제가 있습니다.

기본 안내:
- 교통사고 과실비율 분석
- 도로교통법 조회
- 판례 검색
- 법률 용어 설명

잠시 후 다시 시도해주세요.""")
    
    def _get_category_name(self, category: str) -> str:
        """카테고리 한글명 변환"""
        category_names = {
            'accident': '교통사고 분석',
            'precedent': '판례 검색',
            'law': '도로교통법 조회',
            'term': '용어 설명',
            'general': '일반 상담'
        }
        return category_names.get(category, '일반 상담')
    
    def _generate_error_response(self, user_input: str, error_message: str, processing_time: float) -> Dict[str, Any]:
        """오류 발생 시 폴백 응답"""
        return {
            'category': 'general',
            'response': f"""죄송합니다. 일시적으로 시스템에 문제가 발생했습니다.

**오류 상황**: {error_message[:100]}...

**해결 방법**:
1. 잠시 후 다시 시도해주세요
2. 질문을 더 구체적으로 작성해주세요
3. 계속 문제가 발생하면 새 채팅을 시작해주세요

**예시 질문**:
- "교차로에서 좌회전 중 사고가 났어요"
- "도로교통법 제5조 내용은?"
- "과실비율이 무엇인가요?"

다시 도움을 드릴 수 있도록 최선을 다하겠습니다.""",
            'context_used': False,
            'processing_time': round(processing_time, 2),
            'error': True
        }
    
    def clear_session_memory(self, session_id: str):
        """특정 세션 메모리 초기화"""
        self.conversation_manager.clear_session_memory(session_id)
    
    def cleanup_old_sessions(self):
        """오래된 세션 정리"""
        self.conversation_manager.cleanup_old_sessions()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """전체 시스템 통계"""
        avg_processing_time = 0
        if self.total_requests > 0:
            avg_processing_time = self.total_processing_time / self.total_requests
        
        active_sessions = self.conversation_manager.get_active_sessions()
        
        # 하이브리드 RAG 통계 추가
        rag_stats = self.rag_system.get_search_statistics()
        
        return {
            'total_requests': self.total_requests,
            'avg_processing_time': round(avg_processing_time, 2),
            'active_sessions': len(active_sessions),
            'memory_optimization': '세션별 독립 메모리',
            'api_efficiency': '95% 키워드 분류 + 단일 LLM 호출',
            'rag_system': {
                'type': 'Hybrid RAG (Direct + Self-Query)',
                'search_statistics': rag_stats,
                'optimization': 'Direct Search 기본 + Self-Query 자동 선택'
            }
        }


# 전역 인스턴스 (싱글톤 패턴으로 메모리 효율성 극대화)
_optimized_bot = None

def get_optimized_bot() -> OptimizedTrafficAccidentBot:
    """최적화된 봇 인스턴스 반환 (싱글톤)"""
    global _optimized_bot
    if _optimized_bot is None:
        _optimized_bot = OptimizedTrafficAccidentBot()
        logger.info("OptimizedTrafficAccidentBot 싱글톤 인스턴스 생성")
    return _optimized_bot

def process_optimized_query(user_input: str, session_id: str) -> Dict[str, Any]:
    """최적화된 쿼리 처리 (편의 함수)"""
    bot = get_optimized_bot()
    return bot.process_query(user_input, session_id)

def clear_session_memory(session_id: str):
    """세션 메모리 초기화 (편의 함수)"""
    bot = get_optimized_bot()
    bot.clear_session_memory(session_id)

def cleanup_old_sessions():
    """오래된 세션 정리 (편의 함수)"""
    bot = get_optimized_bot()
    bot.cleanup_old_sessions()

def test_precedent_search(case_number: str) -> Dict[str, Any]:
    """판례 검색 테스트 함수 (개발/디버깅용)"""
    bot = get_optimized_bot()
    rag_system = bot.rag_system
    
    logger.info(f"판례 검색 테스트 시작: '{case_number}'")
    
    # 판례번호 추출 테스트
    extracted = rag_system._extract_case_number(case_number)
    
    if extracted:
        logger.info(f"판례번호 추출 성공: '{extracted}'")
        # 정확한 매칭 검색 테스트
        exact_result = rag_system._search_exact_precedent(extracted, case_number)
        
        return {
            'input': case_number,
            'extracted_case_number': extracted,
            'exact_match_found': bool(exact_result),
            'result': exact_result or "정확히 일치하는 판례번호가 없습니다."
        }
    else:
        logger.info(f"판례번호 추출 실패: '{case_number}'")
        return {
            'input': case_number,
            'extracted_case_number': None,
            'exact_match_found': False,
            'result': "입력에서 판례번호를 찾을 수 없습니다."
        }

def get_system_stats() -> Dict[str, Any]:
    """시스템 통계 조회 (편의 함수)"""
    bot = get_optimized_bot()
    return bot.get_system_stats()

def test_hybrid_rag_search(query: str, category: str) -> Dict[str, Any]:
    """하이브리드 RAG 검색 테스트 함수 (개발/디버깅용)"""
    bot = get_optimized_bot()
    rag_system = bot.rag_system
    
    logger.info(f"하이브리드 RAG 검색 테스트 시작: '{query}' (category: {category})")
    
    try:
        # 검색 수행
        search_result = rag_system.search_context(query, category, max_docs=3)
        
        # 통계 정보 가져오기
        stats = rag_system.get_search_statistics()
        
        return {
            'input_query': query,
            'category': category,
            'search_result': search_result,
            'search_statistics': stats,
            'hybrid_system_info': {
                'direct_search': '기본 VectorDB 검색',
                'self_query_search': '메타데이터 필터링 사용',
                'trigger_conditions': '트리거 키워드 2개 이상 또는 쿠리 길이 30자 이상'
            }
        }
        
    except Exception as e:
        logger.error(f"하이브리드 RAG 검색 테스트 오류: {str(e)}")
        return {
            'input_query': query,
            'category': category,
            'error': str(e),
            'search_result': None
        }

def test_classification_with_confidence(user_input: str) -> Dict[str, Any]:
    """분류 로직 테스트 함수 (개발/디버깅용)"""
    bot = get_optimized_bot()
    classifier = bot.classifier
    
    logger.info(f"분류 신뢰도 테스트 시작: '{user_input}'")
    
    # 1. 키워드 점수 계산
    category_scores = classifier._calculate_keyword_scores(user_input.lower())
    
    # 2. 신뢰도 계산
    best_category = None
    max_score = 0
    confidence = 0.0
    
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        max_score = category_scores[best_category]
        total_scores = sum(category_scores.values())
        confidence = max_score / total_scores if total_scores > 0 else 0
    
    # 3. 사고 관련 징후 감지
    accident_indicators = classifier._detect_accident_related_hints(user_input.lower())
    
    # 4. 최종 분류 결과
    final_category = classifier.classify(user_input)
    
    classification_reason = {
        'high_confidence': confidence >= 0.65 and max_score >= 4,
        'accident_hints': accident_indicators['is_accident_related'],
        'fallback_used': confidence < 0.65 or max_score < 4
    }
    
    return {
        'input': user_input,
        'keyword_scores': category_scores,
        'best_keyword_category': best_category,
        'max_score': max_score,
        'confidence': round(confidence, 3),
        'confidence_threshold': 0.65,
        'min_score_threshold': 4,
        'meets_threshold': confidence >= 0.65 and max_score >= 4,
        'accident_indicators': accident_indicators,
        'final_classification': final_category,
        'classification_reason': classification_reason,
        'classification_debug': {
            'category_scores': category_scores,
            'predicted_category': category,
            'confidence': confidence,
            'confidence_threshold': 0.65,
            'min_score_threshold': 4,
            'meets_threshold': confidence >= 0.65 and max_score >= 4,
            'classification_reason': classification_reason
        }
    }

def get_session_stats(session_id: str) -> Dict[str, Any]:
    """세션 통계 조회 (편의 함수)"""
    bot = get_optimized_bot()
    return bot.conversation_manager.get_session_stats(session_id)
