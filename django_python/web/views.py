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

    return render(request, 'main.html')


def study_page(request):
    """
    Resource list page (port of the old Vue study.vue), with pagination.
    """


    return render(request, 'study.html')


def record_page(request):
    """
    Study history page (port of the old Vue record.vue).
    """

    return render(request, 'record.html')


def delete_record(request, record_id):
    """
    Delete a single study record for the current user.
    """

    return JsonResponse({'error': 'Record does not exist'}, status=404)


def clear_all_records(request):
    """
    Delete all study records for the current user.
    """

    return JsonResponse({'success': True})


def _create_initial_learning_path(user, scholar_level):
    """
    Create an initial learning path based on the scholar level.
    """

    return None


def signup_view(request):
    """
    Sign-up page: create Django User and initial learning path based on scholar level.
    """


    return render(request, 'signup.html', {'error': error})


def login_view(request):
    """
    Simple login page: username + password.
    """


    return render(request, 'login.html', {'error': error})


def logout_view(request):
    """
    Log out and return to the homepage.
    """
    logout(request)
    return redirect('/')


def profile_view(request):
    """
    User profile page: view and edit basic info.
    """

    return render(request, 'profile.html')


def study_detail_page(request):
    """
    Resource detail + simple quiz page.
    Currently uses static questions; can be moved to DB later.
    """

    return render(request, 'study_detail.html')


def study_detail_record(request):
    """
    Record study duration for a resource.
    """


    return JsonResponse({'error': 'Invalid request.'}, status=400)


def study_detail_legacy(request, rid):
    """
    For compatibility with legacy frontends, use the `/study_detail/<id>` style link:

    - If `<id>` is a pure number, redirect to `/study_detail/?id=<id>`

    - Otherwise, keep the original path but add `?id=` for easier backend handling.
    """
    rid_str = _clean_str(rid)
    return redirect('/study_detail/?id=%s' % rid_str)


def path_page(request):
    """
    Learning path overview: list all paths for the current user.
    """

    return render(request, 'path.html')


def path_detail_page(request, path_id):
    """
    Learning path detail: show and manage items in a path.
    """

    return render(request, 'path_detail.html')


def path_create(request):
    """
    Create a new learning path.
    """


    return render(request, 'path_create.html')


def path_edit(request, path_id):
    """
    Edit an existing learning path.
    Owner or admin can edit.
    """

    return render(request, 'path_edit.html')


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

    return render(request, 'forum.html')


def forum_new_post(request):
    """
    New post page.
    """

    return render(request, 'forum_new.html')


def forum_edit_post(request, post_id):
    """
    Edit a forum post.
    - Normal users can only edit their own posts
    - Admin can edit any posts
    """

    return render(request, 'forum_edit.html')


def forum_delete_post(request, post_id):
    """
    Delete a forum post (admin only).
    """



def groups_page(request):
    """
    Study groups page: list groups the user has joined.
    """

    return render(request, 'groups.html')


def groups_detail_page(request, group_id):
    """
    Group detail page: show group info and messages.
    """

    return render(request, 'groups_detail.html')


def groups_create(request):
    """
    Create a new group.
    """

    return render(request, 'groups_create.html')


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

    return render(request, 'admin_dashboard.html')


def admin_resource_edit(request, resource_id):
    """Admin: edit any resource."""

    return render(request, 'admin_resource_edit.html')


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

    return render(request, 'admin_resource_edit.html', )


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


