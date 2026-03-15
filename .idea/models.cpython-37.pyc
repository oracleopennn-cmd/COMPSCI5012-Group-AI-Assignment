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
