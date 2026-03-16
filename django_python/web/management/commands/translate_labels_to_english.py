#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from web.models import Resource, LearningPath


LANGUAGE_MAP = {
    u"法语": u"French",
    u"英语": u"English",
    u"维语": u"Uyghur",
    u"维吾尔语": u"Uyghur",
    u"日语": u"Japanese",
    u"俄语": u"Russian",
    u"德语": u"German",
    u"韩语": u"Korean",
    u"汉语": u"Chinese",
    u"汉文": u"Chinese",
    u"多语言": u"Multi-language",
}

SCHOLAR_LEVEL_MAP = {
    u"初级学者": u"Beginner Scholar",
    u"中级学者": u"Intermediate Scholar",
    u"高级学者": u"Advanced Scholar",
}


class Command(BaseCommand):
    help = u"Translate Chinese labels in Resource.ltype and LearningPath.language/target_level into English."

    def handle(self, *args, **options):
        self.stdout.write(u"Translating Resource.ltype ...")
        updated_resources = 0
        for res in Resource.objects.all():
            old = (res.ltype or u"").strip()
            new = LANGUAGE_MAP.get(old, old)
            if new != old:
                res.ltype = new
                res.save(update_fields=['ltype'])
                updated_resources += 1
        self.stdout.write(u"Updated %d Resource rows." % updated_resources)

        self.stdout.write(u"Translating LearningPath.language and target_level ...")
        updated_paths = 0
        for path in LearningPath.objects.all():
            changed = False
            lang_old = (path.language or u"").strip()
            lang_new = LANGUAGE_MAP.get(lang_old, lang_old)
            if lang_new != lang_old:
                path.language = lang_new
                changed = True

            level_old = (path.target_level or u"").strip()
            level_new = SCHOLAR_LEVEL_MAP.get(level_old, level_old)
            if level_new != level_old:
                path.target_level = level_new
                changed = True

            if changed:
                path.save(update_fields=['language', 'target_level'])
                updated_paths += 1

        self.stdout.write(u"Updated %d LearningPath rows." % updated_paths)

