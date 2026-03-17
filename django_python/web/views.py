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
    return redirect('main_page')


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


def login_view(request):
    """
    Simple login page: username + password.
    """

def logout_view(request):
    """
    退出登录，并返回首页。
    """



def profile_view(request):
    """
    User profile page: view and edit basic info.
    """



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



def path_detail_page(request, path_id):
    """
    Learning path detail: show and manage items in a path.
    """



def path_create(request):
    """
    Create a new learning path.
    """



def path_edit(request, path_id):
    """
    Edit an existing learning path.
    Owner or admin can edit.
    """


def path_delete(request, path_id):
    """
    Delete a learning path.
    Owner or admin can delete.
    """



def path_add_resource(request, path_id):
    """
    Add a resource to a learning path.
    """



def path_remove_resource(request, path_id, item_id):
    """
    Remove a resource item from a learning path.
    """



def path_toggle_complete(request, path_id, item_id):
    """
    Toggle completion status for a learning path item.
    """


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



def forum_new_post(request):
    """
    New post page.
    """



def forum_edit_post(request, post_id):
    """
    Edit a forum post.
    - Normal users can only edit their own posts
    - Admin can edit any posts
    """


def forum_delete_post(request, post_id):
    """
    Delete a forum post (admin only).
    """



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
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/user/signin/?next=' + request.path)
        if not _is_admin_user(request.user):
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_dashboard(request):
    """
    Admin dashboard home: stats, charts, and preview lists.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/admin-dashboard/')
    if not _is_admin_user(request.user):
        return redirect('/')

    total_resources = Resource.objects.count()
    stats = {
        'resources': total_resources,
        'posts': Post.objects.count(),
        'groups': Group.objects.count(),
        'users': User.objects.count(),
        'paths': LearningPath.objects.count(),
    }

    # Chart: Resource type distribution (ltype -> count)
    type_data = list(Resource.objects.values('ltype').annotate(count=Count('id')).order_by('-count')[:8])
    chart_type_labels = [d['ltype'] or u'Unknown' for d in type_data]
    chart_type_values = [d['count'] for d in type_data]

    # Chart: Difficulty distribution (1-4)
    diff_data = list(Resource.objects.values('difficulty').annotate(count=Count('id')))
    diff_map = {d['difficulty']: d['count'] for d in diff_data}
    chart_diff_labels = [u'Beginner', u'Intermediate', u'Advanced', u'Expert']
    chart_diff_values = [diff_map.get(i, 0) for i in range(1, 5)]

    # Chart: Resource growth trend (by created_at date, last 30 days)
    from datetime import timedelta
    from collections import defaultdict
    since = timezone.now() - timedelta(days=30)
    recent = Resource.objects.filter(created_at__gte=since).values_list('created_at', flat=True)
    daily = defaultdict(int)
    for dt in recent:
        if dt:
            d = dt.date() if hasattr(dt, 'date') else dt
            daily[str(d)] += 1
    sorted_days = sorted(daily.keys())
    chart_trend_labels = [d[5:] if len(d) >= 5 else d for d in sorted_days]  # MM-DD
    chart_trend_values = [daily[d] for d in sorted_days]

    # Preview lists (latest 5 each)
    resources = Resource.objects.all()[:5]
    posts = Post.objects.select_related('user').all()[:5]

    context = {
        'admin_page': 'home',
        'stats': stats,
        'resources': resources,
        'posts': posts,
        'chart_type_labels': json.dumps(chart_type_labels, ensure_ascii=False),
        'chart_type_values': json.dumps(chart_type_values),
        'chart_diff_labels': json.dumps(chart_diff_labels, ensure_ascii=False),
        'chart_diff_values': json.dumps(chart_diff_values),
        'chart_trend_labels': json.dumps(chart_trend_labels),
        'chart_trend_values': json.dumps(chart_trend_values),
    }
    return render(request, 'admin_dashboard.html', context)


def admin_resource_edit(request, resource_id):
    """Admin: edit any resource."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    try:
        resource = Resource.objects.get(id=resource_id)
    except Resource.DoesNotExist:
        return redirect('/admin-dashboard/')
    error = None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        desc = request.POST.get('desc', '')
        url = request.POST.get('url', '').strip()
        ltype = request.POST.get('ltype', '').strip()
        try:
            difficulty = int(request.POST.get('difficulty', 1))
        except (ValueError, TypeError):
            difficulty = 1
        utype = request.POST.get('utype', '').strip()
        author = request.POST.get('author', '').strip()
        image = request.POST.get('image', '').strip()
        time_str = request.POST.get('time', '').strip()
        if not title:
            error = u"Title is required."
        else:
            resource.title = title
            resource.desc = desc
            resource.url = url
            resource.ltype = ltype
            resource.difficulty = max(1, min(4, difficulty))
            resource.utype = utype
            resource.author = author
            resource.image = image
            resource.time = time_str
            resource.save()
            return redirect('/admin-dashboard/resources/')
    return render(request, 'admin_resource_edit.html', {'resource': resource, 'error': error})


