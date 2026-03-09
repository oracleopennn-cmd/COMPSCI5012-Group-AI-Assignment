#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # 对应原 Vue main.vue 的页面
    url(r'^main/$', views.main_page, name='main_page'),
    # 学习资源列表页
    url(r'^study/$', views.study_page, name='study_page'),
    # 学习记录页
    url(r'^record/$', views.record_page, name='record_page'),
    # 删除学习记录
    url(r'^record/delete/(?P<record_id>\d+)/$', views.delete_record, name='delete_record'),
    url(r'^record/clear/$', views.clear_all_records, name='clear_all_records'),
    # 用户认证相关
    url(r'^user/signin/$', views.login_view, name='login'),
    url(r'^user/signup/$', views.signup_view, name='signup'),
    url(r'^user/logout/$', views.logout_view, name='logout'),
    url(r'^user/profile/$', views.profile_view, name='profile'),
    # 资源详情与答题
    url(r'^study_detail/$', views.study_detail_page, name='study_detail'),
    url(r'^study_detail/record/$', views.study_detail_record, name='study_detail_record'),
    # 兼容旧链接：/study_detail/<id> 形式，自动跳转到 ?id=
    url(r'^study_detail/(?P<rid>[^/]+)/$', views.study_detail_legacy, name='study_detail_legacy'),
    # 学习规划相关
    url(r'^path/$', views.path_page, name='path_page'),
    url(r'^path/create/$', views.path_create, name='path_create'),
    url(r'^path/(?P<path_id>\d+)/$', views.path_detail_page, name='path_detail'),
    url(r'^path/(?P<path_id>\d+)/edit/$', views.path_edit, name='path_edit'),
    url(r'^path/(?P<path_id>\d+)/delete/$', views.path_delete, name='path_delete'),
    url(r'^path/(?P<path_id>\d+)/add-resource/$', views.path_add_resource, name='path_add_resource'),
    url(r'^path/(?P<path_id>\d+)/remove-resource/(?P<item_id>\d+)/$', views.path_remove_resource, name='path_remove_resource'),
    url(r'^path/(?P<path_id>\d+)/toggle-complete/(?P<item_id>\d+)/$', views.path_toggle_complete, name='path_toggle_complete'),
    # 论坛相关
    url(r'^forum/$', views.forum_page, name='forum_page'),
    url(r'^forum/new/$', views.forum_new_post, name='forum_new_post'),
    url(r'^forum/(?P<post_id>\d+)/edit/$', views.forum_edit_post, name='forum_edit_post'),
    url(r'^forum/(?P<post_id>\d+)/delete/$', views.forum_delete_post, name='forum_delete_post'),
    # 学习群组相关
    url(r'^groups/$', views.groups_page, name='groups_page'),
    url(r'^groups/create/$', views.groups_create, name='groups_create'),
    url(r'^groups/join/$', views.groups_join, name='groups_join'),
    url(r'^groups/join-request/(?P<req_id>\d+)/$', views.groups_handle_join_request, name='groups_handle_join_request'),
    url(r'^groups/(?P<group_id>\d+)/$', views.groups_detail_page, name='groups_detail'),
    url(r'^groups/(?P<group_id>\d+)/send/$', views.groups_send_message, name='groups_send_message'),
    url(r'^groups/(?P<group_id>\d+)/invite/$', views.groups_invite, name='groups_invite'),
    url(r'^groups/invite/(?P<invite_id>\d+)/respond/$', views.groups_respond_invite, name='groups_respond_invite'),
    url(r'^groups/(?P<group_id>\d+)/kick/(?P<user_id>\d+)/$', views.groups_kick_member, name='groups_kick_member'),
    # Admin dashboard
    url(r'^admin-dashboard/$', views.admin_dashboard, name='admin_dashboard'),
    url(r'^admin-dashboard/resources/$', views.admin_resources_list, name='admin_resources_list'),
    url(r'^admin-dashboard/resources/new/$', views.admin_resource_create, name='admin_resource_create'),
    url(r'^admin-dashboard/resource/(?P<resource_id>\d+)/edit/$', views.admin_resource_edit, name='admin_resource_edit'),
    url(r'^admin-dashboard/resource/(?P<resource_id>\d+)/json/$', views.admin_resource_json, name='admin_resource_json'),
    url(r'^admin-dashboard/resource/(?P<resource_id>\d+)/delete/$', views.admin_resource_delete, name='admin_resource_delete'),
    url(r'^admin-dashboard/posts/$', views.admin_posts_list, name='admin_posts_list'),
    url(r'^admin-dashboard/posts/new/$', views.admin_post_create, name='admin_post_create'),
    url(r'^admin-dashboard/post/(?P<post_id>\d+)/edit/$', views.admin_post_edit, name='admin_post_edit'),
    url(r'^admin-dashboard/post/(?P<post_id>\d+)/json/$', views.admin_post_json, name='admin_post_json'),
    url(r'^admin-dashboard/groups/$', views.admin_groups_list, name='admin_groups_list'),
    url(r'^admin-dashboard/groups/new/$', views.admin_group_create, name='admin_group_create'),
    url(r'^admin-dashboard/users/$', views.admin_users_list, name='admin_users_list'),
    url(r'^admin-dashboard/users/new/$', views.admin_user_create, name='admin_user_create'),
    url(r'^admin-dashboard/paths/$', views.admin_paths_list, name='admin_paths_list'),
    url(r'^admin-dashboard/paths/new/$', views.admin_path_create, name='admin_path_create'),
    url(r'^admin-dashboard/path/(?P<path_id>\d+)/edit/$', views.admin_path_edit, name='admin_path_edit'),
    url(r'^admin-dashboard/path/(?P<path_id>\d+)/json/$', views.admin_path_json, name='admin_path_json'),
    url(r'^admin-dashboard/group/(?P<group_id>\d+)/delete/$', views.admin_group_delete, name='admin_group_delete'),
    url(r'^admin-dashboard/user/(?P<user_id>\d+)/delete/$', views.admin_user_delete, name='admin_user_delete'),
]

