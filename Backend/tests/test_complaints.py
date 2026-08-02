"""API tests for /api/complaints — happy path, validation, authorization and
the assignment / status-transition / scoping business rules."""
import pytest


# ── helpers ───────────────────────────────────────────────────
def raise_complaint(client, headers, apartment_id, **overrides):
    """POST a valid complaint and return the parsed JSON body."""
    payload = {
        "title": "Leaking kitchen tap",
        "description": "Water drips continuously under the sink.",
        "category": "PLUMBING",
        "apartment_id": apartment_id,
    }
    payload.update(overrides)
    res = client.post("/api/complaints/", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def committee_headers(tokens):
    return {"Authorization": f"Bearer {tokens['committee']}"}


# ── happy path ────────────────────────────────────────────────
def test_resident_can_raise_complaint(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Lift is stuck",
        "description": "Lift stops between floors 1 and 2.",
        "category": "ELECTRICAL",
        "priority": "HIGH",
        "apartment_id": seed["apartment_id"],
    }, headers=resident)

    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Lift is stuck"
    assert body["category"] == "ELECTRICAL"
    assert body["priority"] == "HIGH"
    assert body["status"] == "OPEN"
    assert body["flat_number"] == "A-101"
    assert body["raised_by"] == seed["resident_id"]
    assert body["assigned_worker_id"] is None


def test_priority_defaults_to_medium(client, resident, seed):
    body = raise_complaint(client, resident, seed["apartment_id"])
    assert body["priority"] == "MEDIUM"


def test_resident_lists_only_own_complaints(client, admin, resident, seed):
    mine = raise_complaint(client, resident, seed["apartment_id"])
    raise_complaint(client, admin, seed["other_apartment_id"],
                    title="Admin raised elsewhere")

    res = client.get("/api/complaints/", headers=resident)
    assert res.status_code == 200
    ids = [c["id"] for c in res.get_json()]
    assert ids == [mine["id"]]


