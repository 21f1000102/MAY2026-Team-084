"""GET /api/members/workers/<id>/work-history — a worker's completed jobs,
readable by that worker or an admin only."""
from datetime import date, timedelta


def test_worker_sees_own_completed_work(client, admin, worker, seed):
    task = client.post("/api/maintenance/", json={
        "title": "Generator service", "category": "GENERATOR",
        "scheduled_date": str(date.today() + timedelta(days=1)),
        "assigned_to": seed["worker_id"],
    }, headers=admin).get_json()
    client.put(f"/api/maintenance/{task['id']}/complete", headers=worker)

    complaint = client.post("/api/complaints/", json={
        "title": "Leaking tap", "category": "PLUMBING",
        "apartment_id": seed["apartment_id"],
    }, headers=admin).get_json()
    client.put(f"/api/complaints/{complaint['id']}/assign",
              json={"worker_id": seed["worker_id"]}, headers=admin)
    client.put(f"/api/complaints/{complaint['id']}/status",
              json={"status": "IN_PROGRESS"}, headers=worker)
    client.put(f"/api/complaints/{complaint['id']}/status",
              json={"status": "COMPLETED"}, headers=worker)

    res = client.get(f"/api/members/workers/{seed['worker_id']}/work-history", headers=worker)
    assert res.status_code == 200
    body = res.get_json()
    assert body["totals"]["maintenance"] == 1
    assert body["totals"]["complaints"] == 1
    assert body["totals"]["total"] == 2


def test_admin_can_view_any_workers_history(client, admin, seed):
    res = client.get(f"/api/members/workers/{seed['worker_id']}/work-history", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["user_id"] == seed["worker_id"]


def test_resident_cannot_view_worker_history(client, resident, seed):
    res = client.get(f"/api/members/workers/{seed['worker_id']}/work-history", headers=resident)
    assert res.status_code == 403


def test_worker_cannot_view_another_workers_history(client, admin, worker, seed):
    other = client.post("/api/members/", json={
        "name": "Other Worker", "email": "other2@x.com", "password": "Pass@123",
        "role": "WORKER", "apartment_id": seed["apartment_id"],
    }, headers=admin).get_json()

    res = client.get(f"/api/members/workers/{other['user_id']}/work-history", headers=worker)
    assert res.status_code == 403


def test_non_worker_user_id_returns_400(client, admin, seed):
    res = client.get(f"/api/members/workers/{seed['admin_id']}/work-history", headers=admin)
    assert res.status_code == 400
