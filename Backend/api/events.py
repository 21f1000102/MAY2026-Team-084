from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from models import db, Event, Invoice, Vote, MaintenanceTask, Equipment, Resident

from utils import (ApiError, get_body, require, parse_date, parse_enum,
                   parse_int, search_term, ilike, apply_date_range)
from auth.roles import current_user, is_admin, active_user_required, admin_required
from api.equipment import _days_until_due

events_bp = Blueprint("events", __name__)


def _own_apartment_id(user):
    resident = Resident.query.filter_by(user_id=user.id).first()
    return resident.apartment_id if resident else None


def _severity(days_until):
    """Proximity bucket for the frontend's badge-urgent / badge-high /
    badge-low classes. Overdue (negative days_until) is always urgent."""
    if days_until <= 3:
        return "urgent"
    if days_until <= 7:
        return "high"
    return "low"


# GET /api/events — list manual events
@events_bp.route("/", methods=["GET"])
@active_user_required
def get_events():
    query = Event.query.filter_by(is_active=True)

    event_type = parse_enum(request.args.get("event_type"), "event_type", field="event_type")
    if event_type:
        query = query.filter(Event.event_type == event_type)

    q = search_term(request.args.get("q"))
    if q:
        query = query.filter(ilike(Event.title, q))

    query = apply_date_range(query, Event.event_date, request.args)

    events = query.order_by(Event.event_date).all()
    return jsonify([_event_dict(e) for e in events]), 200


# POST /api/events — create event
@events_bp.route("/", methods=["POST"])
@admin_required
def add_event():
    user = current_user()
    data = get_body(request)
    require(data, "title", "event_date")

    event_type = parse_enum(data.get("event_type"), "event_type", field="event_type", default="EVENT")
    event_date = parse_date(data.get("event_date"), "event_date", required=True)

    event = Event(
        title=data["title"].strip(),
        description=data.get("description"),
        event_type=event_type,
        event_date=event_date,
        event_time=data.get("event_time"),
        location=data.get("location"),
        created_by=user.id,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(_event_dict(event)), 201


# PUT /api/events/<id> — update event
@events_bp.route("/<int:eid>", methods=["PUT"])
@admin_required
def update_event(eid):
    event = Event.query.get_or_404(eid)
    data = get_body(request)

    if data.get("title"):
        event.title = data["title"].strip()
    event.description = data.get("description", event.description)
    if "event_type" in data:
        event.event_type = parse_enum(data.get("event_type"), "event_type",
                                      field="event_type", required=True)
    if "event_date" in data:
        event.event_date = parse_date(data.get("event_date"), "event_date", required=True)
    event.event_time = data.get("event_time", event.event_time)
    event.location = data.get("location", event.location)

    db.session.commit()
    return jsonify(_event_dict(event)), 200


# DELETE /api/events/<id> — soft delete, like Announcement
@events_bp.route("/<int:eid>", methods=["DELETE"])
@admin_required
def delete_event(eid):
    event = Event.query.get_or_404(eid)
    event.is_active = False
    db.session.commit()
    return jsonify({"message": "Event deleted"}), 200


# GET /api/events/upcoming — merged, role-aware deadlines feed
@events_bp.route("/upcoming", methods=["GET"])
@active_user_required
def upcoming():
    user = current_user()
    days = parse_int(request.args.get("days"), "days", min_value=1, max_value=365) or 30
    today = date.today()
    cutoff = today + timedelta(days=days)
    items = []

    for e in Event.query.filter_by(is_active=True).filter(Event.event_date <= cutoff).all():
        items.append(_feed_item(e.event_type, e.title, e.event_date, "event", "/app/events"))

    if is_admin(user):
        invoices = Invoice.query.filter(
            Invoice.status != "PAID", Invoice.due_date.isnot(None),
            Invoice.due_date <= cutoff,
        ).all()
    else:
        apartment_id = _own_apartment_id(user)
        invoices = Invoice.query.filter(
            Invoice.status != "PAID", Invoice.due_date.isnot(None),
            Invoice.due_date <= cutoff, Invoice.apartment_id == apartment_id,
        ).all() if apartment_id else []
    for i in invoices:
        title = (f"Invoice due — Flat {i.apartment.flat_number}"
                if is_admin(user) else "Your rent invoice is due")
        items.append(_feed_item("DEADLINE", title, i.due_date, "invoice", "/app/invoices"))

    for v in Vote.query.filter(Vote.status == "ACTIVE", Vote.end_date <= cutoff).all():
        items.append(_feed_item("DEADLINE", f"Poll closes — {v.title}", v.end_date, "poll", "/app/polls"))

    if is_admin(user) or user.role == "WORKER":
        mq = MaintenanceTask.query.filter(
            MaintenanceTask.status != "COMPLETED",
            MaintenanceTask.scheduled_date <= cutoff,
        )
        if not is_admin(user):
            mq = mq.filter(MaintenanceTask.assigned_to == user.id)
        for t in mq.all():
            items.append(_feed_item("MAINTENANCE", t.title, t.scheduled_date, "maintenance", "/app/maintenance"))

    if is_admin(user):
        for eq in Equipment.query.all():
            days_left = _days_until_due(eq)
            if days_left <= days:
                items.append(_feed_item(
                    "MAINTENANCE", f"Service due — {eq.name}",
                    today + timedelta(days=days_left), "equipment", "/app/equipment",
                ))

    for item in items:
        item["days_until"] = (item["date"] - today).days
        item["severity"] = _severity(item["days_until"])
        item["date"] = str(item["date"])

    items.sort(key=lambda x: x["days_until"])
    return jsonify(items), 200


# ── helpers ───────────────────────────────────────────────────
def _feed_item(type_, title, event_date, source, link):
    return {"type": type_, "title": title, "date": event_date, "source": source, "link": link}


def _event_dict(e):
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "event_type": e.event_type,
        "event_date": str(e.event_date),
        "event_time": e.event_time,
        "location": e.location,
        "created_by": e.created_by,
        "created_at": str(e.created_at),
    }
