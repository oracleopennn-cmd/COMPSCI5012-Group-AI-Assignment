#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import csv
import io
import os
import sqlite3
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = u"Update ONLY selected fields (title/desc/ltype/author) in web_resource from a MySQL-style Navicat SQL dump."

    def add_arguments(self, parser):
        parser.add_argument(
            '--sql',
            dest='sql_path',
            default=None,
            help='Path to SQL file (default: <project_root>/gd_language_resources_en.sql)'
        )
        parser.add_argument(
            '--db',
            dest='db_path',
            default=None,
            help='Path to target sqlite3 DB file (default: settings.DATABASES[default].NAME)'
        )
        parser.add_argument(
            '--table',
            dest='table',
            default='web_resource',
            help='Target table name (default: web_resource)'
        )

    def handle(self, *args, **options):
        root_dir = os.path.dirname(settings.BASE_DIR)
        sql_path = options.get('sql_path') or os.path.join(root_dir, 'gd_language_resources_en.sql')
        db_path = options.get('db_path') or settings.DATABASES['default']['NAME']
        table = options.get('table') or 'web_resource'

        if not os.path.exists(sql_path):
            raise Exception("SQL file not found: %s" % sql_path)
        if not os.path.exists(db_path):
            raise Exception("SQLite DB not found: %s" % db_path)

        # Backup target DB
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        bak_path = db_path + ".bak_" + ts
        with open(db_path, 'rb') as rf:
            data = rf.read()
        with open(bak_path, 'wb') as wf:
            wf.write(data)
        self.stdout.write(u"Backed up DB to: %s" % bak_path)

        def to_text(val):
            if val is None:
                return u''
            if isinstance(val, unicode):
                return val
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

        # Connect to SQLite and validate table/columns exist
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("select name from sqlite_master where type='table' and name=?", (table,))
        if cur.fetchone() is None:
            con.close()
            raise Exception("Target table not found in DB: %s" % table)

        # Ensure required columns exist
        cur.execute("pragma table_info(%s)" % table)
        cols = [r[1] for r in cur.fetchall()]
        for need in ['id', 'title', 'desc', 'ltype', 'author']:
            if need not in cols:
                con.close()
                raise Exception("Missing column in %s: %s" % (table, need))

        updated = 0
        missing = 0
        processed = 0

        # Read SQL as UTF-8 (tolerate BOM) and parse only INSERT INTO `resource`
        with io.open(sql_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith('INSERT INTO'):
                    continue
                if not line.startswith("INSERT INTO `resource`"):
                    continue

                values_str = line.split('VALUES', 1)[1].strip()
                start = values_str.find('(')
                end = values_str.rfind(')')
                if start == -1 or end == -1:
                    continue
                values_str = values_str[start + 1:end]

                # MySQL dump uses single quotes and backslash escapes; parse via csv
                for row in csv.reader([values_str.encode('utf-8')], delimiter=str(','), quotechar=str("'"),
                                      escapechar=str('\\'), skipinitialspace=True):
                    processed += 1
                    row_u = []
                    for v in row:
                        vu = to_text(v)
                        if vu.strip().upper() == u'NULL':
                            row_u.append(None)
                        else:
                            row_u.append(vu)
                    row = row_u

                    # Expected: (id, title, desc, url, ltype, difficulty, utype, author, time, image, test)
                    if len(row) < 8:
                        continue
                    rid, title, desc, url, ltype, difficulty, utype, author = row[:8]

                    try:
                        pk = int(clean(rid))
                    except Exception:
                        continue

                    title_v = clean(title)
                    desc_v = clean(desc)
                    ltype_v = clean(ltype)
                    author_v = clean(author)

                    cur.execute("update %s set title=?, desc=?, ltype=?, author=? where id=?" % table,
                                (title_v, desc_v, ltype_v, author_v, pk))
                    if cur.rowcount and cur.rowcount > 0:
                        updated += 1
                    else:
                        missing += 1

        con.commit()
        con.close()

        self.stdout.write(u"Done. processed=%d, updated=%d, missing_ids=%d. Other columns left unchanged." %
                          (processed, updated, missing))

