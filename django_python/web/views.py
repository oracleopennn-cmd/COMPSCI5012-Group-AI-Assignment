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
    # Ensure we have a few sample resources (first-time setup)
    if not Resource.objects.exists():
        Resource.objects.create(
            title=u"[French Basics] Zero-to-Beginner Course Collection",
            desc=u"Study 10 minutes a day and get started with French from scratch.",
            url=u"https://www.bilibili.com/",
            ltype=u"French",
            difficulty=2,
            utype=u"bilibili",
            author=u"Language Learning Channel",
            time=u"· 2022-03-12",
        )
        Resource.objects.create(
            title=u"French: From A1 to B2",
            desc=u"Systematically improve your French level from A1 to B2.",
            url=u"https://www.bilibili.com/",
            ltype=u"French",
            difficulty=1,
            utype=u"bilibili",
            author=u"SampleAcademy",
            time=u"· 2020-09-22",
        )

    difficulty_label_map = {
        1: u"Beginner",
        2: u"Intermediate",
        3: u"Advanced",
        4: u"Hell",
    }

    # Recent / Recommended: random resources so the page changes each time
    recommend_qs = Resource.objects.order_by('?')[:9]
    recommend_videos = list(recommend_qs.values('id', 'title', 'ltype', 'difficulty', 'author', 'time', 'image', 'url'))
    for it in recommend_videos:
        it['title'] = _clean_str(it.get('title'))
        it['ltype'] = _clean_str(it.get('ltype'))
        it['author'] = _clean_str(it.get('author'))
        it['time'] = _clean_str(it.get('time'))
        it['url'] = _clean_str(it.get('url'))
        it['image'] = _clean_image(it.get('image'))
        try:
            it['difficulty_label'] = difficulty_label_map.get(int(it.get('difficulty') or 1), u"Beginner")
        except Exception:
            it['difficulty_label'] = u"Beginner"

    # Study records: filter by current user (if logged in)
    record_qs = StudyRecord.objects.select_related('resource').order_by('-time')
    if request.user.is_authenticated:
        record_qs = record_qs.filter(user=request.user)
    record_qs = record_qs[:5]

    study_records = []
    for r in record_qs:
        img = _clean_image(r.resource.image)
        study_records.append({
            "id": r.resource.id,
            "title": _clean_str(r.resource.title),
            "image": img,
            "studied_minutes": max(0, int(r.dura / 60000)),
            "date": r.time.strftime("%Y/%m/%d"),
        })

    # Similar users: simple mock data for now
    similar_users = [
        {"id": 1, "nickname": u"Admin", "role": u"Teacher"},
        {"id": 2, "nickname": u"1556677", "role": u"Student"},
        {"id": 3, "nickname": u"1234567890", "role": u"Student"},
    ]

    user_info = {
        "avatar": "avatar.png",
        "nickname": request.user.username if request.user.is_authenticated else u"Guest",
        "sex": 1,
        "remark": {u"age": 23, u"national": u"China"},
    }

    context = {
        "user": user_info,
        "recommend_videos": recommend_videos,
        "study_records": study_records,
        "similar_users": similar_users,
        "difficulty_label_map": difficulty_label_map,
    }
    return render(request, 'main.html', context)


def study_page(request):
    """
    Resource list page (port of the old Vue study.vue), with pagination.
    """
    qs = Resource.objects.all().order_by('-created_at')

    # Search: fuzzy match by title / description / language
    q = _clean_str(request.GET.get('q'))
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(desc__icontains=q) |
            Q(ltype__icontains=q)
        )

    total_count = Resource.objects.count()
    filtered_count = qs.count()

    paginator = Paginator(qs, 20)  # 20 per page to avoid rendering too many at once
    page = request.GET.get('page') or 1

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    resources = list(page_obj.object_list.values('id', 'title', 'desc', 'ltype', 'difficulty',
                                                 'author', 'time', 'image', 'url', 'utype'))
    for it in resources:
        it['title'] = _clean_str(it.get('title'))
        it['desc'] = _clean_str(it.get('desc'))
        it['ltype'] = _clean_str(it.get('ltype'))
        it['author'] = _clean_str(it.get('author'))
        it['time'] = _clean_str(it.get('time'))
        it['url'] = _clean_str(it.get('url'))
        it['utype'] = _clean_str(it.get('utype'))
        it['image'] = _clean_image(it.get('image'))

    # Check that the user owns the given learning path
    path_id = request.GET.get('path_id', '').strip()
    path_obj = None
    if path_id and request.user.is_authenticated:
        try:
            path_obj = LearningPath.objects.get(id=path_id, user=request.user)
        except LearningPath.DoesNotExist:
            path_obj = None

    context = {
        "resources": resources,
        "page_obj": page_obj,
        "paginator": paginator,
        "q": q,
        "total_count": total_count,
        "filtered_count": filtered_count,
        "path_id": path_id,
        "path": path_obj,
    }

    # Support AJAX: return only the HTML fragment and statistics
    if request.GET.get('partial') == '1':
        html = render_to_string('partials/study_list.html', context, request=request)
        return JsonResponse({
            'html': html,
            'total': total_count,
            'filtered': filtered_count,
            'page': page_obj.number,
            'pages': paginator.num_pages,
        })

    return render(request, 'study.html', context)


