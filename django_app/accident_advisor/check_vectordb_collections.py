#!/usr/bin/env python3
"""
VectorDB 컬렉션 확인 스크립트
실제 생성된 컬렉션명들을 확인합니다.
"""

import os
import sys
import django
from pathlib import Path

# Django 설정
project_path = Path(__file__).parent
sys.path.append(str(project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accident_advisor.settings')
django.setup()

from main.utils.vector_db import get_vector_db_manager

def main():
    """VectorDB 컬렉션 상태 확인"""
    print("🔍 VectorDB 컬렉션 상태 확인 중...")
    print("=" * 60)
    
    try:
        # VectorDB 매니저 초기화
        manager = get_vector_db_manager()
        
        # 통계 정보 조회
        stats = manager.get_collection_stats()
        
        print("📊 VectorDB 컬렉션 통계:")
        print("-" * 40)
        
        for category, stat in stats.items():
            if category == 'summary':
                continue
                
            print(f"\n🏷️  카테고리: {category}")
            if isinstance(stat, dict):
                if stat.get('exists', False):
                    collection_name = stat.get('collection_name', 'Unknown')
                    doc_count = stat.get('document_count', 'Unknown')
                    cached = "✅" if stat.get('cached', False) else "❌"
                    
                    print(f"   📁 컬렉션명: {collection_name}")
                    print(f"   📄 문서 수: {doc_count}")
                    print(f"   💾 캐시됨: {cached}")
                    
                    if 'error' in stat:
                        print(f"   ⚠️  오류: {stat['error']}")
                else:
                    print(f"   ❌ 컬렉션이 존재하지 않음")
            else:
                print(f"   ⚠️  잘못된 통계 형식: {stat}")
        
        # 요약 정보
        if 'summary' in stats:
            summary = stats['summary']
            print(f"\n📋 요약:")
            print(f"   🗂️  총 컬렉션 수: {summary.get('total_collections', 0)}")
            print(f"   💾 캐시된 컬렉션: {summary.get('cached_collections', 0)}")
            print(f"   📁 VectorDB 경로: {summary.get('vector_db_path', 'Unknown')}")
        
        print("\n" + "=" * 60)
        
        # 컬렉션 매핑 정보 출력
        print("🗺️  카테고리 → 컬렉션 매핑:")
        print("-" * 40)
        for category, collection_name in manager.COLLECTIONS.items():
            print(f"   {category:12} → {collection_name}")
        
        print("\n✅ 컬렉션 상태 확인 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
