"""
교통사고 챗봇 상수 정의

모든 메타데이터 키와 공통 상수들을 한 곳에서 관리합니다.
중복 정의를 방지하고 일관성을 유지하기 위해 생성된 파일입니다.
"""

# ========== 메타데이터 키 정의 ==========

# JSON 파일의 메타데이터 키 (UI.py와 동일)
METADATA_KEYS = {
    # 판례 관련 키
    'PRECEDENT': {
        'COURT': "court",
        'CASE_ID': "case_id",
        'CONTENT': "content",
    },
    
    # 도로교통법 관련 키
    'LOAD_TRAFFIC_LAW': {
        'ARTICLE_TITLE': "article_title",
        'ARTICLE_NUMBER': "article_number", 
        'PARAGRAPH': "paragraph",
        'CONTENT': "content",
    },
    
    # 교통사고 사례 관련 키
    'ACCIDENT_CASE': {
        'CASE_ID': "사건 ID",
        'CASE_TITLE': "사건 제목", 
        'CASE_SITUATION': "사고상황",
        'BASE_RATIO': "기본 과실비율",
        'MODIFIERS': "케이스별 과실비율 조정예시",
        'LAW_REFERENCES': "관련 법규",
        'PRECEDENT': "참고 판례",
        'REASON': "기본 과실비율 해설",
    },
    
    # 용어 관련 키
    'TERM': {
        'TERM': "term",
        'DESCRIPTION': "desc",
        'CATEGORY': "term_category",
        'RELATED_TERMS': "related_terms",
        'LAW_REFERENCE': "law_reference",
        'PRECEDENT_REFERENCE': "precedent_reference",
    }
}

# ========== VectorDB 컬렉션 이름 ==========

VECTOR_DB_COLLECTIONS = {
    'TERM': "term",
    'LOAD_TRAFFIC_LAW': "load_traffic_law", 
    'TRAFFIC_LAW_RAG': "traffic_law_rag",
    'CAR_CASE': "car_case",
    'PRECEDENT': "precedent",
}

# ========== 질문 분류 카테고리 ==========

CLASSIFICATION_CATEGORIES = {
    'ACCIDENT': 'accident',
    'PRECEDENT': 'precedent', 
    'LAW': 'law',
    'TERM': 'term',
    'GENERAL': 'general'
}

VALID_CATEGORIES = set(CLASSIFICATION_CATEGORIES.values())

# ========== 폴백 키워드 정의 ==========

FALLBACK_KEYWORDS = {
    'accident': [
        '사고', '충돌', '접촉', '과실', '비율', '좌회전', '직진', '교차로',
        '신호위반', '주차장', '후진', '차로변경', '추돌', '측면충돌'
    ],
    'precedent': [
        '판례', '대법원', '고등법원', '지방법원', '판결', '사건번호',
        '판단', '요지', '법원', '소송', '재판'
    ],
    'law': [
        '도로교통법', '법률', '조문', '제', '조', '항', '규정', '위반',
        '처벌', '범칙금', '벌점', '법적', '규칙'
    ],
    'term': [
        '정의', '의미', '뜻', '용어', '설명', '개념', '무엇', '어떤',
        '차로', '도로', '차량', '운전자', '보행자'
    ]
}

# ========== 판례 처리 관련 상수 ==========

# 판례번호 정규식 패턴들
CASE_NUMBER_PATTERNS = [
    r'(\d{4}[가나다마바사아자차카타파하][단합]\d+)',     # 2019다12345
    r'(\d{2}[가나다마바사아자차카타파하][단합]\d+)',       # 92도2077  
    r'(\d{4}[가나다마바사아자차카타파하]\d+)',           # 2019다12345 (단/합 없음)
    r'(\d{2}[가나다마바사아자차카타파하]\d+)',             # 92도2077 (단/합 없음)
    r'([가나다마바사아자차카타파하][단합]?\d{4,})',         # 다12345, 다단12345
    r'(\d{4}[나노누로루모보소호][단합]?\d+)',             # 변형된 형태
]

# 법원 이름 정규화 매핑
COURT_NORMALIZATION = {
    '대법원': ['대법원', '대법', '최고법원'],
    '서울고등법원': ['서울고등법원', '서울고법', '서울고등'],
    '서울중앙지방법원': ['서울중앙지방법원', '서울중앙지법', '서울중앙'],
    '서울남부지방법원': ['서울남부지방법원', '서울남부지법', '서울남부'],
    '수원지방법원': ['수원지방법원', '수원지법', '수원'],
    '인천지방법원': ['인천지방법원', '인천지법', '인천'],
    '부산지방법원': ['부산지방법원', '부산지법', '부산'],
    '대구지방법원': ['대구지방법원', '대구지법', '대구'],
    '광주지방법원': ['광주지방법원', '광주지법', '광주'],
    '대전지방법원': ['대전지방법원', '대전지법', '대전'],
}

