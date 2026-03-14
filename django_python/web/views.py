# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Max, Count
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
import json

from .models import Resource, StudyRecord, LearningPath, LearningPathItem, Post, Group, GroupMember, GroupMessage, GroupJoinRequest, GroupInvite, UserProfile


def _clean_str(v):
    if v is None:
        return u''
    try:
        s = unicode(v)
    except Exception:
        s = str(v)
    s = s.strip()
    # Strip wrapping quotes that may come from SQL import artifacts
    if (s.startswith(u"'") and s.endswith(u"'")) or (s.startswith(u'"') and s.endswith(u'"')):
        s = s[1:-1].strip()
    return s


def _clean_image(v):
    s = _clean_str(v)
    # Some imported rows have an extra leading quote or whitespace; normalize.
    return s.lstrip().lstrip(u"'").lstrip(u'"').strip()


def build_player_url(resource_obj):
    """
    Build an embeddable player URL based on utype/url,
    similar to the old frontend s_rurl logic.
    """
    if resource_obj is None:
        return u''
    utype = _clean_str(resource_obj.utype)
    url = _clean_str(resource_obj.url)

    if utype == u"bilibili":
        # 旧前端：从 URL 中取倒数第二段 BV 号
        parts = url.split(u"/")
        if len(parts) >= 2:
            bvid = parts[-2]
            return u"https://player.bilibili.com/player.html?isOutside=true&bvid=%s" % bvid
        return url
    elif utype == u"tiktok":
        return u"https://open.douyin.com/player/video?vid=%s" % url
    return url


def index(request):
    """
    Redirect root (/) to /main/ to keep the old Vue behavior.
    """


def main_page(request):
    """
    Home page (port of the old Vue main.vue).
    """



def study_page(request):
    """
    Resource list page (port of the old Vue study.vue), with pagination.
    """



def record_page(request):
    """
    Study history page (port of the old Vue record.vue).
    """



def delete_record(request, record_id):
    """
    Delete a single study record for the current user.
    """



def clear_all_records(request):
    """
    Delete all study records for the current user.
    """



def _create_initial_learning_path(user, scholar_level):
    """
    Create an initial learning path based on the scholar level.
    """



def signup_view(request):
    """
    Sign-up page: create Django User and initial learning path based on scholar level.
    """
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        scholar_level = request.POST.get('scholar_level', '').strip()
        nickname = request.POST.get('nickname', '').strip()
        phone = request.POST.get('phone', '').strip()
        sex = request.POST.get('sex', '').strip()

        if not username or not password1:
            error = u"Username and password are required."
        elif password1 != password2:
            error = u"The two passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = u"Username already exists."
        elif not scholar_level:
            error = u"Please select a scholar level."
        else:
            try:
                scholar_level = int(scholar_level)
                if scholar_level not in [1, 2, 3]:
                    error = u"Invalid scholar level."
                else:
                    # 创建用户
                    user = User.objects.create_user(username=username, password=password1)

                    # 创建用户资料
                    UserProfile.objects.create(
                        user=user,
                        scholar_level=scholar_level,
                        nickname=nickname or username,
                        phone=phone,
                        sex=sex,
                    )

                    # 根据学者等级创建初始学习路径
                    _create_initial_learning_path(user, scholar_level)

                    login(request, user)
                    return redirect('/')
            except ValueError:
                error = u"Invalid scholar level."


def login_view(request):
    """
    Simple login page: username + password.
    """
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if not next_url or next_url == '/':
                next_url = '/admin-dashboard/' if _is_admin_user(user) else '/'
            return redirect(next_url)
        else:
            error = u"Incorrect username or password."


def logout_view(request):
    """
    退出登录，并返回首页。
    """


