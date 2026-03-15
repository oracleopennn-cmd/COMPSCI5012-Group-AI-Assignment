#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.core.management.base import BaseCommand

from web.models import Resource


CHINESE_RE = re.compile(u'[\u4e00-\u9fff]')


LANGUAGE_KEYWORDS = {
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
}

GENERIC_KEYWORDS = {
    u"零基础": u"Beginner",
    u"入门": u"Intro",
    u"初级": u"Beginner",
    u"中级": u"Intermediate",
    u"高级": u"Advanced",
    u"合集": u"Collection",
    u"全集": u"Complete Series",
    u"课程": u"Course",
    u"教程": u"Tutorial",
    u"系列": u"Series",
    u"一起学": u"Learn Together",
    u"学习": u"Learning",
    u"口语": u"Speaking",
    u"听力": u"Listening",
    u"语法": u"Grammar",
}


def has_chinese(text):
    if not text:
        return False
    return bool(CHINESE_RE.search(text))


def simple_replace(text):
    """
    Best-effort keyword replacement from Chinese to English.
    Does NOT try to fully translate sentences, just replaces known words.
    """
    if not text:
        return text

    new_text = text

    # Replace language words first
    for zh, en in LANGUAGE_KEYWORDS.items():
        new_text = new_text.replace(zh, en)

    # Then more generic words
    for zh, en in GENERIC_KEYWORDS.items():
        new_text = new_text.replace(zh, en)

    return new_text


class Command(BaseCommand):
    help = u"Best-effort: replace common Chinese words in Resource.title/desc with English (does not touch url/image)."

    def handle(self, *args, **options):
        updated = 0

        for res in Resource.objects.all():
            title = res.title or u""
            desc = res.desc or u""

            if not (has_chinese(title) or has_chinese(desc)):
                continue

            new_title = simple_replace(title)
            new_desc = simple_replace(desc)

            if new_title != title or new_desc != desc:
                res.title = new_title
                res.desc = new_desc
                res.save(update_fields=['title', 'desc'])
                updated += 1

        self.stdout.write(u"Updated %d resources (title/desc keyword replacement)." % updated)

