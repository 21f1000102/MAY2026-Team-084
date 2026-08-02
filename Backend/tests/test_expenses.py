"""API tests for /api/expenses — the finance-only ledger, its input validation
and the monthly summary's all-or-nothing month/year filter."""
import pytest


# ── helpers ───────────────────────────────────────────────────
def create_expense(client, headers, **overrides):
    """POST a valid expense and return the parsed JSON body."""
    payload = {
        "category": "MAINTENANCE",
        "description": "Lift annual servicing",
        "amount": 4500,
        "expense_date": "2026-08-05",
    }
    payload.update(overrides)
    res = client.post("/api/expenses/", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def committee_headers(tokens):
    return {"Authorization": f"Bearer {tokens['committee']}"}


# ── happy path ────────────────────────────────────────────────
def test_admin_logs_expense(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "utilities",
        "description": "Common area electricity bill",
        "amount": 12750.25,
        "expense_date": "2026-08-05",
        "receipt_url": "https://example.com/bill.pdf",
    }, headers=admin)

    assert res.status_code == 201
    body = res.get_json()
    assert body["category"] == "UTILITIES"          # normalised to upper case
    assert body["description"] == "Common area electricity bill"
    assert body["amount"] == 12750.25
    assert body["expense_date"] == "2026-08-05"
    assert body["receipt_url"] == "https://example.com/bill.pdf"
    assert body["paid_by"] == seed["admin_id"]
    assert body["paid_by_name"] == "Priya Admin"


def test_treasurer_can_log_expense(client, treasurer, seed):
    body = create_expense(client, treasurer)
    assert body["paid_by"] == seed["treasurer_id"]


def test_paid_by_defaults_to_the_logged_in_user(client, treasurer, seed):
    body = create_expense(client, treasurer, paid_by=None)
    assert body["paid_by"] == seed["treasurer_id"]


def test_admin_may_attribute_expense_to_another_user(client, admin, seed):
    body = create_expense(client, admin, paid_by=seed["worker_id"])
    assert body["paid_by"] == seed["worker_id"]
    assert body["paid_by_name"] == "Ramesh Worker"


def test_paid_by_unknown_user_returns_404(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "SALARY", "description": "Guard salary",
        "amount": 15000, "expense_date": "2026-08-01", "paid_by": 99999,
    }, headers=admin)

    assert res.status_code == 404
    assert res.get_json()["error"] == "paid_by user not found"


