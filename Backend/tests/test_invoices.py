"""API tests for /api/invoices — generation, bulk generation, payment
idempotency, receipts and per-flat scoping."""
import pytest


# ── helpers ───────────────────────────────────────────────────
def create_invoice(client, headers, apartment_id, month=7, year=2026,
                   amount=2500, **overrides):
    """POST a valid invoice and return the parsed JSON body."""
    payload = {"apartment_id": apartment_id, "month": month,
               "year": year, "amount": amount}
    payload.update(overrides)
    res = client.post("/api/invoices/", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def pay(client, headers, invoice_id, **payload):
    return client.put(f"/api/invoices/{invoice_id}/pay",
                      json=payload or {"payment_method": "UPI"},
                      headers=headers)


def committee_headers(tokens):
    return {"Authorization": f"Bearer {tokens['committee']}"}


# ── happy path ────────────────────────────────────────────────
def test_admin_creates_invoice(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500.50, "due_date": "2026-07-15",
    }, headers=admin)

    assert res.status_code == 201
    body = res.get_json()
    assert body["apartment_id"] == seed["apartment_id"]
    assert body["flat_number"] == "A-101"
    assert body["month"] == 7 and body["year"] == 2026
    assert body["amount"] == 2500.50
    assert body["due_date"] == "2026-07-15"
    assert body["status"] == "UNPAID"


def test_treasurer_can_create_invoice(client, treasurer, seed):
    body = create_invoice(client, treasurer, seed["apartment_id"])
    assert body["status"] == "UNPAID"


