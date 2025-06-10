"""
문서 변환 유틸리티
ui.py의 문서 변환 로직을 Django로 이식
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from langchain.schema import Document
from django.conf import settings

# constants.py에서 메타데이터 키 임포트
from ..constants import METADATA_KEYS, get_metadata_key


class DocumentProcessor:
    """
    JSON 데이터를 LangChain Document 객체로 변환하는 유틸리티
    ui.py의 변환 함수들을 Django에 맞게 이식
    """
    
    # constants.py에서 상수들을 사용
    # METADATA_KEYS는 constants.py에서 관리
    
    @staticmethod
    def load_json(file_path: str) -> Any:
        """
        JSON 파일 로드
        
        Args:
            file_path (str): JSON 파일 경로
            
        Returns:
            Any: 로드된 JSON 데이터
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 오류: {file_path} - {str(e)}")
    
    @classmethod
    def convert_term_to_docs(cls, data_list: List[Dict]) -> List[Document]:
        """
        용어 JSON → Document 변환 (ui.py와 동일)
        
        Args:
            data_list: term.json 데이터
            
        Returns:
            List[Document]: 변환된 Document 리스트
        """
        return [
            Document(
                page_content=f"{item[get_metadata_key('TERM', 'TERM')]} : {item[get_metadata_key('TERM', 'DESCRIPTION')]}",
                metadata={
                    get_metadata_key('TERM', 'TERM'): item[get_metadata_key('TERM', 'TERM')]
                }
            ) for item in data_list
        ]
    
    @classmethod
    def convert_precedent_to_docs(cls, data_list: List[Dict]) -> List[Document]:
        """
        판례 JSON → Document 변환 (ui.py와 동일)
        
        Args:
            data_list: precedent.json 데이터
            
        Returns:
            List[Document]: 변환된 Document 리스트
        """
        return [
            Document(
                page_content=f"{item[get_metadata_key('PRECEDENT', 'COURT')]} {item[get_metadata_key('PRECEDENT', 'CASE_ID')]} : {item[get_metadata_key('PRECEDENT', 'CONTENT')]}",
                metadata={
                    get_metadata_key('PRECEDENT', 'COURT'): item[get_metadata_key('PRECEDENT', 'COURT')],
                    get_metadata_key('PRECEDENT', 'CASE_ID'): item[get_metadata_key('PRECEDENT', 'CASE_ID')],
                }
            ) for item in data_list
        ]
    
    @classmethod
    def convert_car_case_to_docs(cls, data_list: List[Dict]) -> List[Document]:
        """
        차대차 사고 JSON → Document 변환 (ui.py와 동일)
        
        Args:
            data_list: car_to_car.json 데이터
            
        Returns:
            List[Document]: 변환된 Document 리스트
        """
        documents = []

        def safe_value(value):
            """null 값 및 복합 타입 안전 처리"""
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
            reason = item.get(get_metadata_key('ACCIDENT_CASE', 'REASON'))
            if isinstance(reason, list):
                reason = "\\n".join(map(str, reason))

            metadata = {
                "type": "car_case",
                "id": safe_value(item.get(get_metadata_key('ACCIDENT_CASE', 'CASE_ID'))),
                "title": safe_value(item.get(get_metadata_key('ACCIDENT_CASE', 'CASE_TITLE'))),
                "situation": safe_value(item.get(get_metadata_key('ACCIDENT_CASE', 'CASE_SITUATION'))),
                "base_ratio": safe_value(item.get(get_metadata_key('ACCIDENT_CASE', 'BASE_RATIO'))),
                "modifiers": safe_value(item.get(get_metadata_key('ACCIDENT_CASE', 'MODIFIERS'))),
                "load_traffic_law": safe_value(item.get(get_metadata_key('ACCIDENT_CASE', 'LAW_REFERENCES'))),
                "precedent": safe_value(item.get(get_metadata_key('ACCIDENT_CASE', 'PRECEDENT'))),
                "reason": safe_value(reason)
            }

            documents.append(Document(page_content=content, metadata=metadata))

        return documents
    
    @classmethod
    def convert_traffic_law_to_docs(cls, data_dict: Dict) -> List[Document]:
        """
        도로교통법 JSON → Document 변환 (traffic_law_rag.json 대응)
        새로운 구조: articles → subsections → nested subsections
        
        Args:
            data_dict: traffic_law_rag.json 데이터
            
        Returns:
            List[Document]: 변환된 Document 리스트
        """
        documents = []
        
        # articles 리스트 가져오기
        articles = data_dict.get('articles', [])
        
        for article in articles:
            article_title = article.get('title', '')
            article_content = article.get('content', '')
            article_id = article.get('id', '')
            
            # 조문 번호 추출 (예: "제5조(신호 또는 지시에 따를 의무)" → "제5조")
            article_number = article_title.split("(")[0].strip() if "(" in article_title else article_title.strip()
            
            # 조문명 추출 (예: "신호 또는 지시에 따를 의무")
            article_name = ""
            if "(" in article_title and ")" in article_title:
                article_name = article_title.split("(")[1].replace(")", "").strip()
            
            # 메인 조문 Document 생성
            main_metadata = {
                "type": "article",
                "article_id": article_id,
                "article_title": article_title,
                "article_number": article_number,
                "article_name": article_name,
                "content": article_content
            }
            
            # 메인 조문 컨텐츠 생성
            main_content = f"{article_title}\n{article_content}"
            
            documents.append(Document(
                page_content=main_content,
                metadata=main_metadata
            ))
            
            # subsections 처리
            for subsection in article.get('subsections', []):
                subsection_id = subsection.get('id', '')
                subsection_title = subsection.get('title', '')
                subsection_content = subsection.get('content', '')
                items = subsection.get('items', [])
                keywords = subsection.get('keywords', [])
                
                # 중첩된 subsections 처리 (예: 제13조의 2)
                nested_subsections = subsection.get('subsections', [])
                
                # items 및 키워드 처리
                full_content = subsection_content
                
                if items:
                    full_content += "\n\n세부 내용:\n" + "\n".join(f"- {item}" for item in items)
                
                # 중첩된 subsections 처리
                if nested_subsections:
                    for nested in nested_subsections:
                        nested_title = nested.get('title', '')
                        nested_content = nested.get('content', '')
                        nested_items = nested.get('items', [])
                        nested_keywords = nested.get('keywords', [])
                        
                        full_content += f"\n\n{nested_title}:\n{nested_content}"
                        
                        if nested_items:
                            full_content += "\n" + "\n".join(f"  - {item}" for item in nested_items)
                        
                        # 중첩된 항목의 독립 Document 생성
                        nested_metadata = {
                            "type": "nested_subsection",
                            "article_id": article_id,
                            "article_title": article_title,
                            "article_number": article_number,
                            "article_name": article_name,
                            "parent_subsection_id": subsection_id,
                            "parent_subsection_title": subsection_title,
                            "subsection_id": nested.get('id', ''),
                            "subsection_title": nested_title,
                            "content": nested_content,
                            "keywords": ", ".join(nested_keywords) if nested_keywords else ""
                        }
                        
                        nested_content_full = f"{nested_title}\n{nested_content}"
                        if nested_items:
                            nested_content_full += "\n" + "\n".join(f"- {item}" for item in nested_items)
                        
                        documents.append(Document(
                            page_content=nested_content_full,
                            metadata=nested_metadata
                        ))
                
                # 메인 subsection 메타데이터
                subsection_metadata = {
                    "type": "subsection",
                    "article_id": article_id,
                    "article_title": article_title,
                    "article_number": article_number,
                    "article_name": article_name,
                    "subsection_id": subsection_id,
                    "subsection_title": subsection_title,
                    "content": full_content,
                    "keywords": ", ".join(keywords) if keywords else ""
                }
                
                documents.append(Document(
                    page_content=f"{subsection_title}\n{full_content}",
                    metadata=subsection_metadata
                ))
        
        return documents
    
    @classmethod
    def convert_list_to_documents(cls, data_list: List[Dict], doc_type: str) -> List[Document]:
        """
        리스트형 JSON → Document 변환 (modifier용)
        
        Args:
            data_list: 리스트 형태의 JSON 데이터
            doc_type: 문서 타입
            
        Returns:
            List[Document]: 변환된 Document 리스트
        """
        return [
            Document(page_content=json.dumps(item, ensure_ascii=False), metadata={"type": doc_type})
            for item in data_list
        ]
    
    @classmethod
    def load_and_convert_all_documents(cls, metadata_path: Path) -> Dict[str, List[Document]]:
        """
        모든 JSON 파일을 로드하고 Document로 변환
        modifier.json은 VectorDB에 저장하지 않고 프롬프트에서 직접 사용
        
        Args:
            metadata_path: metadata 폴더 경로
            
        Returns:
            Dict[str, List[Document]]: 카테고리별 Document 리스트
        """
        # 파일 경로 정의 (modifier.json 제외)
        file_paths = {
            'term': metadata_path / 'term.json',
            'precedent': metadata_path / 'precedent.json',
            'car_case': metadata_path / 'car_to_car.json',
            'law': metadata_path / 'traffic_law_rag.json',
            # modifier.json은 VectorDB에 저장하지 않음 (프롬프트에서 직접 사용)
        }
        
        # 각 파일 로드 및 변환
        documents = {}
        
        try:
            # term 문서
            term_data = cls.load_json(str(file_paths['term']))
            documents['term'] = cls.convert_term_to_docs(term_data)
            
            # precedent 문서
            precedent_data = cls.load_json(str(file_paths['precedent']))
            documents['precedent'] = cls.convert_precedent_to_docs(precedent_data)
            
            # car_case 문서 (modifier 없이 car_to_car만)
            car_case_data = cls.load_json(str(file_paths['car_case']))
            documents['car_case'] = cls.convert_car_case_to_docs(car_case_data)
            
            # law 문서 (도로교통법)
            law_data = cls.load_json(str(file_paths['law']))
            documents['law'] = cls.convert_traffic_law_to_docs(law_data)
            
            return documents
            
        except Exception as e:
            raise Exception(f"문서 로드 및 변환 중 오류 발생: {str(e)}")
    
    @classmethod
    def get_document_stats(cls, documents: Dict[str, List[Document]]) -> Dict[str, Any]:
        """
        변환된 문서들의 통계 정보
        
        Args:
            documents: 카테고리별 Document 딕셔너리
            
        Returns:
            Dict[str, Any]: 통계 정보
        """
        stats = {}
        total_docs = 0
        
        for category, docs in documents.items():
            doc_count = len(docs)
            total_docs += doc_count
            
            # 평균 콘텐츠 길이 계산
            if docs:
                avg_length = sum(len(doc.page_content) for doc in docs) / doc_count
                sample_metadata = docs[0].metadata.keys() if docs else []
            else:
                avg_length = 0
                sample_metadata = []
            
            stats[category] = {
                'document_count': doc_count,
                'avg_content_length': round(avg_length, 2),
                'metadata_fields': list(sample_metadata)
            }
        
        stats['total'] = {
            'total_documents': total_docs,
            'categories': list(documents.keys())
        }
        
        return stats


# 편의 함수들
def load_documents_from_metadata(metadata_path: str = None) -> Dict[str, List[Document]]:
    """
    metadata 폴더에서 모든 문서를 로드하고 변환하는 편의 함수
    
    Args:
        metadata_path: metadata 폴더 경로 (None이면 settings에서 가져옴)
        
    Returns:
        Dict[str, List[Document]]: 카테고리별 Document 리스트
    """
    if metadata_path is None:
        metadata_path = getattr(settings, 'METADATA_PATH', Path(__file__).parent.parent.parent.parent / 'metadata')
    else:
        metadata_path = Path(metadata_path)
    
    return DocumentProcessor.load_and_convert_all_documents(metadata_path)


def get_sample_documents(category: str, count: int = 3) -> List[Document]:
    """
    특정 카테고리의 샘플 문서를 가져오는 함수
    
    Args:
        category: 카테고리명 ('term', 'precedent', 'car_case', 'law')
        count: 가져올 문서 수
        
    Returns:
        List[Document]: 샘플 Document 리스트
    """
    documents = load_documents_from_metadata()
    if category in documents:
        return documents[category][:count]
    return []
