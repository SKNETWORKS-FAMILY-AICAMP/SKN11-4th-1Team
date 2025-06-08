"""
관리자 페이지 설정 (리더가 관리)

Django Admin에서 모든 모델을 쉽게 관리할 수 있도록 설정합니다.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AccidentCase, ChatSession, ChatMessage, Category, Post, Comment, PostLike, CommentLike


# ============= 사용자 관리 =============

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'nickname', 'email', 'total_chats', 'total_posts', 'created_at']
    list_filter = ['is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'nickname', 'email']
    ordering = ['-created_at']
    
    # 기본 UserAdmin에 우리 필드 추가
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('nickname', 'profile_image', 'total_chats', 'total_posts')}),
    )


# ============= AI/데이터 관리 =============

@admin.register(AccidentCase)
class AccidentCaseAdmin(admin.ModelAdmin):
    list_display = ['case_id', 'title', 'case_type', 'fault_ratio_a', 'fault_ratio_b', 'created_at']
    list_filter = ['case_type', 'created_at']
    search_fields = ['case_id', 'title', 'description']
    ordering = ['-created_at']


# ============= 채팅 관리 =============

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'message_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'user__username', 'user__nickname']
    ordering = ['-updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'sender', 'content_preview', 'created_at']
    list_filter = ['sender', 'created_at']
    search_fields = ['content', 'session__title']
    ordering = ['-created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '메시지 미리보기'


# ============= 커뮤니티 관리 =============

# 카테고리 상세에서 게시글 목록 인라인 표시
class CommunityPostInline(admin.TabularInline):
    model = Post
    fk_name = 'category'
    extra = 0
    readonly_fields = ['title', 'author', 'post_type', 'is_resolved', 'view_count', 'created_at']
    fields = ['title', 'author', 'post_type', 'is_resolved', 'is_active', 'view_count', 'created_at']
    max_num = 10  # 최대 10개만 표시
    
    def has_add_permission(self, request, obj=None):
        return False  # 인라인에서는 추가 불가
    
    def has_delete_permission(self, request, obj=None):
        return False  # 인라인에서는 삭제 불가


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'get_community_post_count', 
        'is_active', 
        'order', 
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'description')
        }),
        ('설정', {
            'fields': ('is_active', 'order')  
        }),
        ('통계', {
            'fields': ('post_count', 'get_community_post_count_display'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['post_count', 'get_community_post_count_display']
    inlines = [CommunityPostInline]
    
    def get_community_post_count(self, obj):
        """커뮤니티 게시글 수 표시"""
        return obj.posts.filter(is_active=True).count()
    get_community_post_count.short_description = '커뮤니티 게시글 수'
    
    def get_community_post_count_display(self, obj):
        """관리자 폼에서 커뮤니티 게시글 수 표시"""
        count = obj.posts.filter(is_active=True).count()
        inactive_count = obj.posts.filter(is_active=False).count()
        return f"활성: {count}개, 비활성: {inactive_count}개"
    get_community_post_count_display.short_description = '커뮤니티 게시글 상세'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 카테고리 저장 후 게시글 수 업데이트
        obj.post_count = obj.posts.filter(is_active=True).count()
        obj.save(update_fields=['post_count'])


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'author', 
        'category', 
        'post_type', 
        'is_resolved',
        'is_active',
        'view_count',
        'like_count',
        'comment_count',
        'created_at'
    ]
    
    list_filter = [
        'post_type',
        'is_resolved', 
        'is_active',
        'category',
        'created_at'
    ]
    
    search_fields = ['title', 'content', 'tags', 'author__username']
    
    list_editable = ['is_resolved', 'is_active']
    
    readonly_fields = ['view_count', 'like_count', 'comment_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'content', 'author', 'category', 'post_type')
        }),
        ('추가 정보', {
            'fields': ('tags',)
        }),
        ('상태', {
            'fields': ('is_resolved', 'is_active')
        }),
        ('통계', {
            'fields': ('view_count', 'like_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')
    
    # 게시글 저장 시 카테고리의 게시글 수 업데이트
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 카테고리 게시글 수 업데이트
        if obj.category:
            obj.category.post_count = obj.category.posts.filter(is_active=True).count()
            obj.category.save(update_fields=['post_count'])
    
    # 게시글 삭제 시 카테고리의 게시글 수 업데이트
    def delete_model(self, request, obj):
        category = obj.category
        super().delete_model(request, obj)
        if category:
            category.post_count = category.posts.filter(is_active=True).count()
            category.save(update_fields=['post_count'])


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'author', 'content_preview', 'like_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'author__username', 'post__title']
    ordering = ['-created_at']
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = '게시글 제목'
    
    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = '댓글 미리보기'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post_title', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__title']
    ordering = ['-created_at']
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = '게시글 제목'


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'comment__content']
    ordering = ['-created_at']
    
    def comment_preview(self, obj):
        return obj.comment.content[:30] + '...' if len(obj.comment.content) > 30 else obj.comment.content
    comment_preview.short_description = '댓글 미리보기'


# Django Admin 사이트 커스터마이징
admin.site.site_header = "노느 - 교통사고 상담 챗봇 관리"
admin.site.site_title = "노느 Admin"
admin.site.index_title = "교통사고 상담 챗봇 관리 시스템"
