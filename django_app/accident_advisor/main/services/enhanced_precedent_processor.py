"""
판례번호 정확성 검증이 포함된 Enhanced Precedent Processor
존재하지 않는 판례번호에 대한 적절한 응답 제공
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers import SelfQueryRetriever

# constants.py에서 상수 임포트
from ..constants import CASE_NUMBER_PATTERNS, COURT_NORMALIZATION, get_metadata_key

logger = logging.getLogger(__name__)

class EnhancedPrecedentProcessor:
    """판례번호 정확성 검증이 포함된 판례 검색 프로세서"""
    
    # constants.py에서 상수들을 사용
    # CASE_NUMBER_PATTERNS, COURT_NORMALIZATION, METADATA_KEY는 constants.py에서 관리
    
    def __init__(self, vector_db_manager, gpt_model):
        """
        Enhanced Precedent Processor 초기화
        
        Args:
            vector_db_manager: VectorDB 매니저 인스턴스
            gpt_model: GPT 모델 인스턴스
        """
        self.vector_db_manager = vector_db_manager
        self.gpt_model = gpt_model
        self.precedent_db = self.vector_db_manager.get_vector_db('precedent')
        
        if not self.precedent_db:
            logger.error("precedent VectorDB를 찾을 수 없습니다.")
            raise ValueError("precedent VectorDB 초기화 실패")
    
    def extract_case_numbers(self, query: str) -> List[str]:
        """
        사용자 입력에서 판례번호 추출
        
        Args:
            query (str): 사용자 입력
            
        Returns:
            List[str]: 추출된 판례번호 리스트
        """
        case_numbers = []
        
        for pattern in CASE_NUMBER_PATTERNS:
            matches = re.findall(pattern, query, re.IGNORECASE)
            case_numbers.extend(matches)
        
        # 중복 제거 및 정규화
        normalized_case_numbers = []
        for case_num in case_numbers:
            normalized = self._normalize_case_number(case_num)
            if normalized and normalized not in normalized_case_numbers:
                normalized_case_numbers.append(normalized)
        
        logger.info(f"추출된 판례번호: {normalized_case_numbers}")
        return normalized_case_numbers
    
    def _normalize_case_number(self, case_number: str) -> str:
        """
        판례번호 정규화
        
        Args:
            case_number (str): 원본 판례번호
            
        Returns:
            str: 정규화된 판례번호
        """
        # 공백 제거 및 소문자 변환
        normalized = re.sub(r'\s+', '', case_number).lower()
        
        # 특수 문자 제거
        normalized = re.sub(r'[^\w가-힣]', '', normalized)
        
        return normalized
    
    def extract_court_name(self, query: str) -> Optional[str]:
        """
        사용자 입력에서 법원명 추출
        
        Args:
            query (str): 사용자 입력
            
        Returns:
            Optional[str]: 추출된 법원명 (정규화됨)
        """
        query_lower = query.lower()
        
        for normalized_court, variations in COURT_NORMALIZATION.items():
            for variation in variations:
                if variation.lower() in query_lower:
                    logger.info(f"법원명 추출: {variation} → {normalized_court}")
                    return normalized_court
        
        return None
    
    def verify_case_number_exists(self, case_number: str, court_name: Optional[str] = None) -> Tuple[bool, List[Document]]:
        """
        판례번호가 실제로 DB에 존재하는지 확인
        
        Args:
            case_number (str): 확인할 판례번호
            court_name (Optional[str]): 법원명 (선택적)
            
        Returns:
            Tuple[bool, List[Document]]: (존재 여부, 일치하는 문서들)
        """
        try:
            # 정확한 매칭을 위한 메타데이터 필터 구성
            filter_conditions = {}
            
            # 판례번호 필터 추가 (부분 매칭 포함)
            if case_number:
                # 완전히 일치하는 경우를 먼저 찾고, 없으면 부분 매칭
                exact_matches = self.precedent_db.similarity_search(
                    query=case_number,
                    filter={get_metadata_key('PRECEDENT', 'CASE_ID'): case_number},
                    k=5
                )
                
                if exact_matches:
                    logger.info(f"판례번호 정확 매칭 성공: {case_number}")
                    return True, exact_matches
                
                # 부분 매칭 시도
                partial_matches = self.precedent_db.similarity_search(
                    query=case_number,
                    k=10
                )
                
                # 메타데이터에서 case_id 부분 매칭 확인
                relevant_matches = []
                for doc in partial_matches:
                    doc_case_id = doc.metadata.get(get_metadata_key('PRECEDENT', 'CASE_ID'), '').lower()
                    if case_number.lower() in doc_case_id or doc_case_id in case_number.lower():
                        relevant_matches.append(doc)
                
                if relevant_matches:
                    logger.info(f"판례번호 부분 매칭 성공: {case_number} (매칭된 개수: {len(relevant_matches)})")
                    return True, relevant_matches
                else:
                    logger.warning(f"판례번호 매칭 실패: {case_number}")
                    return False, []
            
            # 법원명만 있는 경우
            if court_name:
                court_matches = self.precedent_db.similarity_search(
                    query=court_name,
                    filter={get_metadata_key('PRECEDENT', 'COURT'): court_name},
                    k=5
                )
                
                if court_matches:
                    logger.info(f"법원명 매칭 성공: {court_name}")
                    return True, court_matches
            
            logger.warning(f"판례 검색 결과 없음: case_number={case_number}, court_name={court_name}")
            return False, []
            
        except Exception as e:
            logger.error(f"판례번호 확인 중 오류: {str(e)}")
            return False, []
    
    def find_similar_precedents(self, query: str, limit: int = 5) -> List[Document]:
        """
        유사한 판례 검색 (주제 기반)
        
        Args:
            query (str): 검색 쿼리
            limit (int): 결과 개수 제한
            
        Returns:
            List[Document]: 유사한 판례 문서들
        """
        try:
            # 주제 기반 유사도 검색
            similar_docs = self.precedent_db.similarity_search(
                query=query,
                k=limit
            )
            
            logger.info(f"유사 판례 검색 결과: {len(similar_docs)}개")
            return similar_docs
            
        except Exception as e:
            logger.error(f"유사 판례 검색 중 오류: {str(e)}")
            return []
    
    def process_precedent_query(self, user_input: str) -> str:
        """
        개선된 판례 검색 메인 함수
        
        Args:
            user_input (str): 사용자 입력
            
        Returns:
            str: 판례 검색 결과
        """
        try:
            logger.info(f"Enhanced 판례 검색 시작: '{user_input[:50]}...'")
            
            # 1. 판례번호와 법원명 추출
            case_numbers = self.extract_case_numbers(user_input)
            court_name = self.extract_court_name(user_input)
            
            logger.info(f"추출 결과 - 판례번호: {case_numbers}, 법원: {court_name}")
            
            # 2. 추출된 정보가 있는 경우 정확성 검증
            verified_docs = []
            exact_matches_found = False
            
            if case_numbers:
                for case_number in case_numbers:
                    exists, docs = self.verify_case_number_exists(case_number, court_name)
                    if exists and docs:
                        verified_docs.extend(docs)
                        exact_matches_found = True
                        logger.info(f"정확한 판례 매칭: {case_number}")
            
            # 3. 정확한 판례번호 매칭이 있는 경우
            if exact_matches_found and verified_docs:
                return self._generate_exact_match_response(user_input, verified_docs)
            
            # 4. 정확한 매칭이 없지만 판례번호가 있는 경우 - 주의 메시지
            if case_numbers and not exact_matches_found:
                return self._generate_no_match_response(user_input, case_numbers, court_name)
            
            # 5. 판례번호가 없는 경우 - 일반적인 주제 기반 검색
            return self._process_general_precedent_search(user_input)
            
        except Exception as e:
            logger.error(f"Enhanced 판례 검색 중 오류: {str(e)}")
            return self._generate_error_response(user_input, str(e))
    
    def _generate_exact_match_response(self, user_input: str, docs: List[Document]) -> str:
        """정확히 매칭된 판례가 있는 경우의 응답 생성"""
        try:
            # Self-Query Retriever를 사용하지 않고 직접 프롬프트 생성
            context = "\n\n".join([
                f"판례 {i+1}:\n"
                f"법원: {doc.metadata.get(get_metadata_key('PRECEDENT', 'COURT'), 'N/A')}\n"
                f"사건번호: {doc.metadata.get(get_metadata_key('PRECEDENT', 'CASE_ID'), 'N/A')}\n"
                f"내용: {doc.page_content[:800]}..."
                for i, doc in enumerate(docs[:3])  # 최대 3개까지만
            ])
            
            prompt = f"""
