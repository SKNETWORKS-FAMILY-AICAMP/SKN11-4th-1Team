"""
VectorDB 관리 유틸리티
ui.py의 ChromaDB 로직을 Django로 이식 (최신 langchain-chroma 사용)
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain_chroma import Chroma  # 최신 방식
from langchain_openai import OpenAIEmbeddings
from django.conf import settings
from .document_processor import DocumentProcessor

# 로거 설정
logger = logging.getLogger(__name__)


class VectorDBManager:
    """
    ChromaDB를 사용한 벡터 데이터베이스 관리자
    ui.py의 VectorDB 로직을 Django에 맞게 이식 (최신 langchain-chroma 0.1.4)
    """
    
    # 벡터DB 컬렉션 이름 정의 (실제 생성된 컬렉션명과 일치)
    VECTOR_DB_COLLECTION = {
        'TERM': "term",
        'TRAFFIC_LAW_RAG': "traffic_law_rag",  # traffic_law_rag.json에서 생성
        'CAR_CASE': "car_case",               # car_to_car.json에서 생성
        'PRECEDENT': "precedent",             # precedent.json에서 생성
    }
    
    # 카테고리별 컬렉션 매핑 (ai_classifier.py에서 사용)
    COLLECTIONS = {
        'term': 'term',                       # 용어 설명
        'law': 'traffic_law_rag',            # 도로교통법 (traffic_law_rag.json)
        'car_case': 'car_case',              # 교통사고 사례 (car_to_car.json)
        'precedent': 'precedent',            # 판례 (precedent.json)
    }
    
    def __init__(self, vector_db_path: str = None, embedding_model_name: str = 'text-embedding-3-large'):
        """
        VectorDB 매니저 초기화
        
        Args:
            vector_db_path: VectorDB 저장 경로 (None이면 settings에서 가져옴)
            embedding_model_name: OpenAI 임베딩 모델명
        """
        # VectorDB 저장 경로 설정
        if vector_db_path:
            self.vector_db_path = Path(vector_db_path)
        else:
            self.vector_db_path = getattr(
                settings, 
                'VECTOR_DB_PATH', 
                Path(__file__).parent.parent.parent / 'vector_db'
            )
        
        # 경로 생성
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # OpenAI 임베딩 모델 초기화
        try:
            self.embedding_model = OpenAIEmbeddings(
                model=embedding_model_name,
                api_key=getattr(settings, 'OPENAI_API_KEY', None)
            )
            logger.info(f"임베딩 모델 초기화 완료: {embedding_model_name}")
        except Exception as e:
            logger.error(f"임베딩 모델 초기화 실패: {str(e)}")
            raise
        
        # 초기화된 컬렉션들 캐시
        self._collection_cache = {}
        
        logger.info(f"VectorDBManager 초기화 완료 - 경로: {self.vector_db_path}")
        logger.info(f"지원 컬렉션: {list(self.COLLECTIONS.keys())} → {list(self.COLLECTIONS.values())}")
    
    def docs_to_chroma_db(self, docs: List[Document], collection_name: str) -> Chroma:
        """
        Document를 ChromaDB에 저장/로드 (배치 처리로 토큰 제한 해결)
        
        Args:
            docs: 저장할 Document 리스트
            collection_name: 컬렉션 이름
            
        Returns:
            Chroma: ChromaDB 인스턴스
        """
        try:
            # 기존 컬렉션 로드 시도
            try:
                vectorstore = Chroma(
                    persist_directory=str(self.vector_db_path),
                    embedding_function=self.embedding_model,
                    collection_name=collection_name
                )
                
                # 컬렉션에 데이터가 있는지 확인 (안전한 방법)
                try:
                    collection_count = vectorstore._collection.count()
                    if collection_count > 0:
                        logger.info(f"컬렉션 '{collection_name}'이(가) 존재하여 불러왔습니다. (문서 수: {collection_count})")
                        # 캐시에 저장
                        self._collection_cache[collection_name] = vectorstore
                        return vectorstore
                    else:
                        # 컬렉션은 있지만 비어있음
                        logger.info(f"컬렉션 '{collection_name}'이 비어있어 새로 생성합니다.")
                        raise Exception("Empty collection")
                except Exception:
                    # 컬렉션 조회 실패 시 새로 생성
                    raise Exception("Collection check failed")
                    
            except Exception:
                # 컬렉션이 없거나 비어있으면 새로 생성
                logger.info(f"컬렉션 '{collection_name}'이(가) 없어 새로 생성하고 저장했습니다.")
                
                if not docs:
                    raise ValueError(f"문서가 없어서 컬렉션 '{collection_name}'을 생성할 수 없습니다.")
                
                # 🔧 배치 처리로 대용량 데이터 처리 (토큰 제한 해결)
                batch_size = 50  # 배치 크기 (토큰 제한에 맞게 조정)
                total_docs = len(docs)
                
                if total_docs <= batch_size:
                    # 작은 데이터는 기존 방식 사용
                    vectorstore = Chroma.from_documents(
                        documents=docs,
                        embedding=self.embedding_model,
                        persist_directory=str(self.vector_db_path),
                        collection_name=collection_name
                    )
                else:
                    # 대용량 데이터는 배치 처리
                    logger.info(f"대용량 데이터 ({total_docs}개) 배치 처리 시작 - 배치 크기: {batch_size}")
                    
                    # 첫 번째 배치로 컬렉션 생성
                    first_batch = docs[:batch_size]
                    vectorstore = Chroma.from_documents(
                        documents=first_batch,
                        embedding=self.embedding_model,
                        persist_directory=str(self.vector_db_path),
                        collection_name=collection_name
                    )
                    logger.info(f"첫 번째 배치 완료: {len(first_batch)}개 문서")
                    
                    # 나머지 배치들을 순차적으로 추가
                    for i in range(batch_size, total_docs, batch_size):
                        batch = docs[i:i + batch_size]
                        vectorstore.add_documents(batch)
                        logger.info(f"배치 {i//batch_size + 1} 완료: {len(batch)}개 문서 추가 ({i + len(batch)}/{total_docs})")
                
                # 캐시에 저장
                self._collection_cache[collection_name] = vectorstore
                logger.info(f"컬렉션 '{collection_name}' 생성 완료 - 총 문서 수: {total_docs}")
                return vectorstore
                
        except Exception as e:
            logger.error(f"컬렉션 '{collection_name}' 처리 중 오류: {str(e)}")
            raise
    
    def get_vector_db(self, collection_name: str) -> Optional[Chroma]:
        """
        기존 컬렉션 로드 (ChromaDB 정확한 확인 방법)
        
        Args:
            collection_name: 컬렉션 이름
            
        Returns:
            Chroma: ChromaDB 인스턴스 (없으면 None)
        """
        # 캐시에서 먼저 확인
        if collection_name in self._collection_cache:
            return self._collection_cache[collection_name]
        
        try:
            # ChromaDB로 직접 컬렉션 로드 시도 (수정된 방식)
            vectorstore = Chroma(
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embedding_model,
                collection_name=collection_name
            )
            
            # 컬렉션에 실제 데이터가 있는지 확인
            try:
                collection_count = vectorstore._collection.count()
                if collection_count > 0:
                    # 캐시에 저장
                    self._collection_cache[collection_name] = vectorstore
                    logger.info(f"컬렉션 '{collection_name}' 로드 완료 - 문서 수: {collection_count}")
                    return vectorstore
                else:
                    logger.warning(f"컬렉션 '{collection_name}'이 비어있습니다.")
                    return None
            except Exception as e:
                logger.warning(f"컬렉션 '{collection_name}' 상태 확인 실패: {str(e)}")
                return None
                
        except Exception as e:
            logger.warning(f"컬렉션 '{collection_name}' 로드 실패: {str(e)}")
            return None
    
    def initialize_all_vector_dbs(self, metadata_path: str = None, force_rebuild: bool = False) -> Dict[str, Chroma]:
        """
        모든 카테고리의 VectorDB를 일괄 초기화
        
        Args:
            metadata_path: metadata 폴더 경로
            force_rebuild: 기존 컬렉션이 있어도 강제로 재구축
            
        Returns:
            Dict[str, Chroma]: 카테고리별 VectorDB 딕셔너리
        """
        logger.info("모든 VectorDB 초기화 시작...")
        
        try:
            # 문서 로드 및 변환
            if metadata_path:
                documents = DocumentProcessor.load_and_convert_all_documents(Path(metadata_path))
            else:
                metadata_path = getattr(settings, 'METADATA_PATH', None)
                if not metadata_path:
                    raise ValueError("metadata_path가 지정되지 않았고 settings.METADATA_PATH도 없습니다.")
                documents = DocumentProcessor.load_and_convert_all_documents(Path(metadata_path))
            
            # 카테고리별 VectorDB 생성
            vector_dbs = {}
            
            for category, docs in documents.items():
                if not docs:
                    logger.warning(f"카테고리 '{category}'에 문서가 없습니다. 건너뛰기.")
                    continue
                
                # 카테고리별 컬렉션명 매핑
                collection_name = self.COLLECTIONS.get(category, category)
                logger.info(f"카테고리 '{category}' → 컬렉션 '{collection_name}' 매핑")
                
                # 기존 컬렉션 확인
                if not force_rebuild:
                    existing_db = self.get_vector_db(collection_name)
                    if existing_db:
                        vector_dbs[category] = existing_db
                        logger.info(f"기존 컬렉션 '{collection_name}' 사용")
                        continue
                
                # 새 컬렉션 생성
                if force_rebuild and collection_name in self._collection_cache:
                    del self._collection_cache[collection_name]
                
                vector_db = self.docs_to_chroma_db(docs, collection_name)
                vector_dbs[category] = vector_db
                
                logger.info(f"카테고리 '{category}' VectorDB 생성 완료 - 문서 수: {len(docs)}")
            
            logger.info(f"모든 VectorDB 초기화 완료 - 총 {len(vector_dbs)}개 카테고리")
            return vector_dbs
            
        except Exception as e:
            logger.error(f"VectorDB 초기화 중 오류: {str(e)}")
            raise
    
    def search_similar_documents(self, query: str, collection_name: str, k: int = 3, 
                               score_threshold: float = 0.0) -> List[Document]:
        """
        유사 문서 검색
        
        Args:
            query: 검색 쿼리
            collection_name: 컬렉션 이름
            k: 반환할 문서 수
            score_threshold: 최소 유사도 점수
            
        Returns:
            List[Document]: 유사한 문서 리스트
        """
        try:
            vector_db = self.get_vector_db(collection_name)
            if not vector_db:
                logger.error(f"컬렉션 '{collection_name}'을 찾을 수 없습니다.")
                return []
            
            # 유사도 검색
            results = vector_db.similarity_search(query, k=k)
            
            # 점수 필터링 (필요한 경우)
            if score_threshold > 0.0:
                scored_results = vector_db.similarity_search_with_score(query, k=k)
                results = [doc for doc, score in scored_results if score >= score_threshold]
            
            logger.info(f"검색 완료 - 쿼리: '{query[:30]}...', 결과: {len(results)}개")
            return results
            
        except Exception as e:
            logger.error(f"검색 중 오류: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        모든 컬렉션의 통계 정보
        
        Returns:
            Dict[str, Any]: 컬렉션별 통계
        """
        stats = {}
        
        try:
            for category, collection_name in self.COLLECTIONS.items():
                vector_db = self.get_vector_db(collection_name)
                if vector_db:
                    try:
                        # 컬렉션의 문서 수 확인
                        collection = vector_db._collection
                        count = collection.count() if hasattr(collection, 'count') else 'Unknown'
                        
                        stats[category] = {
                            'collection_name': collection_name,
                            'document_count': count,
                            'exists': True,
                            'cached': collection_name in self._collection_cache
                        }
                    except Exception as e:
                        stats[category] = {
                            'collection_name': collection_name,
                            'error': str(e),
                            'exists': True,
                            'cached': collection_name in self._collection_cache
                        }
                else:
                    stats[category] = {
                        'collection_name': collection_name,
                        'exists': False,
                        'cached': False
                    }
            
            stats['summary'] = {
                'total_collections': len([s for s in stats.values() if isinstance(s, dict) and s.get('exists', False)]),
                'cached_collections': len(self._collection_cache),
                'vector_db_path': str(self.vector_db_path)
            }
            
        except Exception as e:
            logger.error(f"통계 정보 수집 중 오류: {str(e)}")
            stats['error'] = str(e)
        
        return stats
    
    def get_collection_as_vectorstore(self, collection_name: str) -> Optional[Chroma]:
        """
        Self-Query Retriever에서 사용할 수 있도록 VectorStore 인스턴스 반환
        
        Args:
            collection_name: 컬렉션 이름
            
        Returns:
            Chroma: ChromaDB VectorStore 인스턴스 (없으면 None)
        """
        try:
            vector_db = self.get_vector_db(collection_name)
            if vector_db:
                logger.info(f"VectorStore 로드 성공: {collection_name}")
                return vector_db
            else:
                logger.warning(f"VectorStore를 찾을 수 없음: {collection_name}")
                return None
        except Exception as e:
            logger.error(f"VectorStore 로드 실패 ({collection_name}): {str(e)}")
            return None
    
    def clear_cache(self):
        """컬렉션 캐시 초기화"""
        self._collection_cache.clear()
        logger.info("VectorDB 캐시 초기화 완료")
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        컬렉션 삭제
        
        Args:
            collection_name: 삭제할 컬렉션 이름
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 캐시에서 제거
            if collection_name in self._collection_cache:
                del self._collection_cache[collection_name]
            
            logger.warning(f"컬렉션 '{collection_name}' 캐시에서 제거됨.")
            return True
            
        except Exception as e:
            logger.error(f"컬렉션 '{collection_name}' 삭제 중 오류: {str(e)}")
            return False


