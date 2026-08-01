from flask import Blueprint, request, jsonify
from models import db, Expense, User

from auth.roles import current_user, finance_required, is_admin
from utils import (ApiError, get_body, parse_date, parse_decimal, parse_enum,
                   parse_int, require)

expenses_bp = Blueprint("expenses", __name__)


# GET /api/expenses — list all expenses (the ledger is admin data)
@expenses_bp.route("/", methods=["GET"])
@finance_required
def get_expenses():
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    return jsonify([_expense_dict(e) for e in expenses]), 200


# POST /api/expenses — log new expense
@expenses_bp.route("/", methods=["POST"])
@finance_required
def add_expense():
    user = current_user()
    data = get_body(request)

    require(data, "category", "description", "amount", "expense_date")

    # Parsed before the row is built: raw strings into Numeric/Date columns and
    # unknown enum values used to blow up at flush time or poison later reads.
    category = parse_enum(data.get("category"), "expense_category",
                          required=True)
    amount = parse_decimal(data.get("amount"), "amount", required=True,
                           min_value=0)
    expense_date = parse_date(data.get("expense_date"), "expense_date",
                              required=True)

    # paid_by is a FK to users.id — clients may not pin the spend on an
    # arbitrary account, it defaults to whoever is logged in.
    paid_by = user.id
    if data.get("paid_by") is not None and is_admin(user):
        paid_by = parse_int(data.get("paid_by"), "paid_by", min_value=1)
        if not User.query.get(paid_by):
            raise ApiError("paid_by user not found", 404)

    expense = Expense(
        category=category,
        description=data["description"],
        amount=amount,
        expense_date=expense_date,
        paid_by=paid_by,
        logged_by=user.id,
        receipt_url=data.get("receipt_url")
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify(_expense_dict(expense)), 201


# PUT /api/expenses/<id> — update expense
@expenses_bp.route("/<int:exp_id>", methods=["PUT"])
@finance_required
def update_expense(exp_id):
    expense = Expense.query.get_or_404(exp_id)
    data = get_body(request)

    if data.get("description"):
        expense.description = data["description"]
    if "amount" in data:
        expense.amount = parse_decimal(data.get("amount"), "amount",
                                       required=True, min_value=0)
    if "category" in data:
        expense.category = parse_enum(data.get("category"), "expense_category",
                                      required=True)
    expense.receipt_url = data.get("receipt_url", expense.receipt_url)

    db.session.commit()
    return jsonify(_expense_dict(expense)), 200


# DELETE /api/expenses/<id> — delete expense
@expenses_bp.route("/<int:exp_id>", methods=["DELETE"])
@finance_required
def delete_expense(exp_id):
    expense = Expense.query.get_or_404(exp_id)
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted"}), 200


# GET /api/expenses/summary — monthly P&L summary
@expenses_bp.route("/summary", methods=["GET"])
@finance_required
def summary():
    month = parse_int(request.args.get("month"), "month",
                      min_value=1, max_value=12)
    year = parse_int(request.args.get("year"), "year",
                     min_value=1900, max_value=9999)

    # Half a filter used to fall through to all-time totals, which read as a
    # wildly wrong month on the dashboard.
    if (month is None) != (year is None):
        raise ApiError("Provide both month and year")

    from models import Invoice
    from sqlalchemy import extract

    query = Expense.query
    inv_query = Invoice.query.filter_by(status="PAID")

    if month and year:
        query = query.filter(
            extract("month", Expense.expense_date) == month,
            extract("year", Expense.expense_date) == year
        )
        inv_query = inv_query.filter_by(month=month, year=year)

    expenses = query.all()
    total_expense = sum(float(e.amount) for e in expenses)
    total_income = sum(float(i.amount) for i in inv_query.all())

    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + float(e.amount)

    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
        "by_category": by_category
    }), 200


# ── helper ────────────────────────────────────────────────────
def _expense_dict(e):
    return {
        "id": e.id,
        "category": e.category,
        "description": e.description,
        "amount": float(e.amount),
        "expense_date": str(e.expense_date),
        "paid_by": e.paid_by,
        "paid_by_name": e.payer.name if e.payer else None,
        "receipt_url": e.receipt_url,
        "created_at": str(e.created_at)
    }
