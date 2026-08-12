"""Events blueprint: manual society events/meetings plus the merged, role-aware
GET /api/events/upcoming deadlines feed."""
from datetime import date, timedelta


def _event(client, admin, **overrides):
    payload = {"title": "AGM Meeting", "event_type": "MEETING",
              "event_date": str(date.today() + timedelta(days=5))}
    payload.update(overrides)
    res = client.post("/api/events/", json=payload, headers=admin)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


# ── CRUD ──────────────────────────────────────────────────────
def test_admin_can_create_event(client, admin, seed):
    body = _event(client, admin)
    assert body["title"] == "AGM Meeting"
    assert body["event_type"] == "MEETING"
    assert body["id"] is not None


def test_resident_cannot_create_event(client, resident, seed):
    res = client.post("/api/events/", json={
        "title": "Hack", "event_type": "MEETING", "event_date": "2026-09-01",
    }, headers=resident)
    assert res.status_code == 403


def test_resident_can_list_events(client, admin, resident, seed):
    _event(client, admin)
    res = client.get("/api/events/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_missing_title_returns_400(client, admin, seed):
    res = client.post("/api/events/", json={"event_date": "2026-09-01"}, headers=admin)
    assert res.status_code == 400


def test_invalid_event_type_returns_400(client, admin, seed):
    res = client.post("/api/events/", json={
        "title": "X", "event_type": "NOT_REAL", "event_date": "2026-09-01",
    }, headers=admin)
    assert res.status_code == 400


def test_update_event(client, admin, seed):
    event = _event(client, admin)
    res = client.put(f"/api/events/{event['id']}", json={"title": "Updated AGM"}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["title"] == "Updated AGM"


def test_delete_event_is_soft_and_hides_from_list(client, admin, seed):
    event = _event(client, admin)
    res = client.delete(f"/api/events/{event['id']}", headers=admin)
    assert res.status_code == 200

    listing = client.get("/api/events/", headers=admin)
    assert listing.get_json() == []


def test_filter_events_by_type(client, admin, seed):
    _event(client, admin, event_type="MEETING", title="AGM")
    _event(client, admin, event_type="HOLIDAY", title="Diwali")

    res = client.get("/api/events/?event_type=HOLIDAY", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1 and body[0]["title"] == "Diwali"


# ── upcoming feed ─────────────────────────────────────────────
def test_upcoming_includes_manual_event(client, admin, seed):
    _event(client, admin, title="Society Meeting", event_date=str(date.today() + timedelta(days=6)))
    res = client.get("/api/events/upcoming", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert any(item["title"] == "Society Meeting" for item in body)
    item = next(i for i in body if i["title"] == "Society Meeting")
    assert item["days_until"] == 6
    assert item["severity"] == "high"


def test_upcoming_sorted_chronologically(client, admin, seed):
    _event(client, admin, title="Later", event_date=str(date.today() + timedelta(days=20)))
    _event(client, admin, title="Sooner", event_date=str(date.today() + timedelta(days=2)))

    body = client.get("/api/events/upcoming", headers=admin).get_json()
    titles = [i["title"] for i in body]
    assert titles.index("Sooner") < titles.index("Later")


def test_upcoming_includes_own_unpaid_invoice_for_resident(client, admin, resident, seed):
    client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 1500, "due_date": str(date.today() + timedelta(days=4)),
    }, headers=admin)

    res = client.get("/api/events/upcoming", headers=resident)
    assert res.status_code == 200
    body = res.get_json()
    assert any(i["source"] == "invoice" for i in body)


def test_upcoming_excludes_other_flats_invoice_for_resident(client, admin, resident, seed):
    client.post("/api/invoices/", json={
        "apartment_id": seed["other_apartment_id"], "month": 7, "year": 2026,
        "amount": 1500, "due_date": str(date.today() + timedelta(days=4)),
    }, headers=admin)

    res = client.get("/api/events/upcoming", headers=resident)
    assert res.status_code == 200
    assert not any(i["source"] == "invoice" for i in res.get_json())


def test_upcoming_excludes_maintenance_for_resident(client, admin, resident, seed):
    client.post("/api/maintenance/", json={
        "title": "Generator service", "category": "GENERATOR",
        "scheduled_date": str(date.today() + timedelta(days=2)),
    }, headers=admin)

    res = client.get("/api/events/upcoming", headers=resident)
    assert res.status_code == 200
    assert not any(i["source"] == "maintenance" for i in res.get_json())


def test_upcoming_includes_maintenance_for_assigned_worker(client, admin, worker, seed):
    client.post("/api/maintenance/", json={
        "title": "Generator service", "category": "GENERATOR",
        "scheduled_date": str(date.today() + timedelta(days=2)),
        "assigned_to": seed["worker_id"],
    }, headers=admin)

    res = client.get("/api/events/upcoming", headers=worker)
    assert res.status_code == 200
    assert any(i["source"] == "maintenance" for i in res.get_json())


def test_upcoming_days_param_limits_window(client, admin, seed):
    _event(client, admin, title="Far away", event_date=str(date.today() + timedelta(days=60)))
    res = client.get("/api/events/upcoming?days=7", headers=admin)
    assert res.status_code == 200
    assert not any(i["title"] == "Far away" for i in res.get_json())


def test_upcoming_invalid_days_returns_400(client, admin, seed):
    res = client.get("/api/events/upcoming?days=abc", headers=admin)
    assert res.status_code == 400