def profile_view(request):
    """
    User profile page: view and edit basic info.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/user/profile/')

    profile, created = UserProfile.objects.get_or_create(user=request.user)

    error = None
    success = None

    if request.method == 'POST':
        nickname = request.POST.get('nickname', '').strip()
        phone = request.POST.get('phone', '').strip()
        sex = request.POST.get('sex', '').strip()
        scholar_level = request.POST.get('scholar_level', '').strip()

        profile.nickname = nickname or request.user.username
        profile.phone = phone
        profile.sex = sex

        if scholar_level:
            try:
                profile.scholar_level = int(scholar_level)
            except ValueError:
                error = u"Invalid scholar level."

        if not error:
            profile.save()
            success = u"Profile updated successfully."

    context = {
        'profile': profile,
        'error': error,
        'success': success,
    }
    return render(request, 'profile.html', context)


def study_detail_page(request):
    """
    Resource detail + simple quiz page.
    Currently uses static questions; can be moved to DB later.
    """



def study_detail_record(request):
    """
    Record study duration for a resource.
    """



def study_detail_legacy(request, rid):
    """
    兼容旧前端的 /study_detail/<id> 风格链接：
    - 如果 <id> 是纯数字，则重定向到 /study_detail/?id=<id>
    - 否则保持原路径但加上 ?id=，方便后端统一处理
    """



def path_page(request):
    """
    Learning path overview: list all paths for the current user.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/path/')

    paths = LearningPath.objects.filter(user=request.user).prefetch_related('items__resource')

    # Calculate progress for each path
    path_list = []
    for path in paths:
        items = path.items.all()
        total_count = items.count()
        completed_count = items.filter(is_completed=True).count()
        progress = int((completed_count * 100.0 / total_count) if total_count > 0 else 0)

        path_list.append({
            'id': path.id,
            'title': path.title,
            'description': path.description,
            'language': path.language,
            'target_level': path.target_level,
            'total_items': total_count,
            'completed_items': completed_count,
            'progress': progress,
            'created_at': path.created_at.strftime("%Y/%m/%d"),
            'updated_at': path.updated_at.strftime("%Y/%m/%d"),
        })

    context = {
        'paths': path_list,
    }
    return render(request, 'path.html', context)


def path_detail_page(request, path_id):
    """
    Learning path detail: show and manage items in a path.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/path/%s/' % path_id)

    try:
        path = LearningPath.objects.prefetch_related('items__resource').get(id=path_id, user=request.user)
    except LearningPath.DoesNotExist:
        return redirect('/path/')

    items = path.items.all()
    total_count = items.count()
    completed_count = items.filter(is_completed=True).count()
    progress = int((completed_count * 100.0 / total_count) if total_count > 0 else 0)

    item_list = []
    for item in items:
        item_list.append({
            'id': item.id,
            'resource_id': item.resource.id,
            'title': _clean_str(item.resource.title),
            'desc': _clean_str(item.resource.desc),
            'image': _clean_image(item.resource.image),
            'ltype': _clean_str(item.resource.ltype),
            'utype': _clean_str(item.resource.utype),
            'difficulty': item.resource.difficulty,
            'author': _clean_str(item.resource.author),
            'order': item.order,
            'is_completed': item.is_completed,
            'completed_at': item.completed_at.strftime("%Y/%m/%d %H:%M") if item.completed_at else None,
        })

    context = {
        'path': {
            'id': path.id,
            'title': path.title,
            'description': path.description,
            'language': path.language,
            'target_level': path.target_level,
            'total_items': total_count,
            'completed_items': completed_count,
            'progress': progress,
        },
        'items': item_list,
    }
    return render(request, 'path_detail.html', context)


def path_create(request):
    """
    Create a new learning path.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/path/create/')

    error = None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        language = request.POST.get('language', '').strip()
        target_level = request.POST.get('target_level', '').strip()

        if not title:
            error = u"Title is required."
        else:
            path = LearningPath.objects.create(
                user=request.user,
                title=title,
                description=description,
                language=language,
                target_level=target_level,
            )
            return redirect('/path/%s/' % path.id)

    return render(request, 'path_create.html', {'error': error})


def path_edit(request, path_id):
    """
    Edit an existing learning path.
    Owner or admin can edit.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/')

    try:
        path = LearningPath.objects.get(id=path_id)
    except LearningPath.DoesNotExist:
        return redirect('/path/')
    if path.user_id != request.user.id and not _is_admin_user(request.user):
        return redirect('/path/')

    error = None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        language = request.POST.get('language', '').strip()
        target_level = request.POST.get('target_level', '').strip()

        if not title:
            error = u"Title is required."
        else:
            path.title = title
            path.description = description
            path.language = language
            path.target_level = target_level
            path.save()
            return redirect('/path/%s/' % path.id)

    context = {
        'path': path,
        'error': error,
    }
    return render(request, 'path_edit.html', context)


def path_delete(request, path_id):
    """
    Delete a learning path.
    Owner or admin can delete.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    try:
        path = LearningPath.objects.get(id=path_id)
        if path.user_id != request.user.id and not _is_admin_user(request.user):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        path.delete()
        return JsonResponse({'success': True})
    except LearningPath.DoesNotExist:
        return JsonResponse({'error': 'Path does not exist.'}, status=404)

