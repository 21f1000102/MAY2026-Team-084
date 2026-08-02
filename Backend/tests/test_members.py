"""
Tests for the members API (/api/members).

Covers apartment CRUD, member CRUD and the worker lookup used for complaint
assignment, across four axes: happy path, input validation, role-based
authorization and the business rules (duplicate flat/email/phone, blank phone
normalising to NULL, refusing to delete an occupied flat).
"""
import pytest

from models import db, Invoice


def _member_payload(**overrides):
    payload = {
        "name": "Manoj Member",
        "email": "manoj@test.com",
        "password": "Secret@123",
        "role": "OWNER",
    }
    payload.update(overrides)
    return payload


# ══════════════════════════════════════════════════════════════
#  GET /api/members/apartments
# ══════════════════════════════════════════════════════════════

def test_list_apartments_returns_seeded_flats(client, seed, admin):
    res = client.get("/api/members/apartments", headers=admin)
    assert res.status_code == 200
    assert {a["flat_number"] for a in res.get_json()} == {"A-101", "B-202"}


def test_list_apartments_exposes_block_and_floor(client, seed, admin):
    body = client.get("/api/members/apartments", headers=admin).get_json()
    a101 = next(a for a in body if a["flat_number"] == "A-101")
    assert (a101["id"], a101["block"], a101["floor"]) == (seed["apartment_id"], "A", 1)


@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_apartments_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/members/apartments", headers=headers).status_code == 200


def test_list_apartments_without_token_returns_401(client, seed):
    assert client.get("/api/members/apartments").status_code == 401


# ══════════════════════════════════════════════════════════════
#  POST /api/members/apartments
# ══════════════════════════════════════════════════════════════

def test_create_apartment_returns_201(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "C-303", "block": "C", "floor": 3})
    assert res.status_code == 201
    body = res.get_json()
    assert body["flat_number"] == "C-303"
    assert body["block"] == "C"
    assert body["floor"] == 3
    assert body["id"]


def test_create_apartment_accepts_a_numeric_string_floor(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "D-404", "floor": "4"})
    assert res.status_code == 201
    assert res.get_json()["floor"] == 4


def test_create_apartment_missing_flat_number_returns_400(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin, json={"block": "C"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "flat_number is required"


def test_create_apartment_non_numeric_floor_returns_400(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "E-505", "floor": "top"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "floor must be a whole number"


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_apartment_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/apartments", headers=admin,
                      data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_create_apartment_duplicate_flat_number_returns_409(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "A-101"})
    assert res.status_code == 409
    assert res.get_json()["error"] == "Flat number already exists"


def test_create_apartment_as_resident_returns_403(client, seed, resident):
    res = client.post("/api/members/apartments", headers=resident,
                      json={"flat_number": "C-303"})
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_create_apartment_as_worker_returns_403(client, seed, worker):
    res = client.post("/api/members/apartments", headers=worker,
                      json={"flat_number": "C-303"})
    assert res.status_code == 403


def test_create_apartment_as_treasurer_returns_201(client, seed, treasurer):
    res = client.post("/api/members/apartments", headers=treasurer,
                      json={"flat_number": "C-303"})
    assert res.status_code == 201


def test_create_apartment_without_token_returns_401(client, seed):
    res = client.post("/api/members/apartments", json={"flat_number": "C-303"})
    assert res.status_code == 401


# ══════════════════════════════════════════════════════════════
#  PUT /api/members/apartments/<id>
# ══════════════════════════════════════════════════════════════

def test_update_apartment_renames_the_flat(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"flat_number": "B-999"})
    assert res.status_code == 200
    assert res.get_json()["flat_number"] == "B-999"


def test_update_apartment_updates_block_and_floor(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"block": "Z", "floor": 9})
    assert res.status_code == 200
    assert (res.get_json()["block"], res.get_json()["floor"]) == ("Z", 9)


def test_update_apartment_blank_flat_number_returns_400(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"flat_number": "   "})
    assert res.status_code == 400
    assert res.get_json()["error"] == "flat_number is required"


def test_update_apartment_bad_floor_returns_400(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"floor": "penthouse"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "floor must be a whole number"


def test_update_apartment_duplicate_flat_number_returns_409(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"flat_number": "A-101"})
    assert res.status_code == 409
    assert res.get_json()["error"] == "Flat number already exists"


