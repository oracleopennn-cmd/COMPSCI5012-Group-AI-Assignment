#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import csv
import io
import os
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from web.models import Resource, StudyRecord


class Command(BaseCommand):
    help = u"Import resource and record data from gd_language_resources.sql into SQLite (Django models)"

    def handle(self, *args, **options):
        root_dir = os.path.dirname(settings.BASE_DIR)
        sql_path = os.path.join(root_dir, 'gd_language_resources.sql')

        if not os.path.exists(sql_path):
            self.stderr.write(u"Cannot find SQL file: %s" % sql_path)
            return

        self.stdout.write(u"Reading SQL file: %s" % sql_path)

        imported_resources = 0
        imported_records = 0

        def to_text(val):
            """
            Convert raw SQL field value into a unicode string (Py2-safe).
            """
            if val is None:
                return u''
            if isinstance(val, unicode):
                return val
            # Py2: csv gives us byte-str; decode explicitly
            try:
                return val.decode('utf-8')
            except Exception:
                try:
                    return unicode(val, 'utf-8', errors='replace')
                except Exception:
                    return unicode(str(val), 'utf-8', errors='replace')

        def clean(val):
            v = to_text(val).strip()
            if (v.startswith(u"'") and v.endswith(u"'")) or (v.startswith(u'"') and v.endswith(u'"')):
                v = v[1:-1]
            return v.strip()

        # Read SQL as UTF-8 (Navicat export says 65001). Also tolerate BOM.
        with io.open(sql_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith('INSERT INTO'):
                    continue

                if line.startswith("INSERT INTO `resource`"):
                    values_str = line.split('VALUES', 1)[1].strip()
                    start = values_str.find('(')
                    end = values_str.rfind(')')
                    if start == -1 or end == -1:
                        continue
                    values_str = values_str[start + 1:end]

                    for row in csv.reader([values_str.encode('utf-8')], delimiter=str(','), quotechar=str("'"),
                                          escapechar=str('\\'), skipinitialspace=True):
                        # Normalize to unicode and NULLs to None (avoid Py2 ascii decode issues)
                        row_u = []
                        for v in row:
                            vu = to_text(v)
                            if vu.strip().upper() == u'NULL':
                                row_u.append(None)
                            else:
                                row_u.append(vu)
                        row = row_u
                        if len(row) < 11:
                            continue
                        rid, title, desc, url, ltype, difficulty, utype, author, rtime, image, test = row[:11]

                        try:
                            pk = int(rid)
                        except Exception:
                            pk = None

                        try:
                            difficulty_val = int(difficulty) if difficulty is not None else 1
                        except Exception:
                            difficulty_val = 1

                        # Normalize language type while importing
                        ltype_clean = clean(ltype)
                        from web.management.commands.translate_labels_to_english import LANGUAGE_MAP  # reuse mapping
                        ltype_clean = LANGUAGE_MAP.get(ltype_clean, ltype_clean)

                        obj, created = Resource.objects.update_or_create(
                            id=pk,
                            defaults={
                                'title': clean(title),
                                'desc': clean(desc),
                                'url': clean(url),
                                'ltype': ltype_clean,
                                'difficulty': difficulty_val,
                                'utype': clean(utype),
                                'author': clean(author),
                                'time': clean(rtime),
                                'image': clean(image),
                            }
                        )
                        if created:
                            imported_resources += 1

                elif line.startswith("INSERT INTO `record`"):
                    values_str = line.split('VALUES', 1)[1].strip()
                    start = values_str.find('(')
                    end = values_str.rfind(')')
                    if start == -1 or end == -1:
                        continue
                    values_str = values_str[start + 1:end]

                    for row in csv.reader([values_str.encode('utf-8')], delimiter=str(','), quotechar=str("'"),
                                          escapechar=str('\\'), skipinitialspace=True):
                        row_u = []
                        for v in row:
                            vu = to_text(v)
                            if vu.strip().upper() == u'NULL':
                                row_u.append(None)
                            else:
                                row_u.append(vu)
                        row = row_u
                        if len(row) < 5:
                            continue
                        _id, rid, rtime, dura, uid = row[:5]

                        if rid is None:
                            continue

                        try:
                            resource_id = int(rid)
                        except Exception:
                            continue

                        try:
                            dura_val = int(dura) if dura is not None else 0
                        except Exception:
                            dura_val = 0

                        try:
                            ts_ms = int(rtime) if rtime is not None else None
                        except Exception:
                            ts_ms = None

                        if ts_ms is not None:
                            dt = datetime.datetime.fromtimestamp(ts_ms / 1000.0)
                            dt = timezone.make_aware(dt, timezone.get_default_timezone())
                        else:
                            dt = timezone.now()

                        try:
                            res = Resource.objects.get(id=resource_id)
                        except Resource.DoesNotExist:
                            continue

                        StudyRecord.objects.create(
                            user=None,
                            resource=res,
                            time=dt,
                            dura=dura_val,
                        )
                        imported_records += 1

        self.stdout.write(u"Import finished: %d new Resource rows, %d new StudyRecord rows." %
                          (imported_resources, imported_records))

