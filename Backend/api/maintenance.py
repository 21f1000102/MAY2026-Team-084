from flask import Blueprint, request, jsonify
from models import db, MaintenanceTask
from datetime import datetime

from auth.roles import active_user_required, admin_required, current_user
from utils import (ApiError, get_body, parse_date, parse_enum, parse_int,
                   require)

maintenance_bp = Blueprint("maintenance", __name__)


# GET /api/maintenance — all tasks
@maintenance_bp.route("/", methods=["GET"])
@active_user_required
def get_tasks():
    tasks = MaintenanceTask.query.order_by(MaintenanceTask.scheduled_date).all()
    return jsonify([_task_dict(t) for t in tasks]), 200


# POST /api/maintenance — add new task
@maintenance_bp.route("/", methods=["POST"])
@admin_required
def add_task():
    user = current_user()
    data = get_body(request)

    require(data, "title", "category", "scheduled_date")

    # Both used to go into the row raw: a bad category poisoned later reads and
    # a date string raised a TypeError at flush time.
    category = parse_enum(data.get("category"), "task_category", required=True)
    scheduled_date = parse_date(data.get("scheduled_date"), "scheduled_date",
                                required=True)
    assigned_to = parse_int(data.get("assigned_to"), "assigned_to", min_value=1)

    task = MaintenanceTask(
        title=data["title"],
        description=data.get("description"),
        category=category,
        scheduled_date=scheduled_date,
        created_by=user.id,
        assigned_to=assigned_to
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(_task_dict(task)), 201


# PUT /api/maintenance/<id>/complete — mark task complete
@maintenance_bp.route("/<int:tid>/complete", methods=["PUT"])
@admin_required
def complete_task(tid):
    task = MaintenanceTask.query.get_or_404(tid)
    if task.status == "COMPLETED":
        raise ApiError("Task is already completed", 409)

    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_task_dict(task)), 200


# PUT /api/maintenance/<id> — update task
@maintenance_bp.route("/<int:tid>", methods=["PUT"])
@admin_required
def update_task(tid):
    task = MaintenanceTask.query.get_or_404(tid)
    data = get_body(request)

    if data.get("title"):
        task.title = data["title"]
    task.description = data.get("description", task.description)

    if "category" in data:
        task.category = parse_enum(data.get("category"), "task_category",
                                   required=True)
    if "scheduled_date" in data:
        task.scheduled_date = parse_date(data.get("scheduled_date"),
                                         "scheduled_date", required=True)
    if "assigned_to" in data:
        task.assigned_to = parse_int(data.get("assigned_to"), "assigned_to",
                                     min_value=1)

    if "status" in data:
        status = parse_enum(data.get("status"), "task_status", required=True)
        task.status = status
        # This path used to leave COMPLETED tasks with completed_at = null.
        if status == "COMPLETED":
            if not task.completed_at:
                task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None

    db.session.commit()
    return jsonify(_task_dict(task)), 200


# DELETE /api/maintenance/<id> — delete task
@maintenance_bp.route("/<int:tid>", methods=["DELETE"])
@admin_required
def delete_task(tid):
    task = MaintenanceTask.query.get_or_404(tid)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200


# ── helper ────────────────────────────────────────────────────
def _task_dict(t):
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "category": t.category,
        "scheduled_date": str(t.scheduled_date),
        "status": t.status,
        "created_by": t.created_by,
        "assigned_to": t.assigned_to,
        "assigned_to_name": t.assignee.name if t.assignee else None,
        "completed_at": str(t.completed_at) if t.completed_at else None
    }
