import re
import os
import numpy as np
from langchain.schema import Document
import json
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from langchain.chains import LLMChain
from langchain.chains import RetrievalQA
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers import SelfQueryRetriever
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import streamlit as st
from streamlit_chat import message
from pathlib import Path
import base64
import time

from dotenv import load_dotenv
load_dotenv()

# 파일 경로
FILE_PATH = {
    'TERM' : '../metadata/term.json',                            # 용어
    'LOAD_TRAFFIC_LAW' : '../metadata/load_traffic_law.json',    # 도로교통법
    'MODIFIER' : '../metadata/modifier.json',                    # 수정요소
    'CAR_CASE' : '../metadata/car_to_car.json',                  # 차 s차 사고 케이스
    'PRECEDENT' : '../metadata/precedent.json',                  # 참고 판례

    'VECTOR_DB' : '../vector_db',                                # 벡터 DB 저장경로
}

# 벡터DB 컬렉션 이름 정의
VECTOR_DB_COLLECTION = {
    'TERM' : "term",
    'LOAD_TRAFFIC_LAW' : "load_traffic_law",
    'MODIFIER' : "modifier",
    'CAR_CASE' : "car_case",
    'PRECEDENT' : "precedent",
}

# JSON 파일 KEY 값 정의
METADATA_KEY = {
    'ACCIDENT_CASE' : {
        'CASE_ID' : "사건 ID",
        'CASE_TITLE' : "사건 제목",
        'CASE_SITUATION' : "사고상황",
        'BASE_RATIO' : "기본 과실비율",
        'MODIFIERS' : "케이스별 과실비율 조정예시",
        'LAW_REFERENCES' : "관련 법규",
        'PRECEDENT' : "참고 판례",
        'REASON' : "기본 과실비율 해설",
    },

    'PRECEDENT' : {
        'COURT' : "court",
        'CASE_ID' : "case_id",
        'CONTENT' : "content",
    },

    'TERM' : {
        'TERM' : "term",
        'DESC' : "desc",
    }
}


# # 1. Documentation (문서화)
# ### Function

# JSON 로드 함수
def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)



# 리스트형 JSON -> Document 변환 (modifier)
def convert_list_to_documents(data_list, doc_type):
    return [
        Document(page_content=json.dumps(item, ensure_ascii=False), metadata={"type": doc_type})
        for item in data_list
    ]



# precedent JSON -> Document 변환
def convert_precedent_to_docs(data_list):
    return [
        Document(
            page_content=f"{item[METADATA_KEY['PRECEDENT']['COURT']]} {item[METADATA_KEY['PRECEDENT']['CASE_ID']]} : {item[METADATA_KEY['PRECEDENT']['CONTENT']]}",
            metadata={
                METADATA_KEY['PRECEDENT']['COURT']: item[METADATA_KEY['PRECEDENT']['COURT']],
                METADATA_KEY['PRECEDENT']['CASE_ID']: item[METADATA_KEY['PRECEDENT']['CASE_ID']],
            }
        ) for item in data_list
    ]



# term JSON -> Document 변환
def convert_term_to_docs(data_list):
    return [
        Document(
            page_content=f"{item[METADATA_KEY['TERM']['TERM']]} : {item[METADATA_KEY['TERM']['DESC']]}",
            metadata={
                METADATA_KEY['TERM']['TERM']: item[METADATA_KEY['TERM']['TERM']]
            }
        ) for item in data_list
    ]


