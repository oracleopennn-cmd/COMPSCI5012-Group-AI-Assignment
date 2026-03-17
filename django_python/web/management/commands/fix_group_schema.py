# -*- coding: utf-8 -*-
"""
Fix SQLite schema: replace broken references to web_group__old with web_group.
Run with the SAME Python you use for runserver (e.g. Python 3.12):
  python manage.py fix_group_schema
"""
from __future__ import unicode_literals

import sqlite3
import os

from django.core.management.base import BaseCommand
from django.conf import settings


GROUP_TABLES = ('web_groupmember', 'web_groupmessage', 'web_groupjoinrequest', 'web_groupinvite')
BAD_REF = 'web_group__old'
GOOD_REF = 'web_group'


class Command(BaseCommand):
    help = 'Fix SQLite tables that reference web_group__old (fixes 500 on invite/kick under Python 3.x)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be fixed, do not change DB',
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        if not db_path or 'sqlite3' not in db_path:
            self.stdout.write(self.style.WARNING('Not using SQLite; this command only fixes SQLite.'))
            return
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR('Database file not found: {}'.format(db_path)))
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        fixed = 0
        try:
            for table_name in GROUP_TABLES:
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
                row = cursor.fetchone()
                if not row or not row[0]:
                    continue
                original_sql = row[0]
                if BAD_REF not in original_sql:
                    continue
                cleaned_sql = original_sql.replace(BAD_REF, GOOD_REF)
                if cleaned_sql == original_sql:
                    continue

                if options['dry_run']:
                    self.stdout.write('Would fix table: {}'.format(table_name))
                    fixed += 1
                    continue

                self.stdout.write('Fixing table: {} ...'.format(table_name))
                cursor.execute('PRAGMA foreign_keys=OFF;')
                cursor.execute('BEGIN TRANSACTION;')
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL;",
                    (table_name,),
                )
                index_defs = [r[0] for r in cursor.fetchall()]
                new_name = table_name + '_new'
                create_sql = cleaned_sql.replace(table_name, new_name, 1)
                cursor.execute(create_sql)
                cursor.execute('PRAGMA table_info("{}");'.format(table_name))
                cols = [c[1] for c in cursor.fetchall()]
                quoted = ', '.join('"{}"'.format(c) for c in cols)
                cursor.execute(
                    'INSERT INTO "{}" ({}) SELECT {} FROM "{}";'.format(new_name, quoted, quoted, table_name)
                )
                cursor.execute('DROP TABLE "{}";'.format(table_name))
                cursor.execute('ALTER TABLE "{}" RENAME TO "{}";'.format(new_name, table_name))
                for idx_sql in index_defs:
                    try:
                        cursor.execute(idx_sql)
                    except Exception:
                        pass
                cursor.execute('COMMIT;')
                cursor.execute('PRAGMA foreign_keys=ON;')
                self.stdout.write(self.style.SUCCESS('  OK: {} fixed.'.format(table_name)))
                fixed += 1
        except Exception as e:
            conn.rollback()
            self.stdout.write(self.style.ERROR('Error: {}'.format(e)))
            raise
        finally:
            conn.close()

        if fixed == 0 and not options['dry_run']:
            self.stdout.write(self.style.SUCCESS('No tables needed fixing (schema is OK).'))
        elif fixed and options['dry_run']:
            self.stdout.write(self.style.SUCCESS('Dry run: {} table(s) would be fixed. Run without --dry-run to apply.'.format(fixed)))
