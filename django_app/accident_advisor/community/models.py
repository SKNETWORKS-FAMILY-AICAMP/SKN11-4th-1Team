from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Category(models.Model):
    """카테고리 모델 (core 앱에 있다고 가정)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="카테고리명")
    description = models.TextField(blank=True, verbose_name="설명")
    post_count = models.IntegerField(default=0, verbose_name="게시글 수")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    is_active = models.BooleanField(default=True, verbose_name="활성화")
    order = models.IntegerField(default=0, verbose_name="정렬순서")
    
    class Meta:
        verbose_name = "카테고리"
        verbose_name_plural = "카테고리"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Post(models.Model):
    """게시글 모델 - community 앱"""
    
    POST_TYPE_CHOICES = [
        ('question', '질문'),
        ('experience', '경험담'), 
        ('tip', '팁 공유'),
    ]
    
    # 기본 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    # 게시글 내용
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    post_type = models.CharField(
        max_length=20, 
        choices=POST_TYPE_CHOICES, 
        default='question',
        verbose_name='게시글 유형'
    )
    
    # 상태 필드
    is_resolved = models.BooleanField(
        default=False, 
        verbose_name='해결됨',
        help_text='질문이 해결되었는지 여부'
    )
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    # 통계 필드
    view_count = models.IntegerField(default=0, verbose_name='조회수')
    like_count = models.IntegerField(default=0, verbose_name='좋아요 수')
    comment_count = models.IntegerField(default=0, verbose_name='댓글 수')
    
    # 태그
    tags = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name='태그',
        help_text='쉼표로 구분해서 입력 (예: 교차로,사고,과실비율)'
    )
    
    # 관계 필드 - related_name을 고유하게 설정
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts',  # 'posts' 대신 'community_posts'
        verbose_name='작성자'
    )
    category = models.ForeignKey(
        'core.Category',
        on_delete=models.CASCADE,
        related_name='community_posts',  # 'post_set' 대신 'community_posts'
        verbose_name='카테고리'
    )
    
    class Meta:
        verbose_name = '커뮤니티 게시글'
        verbose_name_plural = '커뮤니티 게시글들'
        ordering = ['-created_at']
        db_table = 'community_post'  # 테이블 이름도 명시적으로 설정
    
    def __str__(self):
        return self.title
    
    def get_tags_list(self):
        """태그를 리스트로 반환"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def set_tags_from_list(self, tag_list):
        """리스트에서 태그 문자열로 설정"""
        self.tags = ','.join(tag_list) if tag_list else ''
    
    def get_status_display(self):
        """게시글 상태 표시"""
        if self.post_type == 'question':
            return '해결됨' if self.is_resolved else '미해결'
        return '활성' if self.is_active else '비활성'