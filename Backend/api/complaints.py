from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from models import db, Complaint, ComplaintUpdate, User, Apartment, Resident
from datetime import datetime

from utils import ApiError, get_body, require, parse_enum, parse_int
from auth.roles import current_user, is_admin, active_user_required, admin_required

complaints_bp = Blueprint("complaints", __name__)

# A worker may only move a job along; residents may close their own.
ALLOWED_TRANSITIONS = {
    "OPEN":        {"ASSIGNED", "IN_PROGRESS", "CLOSED"},
    "ASSIGNED":    {"IN_PROGRESS", "COMPLETED", "CLOSED", "OPEN"},
    "IN_PROGRESS": {"COMPLETED", "CLOSED", "ASSIGNED"},
    "COMPLETED":   {"CLOSED", "IN_PROGRESS"},
    "CLOSED":      {"OPEN"},
}


# GET /api/complaints — all (admin) / assigned (worker) / own (resident)
@complaints_bp.route("/", methods=["GET"])
@active_user_required
def get_complaints():
    user = current_user()
    query = Complaint.query

    if is_admin(user):
        pass
    elif user.role == "WORKER":
        # Workers previously saw only complaints they RAISED, so assigned jobs
        # never reached them and the whole role was unusable.
        query = query.filter(
            or_(Complaint.assigned_worker_id == user.id,
                Complaint.raised_by == user.id)
        )
    else:
        query = query.filter_by(raised_by=user.id)

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return jsonify([_complaint_dict(c) for c in complaints]), 200


# POST /api/complaints — raise new complaint
@complaints_bp.route("/", methods=["POST"])
@active_user_required
def raise_complaint():
    user = current_user()
    data = get_body(request)
    require(data, "title", "category", "apartment_id")

    apartment_id = parse_int(data.get("apartment_id"), "apartment_id", required=True)
    if not Apartment.query.get(apartment_id):
        raise ApiError("Apartment not found", 404)

    complaint = Complaint(
        raised_by=user.id,
        apartment_id=apartment_id,
        title=data["title"].strip(),
        description=data.get("description"),
        category=parse_enum(data.get("category"), "complaint_category",
                            field="category", required=True),
        priority=parse_enum(data.get("priority"), "priority",
                            field="priority", default="MEDIUM"),
    )
    db.session.add(complaint)
    db.session.commit()
    return jsonify(_complaint_dict(complaint)), 201


# GET /api/complaints/<id> — single complaint detail
@complaints_bp.route("/<int:cid>", methods=["GET"])
@active_user_required
def get_complaint(cid):
    user = current_user()
    c = Complaint.query.get_or_404(cid)

    # The list route filtered by owner but the detail route did not, so any
    # resident could read a neighbour's complaint by guessing the id.
    if not _may_view(user, c):
        raise ApiError("You are not allowed to view this complaint", 403)

    result = _complaint_dict(c)
    result["updates"] = [_update_dict(u) for u in c.updates]
    return jsonify(result), 200


# PUT /api/complaints/<id>/assign — assign worker
@complaints_bp.route("/<int:cid>/assign", methods=["PUT"])
@admin_required
def assign_complaint(cid):
    user = current_user()
    c = Complaint.query.get_or_404(cid)
    data = get_body(request)

    # Previously accepted a missing/null worker_id and still flipped the status
    # to ASSIGNED, so complaints were "assigned" to nobody.
    worker_id = parse_int(data.get("worker_id"), "worker_id", required=True)
    worker = User.query.get(worker_id)
    if not worker:
        raise ApiError("Worker not found", 404)
    if worker.role != "WORKER":
        raise ApiError("Selected user is not a maintenance worker")
    if not worker.is_active:
        raise ApiError("Selected worker is deactivated")

    c.assigned_worker_id = worker.id
    c.status = "ASSIGNED"

    db.session.add(ComplaintUpdate(
        complaint_id=c.id,
        updated_by=user.id,
        status="ASSIGNED",
        remarks=data.get("remarks") or f"Assigned to {worker.name}",
    ))
    db.session.commit()
    return jsonify(_complaint_dict(c)), 200


# PUT /api/complaints/<id>/status — update status
@complaints_bp.route("/<int:cid>/status", methods=["PUT"])
@active_user_required
def update_status(cid):
    user = current_user()
    c = Complaint.query.get_or_404(cid)
    data = get_body(request)

    new_status = parse_enum(data.get("status"), "complaint_status",
                            field="status", required=True)

    if not _may_update(user, c):
        raise ApiError("You are not allowed to update this complaint", 403)

    current = c.status or "OPEN"
    if new_status != current and new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ApiError(f"Cannot change status from {current} to {new_status}")

    c.status = new_status
    if new_status in ("COMPLETED", "CLOSED"):
        c.resolved_at = datetime.utcnow()
    else:
        # Reopening used to leave resolved_at set, so the complaint reported as
        # unresolved yet resolved on a date.
        c.resolved_at = None

    db.session.add(ComplaintUpdate(
        complaint_id=c.id,
        updated_by=user.id,
        status=new_status,
        remarks=data.get("remarks"),
    ))
    db.session.commit()
    return jsonify(_complaint_dict(c)), 200


# DELETE /api/complaints/<id> — delete complaint
@complaints_bp.route("/<int:cid>", methods=["DELETE"])
@admin_required
def delete_complaint(cid):
    c = Complaint.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Complaint deleted"}), 200


# ── permissions ───────────────────────────────────────────────
def _may_view(user, c):
    if is_admin(user):
        return True
    if c.raised_by == user.id or c.assigned_worker_id == user.id:
        return True
    resident = Resident.query.filter_by(user_id=user.id).first()
    return bool(resident and resident.apartment_id == c.apartment_id)


def _may_update(user, c):
    if is_admin(user):
        return True
    if user.role == "WORKER":
        return c.assigned_worker_id == user.id
    return c.raised_by == user.id


# ── helpers ───────────────────────────────────────────────────
def _complaint_dict(c):
    return {
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "category": c.category,
        "priority": c.priority,
        "status": c.status,
        "apartment_id": c.apartment_id,
        "flat_number": c.apartment.flat_number if c.apartment else None,
        "raised_by": c.raised_by,
        "raised_by_name": c.raiser.name if c.raiser else None,
        "assigned_worker_id": c.assigned_worker_id,
        "assigned_worker_name": c.worker.name if c.worker else None,
        "created_at": str(c.created_at),
        "resolved_at": str(c.resolved_at) if c.resolved_at else None
    }


def _update_dict(u):
    return {
        "id": u.id,
        "status": u.status,
        "remarks": u.remarks,
        "updated_by": u.updated_by,
        "updated_by_name": u.updated_by_user.name if u.updated_by_user else None,
        "updated_at": str(u.updated_at)
    }
