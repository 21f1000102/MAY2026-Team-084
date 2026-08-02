"""Visitor parking availability: /api/parking.

Residents reserve and release; only management adds or removes slots. A blank
expected_arrival_time (the UI's empty datetime box) must be accepted, and a
resident must not be able to free somebody else's reservation.
"""


def _add_slot(client, headers, slot_number="P1", **overrides):
    """POST a parking slot and return the flask response."""
    payload = {"slot_number": slot_number}
    payload.update(overrides)
    return client.post("/api/parking/", json=payload, headers=headers)


def _slot_id(client, headers, slot_number="P1", **overrides):
    return _add_slot(client, headers, slot_number, **overrides).get_json()["id"]


def _reserve(client, headers, sid, **overrides):
    payload = {"visitor_name": "Anil Kumar", "visitor_vehicle_number": "KA01AB1234"}
    payload.update(overrides)
    return client.put(f"/api/parking/{sid}/reserve", json=payload, headers=headers)


# ── happy path ────────────────────────────────────────────────
def test_admin_can_add_a_slot(client, seed, admin):
    res = _add_slot(client, admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["slot_number"] == "P1"
    assert body["status"] == "AVAILABLE"
    assert body["occupied_by_apartment_id"] is None


def test_slot_can_be_created_with_an_explicit_status(client, seed, admin):
    body = _add_slot(client, admin, "P9", status="OCCUPIED").get_json()
    assert body["status"] == "OCCUPIED"


def test_slot_list_is_ordered_by_slot_number(client, seed, admin):
    _add_slot(client, admin, "P2")
    _add_slot(client, admin, "P1")

    res = client.get("/api/parking/", headers=admin)
    assert res.status_code == 200
    assert [s["slot_number"] for s in res.get_json()] == ["P1", "P2"]


def test_available_returns_only_free_slots(client, seed, admin, resident):
    free = _slot_id(client, admin, "P1")
    taken = _slot_id(client, admin, "P2")
    _reserve(client, resident, taken)

    res = client.get("/api/parking/available", headers=resident)
    assert res.status_code == 200
    assert [s["id"] for s in res.get_json()] == [free]


def test_resident_can_reserve_a_slot_for_a_visitor(client, seed, resident, admin):
    sid = _slot_id(client, admin)

    res = _reserve(client, resident, sid, expected_arrival_time="2026-09-15T18:30:00")
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Slot P1 reserved successfully"
    slot = body["slot"]
    assert slot["status"] == "RESERVED"
    assert slot["visitor_name"] == "Anil Kumar"
    assert slot["expected_arrival_time"] == "2026-09-15 18:30:00"
    assert slot["occupied_by_apartment_id"] == seed["apartment_id"]
    assert slot["flat_number"] == "A-101"
    # a reservation is not an arrival
    assert slot["occupied_since"] is None


def test_occupying_a_reserved_slot_keeps_the_reserving_flat(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)

    res = client.put(f"/api/parking/{sid}/occupy", json={}, headers=admin)
    assert res.status_code == 200
    slot = res.get_json()["slot"]
    assert slot["status"] == "OCCUPIED"
    assert slot["occupied_by_apartment_id"] == seed["apartment_id"]
    assert slot["occupied_since"] is not None
    assert slot["visitor_name"] == "Anil Kumar"


def test_occupying_a_free_slot_attributes_it_to_the_caller(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = client.put(f"/api/parking/{sid}/occupy",
                     json={"visitor_name": "Walk-in"}, headers=resident)
    assert res.status_code == 200
    slot = res.get_json()["slot"]
    assert slot["occupied_by_apartment_id"] == seed["apartment_id"]
    assert slot["visitor_name"] == "Walk-in"


def test_resident_can_release_their_own_reservation(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid, expected_arrival_time="2026-09-15T18:30:00")

    res = client.put(f"/api/parking/{sid}/release", json={}, headers=resident)
    assert res.status_code == 200
    slot = res.get_json()["slot"]
    assert slot["status"] == "AVAILABLE"
    assert slot["occupied_by_apartment_id"] is None
    assert slot["visitor_name"] is None
    assert slot["expected_arrival_time"] is None
    assert slot["occupied_since"] is None


def test_admin_can_release_any_slot(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)
    res = client.put(f"/api/parking/{sid}/release", json={}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["slot"]["status"] == "AVAILABLE"


def test_admin_can_delete_a_slot(client, seed, admin):
    sid = _slot_id(client, admin)
    res = client.delete(f"/api/parking/{sid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Slot removed"
    assert client.get("/api/parking/", headers=admin).get_json() == []


def test_reserving_a_missing_slot_returns_404(client, seed, resident):
    assert client.put("/api/parking/9999/reserve", json={},
                      headers=resident).status_code == 404


# ── business rules ────────────────────────────────────────────
def test_reserving_an_already_reserved_slot_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)

    res = _reserve(client, admin, sid)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Slot is already RESERVED"


def test_occupying_an_already_occupied_slot_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    assert client.put(f"/api/parking/{sid}/occupy", json={},
                      headers=resident).status_code == 200

    res = client.put(f"/api/parking/{sid}/occupy", json={}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Slot is already OCCUPIED"


def test_releasing_someone_elses_reservation_is_forbidden(client, seed, resident,
                                                          admin, worker):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)

    res = client.put(f"/api/parking/{sid}/release", json={}, headers=worker)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You can only release your own reservation"

    # the reservation survived the failed attempt
    assert client.get("/api/parking/", headers=admin).get_json()[0]["status"] == "RESERVED"


def test_duplicate_slot_number_returns_409(client, seed, admin):
    _add_slot(client, admin, "P1")
    res = _add_slot(client, admin, "P1")
    assert res.status_code == 409
    assert res.get_json()["error"] == "Slot already exists"


# ── validation ────────────────────────────────────────────────
def test_blank_expected_arrival_time_is_accepted(client, seed, resident, admin):
    """The UI sends "" when the arrival time box is left empty."""
    sid = _slot_id(client, admin)
    res = _reserve(client, resident, sid, expected_arrival_time="")
    assert res.status_code == 200
    assert res.get_json()["slot"]["expected_arrival_time"] is None


def test_date_only_expected_arrival_time_is_accepted(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = _reserve(client, resident, sid, expected_arrival_time="2026-09-15")
    assert res.status_code == 200
    assert res.get_json()["slot"]["expected_arrival_time"] == "2026-09-15 00:00:00"


def test_unparseable_expected_arrival_time_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = _reserve(client, resident, sid, expected_arrival_time="tomorrow evening")
    assert res.status_code == 400
    assert res.get_json()["error"] == "expected_arrival_time must be a valid date/time"


def test_slot_number_is_required(client, seed, admin):
    res = client.post("/api/parking/", json={"status": "AVAILABLE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "slot_number is required"


def test_blank_slot_number_is_rejected(client, seed, admin):
    res = _add_slot(client, admin, "   ")
    assert res.status_code == 400
    assert res.get_json()["error"] == "slot_number is required"


def test_unknown_status_is_rejected(client, seed, admin):
    res = _add_slot(client, admin, "P3", status="BOOKED")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("parking_status must be one of:")


def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/parking/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"


def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/parking/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"


def test_null_body_on_reserve_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = client.put(f"/api/parking/{sid}/reserve", data="null",
                     content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"


# ── authorization ─────────────────────────────────────────────
def test_parking_requires_authentication(client, seed):
    assert client.get("/api/parking/").status_code == 401
    assert client.get("/api/parking/available").status_code == 401
    assert client.post("/api/parking/", json={"slot_number": "P1"}).status_code == 401
    assert client.put("/api/parking/1/reserve", json={}).status_code == 401


def test_resident_can_read_slots(client, seed, admin, resident):
    _add_slot(client, admin)
    assert client.get("/api/parking/", headers=resident).status_code == 200
    assert client.get("/api/parking/available", headers=resident).status_code == 200


def test_resident_cannot_add_or_delete_slots(client, seed, admin, resident):
    sid = _slot_id(client, admin)

    created = _add_slot(client, resident, "P5")
    assert created.status_code == 403
    assert created.get_json()["error"] == "You are not allowed to perform this action"

    assert client.delete(f"/api/parking/{sid}", headers=resident).status_code == 403