# 전역 VectorDB 매니저 인스턴스 (싱글톤 패턴)
_vector_db_manager = None

def get_vector_db_manager() -> VectorDBManager:
    """
    VectorDB 매니저 싱글톤 인스턴스 반환
    
    Returns:
        VectorDBManager: VectorDB 매니저 인스턴스
    """
    global _vector_db_manager
    
    if _vector_db_manager is None:
        _vector_db_manager = VectorDBManager()
    
    return _vector_db_manager


# 편의 함수들
def initialize_vector_databases(metadata_path: str = None, force_rebuild: bool = False) -> Dict[str, Any]:
    """
    VectorDB 초기화 편의 함수
    
    Args:
        metadata_path: metadata 폴더 경로
        force_rebuild: 강제 재구축 여부
        
    Returns:
        Dict[str, Any]: 초기화 결과
    """
    manager = get_vector_db_manager()
    
    try:
        vector_dbs = manager.initialize_all_vector_dbs(metadata_path, force_rebuild)
        stats = manager.get_collection_stats()
        
        return {
            'success': True,
            'vector_dbs': list(vector_dbs.keys()),
            'stats': stats,
            'message': f"{len(vector_dbs)}개 VectorDB 초기화 완료"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': "VectorDB 초기화 실패"
        }


def search_documents(query: str, category: str, k: int = 3) -> List[Document]:
    """
    문서 검색 편의 함수
    
    Args:
        query: 검색 쿼리
        category: 카테고리 ('term', 'law', 'car_case', 'precedent')
        k: 반환할 문서 수
        
    Returns:
        List[Document]: 검색 결과
    """
    manager = get_vector_db_manager()
    collection_name = manager.COLLECTIONS.get(category, category)
    return manager.search_similar_documents(query, collection_name, k)


def get_vector_db_stats() -> Dict[str, Any]:
    """
    VectorDB 통계 정보 조회 편의 함수
    
    Returns:
        Dict[str, Any]: 통계 정보
    """
    manager = get_vector_db_manager()
    return manager.get_collection_stats()
