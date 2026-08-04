from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from models import db, User
from utils import ApiError, get_body, require, parse_enum, clean_phone
from auth.roles import current_user, active_user_required

auth_bp = Blueprint("auth", __name__)


# ── POST /api/auth/register ────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = get_body(request)
    require(data, "name", "email", "password", "role")

    email = data["email"].strip().lower()
    # phone is UNIQUE: blank must become NULL, otherwise the second blank-phone
    # signup collides with the first. This is what broke registration.
    phone = clean_phone(data.get("phone"))

    if User.query.filter_by(email=email).first():
        raise ApiError("Email already registered", 409)
    if phone and User.query.filter_by(phone=phone).first():
        raise ApiError("Phone number already registered", 409)

# Public registration should not allow privileged/admin roles.
    role = parse_enum(data["role"], "role", required=True)

    blocked_public_roles = ("ADMIN", "SYSTEM_ADMIN", "TREASURER", "COMMITTEE_MEMBER")

    if role in blocked_public_roles:
        return jsonify({
        "error": "Public registration is not allowed for admin or staff roles"
    }), 400

    user = User(
        name=data["name"].strip(),
        email=email,
        phone=phone,
        password_hash=_hash(data["password"]),
        role=role,
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": _user_dict(user)
    }), 201


# ── POST /api/auth/login ───────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = get_body(request)
    require(data, "email", "password")

    user = User.query.filter_by(email=data["email"].strip().lower()).first()
    if not user or not _check(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": _user_dict(user)
    }), 200


# ── GET /api/auth/me ───────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@active_user_required
def me():
    return jsonify(_user_dict(current_user())), 200


# ── PUT /api/auth/change-password ──────────────────────────────
@auth_bp.route("/change-password", methods=["PUT"])
@active_user_required
def change_password():
    user = current_user()
    data = get_body(request)
    require(data, "old_password", "new_password")   # was data["new_password"] -> KeyError 500

    if not _check(user.password_hash, data["old_password"]):
        return jsonify({"error": "Old password is incorrect"}), 400

    if len(data["new_password"]) < 6:
        raise ApiError("New password must be at least 6 characters")

    user.password_hash = _hash(data["new_password"])
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200


# ── helpers ────────────────────────────────────────────────────
def _hash(password):
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password)


def _check(hashed, password):
    from werkzeug.security import check_password_hash
    return check_password_hash(hashed, password)


def _user_dict(u):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "phone": u.phone,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": str(u.created_at)
    }
