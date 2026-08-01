from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import db, ParkingSlot, Resident
from datetime import datetime

from utils import ApiError, get_body, require, parse_datetime, parse_enum
from auth.roles import active_user_required, admin_required, current_user, is_admin

parking_bp = Blueprint("parking", __name__)


def _my_apartment_id(user_id):
    """Apartment of the calling resident, or None if they have no record."""
    resident = Resident.query.filter_by(user_id=user_id).first()
    return resident.apartment_id if resident else None


# GET /api/parking — all slots with status
@parking_bp.route("/", methods=["GET"])
@active_user_required
def get_slots():
    slots = ParkingSlot.query.order_by(ParkingSlot.slot_number).all()
    return jsonify([_slot_dict(s) for s in slots]), 200


# GET /api/parking/available — only available slots
@parking_bp.route("/available", methods=["GET"])
@active_user_required
def get_available():
    slots = ParkingSlot.query.filter_by(status="AVAILABLE").all()
    return jsonify([_slot_dict(s) for s in slots]), 200


# POST /api/parking — add new parking slot (admin)
@parking_bp.route("/", methods=["POST"])
@admin_required
def add_slot():
    data = get_body(request)
    require(data, "slot_number")

    slot_number = str(data["slot_number"]).strip()
    status = parse_enum(data.get("status"), "parking_status", default="AVAILABLE")

    if ParkingSlot.query.filter_by(slot_number=slot_number).first():
        return jsonify({"error": "Slot already exists"}), 409

    slot = ParkingSlot(slot_number=slot_number, status=status)
    db.session.add(slot)
    db.session.commit()
    return jsonify(_slot_dict(slot)), 201


# PUT /api/parking/<id>/reserve — resident reserves slot for visitor
@parking_bp.route("/<int:sid>/reserve", methods=["PUT"])
@active_user_required
def reserve_slot(sid):
    user_id = int(get_jwt_identity())
    slot = ParkingSlot.query.get_or_404(sid)

    if slot.status != "AVAILABLE":
        return jsonify({"error": f"Slot is already {slot.status}"}), 400

    data = get_body(request)

    slot.status = "RESERVED"
    slot.occupied_by_apartment_id = _my_apartment_id(user_id)
    slot.visitor_name = data.get("visitor_name")
    slot.visitor_vehicle_number = data.get("visitor_vehicle_number")
    slot.expected_arrival_time = parse_datetime(
        data.get("expected_arrival_time"), "expected_arrival_time"
    )
    # A reservation is not an arrival — occupied_since is stamped on occupy.
    slot.occupied_since = None
    slot.updated_by = user_id

    db.session.commit()
    return jsonify({
        "message": f"Slot {slot.slot_number} reserved successfully",
        "slot": _slot_dict(slot)
    }), 200


# PUT /api/parking/<id>/occupy — guard marks visitor arrived
@parking_bp.route("/<int:sid>/occupy", methods=["PUT"])
@active_user_required
def occupy_slot(sid):
    user_id = int(get_jwt_identity())
    slot = ParkingSlot.query.get_or_404(sid)

    if slot.status == "OCCUPIED":
        return jsonify({"error": f"Slot is already {slot.status}"}), 400

    data = get_body(request)

    slot.status = "OCCUPIED"
    # keep the reserving apartment; otherwise attribute the slot to the caller
    slot.occupied_by_apartment_id = slot.occupied_by_apartment_id or _my_apartment_id(user_id)
    slot.visitor_name = data.get("visitor_name", slot.visitor_name)
    slot.visitor_vehicle_number = data.get("visitor_vehicle_number", slot.visitor_vehicle_number)
    slot.occupied_since = datetime.utcnow()
    slot.updated_by = user_id

    db.session.commit()
    return jsonify({"message": f"Slot {slot.slot_number} marked occupied", "slot": _slot_dict(slot)}), 200


# PUT /api/parking/<id>/release — mark slot available again
@parking_bp.route("/<int:sid>/release", methods=["PUT"])
@active_user_required
def release_slot(sid):
    user = current_user()
    slot = ParkingSlot.query.get_or_404(sid)

    # Anyone could previously free anyone else's reservation.
    if not is_admin(user):
        apartment_id = _my_apartment_id(user.id)
        if apartment_id is None or slot.occupied_by_apartment_id != apartment_id:
            raise ApiError("You can only release your own reservation", 403)

    slot.status = "AVAILABLE"
    slot.occupied_by_apartment_id = None
    slot.visitor_name = None
    slot.visitor_vehicle_number = None
    slot.expected_arrival_time = None
    slot.occupied_since = None
    slot.updated_by = user.id

    db.session.commit()
    return jsonify({"message": f"Slot {slot.slot_number} released", "slot": _slot_dict(slot)}), 200


# DELETE /api/parking/<id> — remove slot
@parking_bp.route("/<int:sid>", methods=["DELETE"])
@admin_required
def delete_slot(sid):
    slot = ParkingSlot.query.get_or_404(sid)
    db.session.delete(slot)
    db.session.commit()
    return jsonify({"message": "Slot removed"}), 200


# ── helper ────────────────────────────────────────────────────
def _slot_dict(s):
    return {
        "id": s.id,
        "slot_number": s.slot_number,
        "status": s.status,
        "occupied_by_apartment_id": s.occupied_by_apartment_id,
        "flat_number": s.occupied_by_apartment.flat_number if s.occupied_by_apartment else None,
        "visitor_name": s.visitor_name,
        "visitor_vehicle_number": s.visitor_vehicle_number,
        "expected_arrival_time": str(s.expected_arrival_time) if s.expected_arrival_time else None,
        "occupied_since": str(s.occupied_since) if s.occupied_since else None
    }