# car_case JSON -> Document 변환
def convert_car_case_to_docs(data_list):
    documents = []

    def safe_value(value):
        if isinstance(value, list):
            return ", ".join(map(str, value))
        elif isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        elif value is None:
            return ""  # null도 허용 안 되므로 빈 문자열로 처리
        else:
            return str(value)

    for item in data_list:
        if not isinstance(item, dict):
            continue

        # page_content는 원본 전체 JSON 문자열
        content = json.dumps(item, ensure_ascii=False)

        # 기본 과실비율 해설이 리스트일 수 있음 → 문자열로 병합
        reason = item.get(METADATA_KEY['ACCIDENT_CASE']['REASON'])
        if isinstance(reason, list):
            reason = "\n".join(map(str, reason))

        metadata = {
            "type": "car_case",
            "id": safe_value(item.get(METADATA_KEY['ACCIDENT_CASE']['CASE_ID'])),
            "title": safe_value(item.get(METADATA_KEY['ACCIDENT_CASE']['CASE_TITLE'])),
            "situation": safe_value(item.get(METADATA_KEY['ACCIDENT_CASE']['CASE_SITUATION'])),
            "base_ratio": safe_value(item.get(METADATA_KEY['ACCIDENT_CASE']['BASE_RATIO'])),
            "modifiers": safe_value(item.get(METADATA_KEY['ACCIDENT_CASE']['MODIFIERS'])),
            "load_traffic_law": safe_value(item.get(METADATA_KEY['ACCIDENT_CASE']['LAW_REFERENCES'])),
            "precedent": safe_value(item.get(METADATA_KEY['ACCIDENT_CASE']['PRECEDENT'])),
            "reason": safe_value(reason)
        }

        documents.append(Document(page_content=content, metadata=metadata))

    return documents


# 도로교통법 law JSON → 문서화
def convert_traffic_law_to_docs(data_dict):
    documents = []
    for article_title, article_content in data_dict.items():
        main_clause = article_title.split("(")[0].strip()
        clause_name = article_title.split("(")[1].replace(")", "").strip()
        for sub_clause, texts in article_content.items():
            clause_num = int(sub_clause.replace("항", ""))
            content = " ".join(texts)
            metadata = {
                "법률조문": main_clause,
                "조항명": clause_name,
                "항번호": clause_num,
                "전체참조": f"{main_clause} {sub_clause}"
            }
            documents.append(Document(page_content=content, metadata=metadata))
    
    return documents
# ### Make Document
# 전체 문서화

term_docs = convert_term_to_docs(load_json(FILE_PATH['TERM']))
precedent_docs = convert_precedent_to_docs(load_json(FILE_PATH['PRECEDENT']))
load_traffic_law_docs = convert_traffic_law_to_docs(load_json(FILE_PATH['LOAD_TRAFFIC_LAW']))
car_case_docs = convert_car_case_to_docs(load_json(FILE_PATH['CAR_CASE']))
modifier_docs = convert_list_to_documents(load_json(FILE_PATH['MODIFIER']), 'modifier')
accident_docs = car_case_docs + modifier_docs


#  2. Vector DB 저장

# 임베딩 모델
embedding_model = OpenAIEmbeddings(model='text-embedding-3-large')


# 각 문서별 Collection 나눠 저장

# Document -> Vector DB 저장 / 로드
def docs_to_chroma_db(docs, collection_name):
    # Chroma의 persist_directory 내부에 collection_name 디렉토리가 있는지 확인
    collection_path = os.path.join(FILE_PATH['VECTOR_DB'], collection_name)
    collection_exists = os.path.exists(FILE_PATH['VECTOR_DB']) and any(
        collection_name in d for d in os.listdir(FILE_PATH['VECTOR_DB'])
    )
    
    # 컬렉션이 있으면 불러오기 (LangChain Chroma로도 불러올 수 있음)
    if collection_exists:
        print(f"컬렉션 '{collection_name}'이(가) 존재하여 불러왔습니다.")
        return Chroma(
            persist_directory=FILE_PATH['VECTOR_DB'],
            embedding_function=embedding_model,
            collection_name=collection_name
        )
        
    # 컬렉션이 없으면 documents와 embedding_model이 필요
    else:
        print(f"컬렉션 '{collection_name}'이(가) 없어 새로 생성하고 저장했습니다.")

        # 임베딩 후 컬렉션 생성 및 저장
        return Chroma.from_documents(
            documents=docs,
            embedding=embedding_model,
            persist_directory=FILE_PATH['VECTOR_DB'],
            collection_name=collection_name
        )


# ChromaDB에 저장
term_db = docs_to_chroma_db(term_docs, VECTOR_DB_COLLECTION['TERM'])
precedent_db = docs_to_chroma_db(precedent_docs, VECTOR_DB_COLLECTION['PRECEDENT'])
load_traffic_law_db = docs_to_chroma_db(load_traffic_law_docs, VECTOR_DB_COLLECTION['LOAD_TRAFFIC_LAW'])

