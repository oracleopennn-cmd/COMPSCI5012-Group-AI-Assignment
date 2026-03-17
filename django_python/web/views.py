# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q, Max, Count
from django.db.utils import IntegrityError, OperationalError
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
    # Difficulty range per scholar level
    difficulty_map = {
        1: (1, 2),  # Beginner: difficulty 1–2
        2: (2, 3),  # Intermediate: difficulty 2–3
        3: (3, 4),  # Advanced: difficulty 3–4
    }
    min_difficulty, max_difficulty = difficulty_map.get(scholar_level, (1, 2))
    
    # Pick random resources in the difficulty range (up to 9)
    resources = Resource.objects.filter(
        difficulty__gte=min_difficulty,
        difficulty__lte=max_difficulty
    ).order_by('?')[:9]
    
    if resources.exists():
        # Create learning path
        level_names = {
            1: u"Beginner Scholar",
            2: u"Intermediate Scholar",
            3: u"Advanced Scholar",
        }
        level_name = level_names.get(scholar_level, u"Beginner Scholar")
        
        path = LearningPath.objects.create(
            user=user,
            title=u"%s - Initial Learning Plan" % level_name,
            description=u"Automatically generated initial learning plan with resources that match your current level.",
            language=u"Multi-language",
            target_level=level_name,
        )
        
        # Attach resources to the learning path
        for idx, resource in enumerate(resources):
            LearningPathItem.objects.create(
                path=path,
                resource=resource,
                order=idx + 1,
            )
        
        return path
    return None


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

    return render(request, 'signup.html', {'error': error})


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

    return render(request, 'login.html', {'error': error})


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
    if not request.user.is_authenticated:
        return redirect('/user/signin/?next=/groups/')
    
    # Get groups the user has joined
    user_groups = Group.objects.filter(members__user=request.user).distinct()
    
    group_list = []
    for group in user_groups:
        member_count = group.members.count()
        message_count = group.messages.count()
        group_list.append({
            'id': group.id,
            'groupid': group.groupid,
            'title': group.title,
            'description': group.description,
            'creator': group.creator.username,
            'member_count': member_count,
            'message_count': message_count,
            'created_at': group.created_at.strftime("%Y/%m/%d"),
        })
    
    context = {
        'groups': group_list,
        'pending_invites': [],
        'pending_join_requests': [],
        'my_pending_requests': [],
    }

    # Pending invites for current user
    pending_invites_qs = GroupInvite.objects.select_related('group', 'inviter').filter(
        invitee=request.user,
        status=GroupInvite.STATUS_PENDING
    )
    context['pending_invites'] = [
        {
            'id': inv.id,
            'group': {'id': inv.group.id, 'title': inv.group.title, 'groupid': inv.group.groupid},
            'inviter': inv.inviter.username,
            'created_at': inv.created_at.strftime("%Y/%m/%d %H:%M:%S"),
        }
        for inv in pending_invites_qs
    ]

    # Pending join requests for groups owned by current user
    pending_reqs_qs = GroupJoinRequest.objects.select_related('group', 'user').filter(
        group__creator=request.user,
        status=GroupJoinRequest.STATUS_PENDING
    )
    context['pending_join_requests'] = [
        {
            'id': jr.id,
            'group': {'id': jr.group.id, 'title': jr.group.title, 'groupid': jr.group.groupid},
            'user': jr.user.username,
            'message': jr.message,
            'created_at': jr.created_at.strftime("%Y/%m/%d %H:%M:%S"),
        }
        for jr in pending_reqs_qs
    ]

    # My pending join requests
    my_pending = GroupJoinRequest.objects.select_related('group').filter(
        user=request.user,
        status=GroupJoinRequest.STATUS_PENDING
    )
    context['my_pending_requests'] = [
        {
            'id': jr.id,
            'group': {'id': jr.group.id, 'title': jr.group.title, 'groupid': jr.group.groupid},
            'created_at': jr.created_at.strftime("%Y/%m/%d %H:%M:%S"),
        }
        for jr in my_pending
    ]
    return render(request, 'groups.html', context)


