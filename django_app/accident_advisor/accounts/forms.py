"""
사용자 인증 관련 폼 (팀원 A 담당)

회원가입, 로그인에 필요한 폼들을 정의합니다.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User


class CustomUserCreationForm(UserCreationForm):
    """회원가입 폼"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '이메일을 입력하세요'
        })
    )
    nickname = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '닉네임을 입력하세요 (2-20자)'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'nickname', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '사용자명을 입력하세요'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 비밀번호 필드에도 스타일 적용
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '비밀번호를 다시 입력하세요'
        })
    
    def clean_nickname(self):
        """닉네임 중복 확인"""
        nickname = self.cleaned_data['nickname']
        if User.objects.filter(nickname=nickname).exists():
            raise forms.ValidationError('이미 사용 중인 닉네임입니다.')
        return nickname


class LoginForm(forms.Form):
    """로그인 폼"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '사용자명을 입력하세요'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })
    )

# 프로필 수정 폼
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nickname', 'email', 'profile_image']
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