def admin_resource_json(request, resource_id):
    """Admin: get one resource as JSON (for edit modal)."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        r = Resource.objects.get(id=resource_id)
        return JsonResponse({
            'id': r.id, 'title': r.title, 'desc': r.desc or '', 'url': r.url or '',
            'ltype': r.ltype or '', 'difficulty': r.difficulty, 'utype': r.utype or '',
            'author': r.author or '', 'image': r.image or '', 'time': r.time or '',
        })
    except Resource.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


def admin_resource_delete(request, resource_id):
    """Admin: delete any resource."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    try:
        resource = Resource.objects.get(id=resource_id)
        resource.delete()
        return JsonResponse({'success': True})
    except Resource.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


def admin_group_delete(request, group_id):
    """Admin: delete any group."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    try:
        group = Group.objects.get(id=group_id)
        group.delete()
        return JsonResponse({'success': True})
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


def admin_user_delete(request, user_id):
    """Admin: delete user (sets is_active=False to avoid cascade)."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    if int(user_id) == request.user.id:
        return JsonResponse({'error': 'Cannot delete yourself.'}, status=400)
    try:
        user = User.objects.get(id=user_id)
        user.is_active = False
        user.save()
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


def admin_resource_create(request):
    """Admin: create new resource."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    error = None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        desc = request.POST.get('desc', '')
        url = request.POST.get('url', '').strip()
        ltype = request.POST.get('ltype', '').strip()
        try:
            difficulty = int(request.POST.get('difficulty', 1))
        except (ValueError, TypeError):
            difficulty = 1
        utype = request.POST.get('utype', '').strip()
        author = request.POST.get('author', '').strip()
        image = request.POST.get('image', '').strip()
        time_str = request.POST.get('time', '').strip()
        if not title:
            error = u"Title is required."
        else:
            Resource.objects.create(
                title=title, desc=desc, url=url, ltype=ltype,
                difficulty=max(1, min(4, difficulty)), utype=utype,
                author=author, image=image, time=time_str
            )
            return redirect('/admin-dashboard/resources/')
    return render(request, 'admin_resource_edit.html', {'resource': None, 'error': error})


def _admin_list_params(request, model_name, default_per_page=20):
    """Common pagination for admin list views."""
    try:
        p = request.GET.get('per_page') or default_per_page
        per_page = min(int(p), 100)
    except (ValueError, TypeError):
        per_page = default_per_page
    page = request.GET.get('page', 1)
    return per_page, page


def admin_resources_list(request):
    """Admin: resources list with CRUD."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    per_page, page_num = _admin_list_params(request, 'resources')
    qs = Resource.objects.all().order_by('-id')
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'admin_resources.html', {
        'admin_page': 'resources',
        'page_obj': page_obj,
        'items': page_obj,
    })


def admin_posts_list(request):
    """Admin: posts list with CRUD."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    per_page, page_num = _admin_list_params(request, 'posts')
    qs = Post.objects.select_related('user').all().order_by('-id')
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'admin_posts.html', {
        'admin_page': 'posts',
        'page_obj': page_obj,
        'items': page_obj,
    })


def admin_groups_list(request):
    """Admin: groups list with CRUD."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    per_page, page_num = _admin_list_params(request, 'groups')
    qs = Group.objects.select_related('creator').all().order_by('-id')
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'admin_groups.html', {
        'admin_page': 'groups',
        'page_obj': page_obj,
        'items': page_obj,
    })


