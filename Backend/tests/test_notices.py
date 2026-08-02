"""Notice-board endpoints: /api/notices.

Covers the happy path for every verb, input validation (missing fields,
unknown category, malformed bodies) and the authorization split between
society-management roles and ordinary residents.
"""


def _create_notice(client, headers, **overrides):
    """POST a valid notice and return the flask response."""
    payload = {"title": "Water shutdown", "content": "No water 9am-1pm on Friday."}
    payload.update(overrides)
    return client.post("/api/notices/", json=payload, headers=headers)


# ── happy path ────────────────────────────────────────────────
def test_admin_can_publish_a_notice(client, seed, admin):
    res = _create_notice(client, admin, category="MAINTENANCE")
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Water shutdown"
    assert body["category"] == "MAINTENANCE"
    assert body["is_active"] is True
    assert body["published_by_name"] == "Priya Admin"


def test_category_defaults_to_general_when_omitted(client, seed, admin):
    body = _create_notice(client, admin).get_json()
    assert body["category"] == "GENERAL"


def test_treasurer_is_also_allowed_to_publish(client, seed, treasurer):
    assert _create_notice(client, treasurer).status_code == 201


def test_notice_list_returns_newest_notices(client, seed, admin):
    _create_notice(client, admin, title="First")
    _create_notice(client, admin, title="Second")

    res = client.get("/api/notices/", headers=admin)
    assert res.status_code == 200
    titles = [n["title"] for n in res.get_json()]
    assert {"First", "Second"} <= set(titles)


def test_admin_can_update_a_notice(client, seed, admin):
    nid = _create_notice(client, admin).get_json()["id"]

    res = client.put(f"/api/notices/{nid}",
                     json={"title": "Water shutdown (revised)", "category": "EMERGENCY"},
                     headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["title"] == "Water shutdown (revised)"
    assert body["category"] == "EMERGENCY"


def test_delete_soft_deletes_and_hides_the_notice_from_the_list(client, seed, admin):
    nid = _create_notice(client, admin, title="Temporary").get_json()["id"]

    res = client.delete(f"/api/notices/{nid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Notice removed"

    titles = [n["title"] for n in client.get("/api/notices/", headers=admin).get_json()]
    assert "Temporary" not in titles


def test_updating_a_missing_notice_returns_404(client, seed, admin):
    assert client.put("/api/notices/9999", json={"title": "x"}, headers=admin).status_code == 404


# ── validation ────────────────────────────────────────────────
def test_notice_without_title_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", json={"content": "body only"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"


def test_notice_without_content_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", json={"title": "title only"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "content is required"


def test_blank_title_is_rejected(client, seed, admin):
    res = _create_notice(client, admin, title="   ")
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"


def test_unknown_category_is_rejected_instead_of_being_stored(client, seed, admin):
    res = _create_notice(client, admin, category="SPAM")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")


def test_unknown_category_on_update_is_rejected(client, seed, admin):
    nid = _create_notice(client, admin).get_json()["id"]
    res = client.put(f"/api/notices/{nid}", json={"category": "NONSENSE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")


def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"


def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"


# ── authorization ─────────────────────────────────────────────
def test_notices_require_authentication(client, seed):
    assert client.get("/api/notices/").status_code == 401
    assert client.post("/api/notices/", json={"title": "a", "content": "b"}).status_code == 401


def test_resident_can_read_notices(client, seed, admin, resident):
    _create_notice(client, admin)
    res = client.get("/api/notices/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_resident_cannot_publish_a_notice(client, seed, resident):
    res = _create_notice(client, resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"


def test_resident_cannot_update_or_delete_a_notice(client, seed, admin, resident):
    nid = _create_notice(client, admin).get_json()["id"]
    assert client.put(f"/api/notices/{nid}", json={"title": "hacked"},
                      headers=resident).status_code == 403
    assert client.delete(f"/api/notices/{nid}", headers=resident).status_code == 403