def test_update_apartment_to_its_own_flat_number_returns_200(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['apartment_id']}",
                     headers=admin, json={"flat_number": "A-101"})
    assert res.status_code == 200


def test_update_unknown_apartment_returns_404(client, seed, admin):
    res = client.put("/api/members/apartments/9999", headers=admin,
                     json={"flat_number": "X-000"})
    assert res.status_code == 404


def test_update_apartment_as_resident_returns_403(client, seed, resident):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=resident, json={"flat_number": "B-999"})
    assert res.status_code == 403


def test_update_apartment_without_token_returns_401(client, seed):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     json={"flat_number": "B-999"})
    assert res.status_code == 401


# ══════════════════════════════════════════════════════════════
#  DELETE /api/members/apartments/<id>
# ══════════════════════════════════════════════════════════════

def test_delete_empty_apartment_returns_200(client, seed, admin):
    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                        headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Apartment deleted"


def test_delete_apartment_removes_it_from_the_list(client, seed, admin):
    client.delete(f"/api/members/apartments/{seed['other_apartment_id']}", headers=admin)
    listing = client.get("/api/members/apartments", headers=admin).get_json()
    assert {a["flat_number"] for a in listing} == {"A-101"}


def test_delete_apartment_with_residents_returns_409(client, seed, admin):
    res = client.delete(f"/api/members/apartments/{seed['apartment_id']}", headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == \
        "Cannot delete a flat that still has residents or invoices"


def test_delete_apartment_with_invoices_returns_409(client, app, seed, admin):
    with app.app_context():
        db.session.add(Invoice(apartment_id=seed["other_apartment_id"],
                               month=6, year=2026, amount=1500))
        db.session.commit()

    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                        headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == \
        "Cannot delete a flat that still has residents or invoices"


def test_delete_unknown_apartment_returns_404(client, seed, admin):
    assert client.delete("/api/members/apartments/9999", headers=admin).status_code == 404


def test_delete_apartment_as_resident_returns_403(client, seed, resident):
    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                        headers=resident)
    assert res.status_code == 403


def test_delete_apartment_without_token_returns_401(client, seed):
    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}")
    assert res.status_code == 401


# ══════════════════════════════════════════════════════════════
#  GET /api/members/
# ══════════════════════════════════════════════════════════════

def test_list_members_returns_the_seeded_resident(client, seed, admin):
    res = client.get("/api/members/", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1
    assert body[0]["id"] == seed["resident_record_id"]
    assert body[0]["user_id"] == seed["resident_id"]


def test_list_members_includes_flat_details(client, seed, admin):
    row = client.get("/api/members/", headers=admin).get_json()[0]
    assert row["flat_number"] == "A-101"
    assert row["block"] == "A"
    assert row["floor"] == 1
    assert row["is_owner"] is False


def test_list_members_as_resident_returns_403(client, seed, resident):
    res = client.get("/api/members/", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_list_members_as_worker_returns_403(client, seed, worker):
    assert client.get("/api/members/", headers=worker).status_code == 403


def test_list_members_as_treasurer_returns_200(client, seed, treasurer):
    assert client.get("/api/members/", headers=treasurer).status_code == 200


def test_list_members_without_token_returns_401(client, seed):
    assert client.get("/api/members/").status_code == 401


# ══════════════════════════════════════════════════════════════
#  POST /api/members/
# ══════════════════════════════════════════════════════════════

def test_create_member_returns_201(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["other_apartment_id"], phone="9222222222",
        is_owner=True, move_in_date="2026-01-15",
    ))
    assert res.status_code == 201
    body = res.get_json()
    assert body["email"] == "manoj@test.com"
    assert body["role"] == "OWNER"
    assert body["apartment_id"] == seed["other_apartment_id"]
    assert body["flat_number"] == "B-202"
    assert body["is_owner"] is True
    assert body["move_in_date"] == "2026-01-15"


def test_create_member_can_log_in_afterwards(client, seed, admin):
    client.post("/api/members/", headers=admin,
                json=_member_payload(apartment_id=seed["apartment_id"]))
    res = client.post("/api/auth/login",
                      json={"email": "manoj@test.com", "password": "Secret@123"})
    assert res.status_code == 200


def test_create_member_appears_in_the_listing(client, seed, admin):
    client.post("/api/members/", headers=admin,
                json=_member_payload(apartment_id=seed["apartment_id"]))
    body = client.get("/api/members/", headers=admin).get_json()
    assert len(body) == 2


@pytest.mark.parametrize("missing",
                         ["name", "email", "password", "role", "apartment_id"])
def test_create_member_missing_required_field_returns_400(client, seed, admin, missing):
    payload = _member_payload(apartment_id=seed["apartment_id"])
    payload.pop(missing)

    res = client.post("/api/members/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"


def test_create_member_unknown_role_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        role="WIZARD", apartment_id=seed["apartment_id"]))
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("role must be one of:")


