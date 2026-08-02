"""
Tests for the emergency contact directory API (/api/emergency).

The directory is readable by every authenticated role but only writable by
society-management roles. Covers happy path, validation (enum, phone rules,
malformed bodies), authorization and ordering behaviour.
"""
import pytest


CONTACT = {
    "name": "City Ambulance",
    "service_type": "AMBULANCE",
    "phone": "108",
    "availability": "24x7",
}


@pytest.fixture()
def contact_id(client, admin):
    """One AMBULANCE contact already in the directory."""
    res = client.post("/api/emergency/", headers=admin, json=CONTACT)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["id"]


# ══════════════════════════════════════════════════════════════
#  POST /api/emergency/
# ══════════════════════════════════════════════════════════════

def test_create_contact_returns_201(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin, json=CONTACT)
    assert res.status_code == 201
    body = res.get_json()
    assert body["name"] == "City Ambulance"
    assert body["service_type"] == "AMBULANCE"
    assert body["phone"] == "108"
    assert body["availability"] == "24x7"
    assert body["id"]


def test_create_contact_returns_only_real_columns(client, seed, admin):
    body = client.post("/api/emergency/", headers=admin, json=CONTACT).get_json()
    assert set(body) == {"id", "name", "service_type", "phone", "availability"}


def test_create_contact_uppercases_the_service_type(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "service_type": "plumber"})
    assert res.status_code == 201
    assert res.get_json()["service_type"] == "PLUMBER"


def test_create_contact_blank_availability_becomes_null(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "availability": "   "})
    assert res.status_code == 201
    assert res.get_json()["availability"] is None


def test_create_contact_omitted_availability_is_null(client, seed, admin):
    payload = {k: v for k, v in CONTACT.items() if k != "availability"}
    res = client.post("/api/emergency/", headers=admin, json=payload)
    assert res.status_code == 201
    assert res.get_json()["availability"] is None


def test_create_two_contacts_may_share_a_phone(client, seed, admin):
    """phone has no UNIQUE constraint — two services can share a number."""
    first = client.post("/api/emergency/", headers=admin, json=CONTACT)
    second = client.post("/api/emergency/", headers=admin,
                         json={**CONTACT, "name": "Backup Ambulance"})
    assert (first.status_code, second.status_code) == (201, 201)


@pytest.mark.parametrize("missing", ["name", "service_type", "phone"])
def test_create_contact_missing_required_field_returns_400(client, seed, admin, missing):
    payload = {k: v for k, v in CONTACT.items() if k != missing}
    res = client.post("/api/emergency/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"


def test_create_contact_unknown_service_type_returns_400(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "service_type": "ASTRONAUT"})
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("service_type must be one of:")


