# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Resource(models.Model):
    """
    Learning resource table (port of the old Vue 'resource' structure).
    """

    def __unicode__(self):
        return self.title


class StudyRecord(models.Model):
    """
    Study record table (port of the old 'record' structure).
    """

    def __unicode__(self):
        return u"%s - %s" % (self.user or u"Anonymous", self.resource.title)


class LearningPath(models.Model):
    """
    Learning path table: user-created learning plans.
    """
    def __unicode__(self):
        return u"%s - %s" % (self.user.username, self.title)


class LearningPathItem(models.Model):
    """
    Learning path item: resources contained in a path, ordered.
    """

    def __unicode__(self):
        return u"%s - %s" % (self.path.title, self.resource.title)


class Post(models.Model):
    """
    Forum post table.
    """

    def __unicode__(self):
        return u"%s - %s" % (self.user.username, self.content[:50])


class Group(models.Model):
    """
    Study group table.
    """


    def __unicode__(self):
        return u"%s (%s)" % (self.title, self.groupid)


class GroupMember(models.Model):
    """
    Group member table.
    """

    def __unicode__(self):
        return u"%s in %s" % (self.user.username, self.group.title)


class GroupMessage(models.Model):
    """
    Group message table.
    """

    def __unicode__(self):
        return u"%s: %s" % (self.user.username, self.content[:30])


class GroupJoinRequest(models.Model):
    """
    Request to join a group (requires creator approval).
    """
    def __unicode__(self):
        return u"%s -> %s (%s)" % (self.user.username, self.group.title, self.status)


class GroupInvite(models.Model):
    """
    Invitation to join a group (invitee must accept).
    """

    def __unicode__(self):
        return u"Invite %s to %s (%s)" % (self.invitee.username, self.group.title, self.status)


class UserProfile(models.Model):
    """
    User profile table: extended user information.
    """

    def __unicode__(self):
        return u"%s - %s" % (self.user.username, self.get_scholar_level_display())

    def get_scholar_level_display(self):
        return
