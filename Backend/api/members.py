from flask import Blueprint, request, jsonify
from models import db, User, Apartment, Resident
from werkzeug.security import generate_password_hash

from auth.roles import active_user_required, admin_required
from utils import (ApiError, clean_phone, get_body, parse_date, parse_enum,
                   parse_int, require)

members_bp = Blueprint("members", __name__)


# ════════════════════════════════════════════════════════
#  APARTMENTS
# ════════════════════════════════════════════════════════

# GET /api/members/apartments — list all apartments
@members_bp.route("/apartments", methods=["GET"])
@active_user_required
def get_apartments():
    apartments = Apartment.query.all()
    return jsonify([_apt_dict(a) for a in apartments]), 200


# POST /api/members/apartments — add new apartment
@members_bp.route("/apartments", methods=["POST"])
@admin_required
def add_apartment():
    data = get_body(request)
    require(data, "flat_number")

    flat_number = str(data["flat_number"]).strip()
    if Apartment.query.filter_by(flat_number=flat_number).first():
        raise ApiError("Flat number already exists", 409)

    apt = Apartment(
        flat_number=flat_number,
        block=data.get("block"),
        floor=parse_int(data.get("floor"), "floor")
    )
    db.session.add(apt)
    db.session.commit()
    return jsonify(_apt_dict(apt)), 201


# PUT /api/members/apartments/<id> — update apartment
@members_bp.route("/apartments/<int:apt_id>", methods=["PUT"])
@admin_required
def update_apartment(apt_id):
    apt = Apartment.query.get_or_404(apt_id)
    data = get_body(request)

    # flat_number used to be dropped silently, so renaming a flat did nothing.
    if "flat_number" in data:
        flat_number = str(data.get("flat_number") or "").strip()
        if not flat_number:
            raise ApiError("flat_number is required")
        if flat_number != apt.flat_number and \
                Apartment.query.filter_by(flat_number=flat_number).first():
            raise ApiError("Flat number already exists", 409)
        apt.flat_number = flat_number

    apt.block = data.get("block", apt.block)
    if "floor" in data:
        apt.floor = parse_int(data.get("floor"), "floor")

    db.session.commit()
    return jsonify(_apt_dict(apt)), 200


# DELETE /api/members/apartments/<id> — delete apartment
@members_bp.route("/apartments/<int:apt_id>", methods=["DELETE"])
@admin_required
def delete_apartment(apt_id):
    apt = Apartment.query.get_or_404(apt_id)

    # The relationships cascade, so deleting a live flat used to silently take
    # its residents, invoices, complaints and payments with it.
    if apt.residents or apt.invoices:
        raise ApiError(
            "Cannot delete a flat that still has residents or invoices", 409
        )

    db.session.delete(apt)
    db.session.commit()
    return jsonify({"message": "Apartment deleted"}), 200


# ════════════════════════════════════════════════════════
#  MEMBERS (Users + Residents)
# ════════════════════════════════════════════════════════

# GET /api/members — list all members with flat info
@members_bp.route("/", methods=["GET"])
@admin_required
def get_members():
    residents = Resident.query.all()
    return jsonify([_resident_dict(r) for r in residents]), 200


# GET /api/members/workers — WORKER accounts available for complaint assignment
@members_bp.route("/workers", methods=["GET"])
@admin_required
def get_workers():
    # "id" is users.id — complaints.assigned_worker_id points at users.id,
    # never at residents.id.
    workers = User.query.filter_by(role="WORKER", is_active=True)\
                .order_by(User.name).all()
    return jsonify([
        {"id": u.id, "name": u.name, "email": u.email} for u in workers
    ]), 200


# POST /api/members — add new member
@members_bp.route("/", methods=["POST"])
@admin_required
def add_member():
    data = get_body(request)
    require(data, "name", "email", "password", "role", "apartment_id")

    # Validated before anything is constructed: an unknown role used to commit
    # and then break every later read of that row.
    role = parse_enum(data.get("role"), "role", required=True)
    apartment_id = parse_int(data.get("apartment_id"), "apartment_id",
                             required=True, min_value=1)
    phone = clean_phone(data.get("phone"))
    move_in_date = parse_date(data.get("move_in_date"), "move_in_date")
    email = str(data["email"]).strip()

    if User.query.filter_by(email=email).first():
        raise ApiError("Email already registered", 409)

    # users.phone is UNIQUE — a duplicate used to surface as an HTML 500.
    if phone and User.query.filter_by(phone=phone).first():
        raise ApiError("Phone number already registered", 409)

    apt = Apartment.query.get(apartment_id)
    if not apt:
        raise ApiError("Apartment not found", 404)

    user = User(
        name=str(data["name"]).strip(),
        email=email,
        phone=phone,
        password_hash=generate_password_hash(data["password"]),
        role=role
    )
    db.session.add(user)
    db.session.flush()

    resident = Resident(
        user_id=user.id,
        apartment_id=apartment_id,
        is_owner=bool(data.get("is_owner", False)),
        move_in_date=move_in_date
    )
    db.session.add(resident)
    db.session.commit()

    return jsonify(_resident_dict(resident)), 201


# PUT /api/members/<id> — update member details
@members_bp.route("/<int:resident_id>", methods=["PUT"])
@admin_required
def update_member(resident_id):
    resident = Resident.query.get_or_404(resident_id)
    data = get_body(request)

    # update user fields
    user = resident.user
    if data.get("name"):
        user.name = str(data["name"]).strip()

    if "phone" in data:
        phone = clean_phone(data.get("phone"))
        if phone and User.query.filter(User.phone == phone,
                                       User.id != user.id).first():
            raise ApiError("Phone number already registered", 409)
        user.phone = phone

    if data.get("role") is not None:
        user.role = parse_enum(data.get("role"), "role", required=True)

    # update resident fields
    if "is_owner" in data:
        resident.is_owner = bool(data.get("is_owner"))
    if "move_in_date" in data:
        resident.move_in_date = parse_date(data.get("move_in_date"), "move_in_date")
    if "move_out_date" in data:
        resident.move_out_date = parse_date(data.get("move_out_date"), "move_out_date")

    db.session.commit()
    return jsonify(_resident_dict(resident)), 200


# DELETE /api/members/<id> — deactivate member
@members_bp.route("/<int:resident_id>", methods=["DELETE"])
@admin_required
def deactivate_member(resident_id):
    resident = Resident.query.get_or_404(resident_id)
    resident.user.is_active = False
    db.session.commit()
    return jsonify({"message": "Member deactivated"}), 200


# GET /api/members/<id> — get single member
@members_bp.route("/<int:resident_id>", methods=["GET"])
@active_user_required
def get_member(resident_id):
    resident = Resident.query.get_or_404(resident_id)
    return jsonify(_resident_dict(resident)), 200


# ── helpers ───────────────────────────────────────────────────
def _apt_dict(a):
    return {
        "id": a.id,
        "flat_number": a.flat_number,
        "block": a.block,
        "floor": a.floor
    }

def _resident_dict(r):
    return {
        "id": r.id,
        "user_id": r.user_id,
        "name": r.user.name,
        "email": r.user.email,
        "phone": r.user.phone,
        "role": r.user.role,
        "is_active": r.user.is_active,
        "apartment_id": r.apartment_id,
        "flat_number": r.apartment.flat_number,
        "block": r.apartment.block,
        "floor": r.apartment.floor,
        "is_owner": r.is_owner,
        "move_in_date": str(r.move_in_date) if r.move_in_date else None,
        "move_out_date": str(r.move_out_date) if r.move_out_date else None,
    }