def test_create_member_bad_move_in_date_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], move_in_date="not-a-date"))
    assert res.status_code == 400
    assert res.get_json()["error"] == "move_in_date must be a valid date (YYYY-MM-DD)"


def test_create_member_non_numeric_apartment_id_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin,
                      json=_member_payload(apartment_id="ground"))
    assert res.status_code == 400
    assert res.get_json()["error"] == "apartment_id must be a whole number"


def test_create_member_zero_apartment_id_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(apartment_id=0))
    assert res.status_code == 400
    assert res.get_json()["error"] == "apartment_id must be at least 1"


def test_create_member_unknown_apartment_returns_404(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(apartment_id=9999))
    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_create_member_duplicate_email_returns_409(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        email="resident@test.com", apartment_id=seed["apartment_id"]))
    assert res.status_code == 409
    assert res.get_json()["error"] == "Email already registered"


def test_create_member_duplicate_phone_returns_409(client, seed, admin):
    first = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], phone="9333333333"))
    assert first.status_code == 201

    second = client.post("/api/members/", headers=admin, json=_member_payload(
        email="second@test.com", apartment_id=seed["apartment_id"], phone="9333333333"))
    assert second.status_code == 409
    assert second.get_json()["error"] == "Phone number already registered"


def test_create_two_members_with_blank_phone_both_succeed(client, seed, admin):
    """Blank phone must normalise to NULL — users.phone is UNIQUE."""
    first = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], phone=""))
    second = client.post("/api/members/", headers=admin, json=_member_payload(
        email="second@test.com", apartment_id=seed["apartment_id"], phone=""))
    assert (first.status_code, second.status_code) == (201, 201)
    assert first.get_json()["phone"] is None


def test_create_member_as_resident_returns_403(client, seed, resident):
    res = client.post("/api/members/", headers=resident,
                      json=_member_payload(apartment_id=seed["apartment_id"]))
    assert res.status_code == 403


def test_create_member_without_token_returns_401(client, seed):
    res = client.post("/api/members/", json=_member_payload(apartment_id=seed["apartment_id"]))
    assert res.status_code == 401


# ══════════════════════════════════════════════════════════════
#  GET /api/members/workers
# ══════════════════════════════════════════════════════════════

