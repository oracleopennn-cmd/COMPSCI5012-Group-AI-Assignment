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
            group = Group.objects.create(
                groupid=groupid,
                title=title,
                description=description,
                creator=request.user,
            )
            # 创建者自动加入群组
            GroupMember.objects.create(group=group, user=request.user)
            return redirect('/groups/%s/' % group.id)

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
            group = Group.objects.get(groupid=groupid)
            if GroupMember.objects.filter(group=group, user=request.user).exists():
                return JsonResponse({'success': True, 'message': 'Already a member.', 'group_id': group.id})

            # Group owner auto-joins
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

    if action == 'approve':
        jr.status = GroupJoinRequest.STATUS_APPROVED
        jr.save()
        GroupMember.objects.get_or_create(group=jr.group, user=jr.user)
        return JsonResponse({'success': True, 'status': 'approved'})
    else:
        jr.status = GroupJoinRequest.STATUS_REJECTED
        jr.save()
        return JsonResponse({'success': True, 'status': 'rejected'})


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

    inv, created = GroupInvite.objects.get_or_create(group=group, invitee=invitee, defaults={'inviter': request.user})
    if not created:
        if inv.status in [GroupInvite.STATUS_DECLINED, GroupInvite.STATUS_CANCELLED]:
            inv.status = GroupInvite.STATUS_PENDING
            inv.inviter = request.user
            inv.responded_at = None
            inv.save()
        elif inv.status == GroupInvite.STATUS_ACCEPTED:
            GroupMember.objects.get_or_create(group=group, user=invitee)
            return JsonResponse({'success': True, 'message': 'User already accepted invite.'})

    return JsonResponse({'success': True, 'message': 'Invite sent.', 'invite_id': inv.id})


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
    if action == 'accept':
        inv.status = GroupInvite.STATUS_ACCEPTED
        inv.save()
        GroupMember.objects.get_or_create(group=inv.group, user=inv.invitee)
        return JsonResponse({'success': True, 'status': 'accepted', 'group_id': inv.group_id})
    else:
        inv.status = GroupInvite.STATUS_DECLINED
        inv.save()
        return JsonResponse({'success': True, 'status': 'declined'})


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

    GroupMember.objects.filter(group=group, user_id=user_id).delete()
    return JsonResponse({'success': True})


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

    return JsonResponse({'error': 'Invalid request.'}, status=400)


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
