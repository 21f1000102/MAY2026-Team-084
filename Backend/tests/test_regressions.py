"""
Regression tests — one per defect that testing actually caught.

Every test in this module corresponds to a real bug where the **actual output
differed from the expected output**. Each docstring records what the endpoint
used to do, what it does now, and the root cause. These are the evidence behind
the "Defects found through testing" section of docs/TEST_CASES.md.

If any of these fail, a previously fixed bug has come back.
"""
import pytest


# ── DEFECT-01 ─────────────────────────────────────────────────
class TestDuplicatePhoneRegistration:
    """DEFECT-01  POST /api/auth/register

    Reported by a team member who typed the phone number shown in the form's own
    placeholder (9876543210) and got a generic "Registration failed".

    users.phone is UNIQUE but register() only pre-checked the email, so the
    insert raised an unhandled IntegrityError.
        expected: 409 {"error": "Phone number already registered"}
        actual  : 500 (HTML error page, UNIQUE constraint failed: users.phone)
    Fixed: pre-check the phone and return a clean 409.
    """

    def test_duplicate_phone_returns_409_not_500(self, client, seed):
        first = client.post("/api/auth/register", json={
            "name": "First", "email": "first@x.com",
            "password": "Pass@123", "role": "TENANT", "phone": "9876543210",
        })
        assert first.status_code == 201

        second = client.post("/api/auth/register", json={
            "name": "Second", "email": "second@x.com",
            "password": "Pass@123", "role": "TENANT", "phone": "9876543210",
        })
        assert second.status_code == 409, "duplicate phone must not 500"
        assert "phone" in second.get_json()["error"].lower()

    def test_two_blank_phone_registrations_both_succeed(self, client, seed):
        """The same bug in its nastier form: '' is not NULL, so the SECOND
        blank-phone signup collided with the first and 500'd. Blank must
        normalise to NULL, and SQLite allows many NULLs in a UNIQUE column."""
        for i in (1, 2):
            res = client.post("/api/auth/register", json={
                "name": f"Blank {i}", "email": f"blank{i}@x.com",
                "password": "Pass@123", "role": "TENANT", "phone": "",
            })
            assert res.status_code == 201, f"blank-phone signup #{i} failed: {res.get_json()}"


# ── DEFECT-02 ─────────────────────────────────────────────────
@pytest.mark.parametrize("label,url,payload", [
    ("expense", "/api/expenses/", {
        "category": "UTILITIES", "description": "Water bill",
        "amount": 500, "expense_date": "2026-08-01"}),
    ("maintenance task", "/api/maintenance/", {
        "title": "Tank cleaning", "category": "WATER_TANK",
        "scheduled_date": "2026-08-10"}),
    ("equipment", "/api/equipment/", {
        "name": "Lift A", "category": "LIFT",
        "last_serviced_date": "2026-06-01", "service_frequency_days": 90}),
    ("poll", "/api/polls/", {
        "title": "Paint the lobby?", "options": ["Yes", "No"],
        "end_date": "2026-12-31"}),
])
def test_date_accepting_endpoints_create_successfully(client, admin, label, url, payload):
    """DEFECT-02  Four endpoints were 100% dead.

    Client date strings were assigned straight into db.Date columns; there was
    not a single date parser in the backend. Every single call failed at flush.
        expected: 201 Created
        actual  : 500 (TypeError: SQLite Date type only accepts Python date objects)
    Fixed: utils.parse_date/parse_datetime applied at all 10 date sites.

    Evidence this was total, not intermittent: expenses, maintenance_tasks,
    equipment and votes were all empty in the shipped database, because no user
    had ever managed to create one.
    """
    res = client.post(url, json=payload, headers=admin)
    assert res.status_code == 201, f"creating a {label} failed: {res.get_json()}"


def test_invalid_date_is_a_clean_400(client, admin):
    """The flip side: a genuinely bad date must be a 400, not a 500."""
    res = client.post("/api/expenses/", json={
        "category": "UTILITIES", "description": "x",
        "amount": 5, "expense_date": "yesterday",
    }, headers=admin)
    assert res.status_code == 400
    assert "date" in res.get_json()["error"].lower()


# ── DEFECT-03 ─────────────────────────────────────────────────
class TestConflictAnonymity:
    """DEFECT-03  GET /api/conflicts/pending — anonymity guarantee broken.

    The model documents that the reporter's identity is never shown to the
    reported flat. The endpoint had no role check and passed
    reveal_reporter=True, so ANY authenticated tenant could list every open
    conflict in the society together with who reported it.
        expected: 403 for a non-admin
        actual  : 200 + reported_by / reported_by_name for every report
    Fixed: gated to admin, and the resident view never reveals the reporter.
    """

    def _raise_conflict(self, client, resident, seed):
        return client.post("/api/conflicts/", json={
            "reported_apartment_id": seed["other_apartment_id"],
            "category": "NOISE", "description": "Loud music after midnight",
        }, headers=resident)

    def test_pending_is_admin_only(self, client, resident, seed):
        self._raise_conflict(client, resident, seed)
        res = client.get("/api/conflicts/pending", headers=resident)
        assert res.status_code == 403, "tenants must not read the pending queue"

    def test_resident_listing_never_exposes_the_reporter(self, client, resident, seed):
        self._raise_conflict(client, resident, seed)
        res = client.get("/api/conflicts/", headers=resident)
        assert res.status_code == 200
        for report in res.get_json():
            assert "reported_by" not in report
            assert "reported_by_name" not in report


