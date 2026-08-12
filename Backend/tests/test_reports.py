"""Summary and CSV export endpoints added for Feature 2 (reports):
GET /api/{complaints,invoices,maintenance}/summary and
GET /api/{members,complaints,invoices,expenses}/export.
"""
from datetime import date, timedelta


def _raise(client, headers, apartment_id, **overrides):
    payload = {"title": "Leaking tap", "description": "Drips.",
              "category": "PLUMBING", "apartment_id": apartment_id}
    payload.update(overrides)
    res = client.post("/api/complaints/", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def _invoice(client, admin, apartment_id, **overrides):
    payload = {"apartment_id": apartment_id, "month": 7, "year": 2026, "amount": 2500}
    payload.update(overrides)
    res = client.post("/api/invoices/", json=payload, headers=admin)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def _task(client, admin, **overrides):
    payload = {"title": "Generator servicing", "category": "GENERATOR",
              "scheduled_date": str(date.today() + timedelta(days=10))}
    payload.update(overrides)
    res = client.post("/api/maintenance/", json=payload, headers=admin)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


# ════════════════════════════════════════════════════════════
#  COMPLAINTS SUMMARY
# ════════════════════════════════════════════════════════════
def test_complaints_summary_counts(client, admin, seed):
    _raise(client, admin, seed["apartment_id"], category="PLUMBING")
    c2 = _raise(client, admin, seed["apartment_id"], category="ELECTRICAL", title="Fan")
    client.put(f"/api/complaints/{c2['id']}/status", json={"status": "CLOSED"}, headers=admin)

    res = client.get("/api/complaints/summary", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["total"] == 2
    assert body["by_status"]["CLOSED"] == 1
    assert body["by_status"]["OPEN"] == 1
    assert body["pending"] == 1
    assert body["resolved"] == 1
    assert body["by_category"]["PLUMBING"] == 1
    assert body["unassigned_count"] == 2


def test_complaints_summary_scoped_to_resident(client, admin, resident, seed):
    _raise(client, resident, seed["apartment_id"], title="Mine")
    _raise(client, admin, seed["other_apartment_id"], title="Not mine")

    res = client.get("/api/complaints/summary", headers=resident)
    assert res.status_code == 200
    assert res.get_json()["total"] == 1


# ════════════════════════════════════════════════════════════
#  INVOICES SUMMARY
# ════════════════════════════════════════════════════════════
def test_invoices_summary_totals(client, admin, seed):
    # Both on seed["apartment_id"]: other_apartment_id has no resident, so
    # marking an invoice there PAID 404s ("No resident found for this flat").
    unpaid = _invoice(client, admin, seed["apartment_id"], amount=1000, month=7)
    paid = _invoice(client, admin, seed["apartment_id"], amount=2000, month=8)
    pay_res = client.put(f"/api/invoices/{paid['id']}/pay", json={"payment_method": "UPI"}, headers=admin)
    assert pay_res.status_code == 200, pay_res.get_json()

    res = client.get("/api/invoices/summary", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["total_invoiced"] == 3000
    assert body["total_collected"] == 2000
    assert body["total_pending"] == 1000
    assert body["count_paid"] == 1
    assert body["count_unpaid"] == 1
    assert body["collection_rate"] == round(2000 / 3000 * 100, 2)


def test_invoices_summary_counts_overdue_after_sweep(client, admin, seed, app):
    from models import db, Invoice
    with app.app_context():
        inv = Invoice(
            apartment_id=seed["apartment_id"], generated_by=seed["admin_id"],
            month=3, year=date.today().year, amount=800, status="UNPAID",
            due_date=date.today() - timedelta(days=15),
        )
        db.session.add(inv)
        db.session.commit()

    res = client.get("/api/invoices/summary", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["count_overdue"] == 1
    assert body["overdue_amount"] == 800


def test_invoices_summary_scoped_to_resident(client, admin, resident, seed):
    _invoice(client, admin, seed["apartment_id"])
    _invoice(client, admin, seed["other_apartment_id"], month=8)

    res = client.get("/api/invoices/summary", headers=resident)
    assert res.status_code == 200
    assert res.get_json()["total_invoiced"] == 2500


# ════════════════════════════════════════════════════════════
#  MAINTENANCE SUMMARY
# ════════════════════════════════════════════════════════════
def test_maintenance_summary_counts(client, admin, seed):
    _task(client, admin, category="GENERATOR")
    overdue = _task(client, admin, category="CLEANING",
                    scheduled_date=str(date.today() - timedelta(days=5)))

    res = client.get("/api/maintenance/summary", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["total"] == 2
    assert body["by_status"]["PENDING"] == 2
    assert body["overdue_count"] == 1


def test_maintenance_summary_scoped_to_worker(client, admin, worker, seed):
    _task(client, admin, assigned_to=seed["worker_id"], title="Mine")
    _task(client, admin, title="Not mine")

    res = client.get("/api/maintenance/summary", headers=worker)
    assert res.status_code == 200
    assert res.get_json()["total"] == 1


# ════════════════════════════════════════════════════════════
#  CSV EXPORTS
# ════════════════════════════════════════════════════════════
def test_members_export_returns_csv(client, admin, seed):
    res = client.get("/api/members/export", headers=admin)
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    text = res.get_data(as_text=True)
    assert "Name" in text.splitlines()[0]
    assert "Ravi Resident" in text


def test_complaints_export_returns_csv(client, admin, seed):
    _raise(client, admin, seed["apartment_id"], title="Broken tap")
    res = client.get("/api/complaints/export", headers=admin)
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    text = res.get_data(as_text=True)
    assert "Broken tap" in text


def test_invoices_export_returns_csv(client, admin, seed):
    _invoice(client, admin, seed["apartment_id"])
    res = client.get("/api/invoices/export", headers=admin)
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "A-101" in res.get_data(as_text=True)


def test_expenses_export_returns_csv(client, admin, seed):
    client.post("/api/expenses/", json={
        "category": "UTILITIES", "description": "Electricity bill",
        "amount": 3000, "expense_date": "2026-07-01",
    }, headers=admin)
    res = client.get("/api/expenses/export", headers=admin)
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "Electricity bill" in res.get_data(as_text=True)


def test_export_respects_filters(client, admin, seed):
    _invoice(client, admin, seed["apartment_id"], amount=1000)
    _invoice(client, admin, seed["other_apartment_id"], amount=5000, month=8)

    res = client.get("/api/invoices/export?min_amount=2000", headers=admin)
    text = res.get_data(as_text=True)
    assert "5000" in text or "5000.0" in text
    lines = [l for l in text.splitlines()[1:] if l.strip()]
    assert len(lines) == 1


def test_resident_cannot_export_members(client, resident, seed):
    res = client.get("/api/members/export", headers=resident)
    assert res.status_code == 403
