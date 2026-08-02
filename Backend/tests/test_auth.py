"""
Tests for the authentication API (/api/auth).

Covers registration, login, the /me identity endpoint and password changes
across four axes: happy path, input validation, authorization and the
business rules the team fixed (blank-phone collisions, KeyError on
change-password, duplicate email/phone).
"""
import pytest

from conftest import PASSWORD


# ══════════════════════════════════════════════════════════════
#  POST /api/auth/register
# ══════════════════════════════════════════════════════════════

def test_register_returns_201_with_token_and_user(client):
    res = client.post("/api/auth/register", json={
        "name": "Nina Newcomer",
        "email": "nina@test.com",
        "password": "Secret@123",
        "role": "OWNER",
        "phone": "9000000001",
    })
    assert res.status_code == 201
    body = res.get_json()
    assert body["message"] == "User registered successfully"
    assert body["token"]
    assert body["user"]["email"] == "nina@test.com"
    assert body["user"]["role"] == "OWNER"
    assert body["user"]["is_active"] is True


def test_register_lowercases_and_strips_email(client):
    res = client.post("/api/auth/register", json={
        "name": "  Casey Case  ",
        "email": "  MiXeD@Test.COM  ",
        "password": "Secret@123",
        "role": "TENANT",
    })
    assert res.status_code == 201
    assert res.get_json()["user"]["email"] == "mixed@test.com"


def test_register_issues_a_usable_token(client):
    token = client.post("/api/auth/register", json={
        "name": "Token Tester", "email": "token@test.com",
        "password": "Secret@123", "role": "TENANT",
    }).get_json()["token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["email"] == "token@test.com"


@pytest.mark.parametrize("missing", ["name", "email", "password", "role"])
def test_register_missing_required_field_returns_400(client, missing):
    payload = {"name": "No Field", "email": "nofield@test.com",
               "password": "Secret@123", "role": "TENANT"}
    payload.pop(missing)

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"


@pytest.mark.parametrize("blank", ["", "   "])
def test_register_blank_required_field_returns_400(client, blank):
    res = client.post("/api/auth/register", json={
        "name": blank, "email": "blank@test.com",
        "password": "Secret@123", "role": "TENANT",
    })
    assert res.status_code == 400
    assert res.get_json()["error"] == "name is required"


def test_register_unknown_role_returns_400(client):
    res = client.post("/api/auth/register", json={
        "name": "Wanda Wizard", "email": "wizard@test.com",
        "password": "Secret@123", "role": "WIZARD",
    })
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("role must be one of:")


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_register_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/register", data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_register_duplicate_email_returns_409(client, seed):
    res = client.post("/api/auth/register", json={
        "name": "Copycat", "email": "resident@test.com",
        "password": "Secret@123", "role": "TENANT",
    })
    assert res.status_code == 409
    assert res.get_json()["error"] == "Email already registered"


def test_register_duplicate_email_is_case_insensitive(client, seed):
    res = client.post("/api/auth/register", json={
        "name": "Copycat", "email": "RESIDENT@TEST.COM",
        "password": "Secret@123", "role": "TENANT",
    })
    assert res.status_code == 409
    assert res.get_json()["error"] == "Email already registered"


def test_register_duplicate_phone_returns_409(client):
    first = client.post("/api/auth/register", json={
        "name": "Phone One", "email": "phone1@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "9111111111",
    })
    assert first.status_code == 201

    second = client.post("/api/auth/register", json={
        "name": "Phone Two", "email": "phone2@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "9111111111",
    })
    assert second.status_code == 409
    assert second.get_json()["error"] == "Phone number already registered"


def test_register_two_blank_phones_both_succeed(client):
    """Blank phone must normalise to NULL — users.phone is UNIQUE.

    This was a real bug: the second blank-phone signup collided with the first.
    """
    first = client.post("/api/auth/register", json={
        "name": "Blank One", "email": "blank1@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "",
    })
    second = client.post("/api/auth/register", json={
        "name": "Blank Two", "email": "blank2@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "",
    })
    assert (first.status_code, second.status_code) == (201, 201)


def test_register_blank_phone_is_stored_as_null(client):
    res = client.post("/api/auth/register", json={
        "name": "Blank Phone", "email": "blankphone@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "   ",
    })
    assert res.status_code == 201
    assert res.get_json()["user"]["phone"] is None


# ══════════════════════════════════════════════════════════════
#  POST /api/auth/login
# ══════════════════════════════════════════════════════════════

@pytest.mark.parametrize("email,role", [
    ("admin@test.com", "ADMIN"),
    ("treasurer@test.com", "TREASURER"),
    ("committee@test.com", "COMMITTEE_MEMBER"),
    ("resident@test.com", "TENANT"),
    ("owner@test.com", "OWNER"),
    ("worker@test.com", "WORKER"),
])
def test_login_succeeds_for_every_seeded_role(client, seed, email, role):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Login successful"
    assert body["token"]
    assert body["user"]["role"] == role


def test_login_wrong_password_returns_401(client, seed):
    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": "WrongPass1"})
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"


def test_login_unknown_email_returns_401(client, seed):
    res = client.post("/api/auth/login",
                      json={"email": "ghost@test.com", "password": PASSWORD})
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"


@pytest.mark.parametrize("missing", ["email", "password"])
def test_login_missing_required_field_returns_400(client, seed, missing):
    payload = {"email": "resident@test.com", "password": PASSWORD}
    payload.pop(missing)

    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_login_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/login", data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_login_deactivated_account_returns_403(client, seed, admin):
    client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)

    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": PASSWORD})
    assert res.status_code == 403
    assert res.get_json()["error"] == "Account is deactivated"


