"""Contract freeze for the six list endpoints touched by the search/filter
and worker-role work (members, complaints, invoices, invoices/pending,
expenses, maintenance).

These assert the exact key set every item exposes today. If a future change
renames, removes, or (via a builder helper) accidentally adds a key to one of
these dicts, this test catches it — the filtering/summary/export work added
new *endpoints*, it must never change the *shape* of the existing ones.

If this file needs editing, the response shape genuinely changed and that
change must be a deliberate, reviewed decision — not a side effect.
"""
from datetime import date, timedelta

MEMBER_KEYS = {
    "id", "user_id", "name", "email", "phone", "role", "is_active",
    "apartment_id", "flat_number", "block", "floor", "is_owner",
    "move_in_date", "move_out_date",
}

COMPLAINT_KEYS = {
    "id", "title", "description", "category", "priority", "status",
    "apartment_id", "flat_number", "raised_by", "raised_by_name",
    "assigned_worker_id", "assigned_worker_name", "created_at", "resolved_at",
}

INVOICE_KEYS = {
    "id", "apartment_id", "flat_number", "month", "year", "amount",
    "due_date", "status", "created_at",
}

EXPENSE_KEYS = {
    "id", "category", "description", "amount", "expense_date", "paid_by",
    "paid_by_name", "receipt_url", "created_at",
}

TASK_KEYS = {
    "id", "title", "description", "category", "scheduled_date", "status",
    "created_by", "assigned_to", "assigned_to_name", "completed_at",
}


def test_members_shape_unchanged(client, admin, seed):
    res = client.get("/api/members/", headers=admin)
    assert res.status_code == 200
    assert set(res.get_json()[0].keys()) == MEMBER_KEYS


def test_complaints_shape_unchanged(client, admin, seed):
    client.post("/api/complaints/", json={
        "title": "x", "category": "OTHER", "apartment_id": seed["apartment_id"],
    }, headers=admin)
    res = client.get("/api/complaints/", headers=admin)
    assert res.status_code == 200
    assert set(res.get_json()[0].keys()) == COMPLAINT_KEYS


def test_invoices_shape_unchanged(client, admin, seed):
    client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026, "amount": 2500,
    }, headers=admin)
    res = client.get("/api/invoices/", headers=admin)
    assert res.status_code == 200
    assert set(res.get_json()[0].keys()) == INVOICE_KEYS


def test_invoices_pending_shape_unchanged(client, admin, seed):
    client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026, "amount": 2500,
    }, headers=admin)
    res = client.get("/api/invoices/pending", headers=admin)
    assert res.status_code == 200
    assert set(res.get_json()[0].keys()) == INVOICE_KEYS


def test_expenses_shape_unchanged(client, admin, seed):
    client.post("/api/expenses/", json={
        "category": "UTILITIES", "description": "Bill", "amount": 100,
        "expense_date": "2026-07-01",
    }, headers=admin)
    res = client.get("/api/expenses/", headers=admin)
    assert res.status_code == 200
    assert set(res.get_json()[0].keys()) == EXPENSE_KEYS


def test_maintenance_shape_unchanged(client, admin, seed):
    client.post("/api/maintenance/", json={
        "title": "x", "category": "GENERATOR",
        "scheduled_date": str(date.today() + timedelta(days=1)),
    }, headers=admin)
    res = client.get("/api/maintenance/", headers=admin)
    assert res.status_code == 200
    assert set(res.get_json()[0].keys()) == TASK_KEYS


def test_maintenance_no_longer_globally_visible_to_workers(client, admin, worker, seed):
    """Locks in the one deliberate behaviour change in this endpoint: a
    worker used to see every task in the society; now they see only their
    own. This is intentional (Feature 4) and documented in KNOWN_ISSUES /
    the plan — if this test needs to change, that change must be deliberate.
    """
    client.post("/api/maintenance/", json={
        "title": "Not assigned to this worker", "category": "GENERATOR",
        "scheduled_date": str(date.today() + timedelta(days=1)),
    }, headers=admin)
    res = client.get("/api/maintenance/", headers=worker)
    assert res.status_code == 200
    assert res.get_json() == []
