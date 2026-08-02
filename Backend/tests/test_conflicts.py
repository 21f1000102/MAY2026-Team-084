"""Neighbour conflict resolver: /api/conflicts.

The anonymity guarantee is the point of this feature: only society management
may ever see who filed a report. Also covers the one-response / one-resolution
rules and the check that only the reported flat may respond.

Seed layout: the tenant lives in A-101; the worker has no flat, so the worker
can report A-101 and the tenant is then the accused flat.
"""


def _raise_conflict(client, headers, apartment_id, **overrides):
    """POST a conflict report and return the flask response."""
    payload = {
        "reported_apartment_id": apartment_id,
        "category": "NOISE",
        "description": "Loud music after 11pm on weekdays.",
    }
    payload.update(overrides)
    return client.post("/api/conflicts/", json=payload, headers=headers)


def _report_against_resident_flat(client, seed, worker):
    """A report filed by the worker against A-101, where the tenant lives."""
    return _raise_conflict(client, worker, seed["apartment_id"]).get_json()["report_id"]


# ── happy path ────────────────────────────────────────────────
def test_resident_can_raise_a_conflict_against_another_flat(client, seed, resident):
    res = _raise_conflict(client, resident, seed["other_apartment_id"])
    assert res.status_code == 201
    body = res.get_json()
    assert body["report_id"] > 0
    assert "anonymously" in body["message"]


def test_admin_sees_every_report_with_the_reporter_named(client, seed, resident, admin):
    _raise_conflict(client, resident, seed["other_apartment_id"])

    res = client.get("/api/conflicts/", headers=admin)
    assert res.status_code == 200
    report = res.get_json()[0]
    assert report["reported_by"] == seed["resident_id"]
    assert report["reported_by_name"] == "Ravi Resident"
    assert report["reported_flat"] == "B-202"
    assert report["status"] == "OPEN"


def test_reported_flat_can_submit_its_side(client, seed, worker, resident):
    rid = _report_against_resident_flat(client, seed, worker)

    res = client.put(f"/api/conflicts/{rid}/respond",
                     json={"response": "The music was for a birthday, sorry."},
                     headers=resident)
    assert res.status_code == 200
    assert res.get_json()["message"].startswith("Response submitted")

    report = client.get("/api/conflicts/", headers=resident).get_json()[0]
    assert report["status"] == "UNDER_REVIEW"
    assert report["reported_flat_response"] == "The music was for a birthday, sorry."
    assert report["response_submitted_at"] is not None


def test_admin_can_resolve_a_report(client, seed, resident, admin):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]

    res = client.put(f"/api/conflicts/{rid}/resolve",
                     json={"resolution_note": "Both parties agreed on quiet hours."},
                     headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Conflict resolved"
    assert body["report"]["status"] == "RESOLVED"
    assert body["report"]["resolution_note"] == "Both parties agreed on quiet hours."
    assert body["report"]["resolved_at"] is not None


def test_resolution_note_defaults_when_not_supplied(client, seed, resident, admin):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    body = client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin).get_json()
    assert body["report"]["resolution_note"] == "Resolved by secretary"


def test_pending_lists_open_and_under_review_reports_for_admin(client, seed,
                                                               worker, resident, admin):
    open_id = _raise_conflict(client, resident,
                              seed["other_apartment_id"]).get_json()["report_id"]
    reviewing_id = _report_against_resident_flat(client, seed, worker)
    client.put(f"/api/conflicts/{reviewing_id}/respond",
               json={"response": "Noted."}, headers=resident)

    resolved_id = _raise_conflict(client, worker,
                                  seed["other_apartment_id"]).get_json()["report_id"]
    client.put(f"/api/conflicts/{resolved_id}/resolve", json={}, headers=admin)

    res = client.get("/api/conflicts/pending", headers=admin)
    assert res.status_code == 200
    ids = {r["id"] for r in res.get_json()}
    assert ids == {open_id, reviewing_id}


def test_responding_to_a_missing_report_returns_404(client, seed, admin):
    assert client.put("/api/conflicts/9999/respond", json={"response": "hi"},
                      headers=admin).status_code == 404


# ── anonymity ─────────────────────────────────────────────────
def test_resident_view_never_exposes_the_reporter(client, seed, worker, resident):
    """The accused flat must not learn who reported them."""
    _report_against_resident_flat(client, seed, worker)

    res = client.get("/api/conflicts/", headers=resident)
    assert res.status_code == 200
    reports = res.get_json()
    assert len(reports) == 1
    for report in reports:
        assert "reported_by" not in report
        assert "reported_by_name" not in report
    assert reports[0]["description"] == "Loud music after 11pm on weekdays."


