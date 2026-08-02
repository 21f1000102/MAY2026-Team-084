"""
Open defects — tests that are EXPECTED TO FAIL.

Every test in this module asserts the behaviour the API *should* have, and
currently fails because the code does something else. They are deliberately
left failing so the defect stays visible: a red test is a to-do item that
cannot be forgotten, whereas a comment can.

This is the difference between this module and `test_regressions.py`:

    test_regressions.py  — defects we already FIXED. Must always pass.
    test_open_defects.py — defects we have FOUND but not yet fixed. Fail today,
                           and each one is scheduled for the next sprint.

Each docstring records the expected output, the actual output, why it matters,
and the fix. Every failure below has been reproduced against the running API,
not inferred from reading the code.

When a defect is fixed, move its test into test_regressions.py.
"""
import pytest
from datetime import date, timedelta

from models import db, Invoice


# ── DEFECT OD-01 ──────────────────────────────────────────────
def test_unauthenticated_error_uses_the_documented_json_envelope(client):
    """OD-01 · Auth errors use a different JSON envelope from the rest of the API.

    Endpoint  : any protected endpoint, called without a token
    Expected  : {"error": "..."} — the ErrorResponse schema that openapi.yaml
                declares for every single operation
    Actual    : {"msg": "Missing Authorization Header"}

    Cause     : flask-jwt-extended emits its own error envelope, and we never
                overrode it. Our own handlers in app.py all use "error".
    Impact    : the documented contract is wrong for all 67 protected
                operations, and the frontend's errText() reads `data.error`, so
                a session-expiry shows a generic fallback instead of the real
                message.
    Severity  : low — cosmetic to a human, but a contract violation for any
                client generated from the spec.
    Fix       : add @jwt.unauthorized_loader / @jwt.invalid_token_loader /
                @jwt.expired_token_loader in create_app() returning
                {"error": <msg>} with the same status code. ~6 lines.
    """
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    body = response.get_json()
    assert "error" in body, (
        f"openapi.yaml documents every error as {{'error': ...}}, "
        f"but this returned {body}"
    )


# ── DEFECT OD-02 ──────────────────────────────────────────────
def test_public_registration_cannot_grant_itself_admin(client):
    """OD-02 · Anyone on the internet can create an ADMIN account.  [SECURITY]

    Endpoint  : POST /api/auth/register  (public, unauthenticated)
    Input     : {"name": ..., "email": ..., "password": ..., "role": "ADMIN"}
    Expected  : 400 or 403 — public signup must only create residents
    Actual    : 201 Created, with a working ADMIN token

    Verified  : the returned token successfully calls GET /api/members/, an
                admin-only endpoint, so this is real privilege escalation and
                not just a mislabelled record.
    Cause     : register() validates that `role` is a *valid enum value* but
                never that the caller is *allowed* to request it. Every one of
                the 8 roles, including SYSTEM_ADMIN, is accepted.
    Impact    : defeats every role check in the application. An attacker can
                read the full member directory, mark invoices paid, delete
                flats and publish emergency notices.
    Severity  : HIGH.
    Known     : deliberately left open so the team can self-serve test accounts
                (KNOWN_ISSUES.md #1) — but it must be closed before the app is
                used with real data.
    Fix       : restrict the public endpoint to TENANT/OWNER and create staff
                through the existing admin-only POST /api/members/.
    """
    response = client.post("/api/auth/register", json={
        "name": "Self Promoted", "email": "escalate@test.com",
        "password": "Pass@123", "role": "ADMIN",
    })
    assert response.status_code in (400, 403), (
        "public registration granted an ADMIN account "
        f"(status {response.status_code}, role "
        f"{(response.get_json() or {}).get('user', {}).get('role')})"
    )

def test_admin_token_from_public_signup_cannot_reach_admin_endpoints(client):
    """OD-02b · Public signup should not create a usable ADMIN token.

    Expected : ADMIN registration through public signup must be rejected
    Actual after fix : signup returns 400/403 and no token is created
    """
    signup = client.post("/api/auth/register", json={
        "name": "Self Promoted 2",
        "email": "escalate2@test.com",
        "password": "Pass@123",
        "role": "ADMIN",
    })

    assert signup.status_code in (400, 403)

    token = (signup.get_json() or {}).get("token")
    assert token is None, "public signup should not return an ADMIN token"
    
# ── DEFECT OD-03 ──────────────────────────────────────────────
def test_unpaid_invoice_past_its_due_date_becomes_overdue(client, admin, seed, app):
    """OD-03 · Invoices never become OVERDUE.

    Endpoint  : GET /api/invoices/
    Setup     : an UNPAID invoice whose due_date was 60 days ago
    Expected  : status "OVERDUE"
    Actual    : status "UNPAID" — forever

    Cause     : the OVERDUE value exists in invoice_status_enum and due_date is
                stored, but nothing in the codebase ever compares the two. No
                scheduled job, and no check on read.
    Impact    : the treasurer cannot distinguish "due next week" from "unpaid
                since March". The Society Health Score's payment component is
                also blind to lateness, so a society that never pays on time
                still scores well as long as the invoices are eventually paid.
    Severity  : medium — a real functional gap in a headline feature.
    Known     : KNOWN_ISSUES.md #9.
    Fix       : either flip past-due UNPAID invoices on read, or add a small
                scheduled task. Reading is simpler and has no infrastructure
                cost.
    """
    with app.app_context():
        overdue = Invoice(
            apartment_id=seed["apartment_id"], generated_by=seed["admin_id"],
            month=1, year=date.today().year, amount=1500, status="UNPAID",
            due_date=date.today() - timedelta(days=60),
        )
        db.session.add(overdue)
        db.session.commit()
        invoice_id = overdue.id

    listing = client.get("/api/invoices/", headers=admin)
    assert listing.status_code == 200
    invoice = next(i for i in listing.get_json() if i["id"] == invoice_id)
    assert invoice["status"] == "OVERDUE", (
        f"an invoice due {invoice['due_date']} (60 days ago) is still reported "
        f"as {invoice['status']}"
    )


# ── DEFECT OD-04 ──────────────────────────────────────────────
@pytest.mark.parametrize("endpoint,payload,field", [
    ("/api/maintenance/",
     {"title": "x", "category": "BOGUS", "scheduled_date": "2026-09-01"}, "category"),
    ("/api/equipment/",
     {"name": "x", "category": "BOGUS", "last_serviced_date": "2026-06-01",
      "service_frequency_days": 30}, "category"),
])
def test_validation_error_names_the_field_the_client_sent(client, admin, endpoint, payload, field):
    """OD-04 · Validation errors name the internal enum, not the client's field.

    Endpoint  : POST /api/maintenance/ and POST /api/equipment/
    Input     : {"category": "BOGUS", ...}
    Expected  : "category must be one of: ..." — naming the field the client sent
    Actual    : "task_category must be one of: ..."  (maintenance)
                "equipment_category must be one of: ..."  (equipment)

    Cause     : parse_enum() falls back to the enum's internal name when the
                caller omits field=. Notices and conflicts pass field="category"
                and so report it correctly; maintenance and equipment do not.
    Impact    : a frontend that maps error messages back to form fields cannot
                match these, so the message cannot be shown against the offending
                input. It also leaks internal naming into the public contract.
    Severity  : low.
    Fix       : pass field="category" at the two call sites — a one-word change
                each.
    """
    response = client.post(endpoint, json=payload, headers=admin)
    assert response.status_code == 400
    message = response.get_json()["error"]
    assert message.startswith(f"{field} must be one of"), (
        f"error names the internal enum rather than the client's field: {message!r}"
    )