# ========== 응답 템플릿 관련 상수 ==========

# 기본 응답 형식 헤더
RESPONSE_HEADERS = {
    'PRECEDENT': "⚖️ **판례 검색 결과**",
    'LAW': "📚 **도로교통법 조회 결과**",
    'ACCIDENT': "🚗 **교통사고 과실비율 분석 결과**",
    'TERM': "📖 **용어 설명 결과**",
    'GENERAL': "👋 **노느 상담 챗봇**",
    'ERROR': "❌ **시스템 오류**"
}

# ========== 파일 경로 관련 상수 ==========

# 메타데이터 파일명
METADATA_FILES = {
    'CAR_TO_CAR': 'car_to_car.json',
    'PRECEDENT': 'precedent.json',
    'LOAD_TRAFFIC_LAW': 'load_traffic_law.json',
    'TERM': 'term.json',
    'MODIFIER': 'modifier.json',
    'TRAFFIC_LAW_RAG': 'traffic_law_rag.json'
}

# ========== API 설정 관련 상수 ==========

# OpenAI 모델 설정
OPENAI_MODELS = {
    'GPT_4O_MINI': "gpt-4o-mini",
    'GPT_3_5_TURBO': "gpt-3.5-turbo",
    'EMBEDDING': "text-embedding-3-large"
}

# API 타임아웃 설정 (초)
API_TIMEOUTS = {
    'CLASSIFICATION': 5,
    'RAG_RETRIEVAL': 10,
    'RESPONSE_GENERATION': 15
}

# ========== 로깅 관련 상수 ==========

LOG_MESSAGES = {
    'CLASSIFICATION_START': "질문 분류 시작",
    'CLASSIFICATION_SUCCESS': "질문 분류 성공",
    'CLASSIFICATION_FALLBACK': "폴백 분류 사용",
    'RAG_START': "RAG 검색 시작",
    'RAG_SUCCESS': "RAG 검색 완료",
    'RESPONSE_GENERATION_START': "응답 생성 시작",
    'RESPONSE_GENERATION_SUCCESS': "응답 생성 완료",
    'ERROR_OCCURRED': "오류 발생"
}

# ========== UI 관련 상수 ==========

# 예시 질문들
EXAMPLE_QUESTIONS = {
    'ACCIDENT': [
        "교차로에서 좌회전하다가 직진차와 충돌했어요",
        "주차장에서 후진하다가 다른 차와 접촉했어요",
        "신호위반 차량과 사고가 났어요"
    ],
    'PRECEDENT': [
        "대법원 2019다12345 판례 내용은?",
        "교차로 사고 관련 판례를 알려주세요",
        "신호위반 관련 판례 검색"
    ],
    'LAW': [
        "도로교통법 제25조 내용은?",
        "신호위반 관련 법률을 알려주세요",
        "교차로 통행 관련 규정"
    ],
    'TERM': [
        "과실비율이 무엇인가요?",
        "차로변경의 정의는?",
        "보호의무위반이 뭔가요?"
    ]
}

# ========== 간편 접근 함수들 ==========

def get_metadata_key(category: str, key: str) -> str:
    """
    메타데이터 키 조회 함수
    
    Args:
        category (str): 카테고리 (PRECEDENT, LOAD_TRAFFIC_LAW 등)
        key (str): 키 이름 (COURT, CASE_ID 등)
        
    Returns:
        str: 실제 메타데이터 키 값
        
    Example:
        court_key = get_metadata_key('PRECEDENT', 'COURT')  # "court"
    """
    return METADATA_KEYS.get(category, {}).get(key, '')

def get_collection_name(category: str) -> str:
    """
    VectorDB 컬렉션 이름 조회 함수
    
    Args:
        category (str): 카테고리 (TERM, PRECEDENT 등)
        
    Returns:
        str: 컬렉션 이름
        
    Example:
        collection = get_collection_name('PRECEDENT')  # "precedent"
    """
    return VECTOR_DB_COLLECTIONS.get(category, '')

def is_valid_category(category: str) -> bool:
    """
    유효한 분류 카테고리인지 확인
    
    Args:
        category (str): 분류 결과
        
    Returns:
        bool: 유효 여부
    """
    return category and category.lower() in VALID_CATEGORIES

def get_response_header(category: str) -> str:
    """
    카테고리별 응답 헤더 조회
    
    Args:
        category (str): 카테고리
        
    Returns:
        str: 응답 헤더
    """
    category_upper = category.upper() if category else 'GENERAL'
    return RESPONSE_HEADERS.get(category_upper, RESPONSE_HEADERS['GENERAL'])
