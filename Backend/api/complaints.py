from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from models import db, Complaint, ComplaintUpdate, User, Apartment, Resident
from datetime import datetime, timedelta

from utils import (ApiError, get_body, require, parse_enum, parse_int,
                   parse_bool, search_term, ilike, apply_date_range, csv_response)
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

# A complaint has no due date; "overdue" is a derived predicate — still open
# (not COMPLETED/CLOSED) and raised more than this many days ago.
OVERDUE_AFTER_DAYS = 7

UNRESOLVED_STATUSES = ("OPEN", "ASSIGNED", "IN_PROGRESS")
RESOLVED_STATUSES = ("COMPLETED", "CLOSED")


def _filtered_complaints_query(user, args):
    """Complaint query scoped to what `user` may see, with optional filters
    layered on top. Role scoping is applied first and is never touched by the
    filter args below, so a filter can only narrow what a caller could
    already see.
    """
    query = Complaint.query

    if is_admin(user):
        pass
    elif user.role == "WORKER":
        query = query.filter(
            or_(Complaint.assigned_worker_id == user.id,
                Complaint.raised_by == user.id)
        )
    else:
        query = query.filter_by(raised_by=user.id)

    status = parse_enum(args.get("status"), "complaint_status", field="status")
    if status:
        query = query.filter(Complaint.status == status)

    category = parse_enum(args.get("category"), "complaint_category", field="category")
    if category:
        query = query.filter(Complaint.category == category)

    priority = parse_enum(args.get("priority"), "priority", field="priority")
    if priority:
        query = query.filter(Complaint.priority == priority)

    apartment_id = parse_int(args.get("apartment_id"), "apartment_id", min_value=1)
    if apartment_id:
        query = query.filter(Complaint.apartment_id == apartment_id)

    assigned_worker_id = parse_int(args.get("assigned_worker_id"), "assigned_worker_id", min_value=1)
    if assigned_worker_id:
        query = query.filter(Complaint.assigned_worker_id == assigned_worker_id)

    worker = search_term(args.get("worker"))
    if worker:
        Worker = aliased(User)
        query = query.join(Worker, Complaint.assigned_worker_id == Worker.id) \
                     .filter(ilike(Worker.name, worker))

    raised_by = search_term(args.get("raised_by"))
    if raised_by:
        Raiser = aliased(User)
        query = query.join(Raiser, Complaint.raised_by == Raiser.id) \
                     .filter(ilike(Raiser.name, raised_by))

    unassigned = parse_bool(args.get("unassigned"), "unassigned")
    if unassigned is not None:
        query = query.filter(Complaint.assigned_worker_id.is_(None) if unassigned
                             else Complaint.assigned_worker_id.isnot(None))

    overdue = parse_bool(args.get("overdue"), "overdue")
    if overdue is not None:
        cutoff = datetime.utcnow() - timedelta(days=OVERDUE_AFTER_DAYS)
        is_overdue = (Complaint.status.in_(UNRESOLVED_STATUSES)) & (Complaint.created_at < cutoff)
        query = query.filter(is_overdue if overdue else ~is_overdue)

    q = search_term(args.get("q"))
    if q:
        query = query.filter(or_(ilike(Complaint.title, q), ilike(Complaint.description, q)))

    query = apply_date_range(query, Complaint.created_at, args)

    return query


# GET /api/complaints — all (admin) / assigned (worker) / own (resident)
@complaints_bp.route("/", methods=["GET"])
@active_user_required
def get_complaints():
    user = current_user()
    complaints = _filtered_complaints_query(user, request.args) \
        .order_by(Complaint.created_at.desc()).all()
    return jsonify([_complaint_dict(c) for c in complaints]), 200


# GET /api/complaints/summary — counts and breakdowns
@complaints_bp.route("/summary", methods=["GET"])
@active_user_required
def complaints_summary():
    user = current_user()
    complaints = _filtered_complaints_query(user, request.args).all()

    by_status = {s: 0 for s in ("OPEN", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "CLOSED")}
    by_category, by_priority = {}, {}
    resolution_days = []
    unassigned_count = 0

    for c in complaints:
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_category[c.category] = by_category.get(c.category, 0) + 1
        by_priority[c.priority] = by_priority.get(c.priority, 0) + 1
        if not c.assigned_worker_id:
            unassigned_count += 1
        if c.resolved_at and c.created_at:
            resolution_days.append((c.resolved_at - c.created_at).total_seconds() / 86400)

    pending = sum(by_status[s] for s in UNRESOLVED_STATUSES)
    resolved = sum(by_status[s] for s in RESOLVED_STATUSES)
    avg_resolution_days = round(sum(resolution_days) / len(resolution_days), 2) if resolution_days else None

    return jsonify({
        "total": len(complaints),
        "by_status": by_status,
        "pending": pending,
        "resolved": resolved,
        "by_category": by_category,
        "by_priority": by_priority,
        "avg_resolution_days": avg_resolution_days,
        "unassigned_count": unassigned_count,
    }), 200


# GET /api/complaints/export — CSV of the filtered list
@complaints_bp.route("/export", methods=["GET"])
@active_user_required
def export_complaints():
    user = current_user()
    complaints = _filtered_complaints_query(user, request.args) \
        .order_by(Complaint.created_at.desc()).all()
    columns = [
        ("ID", "id"), ("Title", "title"), ("Category", "category"),
        ("Priority", "priority"), ("Status", "status"), ("Flat", "flat_number"),
        ("Raised By", "raised_by_name"), ("Assigned Worker", "assigned_worker_name"),
        ("Created At", "created_at"), ("Resolved At", "resolved_at"),
    ]
    return csv_response([_complaint_dict(c) for c in complaints], columns, "complaints.csv")


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