def path_add_resource(request, path_id):
    """
    Add a resource to a learning path.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    try:
        path = LearningPath.objects.get(id=path_id, user=request.user)
    except LearningPath.DoesNotExist:
        return JsonResponse({'error': 'Path does not exist.'}, status=404)

    if request.method == 'POST':
        resource_id = request.POST.get('resource_id')
        if not resource_id:
            return JsonResponse({'error': 'Resource ID is required.'}, status=400)

        try:
            resource = Resource.objects.get(id=resource_id)
            # Check if already in path
            if LearningPathItem.objects.filter(path=path, resource=resource).exists():
                return JsonResponse({'error': 'This resource is already in the path.'}, status=400)

            # Get current max order
            max_order_obj = LearningPathItem.objects.filter(path=path).aggregate(Max('order'))
            max_order = max_order_obj['order__max'] or 0

            LearningPathItem.objects.create(
                path=path,
                resource=resource,
                order=max_order + 1,
            )
            return JsonResponse({'success': True})
        except Resource.DoesNotExist:
            return JsonResponse({'error': 'Resource does not exist.'}, status=404)

    return JsonResponse({'error': 'Invalid request.'}, status=400)

def path_remove_resource(request, path_id, item_id):
    """
    Remove a resource item from a learning path.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    try:
        path = LearningPath.objects.get(id=path_id, user=request.user)
        item = LearningPathItem.objects.get(id=item_id, path=path)
        item.delete()
        return JsonResponse({'success': True})
    except (LearningPath.DoesNotExist, LearningPathItem.DoesNotExist):
        return JsonResponse({'error': 'Record does not exist.'}, status=404)


def path_toggle_complete(request, path_id, item_id):
    """
    Toggle completion status for a learning path item.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    try:
        path = LearningPath.objects.get(id=path_id, user=request.user)
        item = LearningPathItem.objects.get(id=item_id, path=path)
        item.is_completed = not item.is_completed
        if item.is_completed:
            from django.utils import timezone
            item.completed_at = timezone.now()
        else:
            item.completed_at = None
        item.save()
        return JsonResponse({'success': True, 'is_completed': item.is_completed})
    except (LearningPath.DoesNotExist, LearningPathItem.DoesNotExist):
        return JsonResponse({'error': 'Record does not exist.'}, status=404)

def _is_admin_user(user):
    """
    Admin definition:
    - Django superuser/staff
    - or username == 'admin' (legacy)
    """
    try:
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return bool(getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False) or user.username == 'admin')
    except Exception:
        return False


def forum_page(request):
    """
    Forum index page: list all posts.
    """
    posts = Post.objects.select_related('user').all()

    # 分页
    paginator = Paginator(posts, 20)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    post_list = []
    is_admin = _is_admin_user(request.user)
    for post in page_obj:
        is_own = request.user.is_authenticated and (post.user_id == request.user.id)
        post_list.append({
            'id': post.id,
            'user': {
                'id': post.user.id,
                'username': post.user.username,
            },
            'content': post.content,
            # Post.image is a CharField (URL/path)
            'image': post.image if post.image else None,
            'created_at': post.created_at.strftime("%Y/%m/%d %H:%M:%S"),
            'can_edit': bool(is_own or is_admin),
            'can_delete': bool(is_admin),
        })

    context = {
        'posts': post_list,
        'page_obj': page_obj,
    }
    return render(request, 'forum.html', context)


def forum_new_post(request):
    """
    New post page.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/forum/new/')

    error = None
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            error = u"Content cannot be empty."
        else:
            # 处理图片URL（从content中提取第一个图片URL）
            image_url = request.POST.get('image_url', '').strip()
            # 从content中提取第一个图片URL（如果存在）
            import re
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if img_match and not image_url:
                image_url = img_match.group(1)
            post = Post.objects.create(
                user=request.user,
                content=content,
                image=image_url,
            )
            return redirect('/forum/')

    context = {
        'error': error,
    }
    return render(request, 'forum_new.html', context)



