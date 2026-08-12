from flask import Blueprint, request, jsonify
from sqlalchemy.orm import aliased
from models import db, MaintenanceTask, User
from datetime import datetime, date

from auth.roles import active_user_required, admin_required, current_user, is_admin
from utils import (ApiError, get_body, parse_date, parse_enum, parse_int,
                   search_term, ilike, apply_date_range, require)

maintenance_bp = Blueprint("maintenance", __name__)


def _filtered_tasks_query(user, args):
    """Task query scoped to what `user` may see, with optional filters
    layered on top. Role scoping is applied first and is never touched by
    the filter args below, so a filter can only narrow what a caller could
    already see.

    Admins see every task. A WORKER sees only tasks assigned to them — this
    was previously unscoped, so every worker saw the whole society's
    maintenance schedule. Residents keep read-only visibility of everything,
    matching the pre-existing (unscoped) behaviour for that role.
    """
    query = MaintenanceTask.query

    if is_admin(user):
        pass
    elif user.role == "WORKER":
        query = query.filter(MaintenanceTask.assigned_to == user.id)

    status = parse_enum(args.get("status"), "task_status", field="status")
    if status:
        query = query.filter(MaintenanceTask.status == status)

    category = parse_enum(args.get("category"), "task_category", field="category")
    if category:
        query = query.filter(MaintenanceTask.category == category)

    # Not gated to admins: for a worker this simply intersects with the
    # assigned-to-me scoping already applied above, so it can only narrow
    # their own results — never widen what they may see.
    assigned_to = parse_int(args.get("assigned_to"), "assigned_to", min_value=1)
    if assigned_to:
        query = query.filter(MaintenanceTask.assigned_to == assigned_to)

    worker = search_term(args.get("worker"))
    if worker:
        Worker = aliased(User)
        query = query.join(Worker, MaintenanceTask.assigned_to == Worker.id) \
                     .filter(ilike(Worker.name, worker))

    query = apply_date_range(query, MaintenanceTask.scheduled_date, args)

    return query


def _may_complete(user, task):
    if is_admin(user):
        return True
    return user.role == "WORKER" and task.assigned_to == user.id


# GET /api/maintenance — role-scoped list of tasks
@maintenance_bp.route("/", methods=["GET"])
@active_user_required
def get_tasks():
    user = current_user()
    tasks = _filtered_tasks_query(user, request.args) \
        .order_by(MaintenanceTask.scheduled_date).all()
    return jsonify([_task_dict(t) for t in tasks]), 200


# GET /api/maintenance/summary — counts and breakdowns
@maintenance_bp.route("/summary", methods=["GET"])
@active_user_required
def tasks_summary():
    user = current_user()
    tasks = _filtered_tasks_query(user, request.args).all()

    by_status = {s: 0 for s in ("PENDING", "IN_PROGRESS", "COMPLETED")}
    by_category = {}
    overdue_count = 0
    today = date.today()

    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_category[t.category] = by_category.get(t.category, 0) + 1
        if t.status != "COMPLETED" and t.scheduled_date and t.scheduled_date < today:
            overdue_count += 1

    return jsonify({
        "total": len(tasks),
        "by_status": by_status,
        "by_category": by_category,
        "overdue_count": overdue_count,
    }), 200


# POST /api/maintenance — add new task
@maintenance_bp.route("/", methods=["POST"])
@admin_required
def add_task():
    user = current_user()
    data = get_body(request)

    require(data, "title", "category", "scheduled_date")

    # Both used to go into the row raw: a bad category poisoned later reads and
    # a date string raised a TypeError at flush time.
    category = parse_enum(data.get("category"), "task_category", required=True,field="category")
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
@active_user_required
def complete_task(tid):
    user = current_user()
    task = MaintenanceTask.query.get_or_404(tid)

    # A worker previously could not close out their own assigned job — this
    # endpoint was admin-only, so the WORKER role could see tasks but never
    # finish them.
    if not _may_complete(user, task):
        raise ApiError("You are not allowed to complete this task", 403)

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
                                   required=True, field="category")
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
