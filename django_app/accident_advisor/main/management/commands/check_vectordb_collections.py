"""
VectorDB 컬렉션 확인 Django 관리 명령어
"""
import logging
from django.core.management.base import BaseCommand
from main.utils.vector_db import get_vector_db_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'VectorDB 컬렉션 상태 확인'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='상세한 컬렉션 정보 표시',
        )

    def handle(self, *args, **options):
        """VectorDB 컬렉션 상태 확인 및 출력"""
        
        self.stdout.write("🔍 VectorDB 컬렉션 상태 확인 중...")
        self.stdout.write("=" * 60)
        
        try:
            # VectorDB 매니저 초기화
            manager = get_vector_db_manager()
            
            # 매핑 정보 출력
            self.stdout.write(self.style.SUCCESS("\n🗺️  카테고리 → 컬렉션 매핑:"))
            self.stdout.write("-" * 40)
            for category, collection_name in manager.COLLECTIONS.items():
                self.stdout.write(f"   {category:12} → {collection_name}")
            
            # 통계 정보 조회
            stats = manager.get_collection_stats()
            
            self.stdout.write(self.style.SUCCESS("\n📊 VectorDB 컬렉션 통계:"))
            self.stdout.write("-" * 40)
            
            for category, stat in stats.items():
                if category == 'summary':
                    continue
                    
                self.stdout.write(f"\n🏷️  카테고리: {category}")
                if isinstance(stat, dict):
                    if stat.get('exists', False):
                        collection_name = stat.get('collection_name', 'Unknown')
                        doc_count = stat.get('document_count', 'Unknown')
                        cached = "✅" if stat.get('cached', False) else "❌"
                        
                        self.stdout.write(f"   📁 컬렉션명: {collection_name}")
                        self.stdout.write(f"   📄 문서 수: {doc_count}")
                        self.stdout.write(f"   💾 캐시됨: {cached}")
                        
                        if 'error' in stat:
                            self.stdout.write(
                                self.style.WARNING(f"   ⚠️  오류: {stat['error']}")
                            )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ 컬렉션이 존재하지 않음")
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠️  잘못된 통계 형식: {stat}")
                    )
            
            # 요약 정보
            if 'summary' in stats:
                summary = stats['summary']
                self.stdout.write(self.style.SUCCESS(f"\n📋 요약:"))
                self.stdout.write(f"   🗂️  총 컬렉션 수: {summary.get('total_collections', 0)}")
                self.stdout.write(f"   💾 캐시된 컬렉션: {summary.get('cached_collections', 0)}")
                self.stdout.write(f"   📁 VectorDB 경로: {summary.get('vector_db_path', 'Unknown')}")
            
            # 상세 정보 출력 (옵션)
            if options['detailed']:
                self.stdout.write(self.style.SUCCESS(f"\n🔍 상세 컬렉션 테스트:"))
                self.stdout.write("-" * 40)
                
                for category, collection_name in manager.COLLECTIONS.items():
                    try:
                        db = manager.get_vector_db(collection_name)
                        if db:
                            # 간단한 검색 테스트
                            test_results = db.similarity_search("교통사고", k=1)
                            self.stdout.write(
                                self.style.SUCCESS(f"   ✅ {collection_name}: 검색 테스트 성공 (결과: {len(test_results)}개)")
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"   ⚠️  {collection_name}: 컬렉션 로드 실패")
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ {collection_name}: 테스트 실패 - {str(e)}")
                        )
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("✅ 컬렉션 상태 확인 완료!"))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 오류 발생: {str(e)}")
            )
            logger.error(f"VectorDB 컬렉션 확인 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
