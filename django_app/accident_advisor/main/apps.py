from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"
    verbose_name = "메인 채팅"

    def ready(self):
        """
        Django 앱이 준비되었을 때 실행되는 메서드
        서버 시작 시 VectorDB를 자동으로 초기화합니다.
        """
        import sys
        
        # migrate, collectstatic 등의 명령어에서는 실행하지 않음
        skip_commands = ['migrate', 'makemigrations', 'collectstatic', 'createsuperuser', 'shell', 'test', 'initialize_vectordb']
        
        if any(cmd in sys.argv for cmd in skip_commands):
            return
            
        # RUN_MAIN 환경변수로 개발 서버의 리로드 중복 실행 방지
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        # VectorDB 자동 초기화 실행
        self._auto_initialize_vectordb()

    def _auto_initialize_vectordb(self):
        """vectordb.py의 함수들을 직접 호출하여 VectorDB 자동 초기화"""
        try:
            from django.conf import settings
            from pathlib import Path
            
            # 환경변수로 자동 초기화 제어
            auto_initialize = getattr(settings, 'AUTO_INITIALIZE_VECTORDB', True)
            if not auto_initialize:
                print("⚠️ [VectorDB] 자동 초기화가 비활성화되었습니다.")
                return
            
            print("🚀 [VectorDB] 자동 초기화 시작...")
            
            # vectordb.py에서 함수들 import (management command와 동일한 함수들)
            from .utils.vector_db import initialize_vector_databases, get_vector_db_stats
            
            # 강제 재생성 여부 확인
            force_rebuild = getattr(settings, 'FORCE_REBUILD_VECTORDB', False)
            
            # metadata 경로 확인
            metadata_path = getattr(settings, 'METADATA_PATH', None)
            if not metadata_path:
                print("⚠️ [VectorDB] METADATA_PATH가 설정되지 않았습니다.")
                return
                
            metadata_path = Path(metadata_path)
            if not metadata_path.exists():
                print(f"⚠️ [VectorDB] metadata 폴더가 존재하지 않습니다: {metadata_path}")
                return
            
            # 기존 VectorDB 상태 확인 (강제 재생성이 아닌 경우)
            if not force_rebuild:
                try:
                    stats = get_vector_db_stats()
                    existing_collections = [
                        category for category, info in stats.items() 
                        if isinstance(info, dict) and info.get('exists', False)
                    ]
                    
                    if existing_collections:
                        print(f"✅ [VectorDB] 기존 컬렉션 발견: {existing_collections}")
                        print("기존 컬렉션을 사용합니다. 강제 재생성하려면 FORCE_REBUILD_VECTORDB=true로 설정하세요.")
                        return
                except Exception as e:
                    print(f"⚠️ [VectorDB] 기존 상태 확인 실패: {e}")
            
            # VectorDB 초기화 실행 (management command와 동일한 함수 호출)
            if force_rebuild:
                print("🔨 [VectorDB] 강제 재생성 모드로 실행...")
            else:
                print("🔄 [VectorDB] 초기화 실행...")
            
            result = initialize_vector_databases(
                metadata_path=str(metadata_path),
                force_rebuild=force_rebuild
            )
            
            if result['success']:
                action = "재생성" if force_rebuild else "초기화"
                print(f"✅ [VectorDB] {action} 완료: {result['message']}")
                
                # 초기화된 컬렉션 정보 출력
                vector_dbs = result.get('vector_dbs', [])
                if vector_dbs:
                    print(f"📊 [VectorDB] {action}된 컬렉션: {', '.join(vector_dbs)}")
                
            else:
                print(f"❌ [VectorDB] 초기화 실패: {result.get('error', 'Unknown error')}")
                
        except ImportError as e:
            print(f"❌ [VectorDB] Import 오류: {str(e)}")
            print("필요한 패키지가 설치되어 있는지 확인해주세요.")
        except Exception as e:
            print(f"❌ [VectorDB] 자동 초기화 중 오류 발생: {str(e)}")
            print("수동으로 관리하려면: python manage.py initialize_vectordb")
