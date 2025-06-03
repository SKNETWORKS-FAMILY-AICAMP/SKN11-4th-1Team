"""
초기 데이터 생성 명령어

사용법: python manage.py create_initial_data
"""

from django.core.management.base import BaseCommand
from core.models import User, Category, AccidentCase


class Command(BaseCommand):
    help = '프로젝트 초기 데이터를 생성합니다'

    def handle(self, *args, **options):
        self.stdout.write('초기 데이터 생성을 시작합니다...')
        
        # 1. 관리자 계정 생성
        self.create_admin_user()
        
        # 2. 카테고리 생성
        self.create_categories()
        
        # 3. 샘플 사고 사례 생성
        self.create_sample_cases()
        
        self.stdout.write(
            self.style.SUCCESS('초기 데이터 생성이 완료되었습니다!')
        )

    def create_admin_user(self):
        """관리자 계정 생성"""
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123!',
                nickname='관리자'
            )
            self.stdout.write(f'관리자 계정이 생성되었습니다: {admin_user.username}')
        else:
            self.stdout.write('관리자 계정이 이미 존재합니다.')

    def create_categories(self):
        """커뮤니티 카테고리 생성"""
        categories_data = [
            {
                'name': '교차로 사고',
                'icon': '🚗',
                'description': '교차로에서 발생한 교통사고 관련 질문과 경험담'
            },
            {
                'name': '주차장 사고',
                'icon': '🅿️',
                'description': '주차장 내에서 발생한 접촉사고 관련 내용'
            },
            {
                'name': '차로변경 사고',
                'icon': '🛣️',
                'description': '차로변경 중 발생한 사고 관련 상담'
            },
            {
                'name': '후진 사고',
                'icon': '⬅️',
                'description': '후진 중 발생한 사고 관련 질문'
            },
            {
                'name': '보험 처리',
                'icon': '📋',
                'description': '보험 처리 과정 및 절차 관련 정보'
            },
            {
                'name': '법률 상담',
                'icon': '⚖️',
                'description': '교통사고 관련 법률 해석 및 상담'
            },
            {
                'name': '과실비율',
                'icon': '📊',
                'description': '과실비율 산정 및 이의제기 관련'
            },
            {
                'name': '기타',
                'icon': '💬',
                'description': '기타 교통사고 관련 질문 및 토론'
            }
        ]
        
        created_count = 0
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'description': cat_data['description']
                }
            )
            if created:
                created_count += 1
                
        self.stdout.write(f'{created_count}개의 새로운 카테고리가 생성되었습니다.')

    def create_sample_cases(self):
        """샘플 사고 사례 생성"""
        sample_cases = [
            {
                'case_id': 'CASE001',
                'title': '신호등 교차로 좌회전 vs 직진 사고',
                'description': '신호등이 있는 교차로에서 A차량이 좌회전 신호에 따라 좌회전하던 중, 대향차로에서 직진하던 B차량과 충돌한 사고',
                'fault_ratio_a': 70,
                'fault_ratio_b': 30,
                'case_type': '교차로',
                'legal_basis': '도로교통법 제25조 (교차로 통행방법), 대법원 2019다12345 판결'
            },
            {
                'case_id': 'CASE002',
                'title': '주차장 내 후진 vs 정지차량 사고',
                'description': '주차장에서 A차량이 후진으로 주차하려던 중 이미 정지해 있던 B차량과 접촉한 사고',
                'fault_ratio_a': 100,
                'fault_ratio_b': 0,
                'case_type': '주차장',
                'legal_basis': '도로교통법 제27조 (후진의 금지), 민법 제750조'
            },
            {
                'case_id': 'CASE003',
                'title': '신호위반 vs 정상신호 사고',
                'description': 'A차량이 적색신호를 위반하고 교차로에 진입하여 녹색신호에 따라 정상 진행하던 B차량과 충돌한 사고',
                'fault_ratio_a': 90,
                'fault_ratio_b': 10,
                'case_type': '신호위반',
                'legal_basis': '도로교통법 제5조 (신호등에 따른 통행), 대법원 2020다56789 판결'
            },
            {
                'case_id': 'CASE004',
                'title': '차로변경 vs 직진 사고',
                'description': 'A차량이 좌측 차로로 변경하던 중 좌측 차로를 직진하던 B차량과 충돌한 사고',
                'fault_ratio_a': 80,
                'fault_ratio_b': 20,
                'case_type': '차로변경',
                'legal_basis': '도로교통법 제19조 (차로변경), 대법원 2018다98765 판결'
            },
            {
                'case_id': 'CASE005',
                'title': '무신호 교차로 진입 순서 사고',
                'description': '신호등이 없는 교차로에서 A차량과 B차량이 거의 동시에 진입하여 충돌한 사고',
                'fault_ratio_a': 50,
                'fault_ratio_b': 50,
                'case_type': '무신호교차로',
                'legal_basis': '도로교통법 제26조 (교차로 우선순위), 민법 제750조'
            }
        ]
        
        created_count = 0
        for case_data in sample_cases:
            case, created = AccidentCase.objects.get_or_create(
                case_id=case_data['case_id'],
                defaults=case_data
            )
            if created:
                created_count += 1
                
        self.stdout.write(f'{created_count}개의 새로운 사고 사례가 생성되었습니다.')
