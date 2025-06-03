"""
커뮤니티 관련 폼 (팀원들 공용)

게시글 작성, 댓글 작성에 필요한 폼들을 정의합니다.
"""

from django import forms
from core.models import Post, Comment, Category


class PostForm(forms.ModelForm):
    """게시글 작성 폼"""
    
    class Meta:
        model = Post
        fields = ['category', 'title', 'content', 'post_type', 'tags']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '제목을 입력하세요 (최대 200자)',
                'maxlength': 200
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '내용을 입력하세요',
                'rows': 10
            }),
            'post_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '태그를 쉼표로 구분해서 입력하세요 (예: 교차로,사고,과실비율)',
                'maxlength': 200
            }),
        }
        labels = {
            'category': '카테고리',
            'title': '제목',
            'content': '내용',
            'post_type': '게시글 유형',
            'tags': '태그',
        }


class CommentForm(forms.ModelForm):
    """댓글 작성 폼"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '댓글을 입력하세요',
                'rows': 3
            }),
        }
        labels = {
            'content': '댓글',
        }