def test_admin_lists_all_invoices(client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"])
    create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get("/api/invoices/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_pay_invoice_returns_receipt(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = pay(client, admin, invoice["id"],
              payment_method="UPI", transaction_reference="TXN-9001")
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Invoice marked as paid"
    assert body["invoice"]["status"] == "PAID"
    assert body["receipt"]["receipt_number"].startswith("RCP-")
    assert body["receipt"]["payment_method"] == "UPI"
    assert body["receipt"]["transaction_reference"] == "TXN-9001"
    assert body["receipt"]["amount"] == 2500.0


def test_payment_method_defaults_to_cash(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = client.put(f"/api/invoices/{invoice['id']}/pay", json={}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["receipt"]["payment_method"] == "CASH"


def test_get_receipt_for_paid_invoice(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])
    pay(client, admin, invoice["id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["flat_number"] == "A-101"
    assert body["month"] == 7 and body["year"] == 2026
    assert body["amount"] == 2500.0


def test_resident_can_read_own_receipt(client, admin, resident, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])
    pay(client, admin, invoice["id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=resident)
    assert res.status_code == 200
    assert res.get_json()["flat_number"] == "A-101"


def test_pending_lists_only_unpaid(client, admin, seed):
    paid = create_invoice(client, admin, seed["apartment_id"], month=6)
    unpaid = create_invoice(client, admin, seed["apartment_id"], month=7)
    pay(client, admin, paid["id"])

    res = client.get("/api/invoices/pending", headers=admin)
    assert res.status_code == 200
    assert [i["id"] for i in res.get_json()] == [unpaid["id"]]


# ── bulk generation ───────────────────────────────────────────
def test_bulk_generate_creates_invoice_for_every_flat(client, admin, seed):
    res = client.post("/api/invoices/bulk", json={
        "month": 8, "year": 2026, "amount": 3000, "due_date": "2026-08-10",
    }, headers=admin)

    assert res.status_code == 201
    body = res.get_json()
    assert body["message"] == "Invoices generated for 2 flats"
    assert sorted(body["flats"]) == ["A-101", "B-202"]


def test_bulk_generate_skips_flats_that_already_have_that_month(
        client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"], month=8, year=2026)

    res = client.post("/api/invoices/bulk",
                      json={"month": 8, "year": 2026, "amount": 3000},
                      headers=admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["flats"] == ["B-202"]
    assert body["message"] == "Invoices generated for 1 flats"

    all_invoices = client.get("/api/invoices/", headers=admin).get_json()
    assert len(all_invoices) == 2


# ── validation ────────────────────────────────────────────────
@pytest.mark.parametrize("missing", ["apartment_id", "month", "year", "amount"])
def test_create_invoice_missing_required_field_returns_400(
        client, admin, seed, missing):
    payload = {"apartment_id": seed["apartment_id"], "month": 7,
               "year": 2026, "amount": 2500}
    payload.pop(missing)

    res = client.post("/api/invoices/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"


@pytest.mark.parametrize("month", [0, 13, 99, -1])
def test_create_invoice_month_out_of_range_returns_400(client, admin, seed, month):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": month,
        "year": 2026, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] in ("month must be at least 1",
                                       "month must be at most 12")


def test_bulk_generate_month_out_of_range_returns_400(client, admin, seed):
    res = client.post("/api/invoices/bulk",
                      json={"month": 99, "year": 2026, "amount": 3000},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at most 12"


def test_create_invoice_year_out_of_range_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 1899, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "year must be at least 2000"


def test_create_invoice_non_numeric_amount_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": "one thousand",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be a number"


def test_create_invoice_negative_amount_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": -5,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be at least 0"


def test_create_invoice_bad_due_date_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500, "due_date": "yesterday",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "due_date must be a valid date (YYYY-MM-DD)"


@pytest.mark.parametrize("due_date", ["", "   ", None])
def test_blank_due_date_is_stored_as_null_not_rejected(client, admin,
                                                       seed, due_date):
    """Regression: an empty due_date from the form used to 400 (or crash)."""
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500, "due_date": due_date,
    }, headers=admin)

    assert res.status_code == 201, res.get_json()
    assert res.get_json()["due_date"] is None


def test_create_invoice_unknown_apartment_returns_404(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": 99999, "month": 7, "year": 2026, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"


@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_invoice_malformed_body_returns_400(client, admin, seed, path,
                                            raw, expected_error):
    res = client.post(path, data=raw, content_type="application/json",
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error


# ── authorization ─────────────────────────────────────────────
@pytest.mark.parametrize("method, path", [
    ("get", "/api/invoices/"),
    ("post", "/api/invoices/"),
    ("post", "/api/invoices/bulk"),
    ("put", "/api/invoices/1/pay"),
    ("get", "/api/invoices/1/receipt"),
    ("get", "/api/invoices/pending"),
])
def test_invoice_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401


def test_resident_cannot_create_invoice(client, resident, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": 2500,
    }, headers=resident)

    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_resident_cannot_mark_invoice_paid(client, admin, resident, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = pay(client, resident, invoice["id"])
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
    assert client.get("/api/invoices/",
                      headers=admin).get_json()[0]["status"] == "UNPAID"


def test_resident_cannot_bulk_generate(client, resident, seed):
    res = client.post("/api/invoices/bulk",
                      json={"month": 8, "year": 2026, "amount": 3000},
                      headers=resident)
    assert res.status_code == 403


@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_committee_member_is_not_finance(client, tokens, seed, path):
    """COMMITTEE_MEMBER manages the society but must not touch money."""
    res = client.post(path, json={"apartment_id": seed["apartment_id"],
                                  "month": 7, "year": 2026, "amount": 2500},
                      headers=committee_headers(tokens))
    assert res.status_code == 403


def test_resident_cannot_read_another_flats_receipt(client, admin,
                                                    resident, seed):
    invoice = create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to view this receipt"


# ── business rules ────────────────────────────────────────────
def test_duplicate_invoice_for_same_flat_month_year_returns_409(
        client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"], month=7, year=2026)

    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": 9999,
    }, headers=admin)

    assert res.status_code == 409
    assert res.get_json()["error"] == "An invoice already exists for this flat and month"
    assert len(client.get("/api/invoices/", headers=admin).get_json()) == 1


def test_same_month_different_flat_is_allowed(client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"], month=7, year=2026)
    create_invoice(client, admin, seed["other_apartment_id"], month=7, year=2026)

    assert len(client.get("/api/invoices/", headers=admin).get_json()) == 2


def test_pay_invoice_twice_returns_409(client, admin, seed):
    """Regression: the second payment used to insert a duplicate Payment row."""
    invoice = create_invoice(client, admin, seed["apartment_id"])
    first = pay(client, admin, invoice["id"], payment_method="UPI",
                transaction_reference="TXN-1")
    assert first.status_code == 200
    first_receipt = first.get_json()["receipt"]["receipt_number"]

    second = pay(client, admin, invoice["id"], payment_method="CARD",
                 transaction_reference="TXN-2")
    assert second.status_code == 409
    assert second.get_json()["error"] == "This invoice is already paid"

    receipt = client.get(f"/api/invoices/{invoice['id']}/receipt",
                         headers=admin).get_json()
    assert receipt["receipt_number"] == first_receipt
    assert receipt["transaction_reference"] == "TXN-1"


def test_receipt_for_unpaid_invoice_returns_400(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Invoice not paid yet"


def test_pay_invoice_for_flat_without_resident_returns_404(client, admin, seed):
    invoice = create_invoice(client, admin, seed["other_apartment_id"])

    res = pay(client, admin, invoice["id"])
    assert res.status_code == 404
    assert res.get_json()["error"] == "No resident found for this apartment"


def test_unknown_invoice_returns_404(client, admin, seed):
    assert pay(client, admin, 99999).status_code == 404
    assert client.get("/api/invoices/99999/receipt",
                      headers=admin).status_code == 404


# ── scoping ───────────────────────────────────────────────────
def test_resident_sees_only_own_flat_invoices(client, admin, resident, seed):
    mine = create_invoice(client, admin, seed["apartment_id"])
    create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get("/api/invoices/", headers=resident)
    assert res.status_code == 200
    assert [i["id"] for i in res.get_json()] == [mine["id"]]


def test_resident_pending_is_scoped_to_own_flat(client, admin, resident, seed):
    """Regression: /pending used to leak every flat's outstanding dues."""
    mine = create_invoice(client, admin, seed["apartment_id"])
    create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get("/api/invoices/pending", headers=resident)
    assert res.status_code == 200
    body = res.get_json()
    assert [i["id"] for i in body] == [mine["id"]]
    assert all(i["flat_number"] == "A-101" for i in body)


@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/pending"])
def test_user_without_a_flat_sees_an_empty_list(client, admin, worker,
                                                seed, path):
    create_invoice(client, admin, seed["apartment_id"])

    res = client.get(path, headers=worker)
    assert res.status_code == 200
    assert res.get_json() == []
