# -*- coding: utf-8 -*-
"""
Template context processors.
"""


def admin_context(request):
    """Add is_admin to template context."""
    try:
        user = getattr(request, 'user', None)
        if not user:
            is_admin = False
        else:
            auth = getattr(user, 'is_authenticated', None)
            if callable(auth):
                authenticated = auth()
            else:
                authenticated = bool(auth)
            is_admin = authenticated and (
                getattr(user, 'is_superuser', False) or
                getattr(user, 'is_staff', False) or
                getattr(user, 'username', None) == 'admin'
            )
    except Exception:
        is_admin = False
    return {'is_admin': is_admin}