def groups_detail_page(request, group_id):
    """
    Group detail page: show group info and messages.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/')
    
    try:
        group = Group.objects.prefetch_related('members__user', 'messages__user').get(id=group_id)
        # 检查用户是否是群组成员
        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return redirect('/groups/')
    except Group.DoesNotExist:
        return redirect('/groups/')
    
    # 获取消息列表
    messages = group.messages.all()[:50]  # 最近50条消息
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'user': msg.user.username,
            'content': msg.content,
            'created_at': msg.created_at.strftime("%Y/%m/%d %H:%M:%S"),
            'is_own': msg.user.id == request.user.id,
        })
    
    # 获取成员列表
    members = group.members.all()
    is_owner = (group.creator_id == request.user.id) or _is_admin_user(request.user)
    member_list = []
    for member in members:
        member_list.append({
            'id': member.user.id,
            'username': member.user.username,
            'joined_at': member.joined_at.strftime("%Y/%m/%d"),
            'can_kick': bool(is_owner and (member.user_id != group.creator_id)),
        })
    
    context = {
        'group': {
            'id': group.id,
            'groupid': group.groupid,
            'title': group.title,
            'description': group.description,
            'creator': group.creator.username,
            'is_owner': bool(is_owner),
        },
        'messages': message_list,
        'members': member_list,
    }
    return render(request, 'groups_detail.html', context)


def groups_create(request):
    """
    Create a new group.
    """
    if not request.user.is_authenticated:
        return redirect('/user/signin/')
    
    error = None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        groupid = request.POST.get('groupid', '').strip()
        
        if not title:
            error = u"Group name is required."
        elif not groupid:
            error = u"Group ID is required."
        elif Group.objects.filter(groupid=groupid).exists():
            error = u"Group ID already exists."
        else:
            try:
                with transaction.atomic():
                    group = Group.objects.create(
                        groupid=groupid,
                        title=title,
                        description=description,
                        creator=request.user,
                    )
                    GroupMember.objects.create(group=group, user=request.user)
                return redirect('/groups/%s/' % group.id)
            except (IntegrityError, OperationalError):
                error = u"Group creation failed (possibly duplicate Group ID). Please try again."
    
    # 生成随机群组ID
    import random
    random_groupid = ''.join([str(random.randint(0, 9)) for _ in range(5)])
    
    context = {
        'error': error,
        'random_groupid': random_groupid,
    }
    return render(request, 'groups_create.html', context)


def groups_join(request):
    """
    Request to join a group by group ID (creator approval required).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    
    if request.method == 'POST':
        groupid = request.POST.get('groupid', '').strip()
        if not groupid:
            return JsonResponse({'error': 'Group ID is required.'}, status=400)
        
        try:
            with transaction.atomic():
                group = Group.objects.get(groupid=groupid)
                if GroupMember.objects.filter(group=group, user=request.user).exists():
                    return JsonResponse({'success': True, 'message': 'Already a member.', 'group_id': group.id})

                if group.creator_id == request.user.id:
                    GroupMember.objects.get_or_create(group=group, user=request.user)
                    return JsonResponse({'success': True, 'message': 'Owner joined.', 'group_id': group.id})

                jr, created = GroupJoinRequest.objects.get_or_create(
                    group=group,
                    user=request.user,
                    defaults={'status': GroupJoinRequest.STATUS_PENDING}
                )
                if not created:
                    if jr.status in [GroupJoinRequest.STATUS_REJECTED, GroupJoinRequest.STATUS_CANCELLED]:
                        jr.status = GroupJoinRequest.STATUS_PENDING
                        jr.handled_at = None
                        jr.handled_by = None
                        jr.save()
                    elif jr.status == GroupJoinRequest.STATUS_APPROVED:
                        GroupMember.objects.get_or_create(group=group, user=request.user)
                        return JsonResponse({'success': True, 'message': 'Joined.', 'group_id': group.id})

                return JsonResponse({'success': True, 'message': 'Join request submitted.', 'group_id': group.id, 'request_id': jr.id})
        except Group.DoesNotExist:
            return JsonResponse({'error': 'Group does not exist.'}, status=404)
        except (IntegrityError, OperationalError):
            return JsonResponse({'error': 'Operation failed. Please try again.'}, status=500)
    
    return JsonResponse({'error': 'Invalid request.'}, status=400)


