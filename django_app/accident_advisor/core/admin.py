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

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'post_count', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'post_type', 'view_count', 'like_count', 'comment_count', 'is_resolved', 'created_at']
    list_filter = ['category', 'post_type', 'is_resolved', 'is_active', 'created_at']
    search_fields = ['title', 'content', 'author__username', 'author__nickname']
    ordering = ['-created_at']


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
