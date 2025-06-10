"""
VectorDB 초기화 Django 명령어
python manage.py initialize_vectordb
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import time

from main.utils.vector_db import initialize_vector_databases, get_vector_db_stats


class Command(BaseCommand):
    help = 'VectorDB를 초기화하고 모든 문서를 임베딩하여 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--metadata-path',
            type=str,
            help='metadata 폴더 경로 (기본값: settings.METADATA_PATH)',
        )
        parser.add_argument(
            '--force-rebuild',
            action='store_true',
            help='기존 컬렉션이 있어도 강제로 재구축',
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='초기화 없이 현재 VectorDB 상태만 확인',
        )

    def handle(self, *args, **options):
        """명령어 실행"""
        self.stdout.write(
            self.style.SUCCESS('🚀 VectorDB 초기화 시작...')
        )
        
        # 통계만 확인하는 경우
        if options['stats_only']:
            self.show_stats_only()
            return
        
        # metadata 경로 설정
        metadata_path = options.get('metadata_path')
        if not metadata_path:
            metadata_path = getattr(settings, 'METADATA_PATH', None)
            if not metadata_path:
                raise CommandError(
                    'metadata 경로가 지정되지 않았습니다. '
                    '--metadata-path 옵션을 사용하거나 settings.METADATA_PATH를 설정하세요.'
                )
        
        # 경로 존재 확인
        metadata_path = Path(metadata_path)
        if not metadata_path.exists():
            raise CommandError(f'metadata 폴더가 존재하지 않습니다: {metadata_path}')
        
        self.stdout.write(f'📁 Metadata 경로: {metadata_path}')
        
        # 강제 재구축 확인
        force_rebuild = options.get('force_rebuild', False)
        if force_rebuild:
            self.stdout.write(
                self.style.WARNING('⚠️  강제 재구축 모드: 기존 컬렉션을 모두 재생성합니다.')
            )
        
        # VectorDB 초기화 실행
        start_time = time.time()
        
        try:
            result = initialize_vector_databases(
                metadata_path=str(metadata_path),
                force_rebuild=force_rebuild
            )
            
            elapsed_time = time.time() - start_time
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {result["message"]} (소요시간: {elapsed_time:.2f}초)')
                )
                
                # 상세 결과 표시
                self.show_initialization_results(result)
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {result["message"]}: {result["error"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ VectorDB 초기화 중 오류 발생: {str(e)}')
            )
            raise CommandError(str(e))
    
    def show_stats_only(self):
        """통계 정보만 표시"""
        self.stdout.write('📊 현재 VectorDB 상태 확인 중...')
        
        try:
            stats = get_vector_db_stats()
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write('📈 VectorDB 통계 정보')
            self.stdout.write('='*50)
            
            # 요약 정보
            if 'summary' in stats:
                summary = stats['summary']
                self.stdout.write(f"📁 VectorDB 경로: {summary.get('vector_db_path', 'Unknown')}")
                self.stdout.write(f"📊 총 컬렉션 수: {summary.get('total_collections', 0)}")
                self.stdout.write(f"💾 캐시된 컬렉션: {summary.get('cached_collections', 0)}")
            
            # 카테고리별 상세 정보
            self.stdout.write('\n📋 카테고리별 상태:')
            for category, info in stats.items():
                if category == 'summary' or not isinstance(info, dict):
                    continue
                
                status = '✅' if info.get('exists', False) else '❌'
                cached = '💾' if info.get('cached', False) else '📁'
                
                collection_name = info.get('collection_name', 'Unknown')
                doc_count = info.get('document_count', 'Unknown')
                
                self.stdout.write(f"  {status} {cached} {category}: {collection_name} ({doc_count} docs)")
                
                if 'error' in info:
                    self.stdout.write(f"    ⚠️  오류: {info['error']}")
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 통계 정보 조회 중 오류: {str(e)}')
            )
    
    def show_initialization_results(self, result):
        """초기화 결과 상세 표시"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 초기화 결과')
        self.stdout.write('='*50)
        
        # 생성된 VectorDB 목록
        vector_dbs = result.get('vector_dbs', [])
        self.stdout.write(f'✅ 생성된 카테고리 ({len(vector_dbs)}개):')
        for category in vector_dbs:
            self.stdout.write(f'  - {category}')
        
        # 통계 정보
        if 'stats' in result:
            stats = result['stats']
            
            self.stdout.write('\n📈 컬렉션별 상태:')
            for category, info in stats.items():
                if category == 'summary' or not isinstance(info, dict):
                    continue
                
                collection_name = info.get('collection_name', 'Unknown')
                doc_count = info.get('document_count', 'Unknown')
                exists = '✅' if info.get('exists', False) else '❌'
                
                self.stdout.write(f'  {exists} {category}: {collection_name} ({doc_count} docs)')
        
        # 사용법 안내
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📖 사용법 안내')
        self.stdout.write('='*50)
        self.stdout.write('🔄 상태 확인: python manage.py initialize_vectordb --stats-only')
        self.stdout.write('🔨 강제 재구축: python manage.py initialize_vectordb --force-rebuild')
        self.stdout.write('📁 경로 지정: python manage.py initialize_vectordb --metadata-path /path/to/metadata')
        
        self.stdout.write('\n✨ VectorDB 초기화가 완료되었습니다! 이제 RAG 기능을 사용할 수 있습니다.')
