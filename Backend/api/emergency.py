from flask import Blueprint, request, jsonify
from models import db, EmergencyContact

from auth.roles import active_user_required, admin_required
from utils import ApiError, get_body, parse_enum, require

emergency_bp = Blueprint("emergency", __name__)


def _clean_phone(value, required=False):
    """Keep the number as typed, but reject blanks and obvious junk.

    No uniqueness check: two services can legitimately share a number, and the
    column has no UNIQUE constraint.
    """
    if value is None or not str(value).strip():
        if required:
            raise ApiError("phone is required")
        return None
    phone = str(value).strip()
    if len(phone) > 15:
        raise ApiError("phone must be 15 characters or fewer")
    if not any(ch.isdigit() for ch in phone):
        raise ApiError("phone must contain digits")
    return phone


# GET /api/emergency — every role may read the directory
@emergency_bp.route("/", methods=["GET"])
@active_user_required
def get_contacts():
    contacts = EmergencyContact.query.order_by(
        EmergencyContact.service_type.asc(), EmergencyContact.name.asc()
    ).all()
    return jsonify([_contact_dict(c) for c in contacts]), 200


# POST /api/emergency — add a contact (admin)
@emergency_bp.route("/", methods=["POST"])
@admin_required
def add_contact():
    data = get_body(request)
    require(data, "name", "service_type", "phone")

    contact = EmergencyContact(
        name=data["name"].strip(),
        service_type=parse_enum(data.get("service_type"), "service_type",
                                field="service_type", required=True),
        phone=_clean_phone(data.get("phone"), required=True),
        availability=(data.get("availability") or "").strip() or None,
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify(_contact_dict(contact)), 201


# PUT /api/emergency/<id> — update a contact (admin)
@emergency_bp.route("/<int:cid>", methods=["PUT"])
@admin_required
def update_contact(cid):
    contact = EmergencyContact.query.get_or_404(cid)
    data = get_body(request)

    if data.get("name"):
        contact.name = data["name"].strip()
    if "service_type" in data:
        contact.service_type = parse_enum(data.get("service_type"), "service_type",
                                          field="service_type",
                                          default=contact.service_type)
    if "phone" in data:
        contact.phone = _clean_phone(data.get("phone"), required=True)
    if "availability" in data:
        contact.availability = (data.get("availability") or "").strip() or None

    db.session.commit()
    return jsonify(_contact_dict(contact)), 200


# DELETE /api/emergency/<id> — remove a contact (admin)
# Hard delete: this model has no is_active column, unlike Announcement.
@emergency_bp.route("/<int:cid>", methods=["DELETE"])
@admin_required
def delete_contact(cid):
    contact = EmergencyContact.query.get_or_404(cid)
    db.session.delete(contact)
    db.session.commit()
    return jsonify({"message": "Contact removed"}), 200


# ── helper ────────────────────────────────────────────────────
def _contact_dict(c):
    # Only real columns — this model has no timestamps or relationships.
    return {
        "id": c.id,
        "name": c.name,
        "service_type": c.service_type,
        "phone": c.phone,
        "availability": c.availability,
    }