def admin_users_list(request):
    """Admin: users list with CRUD."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    per_page, page_num = _admin_list_params(request, 'users')
    qs = User.objects.all().order_by('-id')
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'admin_users.html', {
        'admin_page': 'users',
        'page_obj': page_obj,
        'items': page_obj,
    })


def admin_user_create(request):
    """Admin: create new user (modal or page submit)."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    if request.method != 'POST':
        return render(request, 'admin_user_create.html', {'error': None})
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    email = request.POST.get('email', '').strip()
    if not username:
        return redirect('/admin-dashboard/users/?error=username')
    if not password:
        return redirect('/admin-dashboard/users/?error=password')
    if User.objects.filter(username=username).exists():
        return redirect('/admin-dashboard/users/?error=exists')
    User.objects.create_user(username=username, password=password, email=email)
    return redirect('/admin-dashboard/users/')


def admin_paths_list(request):
    """Admin: learning paths list with CRUD."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    per_page, page_num = _admin_list_params(request, 'paths')
    qs = LearningPath.objects.select_related('user').all().order_by('-id')
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'admin_paths.html', {
        'admin_page': 'paths',
        'page_obj': page_obj,
        'items': page_obj,
    })


def admin_post_create(request):
    """Admin: create post (modal submit), redirect to admin posts list."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    if request.method != 'POST':
        return redirect('/admin-dashboard/posts/')
    content = request.POST.get('content', '').strip()
    image = request.POST.get('image', '').strip()
    if not content:
        return redirect('/admin-dashboard/posts/?error=content')
    Post.objects.create(user=request.user, content=content, image=image)
    return redirect('/admin-dashboard/posts/')


def admin_post_edit(request, post_id):
    """Admin: update post (modal submit), redirect to admin posts list."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    if request.method != 'POST':
        return redirect('/admin-dashboard/posts/')
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return redirect('/admin-dashboard/posts/')
    content = request.POST.get('content', '').strip()
    image = request.POST.get('image', '').strip()
    if not content:
        return redirect('/admin-dashboard/posts/?error=content')
    post.content = content
    post.image = image
    post.save()
    return redirect('/admin-dashboard/posts/')


def admin_post_json(request, post_id):
    """Admin: get one post as JSON (for edit modal)."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        p = Post.objects.get(id=post_id)
        return JsonResponse({'id': p.id, 'content': p.content or '', 'image': p.image or ''})
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


def admin_group_create(request):
    """Admin: create group (modal submit), redirect to admin groups list."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    if request.method != 'POST':
        return redirect('/admin-dashboard/groups/')
    title = request.POST.get('title', '').strip()
    groupid = request.POST.get('groupid', '').strip()
    description = request.POST.get('description', '')
    if not title:
        return redirect('/admin-dashboard/groups/?error=title')
    if not groupid:
        return redirect('/admin-dashboard/groups/?error=groupid')
    if Group.objects.filter(groupid=groupid).exists():
        return redirect('/admin-dashboard/groups/?error=exists')
    Group.objects.create(groupid=groupid, title=title, creator=request.user, description=description)
    return redirect('/admin-dashboard/groups/')


def admin_path_create(request):
    """Admin: create path (modal submit), redirect to admin paths list."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    if request.method != 'POST':
        return redirect('/admin-dashboard/paths/')
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '')
    language = request.POST.get('language', '').strip()
    target_level = request.POST.get('target_level', '').strip()
    if not title:
        return redirect('/admin-dashboard/paths/?error=title')
    LearningPath.objects.create(user=request.user, title=title, description=description, language=language, target_level=target_level)
    return redirect('/admin-dashboard/paths/')


def admin_path_edit(request, path_id):
    """Admin: update path (modal submit), redirect to admin paths list."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return redirect('/')
    if request.method != 'POST':
        return redirect('/admin-dashboard/paths/')
    try:
        path = LearningPath.objects.get(id=path_id)
    except LearningPath.DoesNotExist:
        return redirect('/admin-dashboard/paths/')
    if path.user_id != request.user.id and not _is_admin_user(request.user):
        return redirect('/admin-dashboard/paths/')
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '')
    language = request.POST.get('language', '').strip()
    target_level = request.POST.get('target_level', '').strip()
    if not title:
        return redirect('/admin-dashboard/paths/?error=title')
    path.title = title
    path.description = description
    path.language = language
    path.target_level = target_level
    path.save()
    return redirect('/admin-dashboard/paths/')


def admin_path_json(request, path_id):
    """Admin: get one path as JSON (for edit modal)."""
    if not request.user.is_authenticated or not _is_admin_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        p = LearningPath.objects.get(id=path_id)
        return JsonResponse({
            'id': p.id, 'title': p.title or '', 'description': p.description or '',
            'language': p.language or '', 'target_level': p.target_level or '',
        })
    except LearningPath.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