car_case_db = docs_to_chroma_db(car_case_docs + modifier_docs, VECTOR_DB_COLLECTION['CAR_CASE'])


# 사용자 질의 목적 정의
SITUATION_CASE = {
    'GENERAL' : "general",

    'ACCIDENT' : "accident",
    'TERM' : "term",
    'PRECEDENT' : "precedent",
    'LAW' : "law",
}

GPT_4O_MODEL = ChatOpenAI(model="gpt-4o-mini", temperature=0)
GPT_3_5_MODEL = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)


# 기능

# 질의 목적 구분
def classify_query(user_input: str) -> str:
    classification_prompt = PromptTemplate.from_template("""
너는 교통사고 상담 챗봇의 질문 분류기야.

사용자의 질문이 다음 중 어떤 유형인지 판단해:

1. 사고 상황 판단 질문 (예: 사고 경위 설명, 과실비율 요청)
2. 도로교통법률 설명 질문 (예: 도로교통법 조항 정의, 도로교통법 제5조 1항 등)
3. 판례 설명 질문 (예: 판례 번호, 서울고등법원 2002나57692 등)
4. 교통사고 용어 설명 질문 (예: 용어, '과실' 정의, '회전교차로' 정의 등)
5. 일반 질문 (예: "너는 누구야?", "날씨 어때?", "GPT란 뭐야?" 등 교통사고와 무관한 질문)

출력은 반드시 아래 중 하나만 해:
- accident
- precedent
- law
- term
- general

다른 말 없이 위 다섯 단어 중 하나만 정확히 출력해.

질문:
{question}

출력:
""")
    
    prompt = classification_prompt.format(question=user_input)
    result = GPT_4O_MODEL.invoke(prompt)

    return result.content.strip().lower()

