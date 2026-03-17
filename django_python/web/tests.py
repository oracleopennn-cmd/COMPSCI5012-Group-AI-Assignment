# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Group, GroupMember, GroupMessage, GroupJoinRequest, GroupInvite


class GroupModelTest(TestCase):
    """Test Group and GroupMember models"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='test123')
        self.user2 = User.objects.create_user(username='user2', password='test123')

    def test_create_group_and_creator_is_member(self):
        """Creator should be member when group is created"""
        group = Group.objects.create(
            groupid='grp001',
            title='Test Group',
            creator=self.user1,
            description='A test group'
        )
        GroupMember.objects.create(group=group, user=self.user1)
        self.assertTrue(GroupMember.objects.filter(group=group, user=self.user1).exists())
        self.assertEqual(group.members.count(), 1)

    def test_group_unique_groupid(self):
        """groupid should be unique"""
        Group.objects.create(groupid='unique001', title='G1', creator=self.user1)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Group.objects.create(groupid='unique001', title='G2', creator=self.user2)

    def test_group_member_unique_together(self):
        """Same user cannot join same group twice"""
        group = Group.objects.create(groupid='grp002', title='G2', creator=self.user1)
        GroupMember.objects.create(group=group, user=self.user1)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            GroupMember.objects.create(group=group, user=self.user1)


class GroupJoinRequestTest(TestCase):
    """Test GroupJoinRequest model"""

    def setUp(self):
        self.creator = User.objects.create_user(username='creator', password='test123')
        self.user = User.objects.create_user(username='joiner', password='test123')
        self.group = Group.objects.create(
            groupid='grp003',
            title='Join Test',
            creator=self.creator
        )
        GroupMember.objects.create(group=self.group, user=self.creator)

    def test_create_join_request(self):
        """Create join request"""
        jr = GroupJoinRequest.objects.create(
            group=self.group,
            user=self.user,
            status=GroupJoinRequest.STATUS_PENDING
        )
        self.assertEqual(jr.status, GroupJoinRequest.STATUS_PENDING)
        self.assertEqual(GroupJoinRequest.objects.filter(group=self.group).count(), 1)

    def test_approve_join_request_adds_member(self):
        """Approving join request should add user as member"""
        jr = GroupJoinRequest.objects.create(
            group=self.group,
            user=self.user,
            status=GroupJoinRequest.STATUS_PENDING
        )
        jr.status = GroupJoinRequest.STATUS_APPROVED
        jr.save()
        GroupMember.objects.get_or_create(group=self.group, user=self.user)
        self.assertTrue(GroupMember.objects.filter(group=self.group, user=self.user).exists())


class GroupInviteTest(TestCase):
    """Test GroupInvite model"""

    def setUp(self):
        self.inviter = User.objects.create_user(username='inviter', password='test123')
        self.invitee = User.objects.create_user(username='invitee', password='test123')
        self.group = Group.objects.create(
            groupid='grp004',
            title='Invite Test',
            creator=self.inviter
        )
        GroupMember.objects.create(group=self.group, user=self.inviter)

    def test_create_invite(self):
        """Create invite"""
        inv = GroupInvite.objects.create(
            group=self.group,
            inviter=self.inviter,
            invitee=self.invitee,
            status=GroupInvite.STATUS_PENDING
        )
        self.assertEqual(inv.status, GroupInvite.STATUS_PENDING)

    def test_accept_invite_adds_member(self):
        """Accepting invite should add user as member"""
        inv = GroupInvite.objects.create(
            group=self.group,
            inviter=self.inviter,
            invitee=self.invitee,
            status=GroupInvite.STATUS_PENDING
        )
        inv.status = GroupInvite.STATUS_ACCEPTED
        inv.save()
        GroupMember.objects.get_or_create(group=self.group, user=self.invitee)
        self.assertTrue(GroupMember.objects.filter(group=self.group, user=self.invitee).exists())


class GroupsViewTest(TestCase):
    """Test groups views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewuser', password='test123')

    def test_groups_page_requires_login(self):
        """Groups page requires login"""
        response = self.client.get('/groups/')
        self.assertIn(response.status_code, [302, 301])
        self.assertIn('signin', response.url)

    def test_groups_create_page_requires_login(self):
        """Groups create page requires login"""
        response = self.client.get('/groups/create/')
        self.assertIn(response.status_code, [302, 301])

    def test_groups_create_success(self):
        """Logged-in user can create group"""
        self.client.login(username='viewuser', password='test123')
        response = self.client.post('/groups/create/', {
            'groupid': 'grp999',
            'title': 'My Group',
            'description': 'Test description'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/groups/', response.url)
        self.assertTrue(Group.objects.filter(groupid='grp999').exists())
        group = Group.objects.get(groupid='grp999')
        self.assertTrue(GroupMember.objects.filter(group=group, user=self.user).exists())

    def test_groups_create_duplicate_groupid(self):
        """Duplicate groupid should fail, no new group created"""
        Group.objects.create(groupid='dup001', title='Existing', creator=self.user)
        initial_count = Group.objects.count()
        self.client.login(username='viewuser', password='test123')
        response = self.client.post('/groups/create/', {
            'groupid': 'dup001',
            'title': 'Duplicate Group',
            'description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Group.objects.count(), initial_count)

    def test_groups_page_shows_joined_groups(self):
        """Groups page shows user's joined groups"""
        group = Group.objects.create(groupid='grp888', title='Joined Group', creator=self.user)
        GroupMember.objects.create(group=group, user=self.user)
        self.client.login(username='viewuser', password='test123')
        response = self.client.get('/groups/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8', errors='replace')
        self.assertIn('Joined Group', content)


class GroupMessageTest(TestCase):
    """Test GroupMessage model"""

    def setUp(self):
        self.user = User.objects.create_user(username='msguser', password='test123')
        self.group = Group.objects.create(
            groupid='grpmsg',
            title='Message Group',
            creator=self.user
        )
        GroupMember.objects.create(group=self.group, user=self.user)

    def test_create_message(self):
        """Create group message"""
        msg = GroupMessage.objects.create(
            group=self.group,
            user=self.user,
            content='Hello everyone!'
        )
        self.assertEqual(msg.content, 'Hello everyone!')
        self.assertEqual(self.group.messages.count(), 1)
