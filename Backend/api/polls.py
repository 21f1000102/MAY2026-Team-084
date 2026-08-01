from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import db, Vote, VoteOption, VoteResponse
from datetime import date

from utils import ApiError, get_body, require, parse_date, parse_enum, parse_int
from auth.roles import active_user_required, admin_required, current_user

polls_bp = Blueprint("polls", __name__)


# GET /api/polls — all polls
@polls_bp.route("/", methods=["GET"])
@active_user_required
def get_polls():
    polls = Vote.query.order_by(Vote.created_at.desc()).all()
    return jsonify([_poll_dict(p) for p in polls]), 200


# POST /api/polls — create poll
@polls_bp.route("/", methods=["POST"])
@admin_required
def create_poll():
    user_id = int(get_jwt_identity())
    data = get_body(request)

    require(data, "title")

    # A plain string used to iterate into one option per character.
    raw_options = data.get("options")
    if not isinstance(raw_options, list):
        return jsonify({"error": "options must be a list"}), 400

    options = [str(o).strip() for o in raw_options if o is not None and str(o).strip()]
    if len(options) < 2:
        return jsonify({"error": "At least 2 options required"}), 400

    # start_date/end_date are NOT NULL columns and used to be passed as raw
    # strings, so every create failed at flush time.
    start_date = parse_date(data.get("start_date"), "start_date") or date.today()
    end_date = parse_date(data.get("end_date"), "end_date", required=True)
    if end_date < start_date:
        raise ApiError("end_date cannot be before start_date")

    status = parse_enum(data.get("status"), "vote_status", default="ACTIVE")

    poll = Vote(
        title=data["title"],
        description=data.get("description"),
        created_by=user_id,
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    db.session.add(poll)
    db.session.flush()

    for opt_text in options:
        opt = VoteOption(vote_id=poll.id, option_text=opt_text)
        db.session.add(opt)

    db.session.commit()
    return jsonify(_poll_dict(poll)), 201


# GET /api/polls/<id> — single poll with results
@polls_bp.route("/<int:pid>", methods=["GET"])
@active_user_required
def get_poll(pid):
    poll = Vote.query.get_or_404(pid)
    return jsonify(_poll_dict(poll)), 200


# POST /api/polls/<id>/vote — cast vote
@polls_bp.route("/<int:pid>/vote", methods=["POST"])
@active_user_required
def cast_vote(pid):
    user_id = int(get_jwt_identity())
    poll = Vote.query.get_or_404(pid)

    if poll.status != "ACTIVE":
        return jsonify({"error": "Poll is not active"}), 400

    # check already voted
    already = VoteResponse.query.filter_by(vote_id=pid, user_id=user_id).first()
    if already:
        return jsonify({"error": "You have already voted"}), 409

    # an ACTIVE poll still only accepts votes inside its own window
    today = date.today()
    if poll.start_date and today < poll.start_date:
        return jsonify({"error": f"Voting opens on {poll.start_date}"}), 400
    if poll.end_date and today > poll.end_date:
        return jsonify({"error": f"Voting closed on {poll.end_date}"}), 400

    data = get_body(request)
    option_id = parse_int(data.get("option_id"), "option_id", required=True)
    option = VoteOption.query.filter_by(
        id=option_id, vote_id=pid
    ).first()
    if not option:
        return jsonify({"error": "Invalid option"}), 400

    response = VoteResponse(
        vote_id=pid,
        option_id=option.id,
        user_id=user_id
    )
    db.session.add(response)
    db.session.commit()
    return jsonify({"message": "Vote cast successfully", "poll": _poll_dict(poll)}), 200


# PUT /api/polls/<id>/close — close poll
@polls_bp.route("/<int:pid>/close", methods=["PUT"])
@admin_required
def close_poll(pid):
    poll = Vote.query.get_or_404(pid)
    poll.status = "CLOSED"
    db.session.commit()
    return jsonify({"message": "Poll closed", "poll": _poll_dict(poll)}), 200


# DELETE /api/polls/<id> — delete poll
@polls_bp.route("/<int:pid>", methods=["DELETE"])
@admin_required
def delete_poll(pid):
    poll = Vote.query.get_or_404(pid)
    db.session.delete(poll)
    db.session.commit()
    return jsonify({"message": "Poll deleted"}), 200


# ── helper ────────────────────────────────────────────────────
def _poll_dict(p):
    total_votes = len(p.responses)
    options = []
    for opt in p.options:
        count = VoteResponse.query.filter_by(option_id=opt.id).count()
        options.append({
            "id": opt.id,
            "text": opt.option_text,
            "votes": count,
            "percentage": round((count / total_votes * 100), 1) if total_votes > 0 else 0
        })

    # The frontend kept the vote-lock in local state only, so it reset on
    # reload and let a user re-submit (then get a 409). Report it from the DB.
    user = current_user()
    my_vote = (
        VoteResponse.query.filter_by(vote_id=p.id, user_id=user.id).first()
        if user else None
    )

    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "status": p.status,
        "total_votes": total_votes,
        "options": options,
        "has_voted": my_vote is not None,
        "my_option_id": my_vote.option_id if my_vote else None,
        "created_by": p.created_by,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "created_at": str(p.created_at)
    }
