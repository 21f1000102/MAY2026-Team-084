from flask import Blueprint, request, jsonify
from sqlalchemy import extract
from models import (db, SocietyHealthScore, Invoice, Complaint, Vote,
                    VoteResponse, Announcement, Equipment, Resident)
from datetime import date
from calendar import monthrange

from utils import parse_int
from auth.roles import active_user_required, admin_required

health_bp = Blueprint("health", __name__)


def _month_end(month, year):
    """Reference date for a historical month, so scoring a past month doesn't
    silently grade it against today's state."""
    last_day = monthrange(year, month)[1]
    today = date.today()
    end = date(year, month, last_day)
    return min(end, today) if (year, month) <= (today.year, today.month) else end


def _calculate_score(month, year):
    """Society Health Score for a month.

    Components with no underlying data are marked not-applicable and excluded
    from the total, which is then scaled to 100. Previously "no invoices" scored
    0/30 (max penalty) while "no complaints" scored 25/25 (max reward), so an
    empty society scored a meaningless 55/100.
    """
    components = {}

    # ── 1. Payment (30) ───────────────────────────────────────
    total_invoices = Invoice.query.filter_by(month=month, year=year).count()
    paid_invoices = Invoice.query.filter_by(month=month, year=year, status="PAID").count()
    components["payment"] = (
        round(paid_invoices / total_invoices * 30, 2) if total_invoices else 0.0,
        30, total_invoices > 0,
    )

    # ── 2. Complaint resolution (25) ──────────────────────────
    all_complaints = Complaint.query.filter(
        extract("month", Complaint.created_at) == month,
        extract("year", Complaint.created_at) == year,
    ).count()
    resolved_complaints = Complaint.query.filter(
        extract("month", Complaint.created_at) == month,
        extract("year", Complaint.created_at) == year,
        Complaint.status.in_(["COMPLETED", "CLOSED"]),
    ).count()
    components["complaint"] = (
        round(resolved_complaints / all_complaints * 25, 2) if all_complaints else 0.0,
        25, all_complaints > 0,
    )

    # ── 3. Notice engagement (15) ─────────────────────────────
    notices_posted = Announcement.query.filter(
        extract("month", Announcement.created_at) == month,
        extract("year", Announcement.created_at) == year,
        Announcement.is_active.is_(True),
    ).count()
    # Always applicable: posting no notices in a month is itself the signal.
    components["notice"] = (15.0 if notices_posted > 0 else 0.0, 15, True)

    # ── 4. Poll participation (15) ────────────────────────────
    polls = Vote.query.filter(
        extract("month", Vote.created_at) == month,
        extract("year", Vote.created_at) == year,
    ).all()
    total_residents = Resident.query.count()
    poll_score, poll_applicable = 0.0, False
    if polls and total_residents:
        poll_applicable = True
        poll_ids = [p.id for p in polls]
        # Count votes cast ON these polls (previously counted votes created in
        # the month regardless of which poll they belonged to).
        votes_cast = VoteResponse.query.filter(VoteResponse.vote_id.in_(poll_ids)).count()
        rate = votes_cast / (len(polls) * total_residents)
        poll_score = round(min(rate * 15, 15), 2)
    components["poll"] = (poll_score, 15, poll_applicable)

    # ── 5. Maintenance (15) ───────────────────────────────────
    reference = _month_end(month, year)
    all_equipment = Equipment.query.all()
    on_time = 0
    for eq in all_equipment:
        freq = eq.service_frequency_days or 0
        if not eq.last_serviced_date or freq <= 0:
            continue
        if (reference - eq.last_serviced_date).days <= freq:
            on_time += 1
    components["maintenance"] = (
        round(on_time / len(all_equipment) * 15, 2) if all_equipment else 0.0,
        15, bool(all_equipment),
    )

    # ── Total, scaled over applicable components only ─────────
    earned = sum(s for s, _m, ok in components.values() if ok)
    possible = sum(m for _s, m, ok in components.values() if ok)
    total = round(earned / possible * 100, 2) if possible else 0.0

    # ── Alerts ────────────────────────────────────────────────
    alerts = []
    if total_invoices and paid_invoices < total_invoices:
        alerts.append(f"{total_invoices - paid_invoices} invoices unpaid")
    if all_complaints and resolved_complaints < all_complaints:
        alerts.append(f"{all_complaints - resolved_complaints} complaints unresolved")
    if notices_posted == 0:
        alerts.append("No notices posted this month")

    not_scored = [k for k, (_s, _m, ok) in components.items() if not ok]
    if not possible:
        alert_reason = "Not enough data yet to score this month"
    else:
        if not_scored:
            alerts.append("not scored (no data): " + ", ".join(sorted(not_scored)))
        alert_reason = " | ".join(alerts) if alerts else "All metrics healthy"

    return {
        "month": month,
        "year": year,
        "payment_score": components["payment"][0],
        "complaint_score": components["complaint"][0],
        "notice_score": components["notice"][0],
        "poll_score": components["poll"][0],
        "maintenance_score": components["maintenance"][0],
        "total_score": total,
        "alert_reason": alert_reason,
        "has_data": bool(possible),
        "grade": _grade(total) if possible else "RED",
    }


def _grade(total):
    return "GREEN" if total >= 71 else ("YELLOW" if total >= 41 else "RED")


# GET|POST /api/health/calculate?month=6&year=2026 — calculate & save score
# Admin-only: this writes the society's official record for the month.
@health_bp.route("/calculate", methods=["GET", "POST"])
@admin_required
def calculate():
    today = date.today()
    month = parse_int(request.args.get("month", today.month), "month",
                      min_value=1, max_value=12) or today.month
    year = parse_int(request.args.get("year", today.year), "year",
                     min_value=2000, max_value=2200) or today.year

    result = _calculate_score(month, year)

    # upsert into DB
    record = SocietyHealthScore.query.filter_by(month=month, year=year).first()
    if not record:
        record = SocietyHealthScore(month=month, year=year)
        db.session.add(record)

    record.payment_score = result["payment_score"]
    record.complaint_score = result["complaint_score"]
    record.notice_score = result["notice_score"]
    record.poll_score = result["poll_score"]
    record.maintenance_score = result["maintenance_score"]
    record.total_score = result["total_score"]
    record.alert_reason = result["alert_reason"]

    db.session.commit()
    return jsonify(result), 200


# GET /api/health/history — last 6 months scores
@health_bp.route("/history", methods=["GET"])
@active_user_required
def history():
    scores = SocietyHealthScore.query\
                .order_by(SocietyHealthScore.year.desc(), SocietyHealthScore.month.desc())\
                .limit(6).all()
    return jsonify([_score_dict(s) for s in scores]), 200


# ── helper ────────────────────────────────────────────────────
def _score_dict(s):
    total = float(s.total_score)
    return {
        "id": s.id,
        "month": s.month,
        "year": s.year,
        "payment_score": float(s.payment_score),
        "complaint_score": float(s.complaint_score),
        "notice_score": float(s.notice_score),
        "poll_score": float(s.poll_score),
        "maintenance_score": float(s.maintenance_score),
        "total_score": total,
        "grade": _grade(total),
        "alert_reason": s.alert_reason,
        "calculated_at": str(s.calculated_at)
    }