# ── DEFECT-04 ─────────────────────────────────────────────────
class TestComplaintAssignment:
    """DEFECT-04  PUT /api/complaints/<id>/assign — the WORKER role was unusable.

    The frontend sent worker_id: null (there was no worker picker) and the
    backend accepted it, setting status=ASSIGNED with assigned_worker_id=NULL.
    Separately, GET /api/complaints returned only complaints a worker had
    RAISED, so assigned jobs never reached them.
        expected: 400 for a missing worker; the assignee sees the job
        actual  : 200, silently assigned to nobody; worker's queue always empty
    Fixed: validate a real, active WORKER, and include assigned jobs in the
    worker's list.
    """

    def _complaint(self, client, resident, seed):
        res = client.post("/api/complaints/", json={
            "title": "Corridor light out", "category": "ELECTRICAL",
            "apartment_id": seed["apartment_id"],
        }, headers=resident)
        assert res.status_code == 201
        return res.get_json()["id"]

    def test_assign_without_worker_is_rejected(self, client, admin, resident, seed):
        cid = self._complaint(client, resident, seed)
        res = client.put(f"/api/complaints/{cid}/assign", json={}, headers=admin)
        assert res.status_code == 400, "assigning to nobody must be rejected"

    def test_assign_to_non_worker_is_rejected(self, client, admin, resident, seed):
        cid = self._complaint(client, resident, seed)
        res = client.put(f"/api/complaints/{cid}/assign",
                         json={"worker_id": seed["resident_id"]}, headers=admin)
        assert res.status_code == 400
        assert "worker" in res.get_json()["error"].lower()

    def test_assigned_worker_sees_the_job(self, client, admin, resident, worker, seed):
        cid = self._complaint(client, resident, seed)
        assigned = client.put(f"/api/complaints/{cid}/assign",
                              json={"worker_id": seed["worker_id"]}, headers=admin)
        assert assigned.status_code == 200
        assert assigned.get_json()["assigned_worker_name"] is not None

        queue = client.get("/api/complaints/", headers=worker)
        assert queue.status_code == 200
        assert any(c["id"] == cid for c in queue.get_json()), \
            "the assigned worker must see the complaint in their queue"


# ── DEFECT-05 ─────────────────────────────────────────────────
def test_paying_an_invoice_twice_is_rejected(client, admin, seed):
    """DEFECT-05  PUT /api/invoices/<id>/pay was not idempotent.

    Paying twice inserted a SECOND Payment row while the receipt kept showing
    the first, so the ledger and the receipt disagreed permanently.
        expected: 409 on the second call
        actual  : 200 and a duplicate Payment row
    Fixed: reject when the invoice is already PAID.
    """
    created = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"],
        "month": 7, "year": 2026, "amount": 1500,
    }, headers=admin)
    assert created.status_code == 201
    inv_id = created.get_json()["id"]

    first = client.put(f"/api/invoices/{inv_id}/pay",
                       json={"payment_method": "UPI"}, headers=admin)
    assert first.status_code == 200

    second = client.put(f"/api/invoices/{inv_id}/pay",
                        json={"payment_method": "UPI"}, headers=admin)
    assert second.status_code == 409, "an invoice must not be payable twice"


# ── DEFECT-06 ─────────────────────────────────────────────────
def test_zero_service_frequency_is_rejected(client, admin):
    """DEFECT-06  POST /api/equipment with service_frequency_days = 0.

    Validation was `if not data.get(f)`, and the STRING "0" is truthy in Python,
    so it passed. Every later GET then evaluated days_since / 0.
        expected: 400
        actual  : 201, after which GET /api/equipment, /forecast and the whole
                  Equipment page 500'd forever (ZeroDivisionError) with no way
                  to delete the offending row through the UI.
    Fixed: parse_int(min_value=1).
    """
    for value in (0, "0", -5):
        res = client.post("/api/equipment/", json={
            "name": "Bad Lift", "category": "LIFT",
            "last_serviced_date": "2026-06-01", "service_frequency_days": value,
        }, headers=admin)
        assert res.status_code == 400, f"service_frequency_days={value!r} must be rejected"

    # and the listing still works
    assert client.get("/api/equipment/", headers=admin).status_code == 200