너는 교통사고 판례를 요약 정리해주는 전문가야.

아래 문서를 참고하여 사용자의 질문에 대해 정확히 일치하는 판례를 **간결하고 읽기 쉽게** 설명해줘.

---
질문: {user_input}

검색된 판례 문서:
{context}
---

출력 형식:

⚖️ **판례 검색 결과**

**🔍 검색 내용**: "{user_input}"

**✅ 정확히 일치하는 판례를 찾았습니다**

**📋 판례 상세 정보**:

**1️⃣ {docs[0].metadata.get(get_metadata_key('PRECEDENT', 'CASE_ID'), 'N/A')}**
• **법원**: {docs[0].metadata.get(get_metadata_key('PRECEDENT', 'COURT'), 'N/A')}
• **사고 개요**: [사고 상황을 1-2줄로 간단히]
• **주요 판단**: [핵심 법적 판단 1-2줄] 
• **과실비율**: [명시된 경우만 표시]

{f'''**2️⃣ {docs[1].metadata.get(get_metadata_key('PRECEDENT', 'CASE_ID'), 'N/A')}**
• **법원**: {docs[1].metadata.get(get_metadata_key('PRECEDENT', 'COURT'), 'N/A')}
• **사고 개요**: [사고 상황을 1-2줄로 간단히]
• **주요 판단**: [핵심 법적 판단 1-2줄]
• **과실비율**: [명시된 경우만 표시]''' if len(docs) > 1 else ''}

