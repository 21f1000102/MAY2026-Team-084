from flask import Blueprint, request, jsonify
from models import db, Invoice, Payment, Apartment, Resident
from datetime import datetime, date

from utils import (ApiError, get_body, require, parse_date, parse_decimal,
                   parse_int, parse_enum, search_term, ilike,
                   apply_date_range, parse_amount_range, csv_response)
from auth.roles import current_user, is_admin, active_user_required, finance_required

invoices_bp = Blueprint("invoices", __name__)


def _own_apartment_id(user):
    """The apartment this user lives in, or None."""
    resident = Resident.query.filter_by(user_id=user.id).first()
    return resident.apartment_id if resident else None


def _sweep_overdue_invoices():
    """Promote UNPAID invoices whose due date has passed to OVERDUE, as one
    scoped bulk UPDATE that runs BEFORE any status/date filter is applied.

    Doing this per-fetched-row (the old approach) broke the moment a caller
    filtered by status: filtering status=OVERDUE excluded rows that were about
    to be promoted, and status=UNPAID returned rows that were already stale.
    Running the sweep first, over the whole table, keeps every filter honest.
    """
    changed = Invoice.query.filter(
        Invoice.status == "UNPAID",
        Invoice.due_date.isnot(None),
        Invoice.due_date < date.today(),
    ).update({"status": "OVERDUE"}, synchronize_session=False)
    if changed:
        db.session.commit()


def _filtered_invoice_query(user, args, allow_status=True):
    """Invoice query scoped to what `user` may see, with optional filters
    layered on top. Returns None if a resident has no apartment (caller should
    then return an empty list, matching the pre-filter behaviour).

    Role scoping is applied first and is never touched by the filter args
    below, so a filter can only narrow what a caller could already see.
    """
    if is_admin(user):
        query = Invoice.query
    else:
        apartment_id = _own_apartment_id(user)
        if not apartment_id:
            return None
        query = Invoice.query.filter_by(apartment_id=apartment_id)

    if allow_status:
        status = parse_enum(args.get("status"), "invoice_status", field="status")
        if status:
            query = query.filter_by(status=status)

    month = parse_int(args.get("month"), "month", min_value=1, max_value=12)
    if month:
        query = query.filter_by(month=month)

    year = parse_int(args.get("year"), "year", min_value=2000, max_value=2200)
    if year:
        query = query.filter_by(year=year)

    # Not gated to admins: for a resident this simply intersects with the
    # apartment scoping already applied above, so it can only narrow their
    # own results (typically to nothing, if they pass someone else's flat) —
    # never widen what they may see.
    apartment_id_f = parse_int(args.get("apartment_id"), "apartment_id", min_value=1)
    if apartment_id_f:
        query = query.filter_by(apartment_id=apartment_id_f)

    flat = search_term(args.get("flat") or args.get("q"))
    if flat:
        query = query.join(Apartment).filter(ilike(Apartment.flat_number, flat))

    query = apply_date_range(query, Invoice.due_date, args)

    min_amt, max_amt = parse_amount_range(args)
    if min_amt is not None:
        query = query.filter(Invoice.amount >= min_amt)
    if max_amt is not None:
        query = query.filter(Invoice.amount <= max_amt)

    return query


# GET /api/invoices — all invoices (admin) or own (resident)
@invoices_bp.route("/", methods=["GET"])
@active_user_required
def get_invoices():
    user = current_user()
    _sweep_overdue_invoices()

    query = _filtered_invoice_query(user, request.args)
    if query is None:
        return jsonify([]), 200

    invoices = query.order_by(Invoice.created_at.desc()).all()
    return jsonify([_invoice_dict(i) for i in invoices]), 200


# POST /api/invoices — generate single invoice
@invoices_bp.route("/", methods=["POST"])
@finance_required
def create_invoice():
    user = current_user()
    data = get_body(request)
    require(data, "apartment_id", "month", "year", "amount")

    apartment_id = parse_int(data.get("apartment_id"), "apartment_id", required=True)
    month = parse_int(data.get("month"), "month", required=True, min_value=1, max_value=12)
    year = parse_int(data.get("year"), "year", required=True, min_value=2000, max_value=2200)
    amount = parse_decimal(data.get("amount"), "amount", required=True, min_value=0)
    due_date = parse_date(data.get("due_date"), "due_date")

    if not Apartment.query.get(apartment_id):
        raise ApiError("Apartment not found", 404)

    # bulk already guarded against duplicates; the single route did not.
    if Invoice.query.filter_by(apartment_id=apartment_id, month=month, year=year).first():
        raise ApiError("An invoice already exists for this flat and month", 409)

    invoice = Invoice(
        apartment_id=apartment_id,
        generated_by=user.id,
        month=month,
        year=year,
        amount=amount,
        due_date=due_date,
    )
    db.session.add(invoice)
    db.session.commit()
    return jsonify(_invoice_dict(invoice)), 201


# POST /api/invoices/bulk — generate invoices for ALL flats in one click
@invoices_bp.route("/bulk", methods=["POST"])
@finance_required
def bulk_generate():
    user = current_user()
    data = get_body(request)
    require(data, "month", "year", "amount")

    month = parse_int(data.get("month"), "month", required=True, min_value=1, max_value=12)
    year = parse_int(data.get("year"), "year", required=True, min_value=2000, max_value=2200)
    amount = parse_decimal(data.get("amount"), "amount", required=True, min_value=0)
    due_date = parse_date(data.get("due_date"), "due_date")

    created = []
    for apt in Apartment.query.all():
        # skip if invoice already exists for this month/year
        exists = Invoice.query.filter_by(
            apartment_id=apt.id, month=month, year=year
        ).first()
        if exists:
            continue

        db.session.add(Invoice(
            apartment_id=apt.id,
            generated_by=user.id,
            month=month,
            year=year,
            amount=amount,
            due_date=due_date,
        ))
        created.append(apt.flat_number)

    db.session.commit()
    return jsonify({
        "message": f"Invoices generated for {len(created)} flats",
        "flats": created
    }), 201


