from flask import Blueprint, request, jsonify
from models import db, Announcement

from auth.roles import active_user_required, admin_required, current_user
from utils import get_body, parse_enum, require

notices_bp = Blueprint("notices", __name__)


# GET /api/notices — all active notices
@notices_bp.route("/", methods=["GET"])
@active_user_required
def get_notices():
    notices = Announcement.query.filter_by(is_active=True)\
                .order_by(Announcement.created_at.desc()).all()
    return jsonify([_notice_dict(n) for n in notices]), 200


# POST /api/notices — post new notice
@notices_bp.route("/", methods=["POST"])
@admin_required
def add_notice():
    user = current_user()
    data = get_body(request)

    require(data, "title", "content")
    # An unknown category used to commit and then break every later read.
    category = parse_enum(data.get("category"), "announcement_category",
                          field="category", default="GENERAL")

    notice = Announcement(
        title=data["title"],
        content=data["content"],
        category=category,
        published_by=user.id
    )
    db.session.add(notice)
    db.session.commit()
    return jsonify(_notice_dict(notice)), 201


# PUT /api/notices/<id> — update notice
@notices_bp.route("/<int:nid>", methods=["PUT"])
@admin_required
def update_notice(nid):
    notice = Announcement.query.get_or_404(nid)
    data = get_body(request)

    if data.get("title"):
        notice.title = data["title"]
    if data.get("content"):
        notice.content = data["content"]
    if "category" in data:
        notice.category = parse_enum(data.get("category"), "announcement_category",
                                     field="category", default=notice.category)

    db.session.commit()
    return jsonify(_notice_dict(notice)), 200


# DELETE /api/notices/<id> — soft delete (deactivate)
@notices_bp.route("/<int:nid>", methods=["DELETE"])
@admin_required
def delete_notice(nid):
    notice = Announcement.query.get_or_404(nid)
    notice.is_active = False
    db.session.commit()
    return jsonify({"message": "Notice removed"}), 200


# ── helper ────────────────────────────────────────────────────
def _notice_dict(n):
    return {
        "id": n.id,
        "title": n.title,
        "content": n.content,
        "category": n.category,
        "published_by": n.published_by,
        "published_by_name": n.publisher.name if n.publisher else None,
        "is_active": n.is_active,
        "created_at": str(n.created_at)
    }
