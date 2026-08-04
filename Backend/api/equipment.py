from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import db, Equipment, EquipmentServiceLog
from datetime import date

from utils import get_body, require, parse_date, parse_decimal, parse_enum, parse_int
from auth.roles import active_user_required, admin_required

equipment_bp = Blueprint("equipment", __name__)


def _risk_level(equipment):
    """Calculate risk level based on days since last service."""
    freq = equipment.service_frequency_days
    # Rows saved before service_frequency_days was validated could hold 0/NULL,
    # which raised ZeroDivisionError here and 500'd every read of the page.
    if not freq or freq <= 0 or not equipment.last_serviced_date:
        return "HIGH"

    today = date.today()
    days_since = (today - equipment.last_serviced_date).days
    pct = (days_since / freq) * 100

    if pct >= 100:
        return "HIGH"
    elif pct >= 80:
        return "MEDIUM"
    else:
        return "LOW"


def _days_until_due(equipment):
    freq = equipment.service_frequency_days
    if not freq or freq <= 0 or not equipment.last_serviced_date:
        return 0

    today = date.today()
    days_since = (today - equipment.last_serviced_date).days
    # Negative == overdue. The old max(0, ...) collapsed every overdue item to
    # "due today", so nothing overdue was distinguishable in the UI.
    return freq - days_since


# GET /api/equipment — list all equipment with risk levels
@equipment_bp.route("/", methods=["GET"])
@active_user_required
def get_equipment():
    items = Equipment.query.all()
    return jsonify([_equipment_dict(e) for e in items]), 200


# POST /api/equipment — add equipment
@equipment_bp.route("/", methods=["POST"])
@admin_required
def add_equipment():
    user_id = int(get_jwt_identity())
    data = get_body(request)

    require(data, "name")

    category = parse_enum(data.get("category"), "equipment_category", required=True,field="category")
    last_serviced_date = parse_date(data.get("last_serviced_date"), "last_serviced_date", required=True)
    # min_value=1: 0 used to be accepted and then divided by on every read.
    service_frequency_days = parse_int(
        data.get("service_frequency_days"), "service_frequency_days", required=True, min_value=1
    )
    estimated_service_cost = parse_decimal(
        data.get("estimated_service_cost"), "estimated_service_cost", min_value=0
    )

    eq = Equipment(
        name=data["name"],
        category=category,
        last_serviced_date=last_serviced_date,
        service_frequency_days=service_frequency_days,
        estimated_service_cost=estimated_service_cost,
        created_by=user_id
    )
    db.session.add(eq)
    db.session.commit()
    return jsonify(_equipment_dict(eq)), 201


# PUT /api/equipment/<id>/service — mark serviced (today by default)
@equipment_bp.route("/<int:eid>/service", methods=["PUT"])
@admin_required
def mark_serviced(eid):
    user_id = int(get_jwt_identity())
    eq = Equipment.query.get_or_404(eid)
    data = get_body(request)

    # optional serviced_date so a service done last week can still be logged
    serviced_date = parse_date(data.get("serviced_date"), "serviced_date") or date.today()
    cost = parse_decimal(data.get("cost"), "cost", min_value=0)

    # update last serviced date
    eq.last_serviced_date = serviced_date

    # log the service
    log = EquipmentServiceLog(
        equipment_id=eq.id,
        serviced_date=serviced_date,
        cost=cost,
        vendor_name=data.get("vendor_name"),
        notes=data.get("notes"),
        logged_by=user_id
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "message": "Equipment marked as serviced",
        "equipment": _equipment_dict(eq)
    }), 200


# GET /api/equipment/forecast — 30-day maintenance forecast
@equipment_bp.route("/forecast", methods=["GET"])
@active_user_required
def forecast():
    items = Equipment.query.all()
    due_in_30 = []

    for eq in items:
        days_left = _days_until_due(eq)
        # days_left is negative when overdue, so overdue items stay in the list
        if days_left <= 30:
            due_in_30.append({
                "id": eq.id,
                "name": eq.name,
                "category": eq.category,
                "days_until_due": days_left,
                "estimated_cost": float(eq.estimated_service_cost) if eq.estimated_service_cost else 0,
                "risk_level": _risk_level(eq)
            })

    total_estimated_cost = sum(item["estimated_cost"] for item in due_in_30)

    return jsonify({
        "due_in_30_days": due_in_30,
        "total_estimated_cost": total_estimated_cost,
        "count": len(due_in_30)
    }), 200


# GET /api/equipment/<id>/history — service log history
@equipment_bp.route("/<int:eid>/history", methods=["GET"])
@active_user_required
def get_history(eid):
    eq = Equipment.query.get_or_404(eid)
    logs = EquipmentServiceLog.query.filter_by(equipment_id=eid)\
            .order_by(EquipmentServiceLog.serviced_date.desc()).all()
    return jsonify([_log_dict(l) for l in logs]), 200


# DELETE /api/equipment/<id> — delete equipment
@equipment_bp.route("/<int:eid>", methods=["DELETE"])
@admin_required
def delete_equipment(eid):
    eq = Equipment.query.get_or_404(eid)
    db.session.delete(eq)
    db.session.commit()
    return jsonify({"message": "Equipment deleted"}), 200


# ── helpers ───────────────────────────────────────────────────
def _equipment_dict(e):
    return {
        "id": e.id,
        "name": e.name,
        "category": e.category,
        "last_serviced_date": str(e.last_serviced_date),
        "service_frequency_days": e.service_frequency_days,
        "estimated_service_cost": float(e.estimated_service_cost) if e.estimated_service_cost else None,
        "days_until_due": _days_until_due(e),
        "risk_level": _risk_level(e),
        "created_at": str(e.created_at)
    }

def _log_dict(l):
    return {
        "id": l.id,
        "serviced_date": str(l.serviced_date),
        "cost": float(l.cost) if l.cost else None,
        "vendor_name": l.vendor_name,
        "notes": l.notes,
        "logged_by_name": l.logger.name if l.logger else None
    }