# PUT /api/invoices/<id>/pay — mark invoice as paid
@invoices_bp.route("/<int:inv_id>/pay", methods=["PUT"])
@finance_required
def mark_paid(inv_id):
    invoice = Invoice.query.get_or_404(inv_id)
    data = get_body(request)

    # Was not idempotent: paying twice inserted a second Payment row while the
    # receipt kept showing the first.
    if invoice.status == "PAID":
        raise ApiError("This invoice is already paid", 409)

    resident = Resident.query.filter_by(apartment_id=invoice.apartment_id).first()
    if not resident:
        return jsonify({"error": "No resident found for this apartment"}), 404

    invoice.status = "PAID"

    payment = Payment(
        invoice_id=invoice.id,
        resident_id=resident.id,
        amount=invoice.amount,
        payment_method=data.get("payment_method", "CASH"),
        transaction_reference=data.get("transaction_reference"),
        payment_date=datetime.utcnow(),
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({
        "message": "Invoice marked as paid",
        "invoice": _invoice_dict(invoice),
        "receipt": _receipt_dict(payment, invoice)
    }), 200


# GET /api/invoices/<id>/receipt — download receipt data
@invoices_bp.route("/<int:inv_id>/receipt", methods=["GET"])
@active_user_required
def get_receipt(inv_id):
    user = current_user()
    invoice = Invoice.query.get_or_404(inv_id)

    # Residents may only read receipts for their own flat.
    if not is_admin(user) and invoice.apartment_id != _own_apartment_id(user):
        raise ApiError("You are not allowed to view this receipt", 403)

    if invoice.status != "PAID":
        return jsonify({"error": "Invoice not paid yet"}), 400

    payment = Payment.query.filter_by(invoice_id=inv_id).first()
    if not payment:
        raise ApiError("No payment record found for this invoice", 404)

    return jsonify(_receipt_dict(payment, invoice)), 200


# GET /api/invoices/pending — unpaid invoices (own flat unless admin)
@invoices_bp.route("/pending", methods=["GET"])
@active_user_required
def get_pending():
    user = current_user()
    _sweep_overdue_invoices()

    query = _filtered_invoice_query(user, request.args, allow_status=False)
    if query is None:
        return jsonify([]), 200

    query = query.filter(Invoice.status != "PAID")
    invoices = query.all()
    return jsonify([_invoice_dict(i) for i in invoices]), 200


# GET /api/invoices/summary — totals, counts and collection rate
@invoices_bp.route("/summary", methods=["GET"])
@active_user_required
def invoice_summary():
    user = current_user()
    _sweep_overdue_invoices()

    query = _filtered_invoice_query(user, request.args)
    invoices = query.all() if query is not None else []

    paid = [i for i in invoices if i.status == "PAID"]
    unpaid = [i for i in invoices if i.status == "UNPAID"]
    overdue = [i for i in invoices if i.status == "OVERDUE"]

    total_invoiced = sum(float(i.amount) for i in invoices)
    total_collected = sum(float(i.amount) for i in paid)
    total_pending = sum(float(i.amount) for i in unpaid) + sum(float(i.amount) for i in overdue)
    overdue_amount = sum(float(i.amount) for i in overdue)
    collection_rate = round((total_collected / total_invoiced) * 100, 2) if total_invoiced else 0.0

    by_month = {}
    for i in invoices:
        key = f"{i.year}-{i.month:02d}"
        entry = by_month.setdefault(key, {"invoiced": 0.0, "collected": 0.0})
        entry["invoiced"] += float(i.amount)
        if i.status == "PAID":
            entry["collected"] += float(i.amount)

    return jsonify({
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "total_pending": total_pending,
        "count_paid": len(paid),
        "count_unpaid": len(unpaid),
        "count_overdue": len(overdue),
        "overdue_amount": overdue_amount,
        "collection_rate": collection_rate,
        "by_month": by_month,
    }), 200


# GET /api/invoices/export — CSV of the filtered list
@invoices_bp.route("/export", methods=["GET"])
@active_user_required
def export_invoices():
    user = current_user()
    _sweep_overdue_invoices()

    query = _filtered_invoice_query(user, request.args)
    invoices = query.order_by(Invoice.created_at.desc()).all() if query is not None else []

    columns = [
        ("ID", "id"), ("Flat", "flat_number"), ("Month", "month"), ("Year", "year"),
        ("Amount", "amount"), ("Due Date", "due_date"), ("Status", "status"),
        ("Created At", "created_at"),
    ]
    return csv_response([_invoice_dict(i) for i in invoices], columns, "invoices.csv")


# ── helpers ───────────────────────────────────────────────────
def _invoice_dict(i):
    return {
        "id": i.id,
        "apartment_id": i.apartment_id,
        "flat_number": i.apartment.flat_number if i.apartment else None,
        "month": i.month,
        "year": i.year,
        "amount": float(i.amount),
        "due_date": str(i.due_date) if i.due_date else None,
        "status": i.status,
        "created_at": str(i.created_at)
    }


def _receipt_dict(p, i):
    return {
        "receipt_number": f"RCP-{str(p.id).zfill(4)}",
        "flat_number": i.apartment.flat_number if i.apartment else None,
        "month": i.month,
        "year": i.year,
        "amount": float(i.amount),
        "payment_method": p.payment_method,
        "transaction_reference": p.transaction_reference,
        "payment_date": str(p.payment_date)
    }