def test_admin_lists_all_complaints(client, admin, resident, seed):
    raise_complaint(client, resident, seed["apartment_id"])
    raise_complaint(client, admin, seed["other_apartment_id"], title="Second")

    res = client.get("/api/complaints/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_get_complaint_detail_includes_updates(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    client.put(f"/api/complaints/{complaint['id']}/assign",
               json={"worker_id": seed["worker_id"]}, headers=admin)

    res = client.get(f"/api/complaints/{complaint['id']}", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == complaint["id"]
    assert [u["status"] for u in body["updates"]] == ["ASSIGNED"]


def test_admin_can_delete_complaint(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.delete(f"/api/complaints/{complaint['id']}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Complaint deleted"
    assert client.get(f"/api/complaints/{complaint['id']}",
                      headers=admin).status_code == 404


def test_committee_member_may_delete_complaint(client, admin, resident,
                                               tokens, seed):
    """COMMITTEE_MEMBER is an admin role even though it is not a finance role."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.delete(f"/api/complaints/{complaint['id']}",
                        headers=committee_headers(tokens))
    assert res.status_code == 200


# ── validation ────────────────────────────────────────────────
@pytest.mark.parametrize("missing", ["title", "category", "apartment_id"])
def test_raise_complaint_missing_required_field_returns_400(
        client, resident, seed, missing):
    payload = {"title": "T", "category": "PLUMBING",
               "apartment_id": seed["apartment_id"]}
    payload.pop(missing)

    res = client.post("/api/complaints/", json=payload, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"


def test_raise_complaint_bad_category_returns_400(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Hungry", "category": "FOOD",
        "apartment_id": seed["apartment_id"],
    }, headers=resident)

    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")


def test_raise_complaint_bad_priority_returns_400(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Noisy", "category": "OTHER", "priority": "URGENT",
        "apartment_id": seed["apartment_id"],
    }, headers=resident)

    assert res.status_code == 400
    assert res.get_json()["error"].startswith("priority must be one of:")


def test_raise_complaint_non_numeric_apartment_id_returns_400(
        client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Broken gate", "category": "SECURITY",
        "apartment_id": "the first one",
    }, headers=resident)

    assert res.status_code == 400
    assert res.get_json()["error"] == "apartment_id must be a whole number"


def test_raise_complaint_unknown_apartment_returns_404(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Ghost flat", "category": "OTHER", "apartment_id": 99999,
    }, headers=resident)

    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"


@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"hello"', "Request body must be a JSON object"),
])
def test_raise_complaint_malformed_body_returns_400(
        client, resident, raw, expected_error):
    res = client.post("/api/complaints/", data=raw,
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error


# ── authorization ─────────────────────────────────────────────
@pytest.mark.parametrize("method, path", [
    ("get", "/api/complaints/"),
    ("post", "/api/complaints/"),
    ("get", "/api/complaints/1"),
    ("put", "/api/complaints/1/assign"),
    ("put", "/api/complaints/1/status"),
    ("delete", "/api/complaints/1"),
])
def test_complaint_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401


def test_resident_cannot_delete_complaint(client, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.delete(f"/api/complaints/{complaint['id']}", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_resident_cannot_assign_a_worker(client, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": seed["worker_id"]}, headers=resident)
    assert res.status_code == 403


def test_resident_cannot_read_another_flats_complaint(
        client, admin, resident, seed):
    other = raise_complaint(client, admin, seed["other_apartment_id"],
                            title="B-202 seepage")

    res = client.get(f"/api/complaints/{other['id']}", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to view this complaint"


def test_resident_cannot_update_another_flats_complaint(
        client, admin, resident, seed):
    other = raise_complaint(client, admin, seed["other_apartment_id"])

    res = client.put(f"/api/complaints/{other['id']}/status",
                     json={"status": "CLOSED"}, headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to update this complaint"


# ── business rules: assignment ────────────────────────────────
def test_assign_worker_returns_200_and_populates_worker_name(
        client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": seed["worker_id"]}, headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ASSIGNED"
    assert body["assigned_worker_id"] == seed["worker_id"]
    assert body["assigned_worker_name"] == "Ramesh Worker"


@pytest.mark.parametrize("payload", [{}, {"worker_id": None},
                                     {"worker_id": ""}, {"remarks": "please fix"}])
def test_assign_without_worker_id_returns_400(client, admin, resident,
                                              seed, payload):
    """Regression: a null worker_id used to flip the status to ASSIGNED anyway."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "worker_id is required"

    after = client.get(f"/api/complaints/{complaint['id']}", headers=admin).get_json()
    assert after["status"] == "OPEN"
    assert after["assigned_worker_id"] is None


def test_assign_to_non_worker_user_returns_400(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": seed["resident_id"]}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Selected user is not a maintenance worker"


def test_assign_to_unknown_user_returns_404(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": 99999}, headers=admin)
    assert res.status_code == 404
    assert res.get_json()["error"] == "Worker not found"


def test_worker_sees_complaint_assigned_to_them(client, admin, resident,
                                                worker, seed):
    """Regression: workers only ever saw complaints they had raised themselves."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    assert client.get("/api/complaints/", headers=worker).get_json() == []

    client.put(f"/api/complaints/{complaint['id']}/assign",
               json={"worker_id": seed["worker_id"]}, headers=admin)

    res = client.get("/api/complaints/", headers=worker)
    assert res.status_code == 200
    assert [c["id"] for c in res.get_json()] == [complaint["id"]]


def test_worker_does_not_see_unassigned_complaints(client, resident,
                                                   worker, seed):
    raise_complaint(client, resident, seed["apartment_id"])

    res = client.get("/api/complaints/", headers=worker)
    assert res.status_code == 200
    assert res.get_json() == []


def test_assigned_worker_can_read_and_update_the_complaint(
        client, admin, resident, worker, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    client.put(f"/api/complaints/{complaint['id']}/assign",
               json={"worker_id": seed["worker_id"]}, headers=admin)

    assert client.get(f"/api/complaints/{complaint['id']}",
                      headers=worker).status_code == 200

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": "IN_PROGRESS"}, headers=worker)
    assert res.status_code == 200
    assert res.get_json()["status"] == "IN_PROGRESS"


# ── business rules: status transitions ────────────────────────
def test_status_flow_open_to_completed_sets_resolved_at(
        client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    cid = complaint["id"]

    assert client.put(f"/api/complaints/{cid}/status",
                      json={"status": "IN_PROGRESS"},
                      headers=admin).status_code == 200
    res = client.put(f"/api/complaints/{cid}/status",
                     json={"status": "COMPLETED", "remarks": "Washer replaced"},
                     headers=admin)
    assert res.status_code == 200
    assert res.get_json()["status"] == "COMPLETED"
    assert res.get_json()["resolved_at"] is not None


def test_reopening_a_closed_complaint_clears_resolved_at(
        client, admin, resident, seed):
    """Regression: resolved_at used to survive a reopen."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    cid = complaint["id"]

    client.put(f"/api/complaints/{cid}/status", json={"status": "CLOSED"},
               headers=admin)
    res = client.put(f"/api/complaints/{cid}/status", json={"status": "OPEN"},
                     headers=admin)
    assert res.status_code == 200
    assert res.get_json()["resolved_at"] is None


@pytest.mark.parametrize("new_status", ["COMPLETED"])
def test_invalid_status_transition_returns_400(client, admin, resident,
                                               seed, new_status):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": new_status}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"Cannot change status from OPEN to {new_status}"


def test_status_update_requires_status_field(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"remarks": "no status"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "status is required"


def test_status_update_bad_enum_returns_400(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": "DONE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("status must be one of:")


def test_setting_the_same_status_is_allowed(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": "OPEN"}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["status"] == "OPEN"


def test_unknown_complaint_id_returns_404(client, admin, seed):
    assert client.get("/api/complaints/99999", headers=admin).status_code == 404
    assert client.delete("/api/complaints/99999", headers=admin).status_code == 404
