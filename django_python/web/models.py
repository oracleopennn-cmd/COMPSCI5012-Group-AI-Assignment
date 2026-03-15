# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Resource(models.Model):
    """
    Learning resource table (port of the old Vue 'resource' structure).
    """
    title = models.CharField(max_length=255)
    desc = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True, help_text=u"URL or external ID")
    ltype = models.CharField(max_length=50, help_text=u"Language type, e.g. French / Russian")
    difficulty = models.IntegerField(default=1, help_text=u"Difficulty level, 1-4")
    utype = models.CharField(max_length=50, blank=True, help_text=u"Platform type, e.g. bilibili / tiktok")
    author = models.CharField(max_length=255, blank=True)
    image = models.CharField(max_length=255, blank=True, help_text=u"Cover image filename or URL")
    time = models.CharField(max_length=50, blank=True, help_text=u"Published time text, e.g. · 2022-03-12")

    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title


class StudyRecord(models.Model):
    """
    Study record table (port of the old 'record' structure).
    """
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    resource = models.ForeignKey(Resource, related_name='records', on_delete=models.CASCADE)
    time = models.DateTimeField(help_text=u"Study time")
    dura = models.IntegerField(help_text=u"Study duration in milliseconds")

    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"%s - %s" % (self.user or u"Anonymous", self.resource.title)


class LearningPath(models.Model):
    """
    Learning path table: user-created learning plans.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text=u"Owner")
    title = models.CharField(max_length=255, help_text=u"Path title")
    description = models.TextField(blank=True, help_text=u"Description")
    language = models.CharField(max_length=50, blank=True, help_text=u"Target language, e.g. French / Russian")
    target_level = models.CharField(max_length=50, blank=True, help_text=u"Target level, e.g. A1 / B2")
    is_public = models.BooleanField(default=False, help_text=u"Whether this path is public")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __unicode__(self):
        return u"%s - %s" % (self.user.username, self.title)


class LearningPathItem(models.Model):
    """
    Learning path item: resources contained in a path, ordered.
    """
    path = models.ForeignKey(LearningPath, related_name='items', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    order = models.IntegerField(default=0, help_text=u"Order index; smaller means earlier")
    is_completed = models.BooleanField(default=False, help_text=u"Whether this item is completed")
    completed_at = models.DateTimeField(null=True, blank=True, help_text=u"Completion timestamp")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __unicode__(self):
        return u"%s - %s" % (self.path.title, self.resource.title)


class Post(models.Model):
    """
    Forum post table.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text=u"Author")
    content = models.TextField(help_text=u"Post content (HTML allowed)")
    image = models.CharField(max_length=255, blank=True, help_text=u"Post image URL or path")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __unicode__(self):
        return u"%s - %s" % (self.user.username, self.content[:50])


class Group(models.Model):
    """
    Study group table.
    """
    groupid = models.CharField(max_length=50, unique=True, help_text=u"Group ID")
    title = models.CharField(max_length=255, help_text=u"Group name")
    creator = models.ForeignKey(User, related_name='created_groups', on_delete=models.CASCADE, help_text=u"Creator")
    description = models.TextField(blank=True, help_text=u"Group description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __unicode__(self):
        return u"%s (%s)" % (self.title, self.groupid)


class GroupMember(models.Model):
    """
    Group member table.
    """
    group = models.ForeignKey(Group, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')
        ordering = ['-joined_at']

    def __unicode__(self):
        return u"%s in %s" % (self.user.username, self.group.title)


class GroupMessage(models.Model):
    """
    Group message table.
    """
    group = models.ForeignKey(Group, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(help_text=u"Message content")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __unicode__(self):
        return u"%s: %s" % (self.user.username, self.content[:30])


class GroupJoinRequest(models.Model):
    """
    Request to join a group (requires creator approval).
    """
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    group = models.ForeignKey(Group, related_name='join_requests', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='group_join_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    message = models.CharField(max_length=255, blank=True, help_text=u"Optional request message")

    created_at = models.DateTimeField(auto_now_add=True)
    handled_at = models.DateTimeField(null=True, blank=True)
    handled_by = models.ForeignKey(User, null=True, blank=True, related_name='handled_join_requests', on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('group', 'user')
        ordering = ['-created_at']

    def __unicode__(self):
        return u"%s -> %s (%s)" % (self.user.username, self.group.title, self.status)


class GroupInvite(models.Model):
    """
    Invitation to join a group (invitee must accept).
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    group = models.ForeignKey(Group, related_name='invites', on_delete=models.CASCADE)
    inviter = models.ForeignKey(User, related_name='sent_group_invites', on_delete=models.CASCADE)
    invitee = models.ForeignKey(User, related_name='received_group_invites', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('group', 'invitee')
        ordering = ['-created_at']

    def __unicode__(self):
        return u"Invite %s to %s (%s)" % (self.invitee.username, self.group.title, self.status)


class UserProfile(models.Model):
    """
    User profile table: extended user information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    scholar_level = models.IntegerField(default=1, help_text=u"Scholar level: 1=Beginner, 2=Intermediate, 3=Advanced")
    nickname = models.CharField(max_length=50, blank=True, help_text=u"Nickname")
    phone = models.CharField(max_length=20, blank=True, help_text=u"Phone number")
    avatar = models.CharField(max_length=255, blank=True, help_text=u"Avatar")
    sex = models.CharField(max_length=1, blank=True, help_text=u"Gender: M=Male, F=Female")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"%s - %s" % (self.user.username, self.get_scholar_level_display())

    def get_scholar_level_display(self):
        level_map = {
            1: u"Beginner Scholar",
            2: u"Intermediate Scholar",
            3: u"Advanced Scholar",
        }
        return level_map.get(self.scholar_level, u"Unknown")
