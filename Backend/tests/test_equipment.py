"""Equipment register and service forecast: /api/equipment.

The important regressions here are a service_frequency_days of 0 (which used
to divide by zero on every subsequent read) and a blank cost when logging a
service (which used to error instead of being treated as "not recorded").
"""
from datetime import date, timedelta


def _create_equipment(client, headers, **overrides):
    """POST a valid piece of equipment and return the flask response."""
    payload = {
        "name": "Diesel Generator",
        "category": "GENERATOR",
        "last_serviced_date": str(date.today() - timedelta(days=10)),
        "service_frequency_days": 90,
        "estimated_service_cost": 4500,
    }
    payload.update(overrides)
    return client.post("/api/equipment/", json=payload, headers=headers)


def _equipment_id(client, headers, **overrides):
    return _create_equipment(client, headers, **overrides).get_json()["id"]


# ── happy path ────────────────────────────────────────────────
def test_admin_can_add_equipment(client, seed, admin):
    res = _create_equipment(client, admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["name"] == "Diesel Generator"
    assert body["category"] == "GENERATOR"
    assert body["service_frequency_days"] == 90
    assert body["estimated_service_cost"] == 4500.0
    assert body["days_until_due"] == 80
    assert body["risk_level"] == "LOW"


def test_equipment_list_is_readable(client, seed, admin):
    _create_equipment(client, admin)
    res = client.get("/api/equipment/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_overdue_equipment_reports_negative_days_and_high_risk(client, seed, admin):
    body = _create_equipment(
        client, admin,
        last_serviced_date=str(date.today() - timedelta(days=120)),
        service_frequency_days=90,
    ).get_json()
    assert body["days_until_due"] == -30
    assert body["risk_level"] == "HIGH"


def test_equipment_nearing_its_due_date_is_medium_risk(client, seed, admin):
    body = _create_equipment(
        client, admin,
        last_serviced_date=str(date.today() - timedelta(days=85)),
        service_frequency_days=100,
    ).get_json()
    assert body["risk_level"] == "MEDIUM"


def test_marking_serviced_updates_the_last_serviced_date(client, seed, admin):
    eid = _equipment_id(client, admin)
    res = client.put(f"/api/equipment/{eid}/service",
                     json={"cost": 5000, "vendor_name": "PowerCare",
                           "notes": "Oil and filter changed"},
                     headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Equipment marked as serviced"
    assert body["equipment"]["last_serviced_date"] == str(date.today())
    assert body["equipment"]["days_until_due"] == 90


def test_service_can_be_backdated(client, seed, admin):
    eid = _equipment_id(client, admin)
    backdate = str(date.today() - timedelta(days=5))
    res = client.put(f"/api/equipment/{eid}/service",
                     json={"serviced_date": backdate}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["equipment"]["last_serviced_date"] == backdate


def test_service_history_lists_logged_services(client, seed, admin):
    eid = _equipment_id(client, admin)
    client.put(f"/api/equipment/{eid}/service",
               json={"cost": 5000, "vendor_name": "PowerCare"}, headers=admin)

    res = client.get(f"/api/equipment/{eid}/history", headers=admin)
    assert res.status_code == 200
    logs = res.get_json()
    assert len(logs) == 1
    assert logs[0]["cost"] == 5000.0
    assert logs[0]["vendor_name"] == "PowerCare"
    assert logs[0]["logged_by_name"] == "Priya Admin"


def test_history_of_unserviced_equipment_is_empty(client, seed, admin):
    eid = _equipment_id(client, admin)
    assert client.get(f"/api/equipment/{eid}/history", headers=admin).get_json() == []


def test_forecast_returns_items_due_within_30_days(client, seed, admin):
    _create_equipment(client, admin, name="Lift", category="LIFT",
                      last_serviced_date=str(date.today() - timedelta(days=80)),
                      service_frequency_days=90, estimated_service_cost=2000)
    _create_equipment(client, admin, name="Fire panel", category="FIRE_SAFETY",
                      last_serviced_date=str(date.today()),
                      service_frequency_days=365, estimated_service_cost=999)

    res = client.get("/api/equipment/forecast", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["count"] == 1
    assert body["due_in_30_days"][0]["name"] == "Lift"
    assert body["due_in_30_days"][0]["days_until_due"] == 10
    assert body["total_estimated_cost"] == 2000.0


def test_forecast_works_with_no_equipment(client, seed, admin):
    res = client.get("/api/equipment/forecast", headers=admin)
    assert res.status_code == 200
    assert res.get_json() == {"due_in_30_days": [], "total_estimated_cost": 0, "count": 0}


def test_admin_can_delete_equipment(client, seed, admin):
    eid = _equipment_id(client, admin)
    res = client.delete(f"/api/equipment/{eid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Equipment deleted"
    assert client.get("/api/equipment/", headers=admin).get_json() == []


def test_history_of_missing_equipment_returns_404(client, seed, admin):
    assert client.get("/api/equipment/9999/history", headers=admin).status_code == 404


# ── validation ────────────────────────────────────────────────
def test_equipment_requires_a_name(client, seed, admin):
    res = client.post("/api/equipment/",
                      json={"category": "GENERATOR",
                            "last_serviced_date": str(date.today()),
                            "service_frequency_days": 90},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "name is required"


def test_equipment_requires_a_last_serviced_date(client, seed, admin):
    res = client.post("/api/equipment/",
                      json={"name": "Pump", "category": "OTHER",
                            "service_frequency_days": 30},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "last_serviced_date is required"


def test_blank_last_serviced_date_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, last_serviced_date="")
    assert res.status_code == 400
    assert res.get_json()["error"] == "last_serviced_date is required"


def test_bad_last_serviced_date_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, last_serviced_date="10/08/2026")
    assert res.status_code == 400
    assert res.get_json()["error"] == "last_serviced_date must be a valid date (YYYY-MM-DD)"


def test_zero_service_frequency_is_rejected(client, seed, admin):
    """A 0 frequency used to be stored and then divided by on every GET."""
    res = _create_equipment(client, admin, service_frequency_days=0)
    assert res.status_code == 400
    assert res.get_json()["error"] == "service_frequency_days must be at least 1"


def test_zero_service_frequency_as_a_string_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, service_frequency_days="0")
    assert res.status_code == 400
    assert res.get_json()["error"] == "service_frequency_days must be at least 1"


def test_missing_service_frequency_is_rejected(client, seed, admin):
    res = client.post("/api/equipment/",
                      json={"name": "Pump", "category": "OTHER",
                            "last_serviced_date": str(date.today())},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "service_frequency_days is required"


def test_negative_estimated_cost_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, estimated_service_cost=-1)
    assert res.status_code == 400
    assert res.get_json()["error"] == "estimated_service_cost must be at least 0"


def test_unknown_category_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, category="ROBOT")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")


def test_blank_cost_when_marking_serviced_is_accepted(client, seed, admin):
    """An empty cost box in the UI must mean "not recorded", not an error."""
    eid = _equipment_id(client, admin)
    res = client.put(f"/api/equipment/{eid}/service", json={"cost": ""}, headers=admin)
    assert res.status_code == 200

    logs = client.get(f"/api/equipment/{eid}/history", headers=admin).get_json()
    assert logs[0]["cost"] is None


def test_non_numeric_cost_when_marking_serviced_is_rejected(client, seed, admin):
    eid = _equipment_id(client, admin)
    res = client.put(f"/api/equipment/{eid}/service", json={"cost": "five"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "cost must be a number"


def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/equipment/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"


def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/equipment/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"


# ── authorization ─────────────────────────────────────────────
def test_equipment_requires_authentication(client, seed):
    assert client.get("/api/equipment/").status_code == 401
    assert client.get("/api/equipment/forecast").status_code == 401
    assert client.post("/api/equipment/", json={"name": "x"}).status_code == 401


def test_resident_can_read_equipment_and_forecast(client, seed, admin, resident):
    _create_equipment(client, admin)
    assert client.get("/api/equipment/", headers=resident).status_code == 200
    assert client.get("/api/equipment/forecast", headers=resident).status_code == 200


def test_resident_cannot_add_service_or_delete_equipment(client, seed, admin, resident):
    eid = _equipment_id(client, admin)

    created = _create_equipment(client, resident, name="Sneaky pump")
    assert created.status_code == 403
    assert created.get_json()["error"] == "You are not allowed to perform this action"

    assert client.put(f"/api/equipment/{eid}/service", json={},
                      headers=resident).status_code == 403
    assert client.delete(f"/api/equipment/{eid}", headers=resident).status_code == 403