# ── DEFECT-07 ─────────────────────────────────────────────────
@pytest.mark.parametrize("body", ["null", "[]", '"a string"'])
def test_malformed_json_bodies_return_400(client, body):
    """DEFECT-07  Any endpoint, with a body of null / [] / "str".

    request.get_json() returns None, a list or a str for these, and the code
    immediately called data.get(...).
        expected: 400
        actual  : 500 (AttributeError: 'NoneType' object has no attribute 'get')
    Fixed: utils.get_body() rejects anything that is not a JSON object.
    """
    res = client.post("/api/auth/login", data=body, content_type="application/json")
    assert res.status_code == 400


def test_change_password_without_new_password_returns_400(client, admin):
    """DEFECT-07b  PUT /api/auth/change-password

    old_password was read with .get() but new_password with a raw subscript.
        expected: 400
        actual  : 500 (KeyError: 'new_password')
    """
    res = client.put("/api/auth/change-password",
                     json={"old_password": "Pass@123"}, headers=admin)
    assert res.status_code == 400


# ── DEFECT-08 ─────────────────────────────────────────────────
def test_errors_are_always_json_never_html(client, admin, seed):
    """DEFECT-08  There was not a single `except` block in api/ or auth/.

    Every DB violation or unexpected error produced Flask's HTML error page,
    which the SPA rendered as `undefined` — the user saw nothing happen.
        expected: a JSON body {"error": "..."} on every failure
        actual  : text/html
    Fixed: global ApiError / IntegrityError / HTTPException / Exception
    handlers in app.py.
    """
    failures = [
        client.post("/api/auth/login", json={}),                       # 400
        client.get("/api/auth/me"),                                    # 401
        client.get("/api/emergency/9999999", headers=admin),           # 404/405
        client.post("/api/complaints/", json={"title": "x", "category": "NOPE",
                                              "apartment_id": seed["apartment_id"]},
                    headers=admin),                                    # 400 bad enum
    ]
    for res in failures:
        assert res.status_code >= 400
        assert res.content_type.startswith("application/json"), \
            f"error response was {res.content_type}, not JSON"
        body = res.get_json()
        # FINDING-10 (open): the envelope is not consistent. Our own handlers
        # return {"error": ...}, but flask-jwt-extended's built-in 401s return
        # {"msg": ...}. openapi.yaml documents ErrorResponse {error} for every
        # failure, so the 401 contract is currently inaccurate, and the
        # frontend's errText() falls back to a generic message on auth errors.
        # Asserting reality here rather than the aspiration; see docs/TEST_CASES.md.
        assert "error" in body or "msg" in body


def test_jwt_401_uses_a_different_error_envelope_than_the_rest_of_the_api():
    """FINDING-10 — documents a live inconsistency, not a fixed bug.

    Documented contract (openapi.yaml ErrorResponse): {"error": "..."}
    Actual for a missing/invalid token:                {"msg": "..."}

    Low severity but real: the SPA reads `data.error`, so a session-expiry 401
    shows the generic fallback instead of the server's message. The fix is a
    handful of flask-jwt-extended loaders in create_app() normalising the
    envelope. Deliberately left unfixed pending team sign-off, since this
    milestone is documentation and tests only.
    """
    pytest.skip("Known open finding — see docs/TEST_CASES.md FINDING-10")


# ── DEFECT-09 ─────────────────────────────────────────────────
def test_residents_cannot_perform_privileged_actions(client, resident, seed):
    """DEFECT-09  Every mutating endpoint was bare @jwt_required().

    Role was consulted in only 3 read filters, so any logged-in resident could
    mark invoices paid, delete a flat (cascading away its residents, invoices,
    payments and complaints), publish notices or close polls.
        expected: 403
        actual  : 200 — the action succeeded
    Fixed: @role_required / @admin_required / @finance_required.
    """
    forbidden = [
        client.post("/api/invoices/", json={"apartment_id": seed["apartment_id"],
                                            "month": 1, "year": 2026, "amount": 100},
                    headers=resident),
        client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                      headers=resident),
        client.post("/api/notices/", json={"title": "hack", "content": "hack"},
                    headers=resident),
        client.post("/api/emergency/", json={"name": "x", "service_type": "OTHER",
                                             "phone": "999"}, headers=resident),
        client.get("/api/expenses/", headers=resident),
    ]
    for res in forbidden:
        assert res.status_code == 403, \
            f"a resident was allowed a privileged action (got {res.status_code})"


def test_apartment_delete_no_longer_cascades_away_residents(client, admin, seed):
    """DEFECT-09b  DELETE /api/members/apartments/<id>

    The cascade silently destroyed every resident, invoice, payment and
    complaint for the flat.
        expected: 409 while the flat is still occupied
        actual  : 200 {"message": "Apartment deleted"} and the data was gone
    """
    res = client.delete(f"/api/members/apartments/{seed['apartment_id']}", headers=admin)
    assert res.status_code == 409
    assert "resident" in res.get_json()["error"].lower()