def test_list_expenses(client, admin, seed):
    create_expense(client, admin, description="First", expense_date="2026-08-01")
    create_expense(client, admin, description="Second", expense_date="2026-08-20")

    res = client.get("/api/expenses/", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 2
    assert body[0]["description"] == "Second"       # newest expense_date first


def test_update_expense(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.put(f"/api/expenses/{expense['id']}", json={
        "description": "Lift servicing (revised)",
        "amount": 5200,
        "category": "CONSUMABLES",
        "receipt_url": "https://example.com/new.pdf",
    }, headers=admin)

    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == expense["id"]
    assert body["description"] == "Lift servicing (revised)"
    assert body["amount"] == 5200.0
    assert body["category"] == "CONSUMABLES"
    assert body["receipt_url"] == "https://example.com/new.pdf"


def test_delete_expense(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.delete(f"/api/expenses/{expense['id']}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Expense deleted"
    assert client.get("/api/expenses/", headers=admin).get_json() == []


def test_unknown_expense_returns_404(client, admin, seed):
    assert client.put("/api/expenses/99999", json={"amount": 1},
                      headers=admin).status_code == 404
    assert client.delete("/api/expenses/99999", headers=admin).status_code == 404


# ── summary ───────────────────────────────────────────────────
def test_summary_for_a_month(client, admin, seed):
    create_expense(client, admin, category="SALARY", amount=15000,
                   expense_date="2026-08-01")
    create_expense(client, admin, category="UTILITIES", amount=2500,
                   expense_date="2026-08-20")
    create_expense(client, admin, category="SALARY", amount=999,
                   expense_date="2026-09-01")   # different month, excluded

    invoice = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 8,
        "year": 2026, "amount": 3000,
    }, headers=admin).get_json()
    client.put(f"/api/invoices/{invoice['id']}/pay", json={}, headers=admin)

    res = client.get("/api/expenses/summary?month=8&year=2026", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["total_expense"] == 17500.0
    assert body["total_income"] == 3000.0
    assert body["net_balance"] == -14500.0
    assert body["by_category"] == {"SALARY": 15000.0, "UTILITIES": 2500.0}


def test_summary_without_filters_is_all_time(client, admin, seed):
    create_expense(client, admin, amount=100, expense_date="2026-08-01")
    create_expense(client, admin, amount=250, expense_date="2025-01-01")

    res = client.get("/api/expenses/summary", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["total_expense"] == 350.0


@pytest.mark.parametrize("query", ["?month=8", "?year=2026",
                                   "?month=8&year=", "?month=&year=2026"])
def test_summary_with_partial_filter_returns_400(client, admin, seed, query):
    """Regression: half a filter silently fell through to all-time totals."""
    res = client.get(f"/api/expenses/summary{query}", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Provide both month and year"


def test_summary_month_out_of_range_returns_400(client, admin, seed):
    res = client.get("/api/expenses/summary?month=99&year=2026", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at most 12"


def test_summary_non_numeric_month_returns_400(client, admin, seed):
    res = client.get("/api/expenses/summary?month=August&year=2026",
                     headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be a whole number"


# ── validation ────────────────────────────────────────────────
@pytest.mark.parametrize("missing", ["category", "description",
                                     "amount", "expense_date"])
def test_add_expense_missing_required_field_returns_400(client, admin,
                                                        seed, missing):
    payload = {"category": "MAINTENANCE", "description": "Painting",
               "amount": 1000, "expense_date": "2026-08-05"}
    payload.pop(missing)

    res = client.post("/api/expenses/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"


def test_add_expense_bad_category_returns_400(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "PIZZA", "description": "Team lunch",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"].startswith("expense_category must be one of:")


@pytest.mark.parametrize("bad_date", ["yesterday", "05-08-2026", "2026-13-01"])
def test_add_expense_bad_date_returns_400(client, admin, seed, bad_date):
    """Regression: raw strings used to reach the Date column and 500."""
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": bad_date,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "expense_date must be a valid date (YYYY-MM-DD)"


def test_add_expense_blank_date_returns_400(client, admin, seed):
    """expense_date is required, so a blank one is rejected by require()."""
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "expense_date is required"


def test_add_expense_non_numeric_amount_returns_400(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": "one thousand", "expense_date": "2026-08-05",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be a number"


def test_add_expense_negative_amount_returns_400(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": -1, "expense_date": "2026-08-05",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be at least 0"


def test_update_expense_bad_category_returns_400(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.put(f"/api/expenses/{expense['id']}",
                     json={"category": "PIZZA"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("expense_category must be one of:")


def test_update_expense_non_numeric_amount_returns_400(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.put(f"/api/expenses/{expense['id']}",
                     json={"amount": "one thousand"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be a number"


@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
def test_add_expense_malformed_body_returns_400(client, admin, seed,
                                                raw, expected_error):
    res = client.post("/api/expenses/", data=raw,
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error


# ── authorization ─────────────────────────────────────────────
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("put", "/api/expenses/1"),
    ("delete", "/api/expenses/1"),
    ("get", "/api/expenses/summary"),
])
def test_expense_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401


def test_resident_cannot_list_expenses(client, resident, seed):
    res = client.get("/api/expenses/", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_resident_cannot_add_expense(client, resident, seed):
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=resident)

    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_resident_cannot_delete_expense(client, admin, resident, seed):
    expense = create_expense(client, admin)

    res = client.delete(f"/api/expenses/{expense['id']}", headers=resident)
    assert res.status_code == 403
    assert len(client.get("/api/expenses/", headers=admin).get_json()) == 1


def test_worker_cannot_read_the_ledger(client, worker, seed):
    assert client.get("/api/expenses/", headers=worker).status_code == 403
    assert client.get("/api/expenses/summary", headers=worker).status_code == 403


@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("get", "/api/expenses/summary"),
])
def test_committee_member_is_not_finance(client, tokens, seed, method, path):
    """COMMITTEE_MEMBER is an admin role but must not reach the ledger."""
    res = getattr(client, method)(path, json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=committee_headers(tokens))

    assert res.status_code == 403