def test_create_contact_phone_without_digits_returns_400(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "phone": "call-us"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must contain digits"


def test_create_contact_phone_longer_than_15_chars_returns_400(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "phone": "1234567890123456"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must be 15 characters or fewer"


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_contact_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/emergency/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_create_contact_as_resident_returns_403(client, seed, resident):
    res = client.post("/api/emergency/", headers=resident, json=CONTACT)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_create_contact_as_worker_returns_403(client, seed, worker):
    assert client.post("/api/emergency/", headers=worker, json=CONTACT).status_code == 403


def test_create_contact_as_treasurer_returns_201(client, seed, treasurer):
    assert client.post("/api/emergency/", headers=treasurer, json=CONTACT).status_code == 201


def test_create_contact_without_token_returns_401(client, seed):
    assert client.post("/api/emergency/", json=CONTACT).status_code == 401


# ══════════════════════════════════════════════════════════════
#  GET /api/emergency/
# ══════════════════════════════════════════════════════════════

def test_list_contacts_empty_directory_returns_empty_list(client, seed, admin):
    res = client.get("/api/emergency/", headers=admin)
    assert res.status_code == 200
    assert res.get_json() == []


def test_list_contacts_returns_the_created_contact(client, seed, admin, contact_id):
    res = client.get("/api/emergency/", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert [c["id"] for c in body] == [contact_id]
    assert body[0]["name"] == "City Ambulance"


def test_list_contacts_is_ordered_by_service_type_then_name(client, seed, admin):
    for name, service in [("Zed Sparks", "ELECTRICIAN"), ("Amit Sparks", "ELECTRICIAN"),
                          ("Nita Pipes", "PLUMBER"), ("Fire HQ", "FIRE")]:
        client.post("/api/emergency/", headers=admin,
                    json={"name": name, "service_type": service, "phone": "9990001111"})

    body = client.get("/api/emergency/", headers=admin).get_json()
    assert [(c["service_type"], c["name"]) for c in body] == [
        ("ELECTRICIAN", "Amit Sparks"),
        ("ELECTRICIAN", "Zed Sparks"),
        ("FIRE", "Fire HQ"),
        ("PLUMBER", "Nita Pipes"),
    ]


def test_list_contacts_as_resident_returns_200(client, seed, resident, contact_id):
    """Every role may read the emergency directory."""
    res = client.get("/api/emergency/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_contacts_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/emergency/", headers=headers).status_code == 200


def test_list_contacts_without_token_returns_401(client, seed):
    assert client.get("/api/emergency/").status_code == 401


# ══════════════════════════════════════════════════════════════
#  PUT /api/emergency/<cid>
# ══════════════════════════════════════════════════════════════

def test_update_contact_returns_200(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"name": "State Ambulance", "phone": "102",
                           "service_type": "FIRE", "availability": "Mon-Fri"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == contact_id
    assert body["name"] == "State Ambulance"
    assert body["phone"] == "102"
    assert body["service_type"] == "FIRE"
    assert body["availability"] == "Mon-Fri"


def test_update_contact_leaves_omitted_fields_untouched(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"name": "Renamed Ambulance"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["name"] == "Renamed Ambulance"
    assert body["service_type"] == "AMBULANCE"
    assert body["phone"] == "108"
    assert body["availability"] == "24x7"


def test_update_contact_blank_service_type_keeps_the_current_one(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"service_type": ""})
    assert res.status_code == 200
    assert res.get_json()["service_type"] == "AMBULANCE"


def test_update_contact_blank_availability_clears_it(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"availability": ""})
    assert res.status_code == 200
    assert res.get_json()["availability"] is None


def test_update_contact_unknown_service_type_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"service_type": "ASTRONAUT"})
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("service_type must be one of:")


def test_update_contact_blank_phone_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, json={"phone": ""})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone is required"


def test_update_contact_phone_without_digits_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, json={"phone": "ring-us"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must contain digits"


def test_update_contact_phone_longer_than_15_chars_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"phone": "1234567890123456"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must be 15 characters or fewer"


@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_contact_malformed_body_returns_400(client, seed, admin, contact_id,
                                                   raw, expected):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, data=raw,
                     content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected


def test_update_unknown_contact_returns_404(client, seed, admin):
    res = client.put("/api/emergency/9999", headers=admin, json={"name": "Ghost"})
    assert res.status_code == 404


def test_update_contact_as_resident_returns_403(client, seed, resident, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=resident,
                     json={"name": "Hijacked"})
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_update_contact_as_worker_returns_403(client, seed, worker, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=worker, json={"name": "Nope"})
    assert res.status_code == 403


def test_update_contact_without_token_returns_401(client, seed, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", json={"name": "Anonymous"})
    assert res.status_code == 401


# ══════════════════════════════════════════════════════════════
#  DELETE /api/emergency/<cid>
# ══════════════════════════════════════════════════════════════

def test_delete_contact_returns_200(client, seed, admin, contact_id):
    res = client.delete(f"/api/emergency/{contact_id}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Contact removed"


def test_delete_contact_is_a_hard_delete(client, seed, admin, contact_id):
    client.delete(f"/api/emergency/{contact_id}", headers=admin)
    assert client.get("/api/emergency/", headers=admin).get_json() == []


def test_delete_contact_twice_returns_404(client, seed, admin, contact_id):
    client.delete(f"/api/emergency/{contact_id}", headers=admin)
    assert client.delete(f"/api/emergency/{contact_id}", headers=admin).status_code == 404


def test_delete_unknown_contact_returns_404(client, seed, admin):
    assert client.delete("/api/emergency/9999", headers=admin).status_code == 404


def test_delete_contact_as_resident_returns_403(client, seed, resident, contact_id):
    res = client.delete(f"/api/emergency/{contact_id}", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_delete_contact_as_worker_returns_403(client, seed, worker, contact_id):
    assert client.delete(f"/api/emergency/{contact_id}", headers=worker).status_code == 403


def test_delete_contact_without_token_returns_401(client, seed, contact_id):
    assert client.delete(f"/api/emergency/{contact_id}").status_code == 401