**💡 참고사항**:
- 구체적인 사고 상황에 따라 과실비율이 달라질 수 있습니다
- 정확한 분석을 위해서는 상세한 사고 경위가 필요합니다

조건:
- 각 판례를 명확히 구분하여 표시하세요
- 과실비율은 명시된 경우만 표시하고, 없으면 생략하세요
- 긴 내용은 1-2줄로 요약하여 읽기 쉽게 하세요
- 문서에 없는 정보는 임의로 만들지 마세요
- 사건번호와 법원명을 정확히 표시하세요

답변:
"""
            
            # GPT로 응답 생성
            response = self.gpt_model.invoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"정확 매칭 응답 생성 중 오류: {str(e)}")
            return self._generate_fallback_response(user_input)
    
    def _generate_no_match_response(self, user_input: str, case_numbers: List[str], court_name: Optional[str]) -> str:
        """매칭되는 판례가 없는 경우의 응답 생성 (간결한 버전)"""
        
        response = f"""⚖️ **판례 검색 결과**

**🔍 검색 내용**: "{user_input}"

**❌ 정확히 일치하는 판례를 찾을 수 없습니다**

**⚠️ 확인 사항**:
• 판례번호가 정확한지 다시 확인해주세요
• 법원명이 정확한지 확인해주세요
• 해당 판례가 교통사고 관련 판례인지 확인해주세요

**💡 올바른 검색 방법**:

**🎯 정확한 사건번호로 검색**
• "대법원 2019다12345 판례 내용은?"
• "서울고등법원 2015나60480 판례 검색"

**🎯 사고 유형과 함께 검색**
• "교차로 좌회전 사고 판례"
• "신호위반 관련 판례"
• "주차장 접촉사고 판례"

**🎯 법원별 검색**
• "대법원 교통사고 판례"
• "고등법원 과실비율 판례"

**📞 다른 방식으로 질문해주시면 더 정확한 도움을 드릴 수 있습니다!**"""

        return response
    
    def _process_general_precedent_search(self, user_input: str) -> str:
        """일반적인 주제 기반 판례 검색"""
        try:
            # 기존 Self-Query Retriever 방식 사용
            metadata_field_info = [
                AttributeInfo(
                    name=get_metadata_key('PRECEDENT', 'COURT'),
                    description="판례의 법원명 (예: 대법원, 서울고등법원, 지방법원 등)",
                    type="string"
                ),
                AttributeInfo(
                    name=get_metadata_key('PRECEDENT', 'CASE_ID'),
                    description="사건번호 (예: 92도2077, 2019다12345, 2015나60480 등)",
                    type="string"
                )
            ]
            
            self_retriever = SelfQueryRetriever.from_llm(
                llm=self.gpt_model,
                vectorstore=self.precedent_db,
                document_contents="교통사고 관련 법원 판례 데이터",
                metadata_field_info=metadata_field_info
            )
            
            prompt = PromptTemplate(
                input_variables=["question", "context"],
                template="""
