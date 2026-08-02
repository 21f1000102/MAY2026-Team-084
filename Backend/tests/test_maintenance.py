"""Preventive-maintenance task endpoints: /api/maintenance.

scheduled_date is mandatory and must parse, completing a task twice is a
conflict, and any path that moves a task to COMPLETED must stamp
completed_at.
"""
from datetime import date, timedelta


SCHEDULED = str(date.today() + timedelta(days=10))


def _create_task(client, headers, **overrides):
    """POST a valid maintenance task and return the flask response."""
    payload = {
        "title": "Generator servicing",
        "description": "Quarterly diesel generator service",
        "category": "GENERATOR",
        "scheduled_date": SCHEDULED,
    }
    payload.update(overrides)
    return client.post("/api/maintenance/", json=payload, headers=headers)


def _task_id(client, headers, **overrides):
    return _create_task(client, headers, **overrides).get_json()["id"]


# ── happy path ────────────────────────────────────────────────
def test_admin_can_create_a_task(client, seed, admin):
    res = _create_task(client, admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Generator servicing"
    assert body["category"] == "GENERATOR"
    assert body["scheduled_date"] == SCHEDULED
    assert body["status"] == "PENDING"
    assert body["completed_at"] is None


def test_task_can_be_assigned_to_a_worker(client, seed, admin):
    body = _create_task(client, admin, assigned_to=seed["worker_id"]).get_json()
    assert body["assigned_to"] == seed["worker_id"]
    assert body["assigned_to_name"] == "Ramesh Worker"


def test_task_list_is_returned(client, seed, admin):
    _create_task(client, admin, title="Tank cleaning", category="WATER_TANK")
    res = client.get("/api/maintenance/", headers=admin)
    assert res.status_code == 200
    assert [t["title"] for t in res.get_json()] == ["Tank cleaning"]


def test_admin_can_update_a_task(client, seed, admin):
    tid = _task_id(client, admin)
    new_date = str(date.today() + timedelta(days=20))

    res = client.put(f"/api/maintenance/{tid}",
                     json={"title": "Generator servicing (rescheduled)",
                           "category": "ELECTRICAL",
                           "scheduled_date": new_date,
                           "status": "IN_PROGRESS"},
                     headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["title"] == "Generator servicing (rescheduled)"
    assert body["category"] == "ELECTRICAL"
    assert body["scheduled_date"] == new_date
    assert body["status"] == "IN_PROGRESS"


def test_admin_can_complete_a_task(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}/complete", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None


def test_admin_can_delete_a_task(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.delete(f"/api/maintenance/{tid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Task deleted"
    assert client.get("/api/maintenance/", headers=admin).get_json() == []


def test_completing_a_missing_task_returns_404(client, seed, admin):
    assert client.put("/api/maintenance/9999/complete", headers=admin).status_code == 404


# ── business rules ────────────────────────────────────────────
def test_completing_an_already_completed_task_returns_409(client, seed, admin):
    tid = _task_id(client, admin)
    assert client.put(f"/api/maintenance/{tid}/complete", headers=admin).status_code == 200

    res = client.put(f"/api/maintenance/{tid}/complete", headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == "Task is already completed"


def test_updating_status_to_completed_stamps_completed_at(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}", json={"status": "COMPLETED"}, headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None


def test_reopening_a_completed_task_clears_completed_at(client, seed, admin):
    tid = _task_id(client, admin)
    client.put(f"/api/maintenance/{tid}/complete", headers=admin)

    res = client.put(f"/api/maintenance/{tid}", json={"status": "PENDING"}, headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "PENDING"
    assert body["completed_at"] is None


# ── validation ────────────────────────────────────────────────
def test_task_requires_a_title(client, seed, admin):
    res = client.post("/api/maintenance/",
                      json={"category": "GENERATOR", "scheduled_date": SCHEDULED},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"


def test_task_requires_a_scheduled_date(client, seed, admin):
    res = client.post("/api/maintenance/",
                      json={"title": "No date", "category": "GENERATOR"},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date is required"


def test_blank_scheduled_date_is_rejected(client, seed, admin):
    res = _create_task(client, admin, scheduled_date="")
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date is required"


def test_day_first_scheduled_date_is_rejected(client, seed, admin):
    res = _create_task(client, admin, scheduled_date="10/08/2026")
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date must be a valid date (YYYY-MM-DD)"


def test_unknown_category_is_rejected(client, seed, admin):
    res = _create_task(client, admin, category="ROOFING")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")


def test_unknown_status_on_update_is_rejected(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}", json={"status": "DONE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("task_status must be one of:")


def test_bad_scheduled_date_on_update_is_rejected(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}",
                     json={"scheduled_date": "not-a-date"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date must be a valid date (YYYY-MM-DD)"


def test_non_numeric_assignee_is_rejected(client, seed, admin):
    res = _create_task(client, admin, assigned_to="ramesh")
    assert res.status_code == 400
    assert res.get_json()["error"] == "assigned_to must be a whole number"


def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/maintenance/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"


def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/maintenance/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"


# ── authorization ─────────────────────────────────────────────
def test_maintenance_requires_authentication(client, seed):
    assert client.get("/api/maintenance/").status_code == 401
    assert client.post("/api/maintenance/", json={"title": "x"}).status_code == 401


def test_resident_can_read_the_task_list(client, seed, admin, resident):
    _create_task(client, admin)
    res = client.get("/api/maintenance/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_worker_cannot_create_a_task(client, seed, worker):
    res = _create_task(client, worker)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_resident_cannot_update_complete_or_delete_a_task(client, seed, admin, resident):
    tid = _task_id(client, admin)
    assert client.put(f"/api/maintenance/{tid}", json={"title": "x"},
                      headers=resident).status_code == 403
    assert client.put(f"/api/maintenance/{tid}/complete", headers=resident).status_code == 403
    assert client.delete(f"/api/maintenance/{tid}", headers=resident).status_code == 403
