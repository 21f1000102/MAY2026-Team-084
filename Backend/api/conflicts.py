from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from models import db, ConflictReport, Apartment, Resident
from datetime import datetime

from utils import ApiError, get_body, require, parse_enum, parse_int
from auth.roles import current_user, is_admin, active_user_required, admin_required

conflicts_bp = Blueprint("conflicts", __name__)


def _own_apartment_id(user):
    resident = Resident.query.filter_by(user_id=user.id).first()
    return resident.apartment_id if resident else None


# GET /api/conflicts — admin sees all; a resident sees reports they raised
# plus (anonymously) any report filed against their own flat.
@conflicts_bp.route("/", methods=["GET"])
@active_user_required
def get_conflicts():
    user = current_user()

    if is_admin(user):
        reports = ConflictReport.query.order_by(ConflictReport.created_at.desc()).all()
        return jsonify([_conflict_dict(r, reveal_reporter=True) for r in reports]), 200

    apartment_id = _own_apartment_id(user)
    query = ConflictReport.query.filter(
        or_(ConflictReport.reported_by == user.id,
            ConflictReport.reported_apartment_id == apartment_id)
        if apartment_id else ConflictReport.reported_by == user.id
    )
    reports = query.order_by(ConflictReport.created_at.desc()).all()
    # reveal_reporter stays False: the accused flat must never learn who reported them.
    return jsonify([_conflict_dict(r, reveal_reporter=False) for r in reports]), 200


# POST /api/conflicts — resident raises a conflict report
@conflicts_bp.route("/", methods=["POST"])
@active_user_required
def raise_conflict():
    user = current_user()
    data = get_body(request)
    require(data, "reported_apartment_id", "category", "description")

    apartment_id = parse_int(data.get("reported_apartment_id"),
                             "reported_apartment_id", required=True)
    if not Apartment.query.get(apartment_id):
        raise ApiError("Apartment not found", 404)
    if apartment_id == _own_apartment_id(user):
        raise ApiError("You cannot raise a conflict against your own flat")

    report = ConflictReport(
        reported_by=user.id,
        reported_apartment_id=apartment_id,
        category=parse_enum(data.get("category"), "conflict_category",
                            field="category", required=True),
        description=data["description"].strip(),
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({
        "message": "Conflict report submitted. The concerned flat will be notified anonymously.",
        "report_id": report.id
    }), 201


# PUT /api/conflicts/<id>/respond — reported flat submits their side
@conflicts_bp.route("/<int:rid>/respond", methods=["PUT"])
@active_user_required
def submit_response(rid):
    user = current_user()
    report = ConflictReport.query.get_or_404(rid)
    data = get_body(request)
    require(data, "response")

    # Previously verified nothing: any user could respond on any report,
    # overwrite an existing response, and reopen a resolved case.
    if not is_admin(user) and report.reported_apartment_id != _own_apartment_id(user):
        raise ApiError("Only the reported flat can respond to this report", 403)
    if report.status == "RESOLVED":
        raise ApiError("This report has already been resolved", 409)
    if report.reported_flat_response:
        raise ApiError("A response has already been submitted for this report", 409)

    report.reported_flat_response = data["response"].strip()
    report.response_submitted_at = datetime.utcnow()
    report.status = "UNDER_REVIEW"
    db.session.commit()

    return jsonify({"message": "Response submitted. Secretary will review both sides."}), 200


# PUT /api/conflicts/<id>/resolve — secretary resolves
@conflicts_bp.route("/<int:rid>/resolve", methods=["PUT"])
@admin_required
def resolve_conflict(rid):
    user = current_user()
    report = ConflictReport.query.get_or_404(rid)
    data = get_body(request)

    if report.status == "RESOLVED":
        raise ApiError("This report is already resolved", 409)

    report.status = "RESOLVED"
    report.resolution_note = data.get("resolution_note") or "Resolved by secretary"
    report.resolved_by = user.id
    report.resolved_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "message": "Conflict resolved",
        "report": _conflict_dict(report, reveal_reporter=True)
    }), 200


# GET /api/conflicts/pending — conflicts awaiting response (secretary only)
@conflicts_bp.route("/pending", methods=["GET"])
@admin_required
def get_pending():
    # Was open to every authenticated user AND revealed reporter identities —
    # the single worst leak of the anonymity guarantee.
    reports = ConflictReport.query.filter(
        ConflictReport.status.in_(["OPEN", "UNDER_REVIEW"])
    ).all()
    return jsonify([_conflict_dict(r, reveal_reporter=True) for r in reports]), 200


# ── helper ────────────────────────────────────────────────────
def _conflict_dict(r, reveal_reporter=False):
    data = {
        "id": r.id,
        "category": r.category,
        "description": r.description,
        "reported_apartment_id": r.reported_apartment_id,
        "reported_flat": r.reported_apartment.flat_number if r.reported_apartment else None,
        "reported_flat_response": r.reported_flat_response,
        "response_submitted_at": str(r.response_submitted_at) if r.response_submitted_at else None,
        "status": r.status,
        "resolution_note": r.resolution_note,
        "resolved_at": str(r.resolved_at) if r.resolved_at else None,
        "created_at": str(r.created_at)
    }
    # reporter identity only visible to admin/secretary
    if reveal_reporter:
        data["reported_by"] = r.reported_by
        data["reported_by_name"] = r.reporter.name if r.reporter else None
    return data
