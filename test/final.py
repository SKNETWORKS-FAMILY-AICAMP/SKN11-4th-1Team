#!/usr/bin/env python
# coding: utf-8

# # Variable

# In[ ]:


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

# ### IMPORT

# In[ ]:


from langchain.schema import Document
import json


# ### Function

# In[ ]:


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

    # def normalize(item):
    #     return json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)

    # for law_name, content in data_dict.items():
    #     if isinstance(content, dict):
    #         for clause, text in content.items():
    #             lines = [normalize(x) for x in (text if isinstance(text, list) else [text])]
    #             full_text = f"{law_name} {clause}\n" + "\n".join(lines)
    #             documents.append(Document(page_content=full_text, metadata={"type": "load_traffic_law"}))
    #     else:
    #         lines = [normalize(x) for x in (content if isinstance(content, list) else [content])]
    #         full_text = f"{law_name}\n" + "\n".join(lines)
    #         documents.append(Document(page_content=full_text, metadata={"type": "load_traffic_law"}))
    
    # return documents
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




# 전체 JSON 문서화
# def convert_all_docs():
#     term_docs = convert_term_to_docs(load_json(FILE_PATH['TERM']))
#     modifier_docs = convert_list_to_documents(load_json(FILE_PATH['MODIFIER']), 'modifier')
#     precedent_docs = convert_precedent_to_docs(load_json(FILE_PATH['PRECEDENT']))
#     car_case_docs = convert_car_case_to_docs(load_json(FILE_PATH['CAR_CASE']))
#     load_traffic_law_docs = convert_load_traffic_law_to_docs(load_json(FILE_PATH['LOAD_TRAFFIC_LAW']))

#     return term_docs + modifier_docs + precedent_docs + car_case_docs + load_traffic_law_docs


# ### Make Document

# In[ ]:


# 전체 문서화
# all_docs = convert_all_docs()

term_docs = convert_term_to_docs(load_json(FILE_PATH['TERM']))
precedent_docs = convert_precedent_to_docs(load_json(FILE_PATH['PRECEDENT']))
load_traffic_law_docs = convert_traffic_law_to_docs(load_json(FILE_PATH['LOAD_TRAFFIC_LAW']))

car_case_docs = convert_car_case_to_docs(load_json(FILE_PATH['CAR_CASE']))
modifier_docs = convert_list_to_documents(load_json(FILE_PATH['MODIFIER']), 'modifier')
accident_docs = car_case_docs + modifier_docs


# # 2. Vector DB 저장

# ### IMPORT

# In[ ]:


from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


# ### Embedding Model

# In[ ]:


# 임베딩 모델
embedding_model = OpenAIEmbeddings(model='text-embedding-3-large')


# ### 각 문서별 Collection 나눠 저장

# In[ ]:


# Document -> Vector DB 저장
def docs_to_chroma_db(docs, collection_name):
    db = Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory=FILE_PATH['VECTOR_DB'],
        collection_name=collection_name
    )
    return db


# In[ ]:


# ChromaDB에 저장
term_db = docs_to_chroma_db(term_docs, VECTOR_DB_COLLECTION['TERM'])
precedent_db = docs_to_chroma_db(precedent_docs, VECTOR_DB_COLLECTION['PRECEDENT'])
load_traffic_law_db = docs_to_chroma_db(load_traffic_law_docs, VECTOR_DB_COLLECTION['LOAD_TRAFFIC_LAW'])

car_case_db = docs_to_chroma_db(car_case_docs + modifier_docs, VECTOR_DB_COLLECTION['CAR_CASE'])


# In[ ]:


# from langchain_text_splitters import RecursiveCharacterTextSplitter

# # 1. 청크 크기 조정 (500~1000 권장)
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=500,
#     chunk_overlap=100,
#     length_function=len,
#     separators=["\n\n", "\n", "(?<=\\. )", " ", ""],
#     is_separator_regex=True,
# )

# # 2. 문서 분할
# all_splits = text_splitter.split_documents(all_docs)

# # 3. 임베딩 모델 ()
# embedding_model = OpenAIEmbeddings(model='text-embedding-3-large')

# # 4. Chroma DB에 배치 처리로 저장
# batch_size = 100  # 한 번에 처리할 청크 수
# vectorstore = Chroma.from_documents(
#     documents=all_splits[:batch_size],  # 첫 배치
#     embedding=embedding_model,
#     persist_directory=FILE_PATH['VECTOR_DB']
# )

# # 남은 청크를 순차적으로 추가 
# for i in range(0, len(all_splits), batch_size):
#     try:
#         batch = all_splits[i:i+batch_size]
#         vectorstore.add_documents(batch)
#         vectorstore.persist()  # 매 배치 후 즉시 저장
#     except Exception as e:
#         print(f"배치 {i}~{i+batch_size} 저장 실패: {e}")

# vectorstore.persist()


# # 사용자 목적에 따른 LLM 수행동작 분리

# ### IMPORT

# In[ ]:


# 기능 분류 및 라우팅 처리 + 사고 상황 기반 과실비율 판단 포함
import re
import numpy as np
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from langchain.chains import LLMChain

from langchain.chains import RetrievalQA
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers import SelfQueryRetriever


# In[ ]:


# 사용자 질의 목적 정의
SITUATION_CASE = {
    'GENERAL' : "general",

    'ACCIDENT' : "accident",
    'TERM' : "term",
    'PRECEDENT' : "precedent",
    'LAW' : "law",
}

GPT_4O_MODEL = ChatOpenAI(model="gpt-4o", temperature=0)
GPT_3_5_MODEL = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)


# ### Function

# In[ ]:


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


# In[ ]:


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

        print(f"\n선택된 사건 ID: {selected_id}")
        print("GPT 최종 판단 결과:\n")
        print(response)

    else:
        print("\n❌ 사건 ID를 정확히 선택하지 못했습니다.")
        print("GPT 응답:\n", selection_result)


# In[ ]:


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
        template="""아래 문서 내용을 바탕으로 사용자가 물어본 판례에 대해 정확하고 간결하게 설명해 주세요.
        
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
    return f"[판례 설명 결과]\n{result['result']}" 


# In[ ]:


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


# In[ ]:


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
        template="""아래 문서 내용을 바탕으로 사용자가 물어본 도로교통법 내용용에 대해 정확하고 간결하게 설명해 주세요.
        
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


# In[ ]:


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


# # Main

# In[ ]:


SITUATION_CASE = {
    'GENERAL' : "general",

    'ACCIDENT' : "accident",
    'TERM' : "term",
    'PRECEDENT' : "precedent",
    'LAW' : "law",
}
# 프로그램 실행
if __name__ == "__main__":
    print("🚗 교통사고 AI 분석기입니다.")
    print("사고 상황이나 알고 싶은 법률/판례 정보를 입력해 주세요.")
    user_input = input("입력 > ").strip()

    if user_input:
        category = classify_query(user_input)
        print(category)
        
        if (category == SITUATION_CASE['ACCIDENT']):
            response = process_accident(user_input)
        elif (category == SITUATION_CASE['TERM']):
            response = process_term(user_input)
        elif (category == SITUATION_CASE['PRECEDENT']):
            response = process_precedent(user_input)
        elif (category == SITUATION_CASE['LAW']):
            response = process_load_traffic_law(user_input)
        else:
            response = process_general(user_input)
        print("\n📘 결과 출력:\n")
        print(response)
    else:
        print("❌ 입력이 비어있습니다. 프로그램을 종료합니다.")


# In[ ]:




