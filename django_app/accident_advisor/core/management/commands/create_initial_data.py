"""
초기 데이터 생성 명령어

python manage.py makemigrations
python manage.py migrate

사용법: 
- 기본 데이터만 생성:           python manage.py create_initial_data
- 게시글과 댓글 포함:           python manage.py create_initial_data --with-posts --posts-count 50
- 좋아요 데이터까지 모두 생성:   python manage.py create_initial_data --with-posts --with-likes --posts-count 40
"""

import random
from django.core.management.base import BaseCommand
from core.models import Comment, CommentLike, Post, PostLike, User, Category, AccidentCase


class Command(BaseCommand):
    help = '프로젝트 초기 데이터를 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-posts',
            action='store_true',
            help='샘플 게시글도 함께 생성합니다',
        )
        parser.add_argument(
            '--posts-count',
            type=int,
            default=30,
            help='생성할 게시글 수 (기본값: 30)',
        )
        parser.add_argument(
            '--with-likes',
            action='store_true',
            help='좋아요 데이터도 함께 생성합니다',
        )

    def handle(self, *args, **options):
        self.stdout.write('초기 데이터 생성을 시작합니다...')
        
        # 1. 관리자 계정 생성
        self.create_admin_user()
        
        # User 계정 생성
        self.create_test_users()
        
        # 2. 카테고리 생성
        self.create_categories()

        # 샘플 게시글 생성 (옵션)
        if options['with_posts']:
            self.create_sample_posts(options['posts_count'])
            
            # 좋아요 데이터 생성 (옵션)
            if options['with_likes']:
                self.create_sample_likes()
        
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


    
    def create_test_users(self):
        """테스트 사용자 생성 (확장된 User 모델 기반)"""
        test_users_data = [
            {
                'username': 'traffic_expert',
                'email': 'expert@noneun.com',
                'nickname': '교통사고전문가',
                'first_name': '전문가',
                'last_name': '김',
                'total_chats': 300,
                'total_posts': 45
            },
            {
                'username': 'newbie_driver',
                'email': 'newbie@example.com',
                'nickname': '초보운전자123',
                'first_name': '초보',
                'last_name': '이',
                'total_chats': 25,
                'total_posts': 8
            },
            {
                'username': 'insurance_pro',
                'email': 'insurance@example.com',
                'nickname': '보험전문가',
                'first_name': '보험',
                'last_name': '박',
                'total_chats': 200,
                'total_posts': 35
            },
            {
                'username': 'law_advisor',
                'email': 'lawyer@example.com',
                'nickname': '법률상담사',
                'first_name': '법률',
                'last_name': '최',
                'total_chats': 180,
                'total_posts': 40
            },
            {
                'username': 'experienced_driver',
                'email': 'experienced@example.com',
                'nickname': '20년차운전자',
                'first_name': '경험자',
                'last_name': '정',
                'total_chats': 80,
                'total_posts': 15
            },
            {
                'username': 'accident_victim',
                'email': 'victim@example.com',
                'nickname': '사고당한사람',
                'first_name': '피해자',
                'last_name': '한',
                'total_chats': 50,
                'total_posts': 12
            },
            {
                'username': 'taxi_driver',
                'email': 'taxi@example.com',
                'nickname': '택시기사님',
                'first_name': '택시',
                'last_name': '조',
                'total_chats': 120,
                'total_posts': 20
            },
            {
                'username': 'delivery_driver',
                'email': 'delivery@example.com',
                'nickname': '배달라이더',
                'first_name': '배달',
                'last_name': '윤',
                'total_chats': 60,
                'total_posts': 10
            },
            {
                'username': 'student_driver',
                'email': 'student@example.com',
                'nickname': '대학생운전자',
                'first_name': '대학생',
                'last_name': '강',
                'total_chats': 30,
                'total_posts': 5
            }
        ]
        
        created_count = 0
        for user_data in test_users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'nickname': user_data['nickname'],
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False),
                    'total_chats': user_data.get('total_chats', 0),
                    'total_posts': user_data.get('total_posts', 0),
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')  # 기본 비밀번호 설정
                user.save()
                created_count += 1
                self.stdout.write(f"✓ 사용자 '{user.nickname}' ({user.username}) 생성됨")
                
        self.stdout.write(f'{created_count}개의 새로운 사용자가 생성되었습니다.')

    def create_additional_sample_users(self, count=20):
        """추가 샘플 사용자 대량 생성"""
        import random
        
        # 닉네임 생성용 데이터
        adjectives = [
            '신중한', '빠른', '조심스러운', '경험많은', '친절한', 
            '성실한', '꼼꼼한', '활발한', '차분한', '열정적인'
        ]
        
        nouns = [
            '운전자', '라이더', '기사님', '학생', '직장인',
            '주부', '사장님', '선생님', '의사', '간호사'
        ]
        
        domains = [
            'gmail.com', 'naver.com', 'daum.net', 'kakao.com', 'example.com'
        ]
        
        created_count = 0
        for i in range(count):
            username = f'user_{i+100:03d}'  # user_100, user_101, ...
            nickname = f'{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1, 999)}'
            email = f'{username}@{random.choice(domains)}'
            
            # 닉네임 중복 체크 및 수정
            original_nickname = nickname
            counter = 1
            while User.objects.filter(nickname=nickname).exists():
                nickname = f'{original_nickname}{counter}'
                counter += 1
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'nickname': nickname,
                    'first_name': f'사용자{i+100}',
                    'last_name': '테스트',
                    'total_chats': random.randint(0, 100),
                    'total_posts': random.randint(0, 20),
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                created_count += 1
                
        self.stdout.write(f'{created_count}개의 추가 샘플 사용자가 생성되었습니다.')



    def create_categories(self):
        """커뮤니티 카테고리 생성"""
        categories_data = [
            {
                'name': '차vs보행자',
                'icon': '🚶‍♂️‍➡️💥🚗',
                'description': '차vs보행자 교통사고 관련 질문과 경험담'
            },
            {
                'name': '차vs차',
                'icon': '🚗💥🚜',
                'description': '차vs차 교통사고 관련 질문과 경험담'
            },
            {
                'name': '차vs자전거(농기구)',
                'icon': '🚴‍♂️💥🚗',
                'description': '차vs자전거(농기구) 교통사고 관련 질문과 경험담'
            },
            {
                'name': '법률상담',
                'icon': '📋',
                'description': '법률상담 과정 및 절차 관련 정보'
            },
            {
                'name': '자유',
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



    def create_sample_posts(self, count=30):
        """실제적인 샘플 게시글 생성"""
        categories = list(Category.objects.all())
        users = list(User.objects.all())
        
        if not categories or not users:
            self.stdout.write(
                self.style.WARNING('카테고리나 사용자가 없어서 게시글을 생성할 수 없습니다.')
            )
            return

        # 실제적인 게시글 데이터
        sample_posts_data = [
            {
                'title': '교차로에서 좌회전 중 사고가 났는데 과실비율이 궁금해요',
                'content': '''신호등이 있는 교차로에서 좌회전 신호에 따라 좌회전을 하던 중 직진차량과 충돌했습니다.

상대방이 신호위반을 했다고 주장하는데 과실비율이 어떻게 될까요?

블랙박스 영상도 있고, 목격자도 있습니다. 보험회사에서는 50:50으로 제시했는데 납득이 안 갑니다.

비슷한 경험 있으신 분들의 조언 부탁드립니다.''',
                'post_type': 'question',
                'tags': '교차로,좌회전,신호위반,과실비율',
                'category_name': '차vs보행자'
            },
            {
                'title': '주차장 접촉사고 경험담 - 보험처리 과정 공유',
                'content': '''마트 주차장에서 후진하다가 옆 차량과 접촉사고가 났었습니다.

처음에는 어떻게 해야 할지 몰라서 당황했는데, 다행히 상대방이 친절하셔서 원만하게 해결했어요.

보험처리 과정과 주의사항을 공유하고 싶어서 글 남깁니다.

1. 현장에서 사진 촬영 (차량 위치, 손상 부위)
2. 상대방과 연락처 교환
3. 보험회사 신고
4. 정비소 견적 받기

주차장 사고는 생각보다 복잡하더라구요. 특히 CCTV가 없는 곳에서는 더욱 조심해야 할 것 같습니다.''',
                'post_type': 'experience',
                'tags': '주차장,접촉사고,후진,보험처리',
                'category_name': '차vs차'
            },
            {
                'title': '차로변경 시 안전거리 확보하는 팁',
                'content': '''차로변경할 때 사고를 예방하는 방법들을 정리해봤습니다.

**1. 방향지시등 미리 켜기**
- 최소 3초 전에 방향지시등을 켜세요
- 상대방에게 의도를 명확히 전달하는 것이 중요합니다

**2. 사각지대 확인**
- 룸미러, 사이드미러만으로는 부족합니다
- 고개를 돌려서 직접 확인하세요

**3. 안전거리 확보**
- 앞차와 최소 3초 거리 유지
- 뒤차와도 충분한 거리가 있는지 확인

**4. 급하게 끼어들지 말기**
- 여유를 가지고 천천히 차로변경
- 상대방이 양보해주면 감사 표시하기

특히 고속도로에서는 더욱 주의해야 합니다!''',
                'post_type': 'tip',
                'tags': '차로변경,안전거리,사각지대,예방',
                'category_name': '차vs자전거(농기구)'
            },
            {
                'title': '보험회사에서 과실비율 80:20 제시, 이의제기 가능한가요?',
                'content': '''직진 중 갑자기 끼어든 차량과 사고가 났습니다.

상황:
- 제가 직진 중이었음
- 상대방이 갑자기 차로변경하면서 충돌
- 블랙박스 영상 있음
- 상대방 방향지시등 사용 안 함

보험회사에서 제 과실을 20%로 잡았는데, 이의제기할 수 있을까요?

블랙박스 영상을 보면 명백히 상대방 잘못인 것 같은데... 어떻게 해야 할지 모르겠습니다.''',
                'post_type': 'question',
                'tags': '과실비율,이의제기,블랙박스,보험회사',
                'category_name': '법률상담'
            },
            {
                'title': '교통사고 발생 시 현장에서 해야 할 일들 (체크리스트)',
                'content': '''교통사고가 발생했을 때 현장에서 반드시 해야 할 일들을 정리했습니다.

**즉시 해야 할 일:**
□ 안전한 곳으로 차량 이동 (가능한 경우)
□ 비상등 켜기
□ 부상자 확인 및 응급처치
□ 112 신고 (인명피해 있는 경우)

**현장 증거 수집:**
□ 사고 현장 사진 촬영 (여러 각도)
□ 차량 손상 부위 촬영
□ 상대방 차량 번호판 촬영
□ 도로 상황, 신호등 상태 촬영

**정보 교환:**
□ 상대방 연락처, 보험회사 정보
□ 목격자 연락처 (있는 경우)
□ 사고 경위 간단히 메모

**하면 안 되는 행동:**
❌ 현장에서 합의금 지급
❌ 과도한 사과나 책임 인정
❌ 음주 의심되면 절대 합의 금지

초보운전자분들께 도움이 되었으면 좋겠어요!''',
                'post_type': 'tip',
                'tags': '교통사고,현장대응,초보운전자,매뉴얼',
                'category_name': '자유'
            }
        ]

        # 추가 게시글 제목과 내용 템플릿
        additional_posts = [
            {
                'title': '고속도로 추돌사고 과실비율 문의드립니다',
                'content': '고속도로에서 앞차가 급정거해서 추돌사고가 났습니다. 과실비율이 어떻게 될까요?',
                'post_type': 'question',
                'tags': '고속도로,추돌,급정거',
                'category_name': '자유'
            },
            {
                'title': '무보험 차량과 사고 났을 때 대처법',
                'content': '상대방이 보험에 가입하지 않은 차량이었습니다. 이런 경우 어떻게 처리해야 하나요?',
                'post_type': 'question',
                'tags': '무보험,대처법',
                'category_name': '법률상담'
            },
            {
                'title': '렌터카 사고 처리 경험담',
                'content': '렌터카로 여행 중 사고가 났던 경험을 공유합니다. 일반 차량과는 처리 과정이 조금 달랐어요.',
                'post_type': 'experience',
                'tags': '렌터카,여행',
                'category_name': '법률상담'
            },
            {
                'title': '음주운전 차량과의 사고 처리 과정',
                'content': '상대방이 음주운전이었던 경우의 처리 과정을 공유합니다.',
                'post_type': 'experience',
                'tags': '음주운전,처리과정',
                'category_name': '법률상담'
            },
            {
                'title': '후진 중 보행자와 접촉사고, 과실비율은?',
                'content': '주차장에서 후진 중 보행자와 접촉사고가 났습니다. 과실비율이 궁금해요.',
                'post_type': 'question',
                'tags': '후진,보행자,주차장',
                'category_name': '차vs보행자'
            }
        ]

        created_count = 0
        all_posts_data = sample_posts_data + additional_posts

        # 기본 샘플 게시글 생성
        for post_data in all_posts_data:
            # 카테고리 찾기
            category = None
            for cat in categories:
                if cat.name == post_data['category_name']:
                    category = cat
                    break
            
            if not category:
                category = random.choice(categories)

            author = random.choice(users)
            
            post, created = Post.objects.get_or_create(
                title=post_data['title'],
                defaults={
                    'author': author,
                    'category': category,
                    'content': post_data['content'],
                    'post_type': post_data['post_type'],
                    'tags': post_data['tags'],
                    'view_count': random.randint(10, 500),
                    'like_count': 0,  # 나중에 실제 좋아요로 업데이트
                    'comment_count': 0,  # 나중에 실제 댓글 수로 업데이트
                    'is_resolved': post_data['post_type'] == 'question' and random.choice([True, False])
                }
            )
            if created:
                created_count += 1
                # 댓글 생성
                comment_count = self.create_sample_comments(post, users)
                # 게시글의 댓글 수 업데이트
                post.comment_count = comment_count
                post.save()

        # 추가 게시글 생성 (남은 개수만큼)
        remaining_count = count - len(all_posts_data)
        if remaining_count > 0:
            question_templates = [
                "{}에 대해 궁금한 점이 있습니다. 경험이 있으신 분들의 조언 부탁드립니다.",
                "{}와 관련해서 질문이 있어요. 어떻게 처리해야 할까요?",
                "{}상황에서 과실비율이 어떻게 될까요?",
                "{}경우 보험처리는 어떻게 하나요?"
            ]
            
            experience_templates = [
                "{}에 대한 제 경험을 공유하고 싶습니다.",
                "{}상황을 겪어봤는데 이렇게 해결했어요.",
                "{}관련 경험담을 공유합니다.",
                "{}처리 과정을 상세히 알려드릴게요."
            ]
            
            tip_templates = [
                "{}에 대한 유용한 정보를 정리해서 공유합니다.",
                "{}예방하는 방법들을 알려드려요.",
                "{}관련 팁을 공유합니다.",
                "{}할 때 주의사항들을 정리했어요."
            ]

            topics = [
                "스쿨존 사고", "자전거 접촉사고", "대리운전 중 사고", 
                "주차된 차량 손상", "경미한 접촉사고", "사고 후 병원 치료",
                "차량 수리비 견적", "보험사기 의심", "외국인과의 사고",
                "오토바이와의 사고", "버스와의 사고", "화물차 사고"
            ]

            for i in range(remaining_count):
                topic = random.choice(topics)
                post_type = random.choice(['question', 'experience', 'tip'])
                category = random.choice(categories)
                author = random.choice(users)
                
                if post_type == 'question':
                    title = f"{topic} 관련 질문입니다"
                    content = random.choice(question_templates).format(topic)
                elif post_type == 'experience':
                    title = f"{topic} 경험담 공유"
                    content = random.choice(experience_templates).format(topic)
                else:  # tip
                    title = f"{topic} 예방 팁"
                    content = random.choice(tip_templates).format(topic)
                
                post = Post.objects.create(
                    title=title,
                    author=author,
                    category=category,
                    content=content,
                    post_type=post_type,
                    tags=f"{topic.replace(' ', '')},{category.name.replace(' ', '')}",
                    view_count=random.randint(5, 200),
                    like_count=0,
                    comment_count=0,
                    is_resolved=post_type == 'question' and random.choice([True, False])
                )
                created_count += 1
                
                # 댓글 생성
                comment_count = self.create_sample_comments(post, users)
                post.comment_count = comment_count
                post.save()

        self.stdout.write(f'{created_count}개의 샘플 게시글이 생성되었습니다.')

    def create_sample_comments(self, post, users):
        """게시글에 현실적인 샘플 댓글 생성"""
        comment_templates = {
            'question': [
                "저도 비슷한 상황을 겪었는데, 전문가 상담을 받아보시는 것을 추천드려요.",
                "보험회사에 문의해보시면 정확한 답변을 받을 수 있을 것 같아요.",
                "법률 상담소에서 무료 상담을 받아보세요.",
                "블랙박스 영상이 있다면 유리할 것 같습니다.",
                "과실비율은 사고 상황에 따라 달라질 수 있어요.",
                "경찰서에서 발급받은 사고사실확인원도 중요합니다.",
                "합의할 때는 신중하게 결정하시기 바랍니다.",
                "비슷한 케이스로 소송까지 간 경우도 봤어요. 신중하게 접근하세요."
            ],
            'experience': [
                "좋은 정보 감사합니다!",
                "저도 비슷한 경험이 있어서 공감됩니다.",
                "덕분에 많이 배웠어요. 감사합니다.",
                "실제 경험담이라 더욱 도움이 되네요.",
                "이런 정보 정말 필요했는데 감사해요!",
                "다음에 비슷한 상황이 생기면 참고하겠습니다.",
                "상세한 설명 감사드려요."
            ],
            'tip': [
                "유용한 팁 감사합니다!",
                "초보운전자에게 정말 도움이 되는 정보네요.",
                "이런 걸 미리 알았으면 좋았을 텐데... 감사해요!",
                "체크리스트로 정리해주셔서 이해하기 쉬워요.",
                "북마크 해두고 자주 봐야겠어요.",
                "가족들에게도 공유하겠습니다.",
                "정말 실용적인 조언이네요!"
            ]
        }
        
        # 0~7개의 랜덤 댓글 생성
        comment_count = random.randint(0, 7)
        templates = comment_templates.get(post.post_type, comment_templates['question'])
        
        for i in range(comment_count):
            comment = Comment.objects.create(
                post=post,
                author=random.choice(users),
                content=random.choice(templates),
                like_count=0  # 나중에 실제 좋아요로 업데이트
            )
        
        return comment_count

    def create_sample_likes(self):
        """게시글과 댓글에 좋아요 데이터 생성"""
        posts = list(Post.objects.all())
        comments = list(Comment.objects.all())
        users = list(User.objects.all())
        
        if not users:
            self.stdout.write(
                self.style.WARNING('사용자가 없어서 좋아요를 생성할 수 없습니다.')
            )
            return

        post_likes_created = 0
        comment_likes_created = 0

        # 게시글 좋아요 생성
        for post in posts:
            # 각 게시글마다 랜덤한 수의 사용자가 좋아요
            like_count = random.randint(0, min(len(users), 15))
            liked_users = random.sample(users, like_count)
            
            for user in liked_users:
                post_like, created = PostLike.objects.get_or_create(
                    user=user,
                    post=post
                )
                if created:
                    post_likes_created += 1
            
            # 게시글의 좋아요 수 업데이트
            post.like_count = PostLike.objects.filter(post=post).count()
            post.save()

        # 댓글 좋아요 생성
        for comment in comments:
            # 각 댓글마다 랜덤한 수의 사용자가 좋아요
            like_count = random.randint(0, min(len(users), 8))
            liked_users = random.sample(users, like_count)
            
            for user in liked_users:
                comment_like, created = CommentLike.objects.get_or_create(
                    user=user,
                    comment=comment
                )
                if created:
                    comment_likes_created += 1
            
            # 댓글의 좋아요 수 업데이트
            comment.like_count = CommentLike.objects.filter(comment=comment).count()
            comment.save()

        self.stdout.write(f'{post_likes_created}개의 게시글 좋아요가 생성되었습니다.')
        self.stdout.write(f'{comment_likes_created}개의 댓글 좋아요가 생성되었습니다.')