def record_page(request):
    """
    Study history page (port of the old Vue record.vue).
    """
    qs = StudyRecord.objects.select_related('resource').order_by('-time')
    if request.user.is_authenticated:
        qs = qs.filter(user=request.user)
    else:
        # 未登录用户不显示记录
        qs = StudyRecord.objects.none()

    records = []
    total_ms = 0
    last_time_obj = None

    for r in qs:
        total_ms += r.dura
        if last_time_obj is None:
            last_time_obj = r.time
        records.append({
            "id": r.id,
            "dura_ms": r.dura,
            "dura_minutes": round(r.dura / 60000.0, 1) if r.dura else 0,
            "time": r.time.strftime("%Y/%m/%d %H:%M:%S"),
            "time_date": r.time.strftime("%Y/%m/%d"),
            "resource": {
                "id": r.resource.id,
                "title": _clean_str(r.resource.title),
                "ltype": _clean_str(r.resource.ltype),
                "utype": _clean_str(r.resource.utype),
                "difficulty": r.resource.difficulty,
                "author": _clean_str(r.resource.author),
                "image": _clean_image(r.resource.image),
            },
        })

    total_hours = round(total_ms / 3600000.0, 1) if total_ms else 0
    total_times = len(records)
    recent_date = last_time_obj.strftime("%Y/%m/%d") if last_time_obj else u"-"

    context = {
        "records": records,
        "total_hours": total_hours,
        "total_times": total_times,
        "recent_date": recent_date,
    }
    return render(request, 'record.html', context)


def delete_record(request, record_id):
    """
    Delete a single study record for the current user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    try:
        record = StudyRecord.objects.get(id=record_id, user=request.user)
        record.delete()
        return JsonResponse({'success': True})
    except StudyRecord.DoesNotExist:
        return JsonResponse({'error': 'Record does not exist'}, status=404)


def clear_all_records(request):
    """
    Delete all study records for the current user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    StudyRecord.objects.filter(user=request.user).delete()
    return JsonResponse({'success': True})


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
    logout(request)
    return redirect('/')


def profile_view(request):
    """
    User profile page: view and edit basic info.
    """



def study_detail_page(request):
    """
    Resource detail + simple quiz page.
    Currently uses static questions; can be moved to DB later.
    """
    rid = request.GET.get('id') or '1'

    try:
        res_obj = Resource.objects.get(id=rid)
    except Resource.DoesNotExist:
        res_obj = None

    resource = {
        "id": int(rid) if rid.isdigit() else 0,
        "title": _clean_str(res_obj.title) if res_obj else (u"Sample resource #%s" % rid),
        "desc": _clean_str(res_obj.desc) if res_obj else u"This is a sample resource description. You can later connect real data here.",
        "ltype": _clean_str(res_obj.ltype) if res_obj else u"French",
        "url": build_player_url(res_obj) if res_obj else u"",
        "utype": _clean_str(res_obj.utype) if res_obj else u"",
    }

    # Related resources: same language type
    related_resources = []
    if res_obj is not None:
        rel_qs = Resource.objects.filter(ltype=res_obj.ltype).exclude(id=res_obj.id).order_by('-created_at')[:6]
        related_resources = [
            {
                "id": r.id,
                "title": _clean_str(r.title),
                "ltype": _clean_str(r.ltype),
                "author": _clean_str(r.author),
                "time": _clean_str(r.time),
                "image": _clean_image(r.image),
            }
            for r in rel_qs
        ]

    questions = [
        {
            "id": 1,
            "text": u"What language does this resource mainly teach?",
            "options": [u"Russian", u"French", u"Uyghur"],
            "answer": "1",
        },
        {
            "id": 2,
            "text": u"How long is recommended to study every day?",
            "options": [u"5 minutes", u"10 minutes", u"1 hour"],
            "answer": "1",
        },
    ]

    score = None
    selected = {}

    if request.method == 'POST':
        correct = 0
        total = len(questions)
        for q in questions:
            key = 'q_%s' % q["id"]
            val = request.POST.get(key)
            selected[str(q["id"])] = val
            if val == q["answer"]:
                correct += 1
        score = u"%d / %d" % (correct, total)

    context = {
        "resource": resource,
        "questions": questions,
        "score": score,
        "selected": selected,
        "related_resources": related_resources,
    }
    return render(request, 'study_detail.html', context)


def study_detail_record(request):
    """
    Record study duration for a resource.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    if request.method == 'POST':
        resource_id = request.POST.get('resource_id')
        duration = request.POST.get('duration', '0')

        if not resource_id:
            return JsonResponse({'error': 'Resource ID is required.'}, status=400)

        try:
            resource = Resource.objects.get(id=resource_id)
            duration_ms = int(duration)

            if duration_ms > 0:
                # Find or create a study record
                record, created = StudyRecord.objects.get_or_create(
                    user=request.user,
                    resource=resource,
                    defaults={
                        'time': timezone.now(),
                        'dura': duration_ms,
                    }
                )

                if not created:
                    # Update existing record: accumulate duration and refresh time
                    record.dura += duration_ms
                    record.time = timezone.now()
                    record.save()

                return JsonResponse({
                    'success': True,
                    'total_duration': record.dura,
                })
            else:
                return JsonResponse({'success': True, 'message': 'Duration too short, not recorded.'})
        except Resource.DoesNotExist:
            return JsonResponse({'error': 'Resource does not exist.'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid duration.'}, status=400)

    return JsonResponse({'error': 'Invalid request.'}, status=400)


def study_detail_legacy(request, rid):
    """
    兼容旧前端的 /study_detail/<id> 风格链接：
    - 如果 <id> 是纯数字，则重定向到 /study_detail/?id=<id>
    - 否则保持原路径但加上 ?id=，方便后端统一处理
    """
    rid_str = _clean_str(rid)
    return redirect('/study_detail/?id=%s' % rid_str)


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


