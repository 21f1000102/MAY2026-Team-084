"""Society Health Score: /api/health.

Calculating is an admin-only write of the society's official monthly record.
The key regression: an empty society used to be graded against components it
had no data for, producing a meaningless score and an "0 invoices unpaid"
alert. Components with no data must now be excluded from the total.
"""
from datetime import datetime

SHAPE_KEYS = {
    "month", "year", "payment_score", "complaint_score", "notice_score",
    "poll_score", "maintenance_score", "total_score", "alert_reason",
    "has_data", "grade",
}


def _utc_month_year():
    """created_at columns are stamped in UTC, so score that month."""
    now = datetime.utcnow()
    return now.month, now.year


def _post_notice(client, headers, title="Monthly circular"):
    return client.post("/api/notices/",
                       json={"title": title, "content": "Please note."},
                       headers=headers)


# ── happy path ────────────────────────────────────────────────
def test_get_calculate_returns_the_full_score_shape(client, seed, admin):
    res = client.get("/api/health/calculate", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert SHAPE_KEYS <= set(body)
    assert isinstance(body["total_score"], (int, float))
    assert body["grade"] in ("GREEN", "YELLOW", "RED")


def test_post_calculate_uses_the_same_view_as_get(client, seed, admin):
    get_body = client.get("/api/health/calculate", headers=admin).get_json()
    res = client.post("/api/health/calculate", headers=admin)
    assert res.status_code == 200
    post_body = res.get_json()
    assert post_body["month"] == get_body["month"]
    assert post_body["total_score"] == get_body["total_score"]


def test_calculate_accepts_explicit_month_and_year(client, seed, admin):
    res = client.get("/api/health/calculate?month=3&year=2025", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["month"] == 3
    assert body["year"] == 2025


def test_calculate_is_an_upsert_for_the_month(client, seed, admin):
    client.get("/api/health/calculate?month=5&year=2026", headers=admin)
    client.get("/api/health/calculate?month=5&year=2026", headers=admin)

    history = client.get("/api/health/history", headers=admin).get_json()
    assert len([s for s in history if (s["month"], s["year"]) == (5, 2026)]) == 1


def test_history_is_empty_before_anything_is_calculated(client, seed, admin):
    res = client.get("/api/health/history", headers=admin)
    assert res.status_code == 200
    assert res.get_json() == []


def test_history_returns_the_saved_score(client, seed, admin):
    calculated = client.get("/api/health/calculate?month=4&year=2026",
                            headers=admin).get_json()

    res = client.get("/api/health/history", headers=admin)
    assert res.status_code == 200
    saved = res.get_json()[0]
    assert (saved["month"], saved["year"]) == (4, 2026)
    assert saved["total_score"] == calculated["total_score"]
    assert saved["alert_reason"] == calculated["alert_reason"]
    assert saved["grade"] == calculated["grade"]


# ── business rules: empty society ─────────────────────────────
def test_empty_society_is_not_awarded_a_perfect_score(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert body["total_score"] < 100
    assert body["grade"] == "RED"


def test_empty_society_does_not_report_nonsense_invoice_alerts(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert "0 invoices unpaid" not in body["alert_reason"]
    assert "0 complaints unresolved" not in body["alert_reason"]


def test_components_without_data_are_named_as_not_scored(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert "not scored (no data)" in body["alert_reason"]
    for component in ("payment", "complaint", "poll", "maintenance"):
        assert component in body["alert_reason"]


def test_missing_notices_are_flagged(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert body["notice_score"] == 0.0
    assert "No notices posted this month" in body["alert_reason"]


def test_total_is_scaled_over_applicable_components_only(client, seed, admin):
    """Only the notice component has data, so a posted notice is a full score."""
    month, year = _utc_month_year()
    assert _post_notice(client, admin).status_code == 201

    body = client.get(f"/api/health/calculate?month={month}&year={year}",
                      headers=admin).get_json()
    assert body["notice_score"] == 15.0
    assert body["total_score"] == 100.0
    assert body["grade"] == "GREEN"
    assert body["has_data"] is True
    assert "No notices posted this month" not in body["alert_reason"]


# ── validation ────────────────────────────────────────────────
def test_month_above_twelve_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?month=13", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at most 12"


def test_month_below_one_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?month=0", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at least 1"


def test_non_numeric_month_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?month=june", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be a whole number"


def test_year_before_2000_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?year=1999", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "year must be at least 2000"


# ── authorization ─────────────────────────────────────────────
def test_health_endpoints_require_authentication(client, seed):
    assert client.get("/api/health/calculate").status_code == 401
    assert client.post("/api/health/calculate").status_code == 401
    assert client.get("/api/health/history").status_code == 401


def test_resident_cannot_calculate_the_score(client, seed, resident):
    for call in (client.get, client.post):
        res = call("/api/health/calculate", headers=resident)
        assert res.status_code == 403
        assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_worker_cannot_calculate_the_score(client, seed, worker):
    assert client.get("/api/health/calculate", headers=worker).status_code == 403


def test_treasurer_can_calculate_the_score(client, seed, treasurer):
    assert client.get("/api/health/calculate", headers=treasurer).status_code == 200


def test_any_authenticated_user_can_read_the_history(client, seed, admin, resident, worker):
    client.get("/api/health/calculate", headers=admin)
    assert client.get("/api/health/history", headers=resident).status_code == 200
    assert client.get("/api/health/history", headers=worker).status_code == 200
