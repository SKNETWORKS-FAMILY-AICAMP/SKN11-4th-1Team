# community/admin.py - related_name 변경에 따른 수정
from django.contrib import admin
from .models import Post

@admin.register(Post)
class CommunityPostAdmin(admin.ModelAdmin):
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
            obj.category.post_count = obj.category.community_posts.filter(is_active=True).count()
            obj.category.save(update_fields=['post_count'])
    
    # 게시글 삭제 시 카테고리의 게시글 수 업데이트
    def delete_model(self, request, obj):
        category = obj.category
        super().delete_model(request, obj)
        if category:
            category.post_count = category.community_posts.filter(is_active=True).count()
            category.save(update_fields=['post_count'])

# core/admin.py - Category 관리 (related_name 변경에 따른 수정)
from django.contrib import admin
from core.models import Category

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
    
    def get_community_post_count(self, obj):
        """커뮤니티 게시글 수 표시"""
        return obj.community_posts.filter(is_active=True).count()
    get_community_post_count.short_description = '커뮤니티 게시글 수'
    
    def get_community_post_count_display(self, obj):
        """관리자 폼에서 커뮤니티 게시글 수 표시"""
        count = obj.community_posts.filter(is_active=True).count()
        inactive_count = obj.community_posts.filter(is_active=False).count()
        return f"활성: {count}개, 비활성: {inactive_count}개"
    get_community_post_count_display.short_description = '커뮤니티 게시글 상세'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 카테고리 저장 후 게시글 수 업데이트
        obj.post_count = obj.community_posts.filter(is_active=True).count()
        obj.save(update_fields=['post_count'])
    
    # 인라인으로 해당 카테고리의 게시글 미리보기 추가
    def get_inline_instances(self, request, obj=None):
        if obj:
            return [CommunityPostInline(self.model, self.admin_site)]
        return []

# 카테고리 상세에서 게시글 목록 인라인 표시
class CommunityPostInline(admin.TabularInline):
    from community.models import Post
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