def test_list_workers_returns_only_worker_role_users(client, seed, admin):
    res = client.get("/api/members/workers", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert [w["email"] for w in body] == ["worker@test.com"]


def test_list_workers_id_is_the_users_id(client, seed, admin):
    """complaints.assigned_worker_id points at users.id, never residents.id."""
    body = client.get("/api/members/workers", headers=admin).get_json()
    assert body[0]["id"] == seed["worker_id"]


def test_list_workers_returns_id_name_email_only(client, seed, admin):
    body = client.get("/api/members/workers", headers=admin).get_json()
    assert set(body[0]) == {"id", "name", "email"}


def test_list_workers_includes_newly_added_workers(client, seed, admin):
    client.post("/api/members/", headers=admin, json=_member_payload(
        name="Anil Worker", email="anil@test.com",
        role="WORKER", apartment_id=seed["apartment_id"]))

    body = client.get("/api/members/workers", headers=admin).get_json()
    assert [w["name"] for w in body] == ["Anil Worker", "Ramesh Worker"]


def test_list_workers_as_resident_returns_403(client, seed, resident):
    assert client.get("/api/members/workers", headers=resident).status_code == 403


def test_list_workers_without_token_returns_401(client, seed):
    assert client.get("/api/members/workers").status_code == 401


# ══════════════════════════════════════════════════════════════
#  GET /api/members/<resident_id>
# ══════════════════════════════════════════════════════════════

def test_get_member_returns_200(client, seed, admin):
    res = client.get(f"/api/members/{seed['resident_record_id']}", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == seed["resident_record_id"]
    assert body["email"] == "resident@test.com"
    assert body["flat_number"] == "A-101"


@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_get_member_is_open_to_every_role(client, seed, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    res = client.get(f"/api/members/{seed['resident_record_id']}", headers=headers)
    assert res.status_code == 200


def test_get_unknown_member_returns_404(client, seed, admin):
    assert client.get("/api/members/9999", headers=admin).status_code == 404


def test_get_member_without_token_returns_401(client, seed):
    assert client.get(f"/api/members/{seed['resident_record_id']}").status_code == 401


# ══════════════════════════════════════════════════════════════
#  PUT /api/members/<resident_id>
# ══════════════════════════════════════════════════════════════

def test_update_member_changes_name_and_role(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"name": "Ravi Renamed", "role": "OWNER"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["name"] == "Ravi Renamed"
    assert body["role"] == "OWNER"


def test_update_member_changes_resident_fields(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"is_owner": True, "move_in_date": "2025-03-01",
                           "move_out_date": "2026-03-01"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["is_owner"] is True
    assert body["move_in_date"] == "2025-03-01"
    assert body["move_out_date"] == "2026-03-01"


def test_update_member_blank_phone_clears_it(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"phone": ""})
    assert res.status_code == 200
    assert res.get_json()["phone"] is None


def test_update_member_unknown_role_returns_400(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"role": "WIZARD"})
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("role must be one of:")


def test_update_member_bad_move_in_date_returns_400(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"move_in_date": "not-a-date"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "move_in_date must be a valid date (YYYY-MM-DD)"


def test_update_member_bad_move_out_date_returns_400(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"move_out_date": "31-12-2026"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "move_out_date must be a valid date (YYYY-MM-DD)"


def test_update_member_duplicate_phone_returns_409(client, seed, admin):
    client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], phone="9444444444"))

    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"phone": "9444444444"})
    assert res.status_code == 409
    assert res.get_json()["error"] == "Phone number already registered"


def test_update_member_keeping_its_own_phone_returns_200(client, seed, admin):
    client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
               json={"phone": "9555555555"})
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"phone": "9555555555"})
    assert res.status_code == 200


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_update_unknown_member_returns_404(client, seed, admin):
    res = client.put("/api/members/9999", headers=admin, json={"name": "Nobody"})
    assert res.status_code == 404


def test_update_member_as_resident_returns_403(client, seed, resident):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=resident,
                     json={"name": "Self Service"})
    assert res.status_code == 403


def test_update_member_without_token_returns_401(client, seed):
    res = client.put(f"/api/members/{seed['resident_record_id']}", json={"name": "X"})
    assert res.status_code == 401


# ══════════════════════════════════════════════════════════════
#  DELETE /api/members/<resident_id>
# ══════════════════════════════════════════════════════════════

def test_deactivate_member_returns_200(client, seed, admin):
    res = client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Member deactivated"


def test_deactivate_member_is_a_soft_delete(client, seed, admin):
    client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)
    body = client.get(f"/api/members/{seed['resident_record_id']}", headers=admin).get_json()
    assert body["is_active"] is False


def test_deactivate_worker_removes_them_from_the_worker_list(client, seed, admin):
    created = client.post("/api/members/", headers=admin, json=_member_payload(
        name="Anil Worker", email="anil@test.com",
        role="WORKER", apartment_id=seed["apartment_id"])).get_json()

    client.delete(f"/api/members/{created['id']}", headers=admin)
    body = client.get("/api/members/workers", headers=admin).get_json()
    assert [w["email"] for w in body] == ["worker@test.com"]


def test_deactivated_member_token_returns_403(client, seed, admin, resident):
    client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)
    res = client.get("/api/auth/me", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "Account is deactivated"


def test_deactivate_unknown_member_returns_404(client, seed, admin):
    assert client.delete("/api/members/9999", headers=admin).status_code == 404


def test_deactivate_member_as_resident_returns_403(client, seed, resident):
    res = client.delete(f"/api/members/{seed['resident_record_id']}", headers=resident)
    assert res.status_code == 403


def test_deactivate_member_without_token_returns_401(client, seed):
    assert client.delete(f"/api/members/{seed['resident_record_id']}").status_code == 401