def groups_handle_join_request(request, req_id):
    """
    Approve or reject a join request (group creator/admin only).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    action = (request.POST.get('action') or '').strip().lower()
    if action not in ['approve', 'reject']:
        return JsonResponse({'error': 'Invalid action.'}, status=400)

    try:
        jr = GroupJoinRequest.objects.select_related('group', 'user').get(id=req_id)
    except GroupJoinRequest.DoesNotExist:
        return JsonResponse({'error': 'Request does not exist.'}, status=404)

    if (jr.group.creator_id != request.user.id) and (not _is_admin_user(request.user)):
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    if jr.status != GroupJoinRequest.STATUS_PENDING:
        return JsonResponse({'error': 'Request is not pending.'}, status=400)

    jr.handled_by = request.user
    jr.handled_at = timezone.now()

    try:
        with transaction.atomic():
            if action == 'approve':
                jr.status = GroupJoinRequest.STATUS_APPROVED
                jr.save()
                GroupMember.objects.get_or_create(group=jr.group, user=jr.user)
                return JsonResponse({'success': True, 'status': 'approved'})
            else:
                jr.status = GroupJoinRequest.STATUS_REJECTED
                jr.save()
                return JsonResponse({'success': True, 'status': 'rejected'})
    except (IntegrityError, OperationalError):
        return JsonResponse({'error': 'Operation failed. Please try again.'}, status=500)


def groups_invite(request, group_id):
    """
    Invite a user to a group (invitee must accept).
    Only group creator/admin can invite.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    username = (request.POST.get('username') or '').strip()
    if not username:
        return JsonResponse({'error': 'Username is required.'}, status=400)

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group does not exist.'}, status=404)

    is_owner = (group.creator_id == request.user.id) or _is_admin_user(request.user)
    if not is_owner:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    try:
        invitee = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist.'}, status=404)

    if GroupMember.objects.filter(group=group, user=invitee).exists():
        return JsonResponse({'success': True, 'message': 'User is already a member.'})

    try:
        with transaction.atomic():
            inv, created = GroupInvite.objects.get_or_create(
                group=group,
                invitee=invitee,
                defaults={
                    'inviter': request.user,
                    'status': GroupInvite.STATUS_PENDING,
                }
            )
            if created:
                GroupMember.objects.filter(group=group, user=invitee).delete()
                return JsonResponse({'success': True, 'message': 'Invite sent.', 'invite_id': inv.id})
            # Existing invite
            if inv.status in [GroupInvite.STATUS_DECLINED, GroupInvite.STATUS_CANCELLED]:
                inv.status = GroupInvite.STATUS_PENDING
                inv.inviter = request.user
                inv.responded_at = None
                inv.save()
            elif inv.status == GroupInvite.STATUS_ACCEPTED:
                # Invite says accepted but invitee is not in group (e.g. old data or was kicked).
                # Reset to PENDING so they can see it on /groups/ and accept again.
                inv.status = GroupInvite.STATUS_PENDING
                inv.inviter = request.user
                inv.responded_at = None
                inv.save()
            GroupMember.objects.filter(group=group, user=invitee).delete()
            return JsonResponse({'success': True, 'message': 'Invite sent.', 'invite_id': inv.id})
    except (IntegrityError, OperationalError):
        return JsonResponse({'error': 'Operation failed. Please try again.'}, status=500)


def groups_respond_invite(request, invite_id):
    """
    Invitee accepts/declines an invitation.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    action = (request.POST.get('action') or '').strip().lower()
    if action not in ['accept', 'decline']:
        return JsonResponse({'error': 'Invalid action.'}, status=400)

    try:
        inv = GroupInvite.objects.select_related('group', 'invitee').get(id=invite_id)
    except GroupInvite.DoesNotExist:
        return JsonResponse({'error': 'Invite does not exist.'}, status=404)

    if inv.invitee_id != request.user.id and (not _is_admin_user(request.user)):
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    if inv.status != GroupInvite.STATUS_PENDING:
        return JsonResponse({'error': 'Invite is not pending.'}, status=400)

    inv.responded_at = timezone.now()
    try:
        with transaction.atomic():
            if action == 'accept':
                inv.status = GroupInvite.STATUS_ACCEPTED
                inv.save()
                GroupMember.objects.get_or_create(group=inv.group, user=inv.invitee)
                return JsonResponse({'success': True, 'status': 'accepted', 'group_id': inv.group_id})
            else:
                inv.status = GroupInvite.STATUS_DECLINED
                inv.save()
                return JsonResponse({'success': True, 'status': 'declined'})
    except (IntegrityError, OperationalError):
        return JsonResponse({'error': 'Operation failed. Please try again.'}, status=500)


def groups_kick_member(request, group_id, user_id):
    """
    Group creator kicks a member.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group does not exist.'}, status=404)

    is_owner = (group.creator_id == request.user.id) or _is_admin_user(request.user)
    if not is_owner:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    if int(user_id) == int(group.creator_id):
        return JsonResponse({'error': 'Cannot kick the group owner.'}, status=400)

    try:
        with transaction.atomic():
            GroupMember.objects.filter(group=group, user_id=user_id).delete()
        return JsonResponse({'success': True})
    except (IntegrityError, OperationalError) as e:
        return JsonResponse({'error': 'Operation failed. Please try again.'}, status=500)


def groups_send_message(request, group_id):
    """
    Send a group message.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    
    try:
        group = Group.objects.get(id=group_id)
        # Check membership
        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return JsonResponse({'error': 'You are not a member of this group.'}, status=403)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group does not exist.'}, status=404)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Message content is required.'}, status=400)
        
        try:
            with transaction.atomic():
                message = GroupMessage.objects.create(
                    group=group,
                    user=request.user,
                    content=content,
                )
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'user': message.user.username,
                    'content': message.content,
                    'created_at': message.created_at.strftime("%Y/%m/%d %H:%M:%S"),
                }
            })
        except (IntegrityError, OperationalError):
            return JsonResponse({'error': 'Failed to send message. Please try again.'}, status=500)
    
    return JsonResponse({'error': 'Invalid request.'}, status=400)


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
        with transaction.atomic():
            group = Group.objects.get(id=group_id)
            group.delete()
        return JsonResponse({'success': True})
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except (IntegrityError, OperationalError):
        return JsonResponse({'error': 'Delete failed. Please try again.'}, status=500)


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
    try:
        with transaction.atomic():
            group = Group.objects.create(groupid=groupid, title=title, creator=request.user, description=description)
            GroupMember.objects.create(group=group, user=request.user)
    except (IntegrityError, OperationalError):
        return redirect('/admin-dashboard/groups/?error=exists')
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