def test_reporter_own_report_is_also_returned_without_identity_fields(client, seed, resident):
    _raise_conflict(client, resident, seed["other_apartment_id"])

    report = client.get("/api/conflicts/", headers=resident).get_json()[0]
    assert "reported_by" not in report
    assert "reported_by_name" not in report


def test_resident_cannot_see_unrelated_reports(client, seed, worker, resident):
    _raise_conflict(client, worker, seed["other_apartment_id"])
    assert client.get("/api/conflicts/", headers=resident).get_json() == []


def test_pending_is_admin_only(client, seed, resident, worker):
    """This endpoint reveals reporter identities, so residents get a 403."""
    res = client.get("/api/conflicts/pending", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
    assert client.get("/api/conflicts/pending", headers=worker).status_code == 403


# ── business rules ────────────────────────────────────────────
def test_reporting_your_own_flat_is_rejected(client, seed, resident):
    res = _raise_conflict(client, resident, seed["apartment_id"])
    assert res.status_code == 400
    assert res.get_json()["error"] == "You cannot raise a conflict against your own flat"


def test_reporting_an_unknown_flat_returns_404(client, seed, resident):
    res = _raise_conflict(client, resident, 9999)
    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"


def test_a_user_from_another_flat_cannot_respond(client, seed, resident):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]

    res = client.put(f"/api/conflicts/{rid}/respond",
                     json={"response": "Not my problem"}, headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "Only the reported flat can respond to this report"


def test_a_user_with_no_flat_cannot_respond(client, seed, worker, resident):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    assert client.put(f"/api/conflicts/{rid}/respond", json={"response": "x"},
                      headers=worker).status_code == 403


def test_responding_twice_returns_409(client, seed, worker, resident):
    rid = _report_against_resident_flat(client, seed, worker)
    assert client.put(f"/api/conflicts/{rid}/respond", json={"response": "First"},
                      headers=resident).status_code == 200

    res = client.put(f"/api/conflicts/{rid}/respond", json={"response": "Second"},
                     headers=resident)
    assert res.status_code == 409
    assert res.get_json()["error"] == "A response has already been submitted for this report"


def test_responding_to_a_resolved_report_returns_409(client, seed, worker, resident, admin):
    rid = _report_against_resident_flat(client, seed, worker)
    client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin)

    res = client.put(f"/api/conflicts/{rid}/respond", json={"response": "Too late"},
                     headers=resident)
    assert res.status_code == 409
    assert res.get_json()["error"] == "This report has already been resolved"


def test_resolving_twice_returns_409(client, seed, resident, admin):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    assert client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin).status_code == 200

    res = client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == "This report is already resolved"


# ── validation ────────────────────────────────────────────────
def test_conflict_requires_a_description(client, seed, resident):
    res = client.post("/api/conflicts/",
                      json={"reported_apartment_id": seed["other_apartment_id"],
                            "category": "NOISE"},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "description is required"


def test_conflict_requires_a_reported_apartment(client, seed, resident):
    res = client.post("/api/conflicts/",
                      json={"category": "NOISE", "description": "Noisy"},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "reported_apartment_id is required"


def test_unknown_category_is_rejected(client, seed, resident):
    res = _raise_conflict(client, resident, seed["other_apartment_id"], category="SHOUTING")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")


def test_non_numeric_apartment_id_is_rejected(client, seed, resident):
    res = _raise_conflict(client, resident, "B-202")
    assert res.status_code == 400
    assert res.get_json()["error"] == "reported_apartment_id must be a whole number"


def test_response_text_is_required(client, seed, worker, resident):
    rid = _report_against_resident_flat(client, seed, worker)
    res = client.put(f"/api/conflicts/{rid}/respond", json={}, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "response is required"


def test_null_body_is_rejected(client, seed, resident):
    res = client.post("/api/conflicts/", data="null",
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"


def test_list_body_is_rejected(client, seed, resident):
    res = client.post("/api/conflicts/", data="[]",
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"


# ── authorization ─────────────────────────────────────────────
def test_conflicts_require_authentication(client, seed):
    assert client.get("/api/conflicts/").status_code == 401
    assert client.post("/api/conflicts/", json={}).status_code == 401
    assert client.get("/api/conflicts/pending").status_code == 401
    assert client.put("/api/conflicts/1/resolve", json={}).status_code == 401


def test_resident_cannot_resolve_a_report(client, seed, resident):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    res = client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
