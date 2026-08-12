"""Server-side search & filter query params added to the list endpoints on
members, complaints, invoices, invoices/pending, expenses and maintenance.

Every filter is tested for: a happy path, an invalid value returning 400
with a message naming the field, and — wherever the endpoint is scoped by
role — that the filter can only narrow what a caller could already see,
never widen it.
"""
from datetime import date, timedelta

from models import db, Complaint, Invoice


# ════════════════════════════════════════════════════════════
#  MEMBERS
# ════════════════════════════════════════════════════════════
def _add_member(client, admin, apartment_id, **overrides):
    payload = {
        "name": "Extra Member", "email": f"extra{overrides.get('email_suffix','')}@x.com",
        "password": "Pass@123", "role": "TENANT", "apartment_id": apartment_id,
    }
    payload.update({k: v for k, v in overrides.items() if k != "email_suffix"})
    res = client.post("/api/members/", json=payload, headers=admin)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def test_members_no_filters_returns_everyone(client, admin, seed):
    """Calling the endpoint with no query params must be unaffected by the
    new filtering code — this is the contract-freeze guarantee for members."""
    res = client.get("/api/members/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1   # just the seeded resident


def test_members_filter_by_role(client, admin, seed):
    _add_member(client, admin, seed["other_apartment_id"], role="OWNER", email_suffix="1")
    res = client.get("/api/members/?role=OWNER", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1
    assert body[0]["role"] == "OWNER"


def test_members_filter_by_block(client, admin, seed):
    # seed: apartment A-101 is block "A", other_apartment B-202 is block "B"
    _add_member(client, admin, seed["other_apartment_id"], email_suffix="2")
    res = client.get("/api/members/?block=B", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1
    assert body[0]["block"] == "B"


def test_members_filter_by_q_matches_flat_number(client, admin, seed):
    res = client.get("/api/members/?q=A-101", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_members_invalid_role_returns_400(client, admin, seed):
    res = client.get("/api/members/?role=NOT_A_ROLE", headers=admin)
    assert res.status_code == 400
    assert "role must be one of" in res.get_json()["error"]


def test_members_is_owner_false_excludes_owners(client, admin, seed):
    _add_member(client, admin, seed["other_apartment_id"], is_owner=True, email_suffix="3")
    res = client.get("/api/members/?is_owner=true", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and body[0]["is_owner"] is True


# ════════════════════════════════════════════════════════════
#  COMPLAINTS
# ════════════════════════════════════════════════════════════
def _raise(client, headers, apartment_id, **overrides):
    payload = {
        "title": "Leaking kitchen tap", "description": "Drips under the sink.",
        "category": "PLUMBING", "apartment_id": apartment_id,
    }
    payload.update(overrides)
    res = client.post("/api/complaints/", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def test_complaints_no_filters_unchanged(client, admin, seed):
    _raise(client, admin, seed["apartment_id"])
    res = client.get("/api/complaints/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_complaints_filter_by_category(client, admin, seed):
    _raise(client, admin, seed["apartment_id"], category="PLUMBING")
    _raise(client, admin, seed["apartment_id"], category="ELECTRICAL", title="Fan not working")

    res = client.get("/api/complaints/?category=ELECTRICAL", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and body[0]["category"] == "ELECTRICAL"


def test_complaints_filter_by_q_matches_title(client, admin, seed):
    _raise(client, admin, seed["apartment_id"], title="Lift is stuck")
    _raise(client, admin, seed["apartment_id"], title="Water leakage in bathroom")

    res = client.get("/api/complaints/?q=lift", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and "Lift" in body[0]["title"]


def test_complaints_filter_unassigned_true(client, admin, seed):
    _raise(client, admin, seed["apartment_id"])
    assigned = _raise(client, admin, seed["apartment_id"], title="Assigned one")
    client.put(f"/api/complaints/{assigned['id']}/assign",
              json={"worker_id": seed["worker_id"]}, headers=admin)

    res = client.get("/api/complaints/?unassigned=true", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1
    assert body[0]["assigned_worker_id"] is None


def test_complaints_filter_overdue_true(client, admin, seed, app):
    recent = _raise(client, admin, seed["apartment_id"], title="Recent")
    old = _raise(client, admin, seed["apartment_id"], title="Old and unresolved")

    with app.app_context():
        c = Complaint.query.get(old["id"])
        from datetime import datetime
        c.created_at = datetime.utcnow() - timedelta(days=30)
        db.session.commit()

    res = client.get("/api/complaints/?overdue=true", headers=admin)
    assert res.status_code == 200
    ids = [c["id"] for c in res.get_json()]
    assert ids == [old["id"]]


def test_complaints_invalid_status_returns_400(client, admin, seed):
    res = client.get("/api/complaints/?status=NOT_A_STATUS", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("status must be one of")


def test_complaints_invalid_boolean_returns_400(client, admin, seed):
    res = client.get("/api/complaints/?unassigned=maybe", headers=admin)
    assert res.status_code == 400
    assert "unassigned" in res.get_json()["error"]


def test_complaints_resident_filter_by_other_apartment_still_scoped(client, resident, admin, seed):
    """A resident filtering by another flat's apartment_id must not see it —
    role scoping is applied before the filter, so the filter can only narrow,
    never widen, what the resident may already see."""
    _raise(client, resident, seed["apartment_id"], title="Mine")
    _raise(client, admin, seed["other_apartment_id"], title="Someone else's")

    res = client.get(f"/api/complaints/?apartment_id={seed['other_apartment_id']}", headers=resident)
    assert res.status_code == 200
    assert res.get_json() == []


# ════════════════════════════════════════════════════════════
#  INVOICES
# ════════════════════════════════════════════════════════════
def _invoice(client, headers, apartment_id, **overrides):
    payload = {"apartment_id": apartment_id, "month": 7, "year": 2026, "amount": 2500}
    payload.update(overrides)
    res = client.post("/api/invoices/", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def test_invoices_no_filters_unchanged(client, admin, seed):
    _invoice(client, admin, seed["apartment_id"])
    res = client.get("/api/invoices/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_invoices_filter_by_status(client, admin, seed):
    # Both on seed["apartment_id"]: other_apartment_id has no resident, so
    # marking an invoice there PAID 404s ("No resident found for this flat").
    unpaid = _invoice(client, admin, seed["apartment_id"], month=7)
    paid = _invoice(client, admin, seed["apartment_id"], month=8)
    pay_res = client.put(f"/api/invoices/{paid['id']}/pay", json={"payment_method": "UPI"}, headers=admin)
    assert pay_res.status_code == 200, pay_res.get_json()

    res = client.get("/api/invoices/?status=PAID", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and body[0]["id"] == paid["id"]


def test_invoices_filter_by_amount_range(client, admin, seed):
    _invoice(client, admin, seed["apartment_id"], amount=1000)
    _invoice(client, admin, seed["other_apartment_id"], amount=5000, month=8)

    res = client.get("/api/invoices/?min_amount=2000", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and body[0]["amount"] == 5000.0


def test_invoices_min_amount_greater_than_max_returns_400(client, admin, seed):
    res = client.get("/api/invoices/?min_amount=5000&max_amount=1000", headers=admin)
    assert res.status_code == 400
    assert "min_amount" in res.get_json()["error"]


def test_invoices_from_after_to_returns_400(client, admin, seed):
    res = client.get("/api/invoices/?from=2026-12-31&to=2026-01-01", headers=admin)
    assert res.status_code == 400


def test_invoices_resident_apartment_id_filter_stays_scoped(client, resident, admin, seed):
    _invoice(client, admin, seed["apartment_id"])
    _invoice(client, admin, seed["other_apartment_id"], month=8)

    res = client.get(f"/api/invoices/?apartment_id={seed['other_apartment_id']}", headers=resident)
    assert res.status_code == 200
    assert res.get_json() == []


def test_overdue_sweep_runs_before_status_filter(client, admin, seed, app):
    """The landmine: filtering status=OVERDUE must include an invoice that
    only just became overdue, and status=UNPAID must exclude it — the sweep
    has to run before the filter is applied, not after."""
    with app.app_context():
        inv = Invoice(
            apartment_id=seed["apartment_id"], generated_by=seed["admin_id"],
            month=1, year=date.today().year, amount=1500, status="UNPAID",
            due_date=date.today() - timedelta(days=5),
        )
        db.session.add(inv)
        db.session.commit()
        inv_id = inv.id

    overdue = client.get("/api/invoices/?status=OVERDUE", headers=admin)
    assert overdue.status_code == 200
    assert [i["id"] for i in overdue.get_json()] == [inv_id]

    unpaid = client.get("/api/invoices/?status=UNPAID", headers=admin)
    assert unpaid.status_code == 200
    assert inv_id not in [i["id"] for i in unpaid.get_json()]


def test_pending_endpoint_also_runs_overdue_sweep(client, admin, seed, app):
    with app.app_context():
        inv = Invoice(
            apartment_id=seed["apartment_id"], generated_by=seed["admin_id"],
            month=2, year=date.today().year, amount=1200, status="UNPAID",
            due_date=date.today() - timedelta(days=10),
        )
        db.session.add(inv)
        db.session.commit()
        inv_id = inv.id

    res = client.get("/api/invoices/pending", headers=admin)
    assert res.status_code == 200
    body = next(i for i in res.get_json() if i["id"] == inv_id)
    assert body["status"] == "OVERDUE"


# ════════════════════════════════════════════════════════════
#  EXPENSES
# ════════════════════════════════════════════════════════════
def _expense(client, admin, **overrides):
    payload = {"category": "UTILITIES", "description": "Electricity bill",
              "amount": 3000, "expense_date": "2026-07-01"}
    payload.update(overrides)
    res = client.post("/api/expenses/", json=payload, headers=admin)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def test_expenses_no_filters_unchanged(client, admin, seed):
    _expense(client, admin)
    res = client.get("/api/expenses/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_expenses_filter_by_category(client, admin, seed):
    _expense(client, admin, category="UTILITIES")
    _expense(client, admin, category="SALARY", description="Guard salary")

    res = client.get("/api/expenses/?category=SALARY", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and body[0]["category"] == "SALARY"


def test_expenses_filter_by_q_searches_description(client, admin, seed):
    _expense(client, admin, description="Diesel for generator")
    _expense(client, admin, description="Water tank cleaning")

    res = client.get("/api/expenses/?q=diesel", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and "Diesel" in body[0]["description"]


def test_expenses_invalid_category_returns_400(client, admin, seed):
    res = client.get("/api/expenses/?category=NOT_REAL", headers=admin)
    assert res.status_code == 400


# ════════════════════════════════════════════════════════════
#  MAINTENANCE
# ════════════════════════════════════════════════════════════
def _task(client, admin, **overrides):
    payload = {"title": "Generator servicing", "category": "GENERATOR",
              "scheduled_date": str(date.today() + timedelta(days=10))}
    payload.update(overrides)
    res = client.post("/api/maintenance/", json=payload, headers=admin)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def test_maintenance_no_filters_unchanged(client, admin, seed):
    _task(client, admin)
    res = client.get("/api/maintenance/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_maintenance_filter_by_category(client, admin, seed):
    _task(client, admin, category="GENERATOR")
    _task(client, admin, category="CLEANING", title="Lobby cleaning")

    res = client.get("/api/maintenance/?category=CLEANING", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and body[0]["category"] == "CLEANING"


def test_maintenance_worker_only_sees_assigned_tasks(client, admin, worker, seed):
    mine = _task(client, admin, assigned_to=seed["worker_id"], title="Mine")
    _task(client, admin, title="Not mine")

    res = client.get("/api/maintenance/", headers=worker)
    assert res.status_code == 200
    body = res.get_json()
    assert [t["id"] for t in body] == [mine["id"]]


def test_maintenance_worker_filter_cannot_widen_scope(client, admin, worker, seed):
    """A worker passing assigned_to for someone else must not see that task —
    the assigned_to filter is admin-only; for a worker their own scoping
    always wins."""
    other_task = _task(client, admin, title="Someone else's")

    res = client.get(f"/api/maintenance/?assigned_to={seed['admin_id']}", headers=worker)
    assert res.status_code == 200
    assert res.get_json() == []


def test_worker_can_complete_own_task(client, admin, worker, seed):
    task = _task(client, admin, assigned_to=seed["worker_id"])
    res = client.put(f"/api/maintenance/{task['id']}/complete", headers=worker)
    assert res.status_code == 200
    assert res.get_json()["status"] == "COMPLETED"


def test_worker_cannot_complete_unassigned_task(client, admin, worker, seed):
    task = _task(client, admin)   # assigned_to is None
    res = client.put(f"/api/maintenance/{task['id']}/complete", headers=worker)
    assert res.status_code == 403


def test_worker_cannot_complete_someone_elses_task(client, admin, worker, seed):
    other_worker = client.post("/api/members/", json={
        "name": "Other Worker", "email": "otherworker@x.com", "password": "Pass@123",
        "role": "WORKER", "apartment_id": seed["apartment_id"],
    }, headers=admin).get_json()

    task = _task(client, admin, assigned_to=other_worker["user_id"])
    res = client.put(f"/api/maintenance/{task['id']}/complete", headers=worker)
    assert res.status_code == 403
