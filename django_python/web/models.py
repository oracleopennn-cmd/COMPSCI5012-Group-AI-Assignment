# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Resource(models.Model):
    """
    Learning resource table (port of the old Vue 'resource' structure).
    """



class StudyRecord(models.Model):
    """
    Study record table (port of the old 'record' structure).
    """



class LearningPath(models.Model):
    """
    Learning path table: user-created learning plans.
    """



class LearningPathItem(models.Model):
    """
    Learning path item: resources contained in a path, ordered.
    """



class Post(models.Model):
    """
    Forum post table.
    """


class Group(models.Model):
    """
    Study group table.
    """



class GroupMember(models.Model):
    """
    Group member table.
    """



class GroupMessage(models.Model):
    """
    Group message table.
    """


class GroupJoinRequest(models.Model):
    """
    Request to join a group (requires creator approval).
    """



class GroupInvite(models.Model):
    """
    Invitation to join a group (invitee must accept).
    """



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
