"""
커뮤니티 뷰 (팀원 B, C, D 담당)

📋 작업 분담:
- 팀원 B: post_list (게시글 목록) 페이지 + 템플릿
- 팀원 C: post_detail (게시글 상세) 페이지 + 템플릿  
- 팀원 D: post_create (게시글 작성) 페이지 + 템플릿

각 팀원은 자신이 담당하는 함수와 해당 템플릿만 작업하면 됩니다.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from core.models import Post, Comment, Category, PostLike, CommentLike
from .forms import PostForm, CommentForm


def post_list(request):
    # 기본 쿼리셋
    posts = Post.objects.filter(is_active=True).select_related('author', 'category')

    # 필터 조건들 저장
    filters = Q()

    # post_type 필터
    post_type = request.GET.get('type')
    if post_type:
        filters &= Q(post_type=post_type)

    # 검색 필터
    search_query = request.GET.get('search', '').strip()
    if search_query:
        filters &= (
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    # 태그 필터
    tag_query = request.GET.get('tag')
    if tag_query:
        filters &= Q(tags__icontains=tag_query)

    # 최종 필터링 적용
    posts = posts.filter(filters).order_by('-created_at')

    # 페이지네이션
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # post_type 라벨 정의
    POST_TYPE_LABELS = {
        'pedestrian': '차 vs 보행자',
        'car': '차 vs 차',
        'bike': '차 vs 자전거(농기구)',
        'legal': '법률상담',
        'free': '자유',
    }

    # ✅ 각 post에 tag_list 및 post_type_label 속성 추가
    for post in page_obj:
        post.tag_list = [tag.strip() for tag in post.tags.split(',') if tag.strip()]
        post.post_type_label = POST_TYPE_LABELS.get(post.post_type, '기타')

    context = {
        'posts': page_obj,
        'search_query': search_query,
        'selected_type': post_type,
        'selected_tag': tag_query,
        'post_type_labels': POST_TYPE_LABELS,
        'title': '커뮤니티'
    }

    return render(request, 'community/list.html', context)




def post_detail(request, post_id):
    """
    게시글 상세 페이지 (팀원 C 담당)
    
    📋 팀원 C 할 일:
    - templates/community/detail.html 파일 작성
    - 게시글 상세 내용 표시
    - 댓글 목록 표시
    - 댓글 작성 폼
    - 좋아요 버튼
    """
    # 게시글 가져오기
    post = get_object_or_404(Post, id=post_id, is_active=True)
    
    # 조회수 증가
    post.view_count += 1
    post.save()
    
    # 댓글 목록 가져오기
    comments = Comment.objects.filter(
        post=post, 
        is_active=True
    ).select_related('author').order_by('created_at')
    
    # 댓글 작성 처리
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            # 댓글 수 업데이트
            post.comment_count = post.comments.filter(is_active=True).count()
            post.save()
            
            messages.success(request, '댓글이 작성되었습니다.')
            return redirect('community:detail', post_id=post.id)
        else:
            messages.error(request, '댓글 작성에 실패했습니다.')
    else:
        comment_form = CommentForm()
    
    # 사용자의 좋아요 여부 확인
    user_liked = False
    if request.user.is_authenticated:
        user_liked = PostLike.objects.filter(user=request.user, post=post).exists()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'user_liked': user_liked,
        'title': post.title
    }
    
    return render(request, 'community/detail.html', context)


@login_required
def post_create(request):
    """
    게시글 작성 페이지 (팀원 D 담당)
    
    📋 팀원 D 할 일:
    - templates/community/write.html 파일 작성
    - 게시글 작성 폼 디자인
    - 카테고리 선택 UI
    - 제목/내용 입력 UI
    - 태그 입력 UI
    """
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            # 사용자 게시글 수 업데이트
            request.user.total_posts += 1
            request.user.save()
            
            # 카테고리 게시글 수 업데이트
            post.category.post_count += 1
            post.category.save()
            
            messages.success(request, '게시글이 작성되었습니다.')
            return redirect('community:detail', post_id=post.id)
        else:
            messages.error(request, '게시글 작성에 실패했습니다. 입력 내용을 확인해주세요.')
    else:
        form = PostForm()
    
    # 카테고리 목록
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'categories': categories,
        'title': '게시글 작성'
    }
    
    return render(request, 'community/write.html', context)


@login_required
@require_POST
@csrf_exempt
def toggle_like(request, post_id):
    """
    게시글 좋아요 토글 (AJAX)
    
    📋 팀원 C 참고:
    - JavaScript에서 AJAX로 호출
    - 좋아요 상태를 토글하고 결과 반환
    """
    try:
        post = get_object_or_404(Post, id=post_id, is_active=True)
        
        # 기존 좋아요 확인
        like, created = PostLike.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if created:
            # 새로 좋아요
            post.like_count += 1
            post.save()
            liked = True
            message = '좋아요!'
        else:
            # 좋아요 취소
            like.delete()
            post.like_count -= 1
            post.save()
            liked = False
            message = '좋아요 취소'
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'like_count': post.like_count,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def post_edit(request, post_id):
    """
    게시글 수정 (선택사항)
    
    📋 팀원 D 참고:
    - 게시글 작성과 유사한 로직
    - 본인 게시글만 수정 가능
    """
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, '게시글이 수정되었습니다.')
            return redirect('community:detail', post_id=post.id)
        else:
            messages.error(request, '게시글 수정에 실패했습니다.')
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'title': '게시글 수정'
    }
    
    return render(request, 'community/write.html', context)


@login_required
def post_delete(request, post_id):
    """
    게시글 삭제 (선택사항)
    
    📋 팀원용 참고:
    - 실제 삭제가 아닌 is_active = False로 설정
    - 본인 게시글만 삭제 가능
    """
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    if request.method == 'POST':
        post.is_active = False
        post.save()
        
        # 카테고리 게시글 수 업데이트
        post.category.post_count -= 1
        post.category.save()
        
        messages.success(request, '게시글이 삭제되었습니다.')
        return redirect('community:list')
    
    context = {
        'post': post,
        'title': '게시글 삭제'
    }
    
    return render(request, 'community/delete_confirm.html', context)