# ══════════════════════════════════════════════════════════════
#  GET /api/auth/me
# ══════════════════════════════════════════════════════════════

def test_me_returns_the_authenticated_user(client, seed, resident):
    res = client.get("/api/auth/me", headers=resident)
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == seed["resident_id"]
    assert body["email"] == "resident@test.com"
    assert body["role"] == "TENANT"


@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_me_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/auth/me", headers=headers).status_code == 200


def test_me_without_token_returns_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_garbage_token_returns_422(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert res.status_code in (401, 422)


# ══════════════════════════════════════════════════════════════
#  PUT /api/auth/change-password
# ══════════════════════════════════════════════════════════════

def test_change_password_returns_200(client, seed, resident):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD, "new_password": "Brand@New1"})
    assert res.status_code == 200
    assert res.get_json()["message"] == "Password changed successfully"


def test_change_password_old_password_stops_working(client, seed, resident):
    client.put("/api/auth/change-password", headers=resident,
               json={"old_password": PASSWORD, "new_password": "Brand@New1"})

    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": PASSWORD})
    assert res.status_code == 401


def test_change_password_new_password_works(client, seed, resident):
    client.put("/api/auth/change-password", headers=resident,
               json={"old_password": PASSWORD, "new_password": "Brand@New1"})

    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": "Brand@New1"})
    assert res.status_code == 200


def test_change_password_missing_new_password_returns_400(client, seed, resident):
    """Regression: this used to be a KeyError -> HTML 500."""
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD})
    assert res.status_code == 400
    assert res.get_json()["error"] == "new_password is required"


def test_change_password_missing_old_password_returns_400(client, seed, resident):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"new_password": "Brand@New1"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "old_password is required"


def test_change_password_wrong_old_password_returns_400(client, seed, resident):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": "NotMyPassword", "new_password": "Brand@New1"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "Old password is incorrect"


@pytest.mark.parametrize("short", ["a", "abcde", "12345"])
def test_change_password_shorter_than_six_chars_returns_400(client, seed, resident, short):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD, "new_password": short})
    assert res.status_code == 400
    assert res.get_json()["error"] == "New password must be at least 6 characters"


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_change_password_malformed_body_returns_400(client, seed, resident, raw, expected):
    res = client.put("/api/auth/change-password", headers=resident,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_change_password_without_token_returns_401(client, seed):
    res = client.put("/api/auth/change-password",
                     json={"old_password": PASSWORD, "new_password": "Brand@New1"})
    assert res.status_code == 401