# 질의 목적 : 사고 과실 비율
# SITUATION_CASE['ACCIDENT'] = "accident"
def process_accident(user_input: str) -> str:
    # car_case 문서 필터링 및 사고상황 추출
    case_texts = [doc.metadata.get("situation", "") for doc in car_case_docs if doc.metadata.get("situation")]

    # ko-sbert 임베딩
    embed_model = SentenceTransformer("jhgan/ko-sbert-nli")
    case_embeddings = embed_model.encode(case_texts)

    # 사용자 입력
    query_embedding = embed_model.encode([user_input])[0]

    # 코사인 유사도 계산 및 Top-3 추출
    cos_similarities = np.dot(case_embeddings, query_embedding) / (
        np.linalg.norm(case_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    top_k_idx = np.argsort(cos_similarities)[-3:][::-1]
    top_candidates = [car_case_docs[i] for i in top_k_idx]

    # 판례 요약 출력
    def summarize(doc, idx):
        return f"{idx+1}. 사건 ID: {doc.metadata.get('id')}\n사고상황: {doc.metadata.get('situation')}"

    case_summaries = "\n\n".join([summarize(doc, i) for i, doc in enumerate(top_candidates)])

    # GPT - 사건ID 선택(3개 중에 하나 판단)
    selection_prompt = PromptTemplate(
        input_variables=["user_input", "case_summaries"],
        template="""
    [사용자 입력 사고 상황]
    {user_input}

    [후보 판례 3건]
    {case_summaries}

    위 3건 중, 사고의 전개 구조(예: 직진 vs 좌회전, 도로 외 장소에서 진입, 교차로 내 진입 여부 등)가 사용자 상황과 가장 유사한 **사건 ID** 하나를 선택하세요.

    반드시 다음 기준을 고려하세요:
    - 차량들의 위치와 진입 경로가 유사한가?
    - 사고 발생 지점과 방향이 유사한가?
    - 각 차량의 신호·우선권 상황이 유사한가?|
    - 도로 구조(교차로, 신호 유무, 도로 외 장소 등)가 유사한가?

    출력 형식 (고정):
    - 사건 ID: 차XX-X
    - 판단 근거: (선택한 이유. 단순 유사성이 아니라, 어떤 지점이 유사했는지 명확히 설명할 것)
    """
    )
    
    selection_chain = LLMChain(llm=GPT_4O_MODEL, prompt=selection_prompt)
    selection_result = selection_chain.run(user_input=user_input, case_summaries=case_summaries)

    # 사건 ID 파싱 및 선택
    match = re.search(r"사건 ID[:：]?\s*(차\d{1,2}-\d{1,2})", selection_result)
    selected_id = match.group(1) if match else None
    selected_doc = next((doc for doc in car_case_docs if doc.metadata.get("id") == selected_id), None)

    # 최종 판단 GPT 프롬프트(선택한 사건 object 내에서 과실비율 판단)
    if selected_doc:
        # 해당 사건 관련 보조 문서들을 함께 전달
        related_docs = [doc for doc in car_case_docs if selected_id in doc.page_content]
        context_str = "\n\n".join(doc.page_content for doc in related_docs)

        final_prompt = PromptTemplate(
            input_variables=["user_input", "case_data"],
            template="""
    너는 교통사고 과실 판단 전문가야.
    아래 '사고 상황'을 분석하여 핵심 요소를 구조화하고, 반드시 문서 내에서 가장 유사한 사례(case)를 찾아 과실비율을 판단해줘.

    ---

    사고 상황 원문:
    {user_input}

    ➤ 사고 상황 요약 (다음 항목 기준):
    - A차량 신호 및 진행 방식:
    - B차량 신호 및 진행 방식:
    - 충돌 방식 및 위치:
    - 교차로/신호기 유무 등 도로 환경:

    문서:
    {case_data}

    출력 형식 (고정):
    1. 과실비율: A차량 xx% vs B차량 xx%
    2. 판단 근거 요약
    3. 적용 법률:
    - [법률명] 제[조]조 [항]
    4. 참고 판례:
    - [법원명] [사건번호]

    조건:
    - 반드시 문서 내 유사 사례를 기반으로 판단해야 해.
    - 유사 사례와 현재 사고 상황이 정확히 일치하지 않으면, 차이점을 명시하고 과실비율 조정 이유를 설명해.
    - 추측이나 상식은 사용하지 말고, 문서 정보만을 기반으로 판단해.
    """
        )

        chain = LLMChain(llm=GPT_4O_MODEL, prompt=final_prompt)
        response = chain.run(user_input=user_input, case_data=context_str)

        return response  # ✅ Streamlit에 반환

    else:
        return f"❌ 사건 ID를 정확히 선택하지 못했습니다.\nGPT 응답:\n{selection_result}"


# 질의 목적 : 판례 검색
# SITUATION_CASE['PRECEDENT'] = "precedent"
def process_precedent(user_input):
    # 메타데이터 필드 정의 (필수!)
    metadata_field_info = [
        AttributeInfo(
            name=METADATA_KEY['PRECEDENT']['COURT'],
            description="판례의 법원명 (예: 대법원, 서울고등법원 등)",
            type="string"
        ),
        AttributeInfo(
            name=METADATA_KEY['PRECEDENT']['CASE_ID'],
            description="사건번호 (예: 92도2077)",
            type="string"
        )
    ]

    # SelfQueryRetriever 생성 (metadata_field_info 필수)
    self_retriever = SelfQueryRetriever.from_llm(
        llm=GPT_4O_MODEL,
        vectorstore=precedent_db,
        document_contents="교통사고 판례 데이터",
        metadata_field_info=metadata_field_info  # ✅ 반드시 필요
    )


    # 프롬프트 구성
    prompt = PromptTemplate(
    input_variables=["question", "context"],
    template="""
너는 교통사고 판례를 요약 정리해주는 전문가야.

아래 문서(context)를 참고하여 사용자의 질문에 대해 관련된 판례를 설명해줘.  
각 판례는 아래와 같은 **깔끔한 형식**으로 나열해 줘.
참고한 **다른** 판례가 있다면 따로 출력해줘 (예시:서울중앙지방법원 2015나60480)

---
질문:
{question}

문서:
{context}
---

출력 형식 (고정):

설명: [{{법원명}}에는 다음과 같은 판례가 있습니다!]

1. 사건번호: 20XX나XXXXX  
    ▪ 사고 유형: (예: 신호등이 있는 교차로에서 발생한 좌회전 차량 간의 충돌 사고)  
    ▪ 법적 판단 요지: (예: A차가 직진, B차가 적색에서 좌회전하며 충돌)  
    ▪ 과실비율: A차량 xx%, B차량 xx%

2. 사건번호: 20XX가단XXXXX  
    ▪ 사고 유형: ...  
    ▪ 법적 판단 요지: ...  
    ▪ 과실비율: ...

...

- 참고한 판례: [{{법원명}} 판례]

조건:
- 판례는 최대 3~5개까지만 출력하세요.
- 사건번호, 사고 유형, 판단 요지, 과실비율을 항목별로 줄바꿈과 들여쓰기를 사용해 깔끔하게 정리하세요.
- 사건번호가 중복되면 한 번만 출력하세요.
- 문서에 없는 정보는 임의로 만들지 마세요.

답변:
"""
)
    
    # QA 체인 구성 및 실행
    qa_chain = RetrievalQA.from_chain_type(
        llm=GPT_4O_MODEL,
        retriever=self_retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa_chain.invoke({"query": user_input})
    return f"[판례 설명 결과]\n{result['result']}" 


# 질의 목적 : 용어 검색
# SITUATION_CASE['TERM'] = "term"
def process_term(user_input):
    # 메타데이터 필드 정의 (필수!)
    metadata_field_info = [
        AttributeInfo(
            name=METADATA_KEY['TERM']['TERM'],
            description="교통사고 관련 용어 (예: 보행자전용도로, 차마 등)",
            type="string"
        )
    ]

    # SelfQueryRetriever 생성 (metadata_field_info 필수)
    self_retriever = SelfQueryRetriever.from_llm(
        llm=GPT_4O_MODEL,
        vectorstore=term_db,
        document_contents="교통사고 관련 용어 데이터",
        metadata_field_info=metadata_field_info  # ✅ 반드시 필요
    )


    # 프롬프트 구성
    prompt = PromptTemplate(
        input_variables=["question", "context"],
        template="""아래 문서 내용을 바탕으로 사용자가 물어본 용어에 대해 정확하고 간결하게 설명해 주세요.
        
        질문: {question}
        
        문서: {context}

        답변 형식:
        - 용어/조항 정의: [정확한 설명]
        - 출처가 명시된 경우: 관련 법률/조문 번호/판례명을 반드시 포함

        답변:
        """
    )

    # QA 체인 구성 및 실행
    qa_chain = RetrievalQA.from_chain_type(
        llm=GPT_4O_MODEL,
        retriever=self_retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa_chain.invoke({"query": user_input})
    return f"[용어 설명 결과]\n{result['result']}" 

# 질의 목적 : 도로교통법법 검색
# SITUATION_CASE['TERM'] = "term"
def process_load_traffic_law(user_input):
    # 메타데이터 필드 정의 (필수!)
    metadata_field_info = [
    AttributeInfo(
        name="법률조문",
        description="법률의 조문 번호 (예: 제5조, 제8조)",
        type="string"
    ),
    AttributeInfo(
        name="조항명",
        description="조항의 제목 (예: 신호 또는 지시에 따를 의무, 보행자의 통행)",
        type="string"
    ),
    AttributeInfo(
        name="항번호",
        description="조항 내 항 번호 (예: 1, 2, 3, ...)",
        type="integer"
    ),
    AttributeInfo(
        name="전체참조",
        description="조문과 항을 합친 전체 참조 (예: 제5조 1항)",
        type="string"
    ),
]

    # SelfQueryRetriever 생성 (metadata_field_info 필수)
    self_retriever = SelfQueryRetriever.from_llm(
        llm=GPT_4O_MODEL,
        vectorstore=load_traffic_law_db,
        document_contents="도로교통법 조문 및 항의 주요 내용",
        metadata_field_info=metadata_field_info  # ✅ 반드시 필요
    )


    # 프롬프트 구성
    prompt = PromptTemplate(
        input_variables=["question", "context"],
        template="""아래 문서 내용을 바탕으로 사용자가 물어본 도로교통법 내용에 대해 정확하고 간결하게 설명해 주세요.
        
        질문: {question}
        
        문서: {context}

        답변 형식:
        - 용어/조항 정의: [정확한 설명]
        - 출처가 명시된 경우: 관련 법률/조문 번호/판례명을 반드시 포함

        답변:
        """
    )

    # QA 체인 구성 및 실행
    qa_chain = RetrievalQA.from_chain_type(
        llm=GPT_4O_MODEL,
        retriever=self_retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa_chain.invoke({"query": user_input})
    return f"[도로교통법로교통법 설명 결과]\n{result['result']}" 


def process_general(user_input):
    general_prompt = PromptTemplate.from_template("""
너는 교통사고 상담 전문 AI 챗봇이야.

교통사고 판례, 도로교통법, 법률 용어 등에 대해 사용자에게 도움을 주는 역할을 해.

하지만 아래와 같은 상황에서도 혼자 유연하게 답변해야 해:
- 문서에서 찾을 수 없는 용어, 법률 조항, 판례 번호가 나왔을 경우
- 문서에 없는 질문이라도, 너의 지식과 상식으로 설명이 가능한 경우
- 문서와 상관없는 일반적인 질문 (예: 자기소개, 인공지능, 날씨 등)

이럴 땐 “문서에 포함되어 있지 않습니다” 같은 말은 하지 말고,
AI 챗봇으로서 너의 지식으로 최대한 정확하고 자연스럽게 답변해줘.

질문:
{question}

답변:
""")    
    
    prompt = general_prompt.format(question=user_input)    
    result = GPT_3_5_MODEL.invoke(prompt)
    
    return result.content.strip()


#  Main

SITUATION_CASE = {
    'GENERAL' : "general",

    'ACCIDENT' : "accident",
    'TERM' : "term",
    'PRECEDENT' : "precedent",
    'LAW' : "law",
}

# 페이지 기본 설정
st.set_page_config(page_title="과실비율 챗봇", page_icon="🤖", layout="centered")

# ✅ 이미지 base64 인코딩 함수
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

chatbot_avatar = encode_image_to_base64("../img/chatbot.png")
main_logo = encode_image_to_base64("../img/mainlogo.png")

# ✅ 상단 타이틀 표시 (텍스트 제거, 이미지만 확대)
st.markdown(f"""
    <div style='text-align: center;'>
        <img src="{main_logo}" width="200" style="margin-bottom: 10px;"><br>
        <p style='color: gray;'>사고 상황을 입력하면 과실비율을 알려드릴게요!</p>
    </div>
""", unsafe_allow_html=True)

# ✅ 대화 기록 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        ("bot", "과실비율 판단봇입니다. 사고 상황을 설명해주세요.")
    ]

# ✅ 사용자 입력
user_input = st.chat_input("사고 상황을 입력해주세요")
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    try:
        category = classify_query(user_input)
        if category == SITUATION_CASE['ACCIDENT']:
            response = process_accident(user_input)
        elif category == SITUATION_CASE['TERM']:
            response = process_term(user_input)
        elif category == SITUATION_CASE['PRECEDENT']:
            response = process_precedent(user_input)
        elif category == SITUATION_CASE['LAW']:
            response = process_load_traffic_law(user_input)
        else:
            response = process_general(user_input)
    except Exception as e:
        response = f"⚠️ 오류가 발생했습니다: {e}"
    st.session_state.chat_history.append(("bot", response))

# ✅ 채팅 출력 (타자 효과는 마지막 응답에만 적용)
for i, (sender, msg) in enumerate(st.session_state.chat_history):
    is_last = (i == len(st.session_state.chat_history) - 1 and sender == "bot")

    if is_last:
        container = st.empty()
        display = ""
        for char in msg:
            display += char
            container.chat_message("assistant", avatar=chatbot_avatar).write(display)
            time.sleep(0.02)
    else:
        if sender == "user":
            st.markdown(f"""
                <div style='display: flex; justify-content: flex-end; margin-top: 0.5rem;'>
                    <div style='background-color: #DCF8C6; padding: 10px 14px; border-radius: 20px; max-width: 70%; font-size: 15px; line-height: 1.5; color: #000;'>
                        😎 {msg}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            with st.chat_message("assistant", avatar=chatbot_avatar):
                st.markdown(msg)