def forum_edit_post(request, post_id):
    """
    Edit a forum post.
    - Normal users can only edit their own posts
    - Admin can edit any posts
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/forum/%s/edit/' % post_id)

    try:
        post = Post.objects.select_related('user').get(id=post_id)
    except Post.DoesNotExist:
        return redirect('/forum/')

    is_admin = _is_admin_user(request.user)
    if (post.user_id != request.user.id) and (not is_admin):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    error = None
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            error = u"Content cannot be empty."
        else:
            image_url = request.POST.get('image_url', '').strip()
            import re
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if img_match and not image_url:
                image_url = img_match.group(1)
            post.content = content
            if image_url:
                post.image = image_url
            post.save()
            return redirect('/forum/')

    context = {
        'error': error,
        'post': {
            'id': post.id,
            'content': post.content,
            'image': post.image,
            'author': post.user.username,
        }
    }
    return render(request, 'forum_edit.html', context)


def forum_delete_post(request, post_id):
    """
    Delete a forum post (admin only).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    if not _is_admin_user(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    try:
        post = Post.objects.get(id=post_id)
        post.delete()
        return JsonResponse({'success': True})
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post does not exist.'}, status=404)

def groups_page(request):
    """
    Study groups page: list groups the user has joined.
    """



def groups_detail_page(request, group_id):
    """
    Group detail page: show group info and messages.
    """



def groups_create(request):
    """
    Create a new group.
    """



def groups_join(request):
    """
    Request to join a group by group ID (creator approval required).
    """


def groups_handle_join_request(request, req_id):
    """
    Approve or reject a join request (group creator/admin only).
    """


def groups_invite(request, group_id):
    """
    Invite a user to a group (invitee must accept).
    Only group creator/admin can invite.
    """



def groups_respond_invite(request, invite_id):
    """
    Invitee accepts/declines an invitation.
    """


def groups_kick_member(request, group_id, user_id):
    """
    Group creator kicks a member.
    """



def groups_send_message(request, group_id):
    """
    Send a group message.
    """



# === Admin Dashboard ===

def _admin_required(view_func):
    """Decorator: require admin user, redirect to home if not."""


def admin_dashboard(request):
    """
    Admin dashboard home: stats, charts, and preview lists.
    """



def admin_resource_edit(request, resource_id):
    """Admin: edit any resource."""



def admin_resource_json(request, resource_id):
    """Admin: get one resource as JSON (for edit modal)."""


def admin_resource_delete(request, resource_id):
    """Admin: delete any resource."""



def admin_group_delete(request, group_id):
    """Admin: delete any group."""



def admin_user_delete(request, user_id):
    """Admin: delete user (sets is_active=False to avoid cascade)."""



def admin_resource_create(request):
    """Admin: create new resource."""



def _admin_list_params(request, model_name, default_per_page=20):
    """Common pagination for admin list views."""


def admin_resources_list(request):
    """Admin: resources list with CRUD."""



def admin_posts_list(request):
    """Admin: posts list with CRUD."""



def admin_groups_list(request):
    """Admin: groups list with CRUD."""


def admin_users_list(request):
    """Admin: users list with CRUD."""


def admin_user_create(request):
    """Admin: create new user (modal or page submit)."""


def admin_paths_list(request):
    """Admin: learning paths list with CRUD."""



def admin_post_create(request):
    """Admin: create post (modal submit), redirect to admin posts list."""



def admin_post_edit(request, post_id):
    """Admin: update post (modal submit), redirect to admin posts list."""


def admin_post_json(request, post_id):
    """Admin: get one post as JSON (for edit modal)."""


def admin_group_create(request):
    """Admin: create group (modal submit), redirect to admin groups list."""



def admin_path_create(request):
    """Admin: create path (modal submit), redirect to admin paths list."""


def admin_path_edit(request, path_id):
    """Admin: update path (modal submit), redirect to admin paths list."""



def admin_path_json(request, path_id):
    """Admin: get one path as JSON (for edit modal)."""

