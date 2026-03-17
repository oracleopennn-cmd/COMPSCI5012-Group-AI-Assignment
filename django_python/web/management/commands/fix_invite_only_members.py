# -*- coding: utf-8 -*-
"""
Remove group members who were wrongly added without accepting an invite.
Run once if you had "invite then directly in group" bug:
  python manage.py fix_invite_only_members
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import transaction

from web.models import GroupInvite, GroupMember


class Command(BaseCommand):
    help = 'Remove members who have a PENDING invite (should not be in group until they accept)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only show what would be removed')

    def handle(self, *args, **options):
        dry = options['dry_run']
        # All pending invites: (group, invitee) should NOT be in GroupMember yet
        pending = GroupInvite.objects.filter(status=GroupInvite.STATUS_PENDING).select_related('group', 'invitee')
        removed = 0
        with transaction.atomic():
            for inv in pending:
                if GroupMember.objects.filter(group=inv.group, user=inv.invitee).exists():
                    self.stdout.write(
                        'Would remove: {} from group "{}" (pending invite)'.format(
                            inv.invitee.username, inv.group.title
                        )
                    )
                    if not dry:
                        GroupMember.objects.filter(group=inv.group, user=inv.invitee).delete()
                    removed += 1
        if dry:
            self.stdout.write(self.style.WARNING('Dry run: {} member(s) would be removed. Run without --dry-run to apply.'.format(removed)))
        else:
            self.stdout.write(self.style.SUCCESS('Removed {} member(s) who had pending invite.'.format(removed)))
