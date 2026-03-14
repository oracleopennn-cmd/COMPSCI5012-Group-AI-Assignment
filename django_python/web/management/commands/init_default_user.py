# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from web.models import UserProfile, LearningPath, LearningPathItem, Resource


class Command(BaseCommand):
    help = u'Create default user (user / 123456) and initial learning path'

    def handle(self, *args, **options):
        username = 'user'
        password = '123456'
        scholar_level = 1  # default: Beginner Scholar
        
        user, created = User.objects.get_or_create(username=username)
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(u'Successfully created default user: %s / %s' % (username, password)))
        else:
            self.stdout.write(self.style.WARNING(u'User "%s" already exists' % username))
        
        # 创建或更新用户资料
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'scholar_level': scholar_level,
                'nickname': username,
            }
        )
        
        if not profile_created:
            # If profile already exists but has no scholar level, update it
            if not profile.scholar_level:
                profile.scholar_level = scholar_level
                profile.save()
        
        # Check whether an initial learning path already exists
        initial_path = LearningPath.objects.filter(
            user=user,
            title__contains=u"Initial Learning Plan"
        ).first()
        
        if not initial_path:
            # Create an initial learning path
            difficulty_map = {
                1: (1, 2),  # Beginner: 1-2
                2: (2, 3),  # Intermediate: 2-3
                3: (3, 4),  # Advanced: 3-4
            }
            min_difficulty, max_difficulty = difficulty_map.get(scholar_level, (1, 2))
            
            resources = Resource.objects.filter(
                difficulty__gte=min_difficulty,
                difficulty__lte=max_difficulty
            ).order_by('?')[:9]
            
            if resources.exists():
                level_names = {
                    1: u"Beginner Scholar",
                    2: u"Intermediate Scholar",
                    3: u"Advanced Scholar",
                }
                level_name = level_names.get(scholar_level, u"Beginner Scholar")
                
                path = LearningPath.objects.create(
                    user=user,
                    title=u"%s - Initial Learning Plan" % level_name,
                    description=u"Automatically generated initial learning plan with resources that match the current level.",
                    language=u"Multi-language",
                    target_level=level_name,
                )
                
                for idx, resource in enumerate(resources):
                    LearningPathItem.objects.create(
                        path=path,
                        resource=resource,
                        order=idx + 1,
                    )
                
                self.stdout.write(self.style.SUCCESS(u'Successfully created initial learning path for "%s"' % username))
            else:
                self.stdout.write(self.style.WARNING(u'Cannot create initial learning path (maybe not enough resources)'))
        else:
            self.stdout.write(self.style.WARNING(u'User "%s" already has an initial learning path, skipping' % username))