너는 교통사고 판례를 요약 정리해주는 전문가야.

아래 문서(context)를 참고하여 사용자의 질문에 대해 관련된 판례를 **간결하고 읽기 쉽게** 설명해줘.

---
질문: {question}

검색된 판례 문서:
{context}
---

출력 형식:

⚖️ **판례 검색 결과**

**🔍 검색 내용**: [사용자 질문 요약]

**📋 관련 판례**:

**1️⃣ [사건번호]**
• **법원**: [법원명]
• **사고 개요**: [사고 상황을 1-2줄로 간단히]
• **주요 판단**: [핵심 법적 판단 1-2줄]
• **과실비율**: [A차량 XX% vs B차량 XX%] *(명시된 경우만)*

**2️⃣ [사건번호]**
• **법원**: [법원명]
• **사고 개요**: [사고 상황을 1-2줄로 간단히]
• **주요 판단**: [핵심 법적 판단 1-2줄]
• **과실비율**: [명시된 경우만 표시]

*(최대 3-4개 판례만 표시)*

**💡 참고사항**:
- 구체적인 사고 상황에 따라 과실비율이 달라질 수 있습니다
- 정확한 분석을 위해서는 상세한 사고 경위가 필요합니다

**조건**:
- 각 판례를 **명확히 구분**하여 표시하세요
- **과실비율**은 명시된 경우만 표시하고, 없으면 생략하세요
- **긴 내용은 1-2줄로 요약**하여 읽기 쉽게 하세요
- 문서에 없는 정보는 임의로 만들지 마세요
- 사건번호와 법원명을 **정확히** 표시하세요

답변:
"""            
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.gpt_model,
                retriever=self_retriever,
                chain_type="stuff",
                chain_type_kwargs={"prompt": prompt}
            )
            
            result = qa_chain.invoke({"query": user_input})
            return result['result']
            
        except Exception as e:
            logger.error(f"일반 판례 검색 중 오류: {str(e)}")
            return self._generate_fallback_response(user_input)
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """최종 폴백 응답"""
        return f"""⚖️ **판례 검색 결과**

**🔍 검색 내용**: "{user_input}"

**⚠️ 일시적 오류 발생**

죄송합니다. 현재 판례 검색 시스템에 일시적인 문제가 발생했습니다.

**💡 다시 시도해 보세요**:

**🎯 구체적인 사건번호로 검색**
• "대법원 2019다12345 판례 내용은?"
• "서울고등법원 2015나60480 판례 검색"

**🎯 사고 유형과 함께 검색**
• "교차로 좌회전 사고 판례"
• "신호위반 관련 판례"
• "주차장 접촉사고 판례"

**🎯 법원별 검색**
• "대법원 교통사고 판례"
• "고등법원 과실비율 판례"

**📞 도움이 필요하시면 다른 방식으로 질문해주세요!**"""
    
    def _generate_error_response(self, user_input: str, error_msg: str) -> str:
        """오류 응답 생성"""
        return f"""⚖️ **판례 검색 결과**

**🔍 검색 내용**: "{user_input}"

**❌ 시스템 오류 발생**

죄송합니다. 판례 검색 중 시스템 오류가 발생했습니다.

**💡 해결 방법**:
• 잠시 후 다시 시도해주세요
• 다른 방식으로 질문해주세요
• 구체적인 사건번호나 키워드를 사용해보세요

**🎯 추천 질문 방식**:
• "대법원 [사건번호] 판례"
• "[사고유형] 관련 판례"
• "[법원명] 교통사고 판례"

**도움이 필요하시면 언제든 말씀해주세요!** 🙏

*기술 정보: {error_msg}*"""
