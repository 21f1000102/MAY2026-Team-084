"""
Role-based authorization.

Previously every mutating endpoint was bare @jwt_required(), so any logged-in
resident could mark invoices paid, delete apartments (cascading away their
residents/invoices/payments), publish notices, close polls, etc.
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User

# Roles that may manage the society.
ADMIN_ROLES = ("ADMIN", "SYSTEM_ADMIN", "TREASURER", "COMMITTEE_MEMBER")
# Financial actions are limited further.
FINANCE_ROLES = ("ADMIN", "SYSTEM_ADMIN", "TREASURER")


def current_user():
    """The authenticated User, or None. Identity is stored as str(user.id)."""
    ident = get_jwt_identity()
    if ident is None:
        return None
    try:
        return User.query.get(int(ident))
    except (TypeError, ValueError):
        return None


def is_admin(user):
    return bool(user and user.role in ADMIN_ROLES)


def role_required(*roles):
    """Require an authenticated, active user holding one of `roles`."""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error": "User not found"}), 404
            # Tokens never expire, so deactivation must be enforced per-request.
            if not user.is_active:
                return jsonify({"error": "Account is deactivated"}), 403
            if roles and user.role not in roles:
                return jsonify({"error": "You are not allowed to perform this action"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Any society-management role."""
    return role_required(*ADMIN_ROLES)(fn)


def finance_required(fn):
    """Money-touching endpoints (invoices, expenses)."""
    return role_required(*FINANCE_ROLES)(fn)


def active_user_required(fn):
    """Authenticated + active, any role. Replaces bare @jwt_required()."""
    return role_required()(fn)
