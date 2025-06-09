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
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from core.models import Post, Comment, Category, PostLike, CommentLike
from .forms import PostForm, CommentForm

import json

def post_list(request):
    # 모든 카테고리 가져오기
    categories = Category.objects.all()
    # 기본 쿼리셋
    posts = Post.objects.filter(is_active=True).select_related('author', 'category')
    # 카테고리 필터링
    category_id = request.GET.get('category')
    if category_id:
        posts = posts.filter(category_id=category_id)

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
        'pedestrian': '차vs보행자',
        'car': '차vs차',
        'bike': '차vs자전거(농기구)',
        'legal': '법률상담',
        'free': '자유',
    }

    # ✅ 각 post에 tag_list 및 post_type_label 속성 추가
    for post in page_obj:
        post.tag_list = [tag.strip() for tag in post.tags.split(',') if tag.strip()]
        post.post_type_label = POST_TYPE_LABELS.get(post.post_type, '기타')

    context = {
        'categories': categories,
        'posts': page_obj,
        'search_query': search_query,
        'selected_category': int(category_id) if category_id else None,
        'selected_type': post_type,
        'selected_tag': tag_query,
        'post_type_labels': POST_TYPE_LABELS,
        'title': '커뮤니티'
    }

    return render(request, 'community/list.html', context)

@login_required
def post_create(request):
    """게시글 작성 페이지"""
    
    if request.method == 'POST':
        # AJAX 요청 처리
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                
                # 필수 필드 추출
                title = data.get('title', '').strip()
                content = data.get('content', '').strip()
                category_id = data.get('category')  # ✅ category_id 사용
                post_type = data.get('type', 'question')
                
                # 유효성 검사
                if not title or len(title) < 5:
                    return JsonResponse({'success': False, 'error': '제목은 5자 이상 입력해주세요.'})
                if not content or len(content) < 10:
                    return JsonResponse({'success': False, 'error': '내용은 10자 이상 입력해주세요.'})
                if not category_id:
                    return JsonResponse({'success': False, 'error': '카테고리를 선택해주세요.'})
                
                category = get_object_or_404(Category, id=category_id, is_active=True)
                
                # 게시글 유형 검증
                if post_type not in ['question', 'experience', 'tip']:
                    post_type = 'question'
                
                tags_list = data.get('tags', [])
                tags_string = ','.join(tags_list) if tags_list else ''
                
                post = Post.objects.create(
                    title=title,
                    content=content,
                    author=request.user,
                    category=category,
                    post_type=post_type,
                    tags=tags_string,
                    is_active=True
                )
                
                category.post_count = category.posts.filter(is_active=True).count()
                category.save(update_fields=['post_count'])
                
                return JsonResponse({
                    'success': True,
                    'post_id': post.id,
                    'message': '게시글이 성공적으로 작성되었습니다.',
                    'redirect_url': f'/community/detail/{post.id}/'
                })
            
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'오류 발생: {str(e)}'})
        
        # 일반 폼 제출 처리
        else:
            try:
                title = request.POST.get('title', '').strip()
                content = request.POST.get('content', '').strip()
                category_id = request.POST.get('category')  # ✅ 여기도 id 기준
                post_type = request.POST.get('post_type', 'question')
                tags = request.POST.get('tags', '').strip()
                
                if not all([title, content, category_id]):
                    messages.error(request, '모든 필수 항목을 입력해주세요.')
                    return redirect('community:create')
                
                category = get_object_or_404(Category, id=category_id, is_active=True)
                
                post = Post.objects.create(
                    title=title,
                    content=content,
                    author=request.user,
                    category=category,
                    post_type=post_type,
                    tags=tags,
                    is_active=True
                )
                
                category.post_count = category.posts.filter(is_active=True).count()
                category.save(update_fields=['post_count'])
                
                messages.success(request, '게시글이 작성되었습니다.')
                return redirect('community:detail', post_id=post.id)
            
            except Exception as e:
                messages.error(request, f'게시글 작성에 실패했습니다: {str(e)}')
                return redirect('community:create')
    
    # GET 요청 - 페이지 렌더링
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')
    for category in categories:
        category.community_post_count = category.posts.filter(is_active=True).count()
    
    context = {
        'post': None,
        'title': '게시글 작성',
        'categories': categories,
        'post_types': Post.POST_TYPE_CHOICES
    }

    return render(request, 'community/write.html', context)

@require_http_methods(["GET"])
def category_list_api(request):
    """카테고리 목록 API"""
    try:
        categories = Category.objects.filter(is_active=True).order_by('order', 'name')
        
        categories_data = []
        for category in categories:
            # 커뮤니티 게시글 수 계산 (related_name 변경에 따른 수정)
            community_post_count = category.posts.filter(is_active=True).count()
            
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'post_count': community_post_count,
                'order': category.order
            })
        
        return JsonResponse({
            'success': True,
            'categories': categories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



def post_detail(request, post_id):
    """게시글 상세 보기"""
    post = get_object_or_404(Post, id=post_id, is_active=True)
    
    # 조회수 증가
    post.view_count += 1
    post.save(update_fields=['view_count'])
    
    context = {
        'post': post,
        'tags': post.get_tags_list()
    }
    return render(request, 'community/detail.html', context)



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
    게시글 수정 (폼 기반 아님, 직접 값 수정)
    """
    post = get_object_or_404(Post, id=post_id, author=request.user)

    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            category_id = request.POST.get('category')
            post_type = request.POST.get('post_type', 'question')
            tags = request.POST.get('tags', '').strip()

            # 유효성 검사
            if not all([title, content, category_id]):
                messages.error(request, '모든 필수 항목을 입력해주세요.')
                return redirect('community:edit', post_id=post.id)

            category = get_object_or_404(Category, id=category_id, is_active=True)

            # 값 업데이트
            post.title = title
            post.content = content
            post.category = category
            post.post_type = post_type
            post.tags = tags
            post.save()

            # 카테고리 게시글 수 재계산
            category.post_count = category.posts.filter(is_active=True).count()
            category.save(update_fields=['post_count'])

            messages.success(request, '게시글이 수정되었습니다.')
            return redirect('community:detail', post_id=post.id)

        except Exception as e:
            messages.error(request, f'게시글 수정 중 오류가 발생했습니다: {str(e)}')
            return redirect('community:edit', post_id=post.id)

    # GET 요청 시 - 수정폼 렌더링
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')

    context = {
        'post': post,
        'title': '게시글 수정',
        'categories': categories,
        'post_types': Post.POST_TYPE_CHOICES
    }

    return render(request, 'community/write.html', context)



@login_required
def post_delete(request, post_id):
    """
    게시글 즉시 삭제 (확인 없이)
    """
    post = get_object_or_404(Post, id=post_id, author=request.user)

    post.is_active = False
    post.save()

    # 카테고리 게시글 수 업데이트
    post.category.post_count = post.category.posts.filter(is_active=True).count()
    post.category.save(update_fields=['post_count'])

    messages.success(request, '게시글이 삭제되었습니다.')
    return redirect('community:list')
