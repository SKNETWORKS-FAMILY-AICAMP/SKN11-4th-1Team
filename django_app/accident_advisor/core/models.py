"""
핵심 모델들 (리더가 전담 관리)

이 파일에는 모든 데이터베이스 모델이 정의되어 있습니다.
팀원들은 이 파일을 수정하지 않고, 자신의 views.py에서만 사용합니다.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


# ============= 기본 모델들 =============

class User(AbstractUser):
    """확장된 사용자 모델"""
    nickname = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,
        verbose_name='닉네임',
        help_text='사용자의 표시 이름'
    )
    profile_image = models.ImageField(
        upload_to='profiles/', 
        blank=True,
        verbose_name='프로필 이미지'
    )
    
    # 사용자 통계 (자동 업데이트)
    total_chats = models.IntegerField(default=0, verbose_name='총 채팅 수')
    total_posts = models.IntegerField(default=0, verbose_name='총 게시글 수')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='가입일')
    
    def __str__(self):
        return self.nickname or self.username
    
    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'


class BaseModel(models.Model):
    """모든 모델의 기본 클래스 (추상 모델)"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        abstract = True


# ============= AI/데이터 모델들  =============

class AccidentCase(BaseModel):
    """교통사고 사례 데이터베이스 (AI 학습용)"""
    case_id = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='사례 ID'
    )
    title = models.CharField(max_length=200, verbose_name='사례 제목')
    description = models.TextField(verbose_name='사고 상황 설명')
    fault_ratio_a = models.IntegerField(verbose_name='A차량 과실비율(%)')
    fault_ratio_b = models.IntegerField(verbose_name='B차량 과실비율(%)')
    case_type = models.CharField(
        max_length=50, 
        verbose_name='사고 유형',
        help_text='교차로, 주차장, 차로변경 등'
    )
    legal_basis = models.TextField(
        blank=True,
        verbose_name='법적 근거',
        help_text='도로교통법 조문, 판례 등'
    )
    
    def __str__(self):
        return f"[{self.case_id}] {self.title}"
    
    class Meta:
        verbose_name = '교통사고 사례'
        verbose_name_plural = '교통사고 사례들'
        ordering = ['-created_at']


# ============= 채팅 모델들 =============

class ChatSession(BaseModel):
    """채팅 세션 관리"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='chat_sessions',
        verbose_name='사용자'
    )
    session_id = models.CharField(
        max_length=50, 
        unique=True,
        default=uuid.uuid4,
        verbose_name='세션 ID'
    )
    title = models.CharField(
        max_length=100, 
        default='새 상담',
        verbose_name='상담 제목'
    )
    message_count = models.IntegerField(default=0, verbose_name='메시지 수')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    def __str__(self):
        return f"{self.title} ({self.user or '익명'})"
    
    class Meta:
        verbose_name = '채팅 세션'
        verbose_name_plural = '채팅 세션들'
        ordering = ['-updated_at']


class ChatMessage(BaseModel):
    """채팅 메시지"""
    SENDER_CHOICES = [
        ('user', '사용자'),
        ('bot', '챗봇'),
    ]
    
    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='채팅 세션'
    )
    sender = models.CharField(
        max_length=10, 
        choices=SENDER_CHOICES,
        verbose_name='발신자'
    )
    content = models.TextField(verbose_name='메시지 내용')
    
    # AI 관련 메타데이터 (선택사항)
    ai_confidence = models.FloatField(
        null=True, 
        blank=True,
        verbose_name='AI 신뢰도'
    )
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."
    
    class Meta:
        verbose_name = '채팅 메시지'
        verbose_name_plural = '채팅 메시지들'
        ordering = ['created_at']


# ============= 커뮤니티 모델들 =============

class Category(BaseModel):
    """게시글 카테고리"""
    name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='카테고리명'
    )
    description = models.TextField(
        blank=True,
        verbose_name='카테고리 설명'
    )
    icon = models.CharField(
        max_length=10, 
        default='📝',
        verbose_name='아이콘',
        help_text='이모지 하나'
    )
    post_count = models.IntegerField(
        default=0,
        verbose_name='게시글 수'
    )
    
    # 누락된 필드들 추가
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태',
        help_text='체크 해제 시 카테고리가 비활성화됩니다'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='정렬 순서',
        help_text='숫자가 작을수록 먼저 표시됩니다'
    )
    
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리들'
        ordering = ['order', 'name']  # order 필드로 먼저 정렬, 그 다음 이름순



class Post(BaseModel):
    """커뮤니티 게시글"""
    POST_TYPE_CHOICES = [
        ('question', '질문'),
        ('experience', '경험담'),
        ('tip', '팁 공유'),
    ]
    
    # 기본 정보
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='작성자'
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        verbose_name='카테고리'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    post_type = models.CharField(
        max_length=20, 
        choices=POST_TYPE_CHOICES, 
        default='question',
        verbose_name='게시글 유형'
    )
    
    # 상태
    is_resolved = models.BooleanField(
        default=False, 
        verbose_name='해결됨',
        help_text='질문이 해결되었는지 여부'
    )
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    # 통계 (자동 업데이트)
    view_count = models.IntegerField(default=0, verbose_name='조회수')
    like_count = models.IntegerField(default=0, verbose_name='좋아요 수')
    comment_count = models.IntegerField(default=0, verbose_name='댓글 수')
    
    # 태그 (간단하게 문자열로 저장)
    tags = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name='태그',
        help_text='쉼표로 구분해서 입력 (예: 교차로,사고,과실비율)'
    )
    
    def __str__(self):
        return f"[{self.category.name}] {self.title}"
    
    def get_tags_list(self):
        """태그를 리스트로 반환"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_from_list(self, tag_list):
        """리스트에서 태그 문자열로 설정"""
        self.tags = ','.join(tag_list) if tag_list else ''
    
    def get_status_display(self):
        """게시글 상태 표시"""
        if self.post_type == 'question':
            return '해결됨' if self.is_resolved else '미해결'
        return '활성' if self.is_active else '비활성'
    
    class Meta:
        verbose_name = '게시글'
        verbose_name_plural = '게시글들'
        ordering = ['-created_at']


class Comment(BaseModel):
    """댓글"""
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='게시글'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='작성자'
    )
    content = models.TextField(verbose_name='댓글 내용')
    like_count = models.IntegerField(default=0, verbose_name='좋아요 수')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    def __str__(self):
        return f"{self.author.nickname}: {self.content[:30]}..."
    
    class Meta:
        verbose_name = '댓글'
        verbose_name_plural = '댓글들'
        ordering = ['created_at']


class PostLike(BaseModel):
    """게시글 좋아요 (중복 방지)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='게시글')
    
    class Meta:
        unique_together = ['user', 'post']  # 한 사용자는 한 게시글에 한 번만 좋아요
        verbose_name = '게시글 좋아요'
        verbose_name_plural = '게시글 좋아요들'


class CommentLike(BaseModel):
    """댓글 좋아요 (중복 방지)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='댓글')
    
    class Meta:
        unique_together = ['user', 'comment']  # 한 사용자는 한 댓글에 한 번만 좋아요
        verbose_name = '댓글 좋아요'
        verbose_name_plural = '댓글 좋아요들'
