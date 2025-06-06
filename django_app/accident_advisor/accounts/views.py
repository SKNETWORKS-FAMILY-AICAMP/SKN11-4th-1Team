"""
사용자 인증 뷰 (팀원 A 담당)

이 파일은 로그인, 회원가입, 로그아웃 페이지를 담당합니다.

📝 팀원 A 작업 가이드:
1. 이 파일의 뷰 함수들은 이미 기본 로직이 작성되어 있습니다
2. templates/accounts/ 폴더에 HTML 파일을 작성하세요
3. 각 뷰 함수에서 context로 전달되는 데이터를 템플릿에서 사용하세요
4. CSS는 static/css/ 폴더에 작성하세요
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, LoginForm
from .forms import ProfileUpdateForm
from core.models import User


def signup_view(request):
    """
    회원가입 페이지
    
    📋 팀원 A 할 일:
    - templates/accounts/signup.html 파일 작성
    - 회원가입 폼 디자인
    - 성공/실패 메시지 표시
    """
    if request.user.is_authenticated:
        return redirect('main:index')  # 이미 로그인된 경우 메인으로
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'{username}님, 회원가입이 완료되었습니다!')
            return redirect('accounts:login')
        else:
            messages.error(request, '회원가입 정보를 다시 확인해주세요.')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'title': '회원가입'
    }
    return render(request, 'accounts/signup.html', context)


def login_view(request):
    """
    로그인 페이지
    
    📋 팀원 A 할 일:
    - templates/accounts/login.html 파일 작성
    - 로그인 폼 디자인
    - 회원가입 링크 추가
    """
    if request.user.is_authenticated:
        return redirect('main:index')  # 이미 로그인된 경우 메인으로
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'{user.nickname or user.username}님, 환영합니다!')
                
                # 로그인 후 이동할 페이지 (next 파라미터 확인)
                next_url = request.GET.get('next', 'main:index')
                return redirect(next_url)
            else:
                messages.error(request, '사용자명 또는 비밀번호가 올바르지 않습니다.')
        else:
            messages.error(request, '입력 정보를 다시 확인해주세요.')
    else:
        form = LoginForm()
    
    context = {
        'form': form,
        'title': '로그인'
    }
    return render(request, 'accounts/login.html', context)



def logout_view(request):
    """
    로그아웃 처리
    
    📋 팀원 A 할 일: ✅완료(로그아웃 확인 페이지 추가)✅
    - 특별한 템플릿 필요 없음 (자동 리다이렉트)
    - 필요시 로그아웃 확인 페이지 추가 가능
    """
    if request.user.is_authenticated:
        username = request.user.nickname or request.user.username
        logout(request)
        messages.info(request, f'{username}님, 로그아웃되었습니다.')
    
    return render(request, 'accounts/logout.html')



@login_required
def profile_view(request):
    """
    프로필 페이지✅완료✅
    
    📋 팀원 A 할 일:
    - templates/accounts/profile.html 파일 작성
    - 사용자 정보 표시
    - 프로필 수정 기능 (선택사항)
    """
    user = request.user
    
    context = {
        'user': user,
        'title': '내 프로필'
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_update_view(request):
    """프로필 수정 페이지✅완료✅"""
    user = request.user

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '프로필이 수정되었습니다.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=user)

    return render(request, 'accounts/profile_update.html', {
        'form': form,
        'title': '프로필 수정',
        'user': user,
    })


def password_reset_view(request):
    """비밀번호 찾기 페이지 (선택사항) :✅html만 구현 / 기능 준비중✅  
     📋 팀원 A 할 일:
     - templates/accounts/password_reset.html 파일 작성
     - 이메일 입력 폼
     - 간단한 안내 메시지"""
    if request.method == 'POST':
        messages.info(request, '비밀번호 재설정 기능은 준비 중입니다.')
        return redirect('accounts:password_reset')
    return render(request, 'accounts/password_reset.html', {'title': '비밀번호 재설정'})


