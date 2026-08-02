"""Poll / voting endpoints: /api/polls.

Focuses on the rules that were previously broken: end_date is mandatory,
`options` must be a real list (a bare string used to become one option per
character), a second vote is a 409, and `has_voted` is reported from the
database rather than kept in frontend state.
"""
from datetime import date, timedelta


TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
NEXT_WEEK = TODAY + timedelta(days=7)


def _create_poll(client, headers, **overrides):
    """POST a valid, currently-open poll and return the flask response."""
    payload = {
        "title": "New gym equipment?",
        "description": "Should we buy a treadmill?",
        "options": ["Yes", "No"],
        "end_date": str(NEXT_WEEK),
    }
    payload.update(overrides)
    return client.post("/api/polls/", json=payload, headers=headers)


def _open_poll(client, headers, **overrides):
    """Create a poll and return (poll_id, first_option_id)."""
    body = _create_poll(client, headers, **overrides).get_json()
    return body["id"], body["options"][0]["id"]


# ── happy path ────────────────────────────────────────────────
def test_admin_can_create_a_poll_with_options(client, seed, admin):
    res = _create_poll(client, admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "New gym equipment?"
    assert body["status"] == "ACTIVE"
    assert [o["text"] for o in body["options"]] == ["Yes", "No"]
    assert body["total_votes"] == 0
    assert body["has_voted"] is False


def test_start_date_defaults_to_today_when_omitted(client, seed, admin):
    body = _create_poll(client, admin).get_json()
    assert body["start_date"] == str(TODAY)
    assert body["end_date"] == str(NEXT_WEEK)


def test_explicit_start_date_is_kept(client, seed, admin):
    body = _create_poll(client, admin, start_date=str(TODAY - timedelta(days=2))).get_json()
    assert body["start_date"] == str(TODAY - timedelta(days=2))


def test_single_poll_can_be_fetched(client, seed, admin):
    pid, _ = _open_poll(client, admin)
    res = client.get(f"/api/polls/{pid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["id"] == pid


def test_resident_can_vote_and_results_are_tallied(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin)

    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 200
    poll = res.get_json()["poll"]
    assert poll["total_votes"] == 1
    voted_option = next(o for o in poll["options"] if o["id"] == option_id)
    assert voted_option["votes"] == 1
    assert voted_option["percentage"] == 100.0


def test_admin_can_close_a_poll(client, seed, admin):
    pid, _ = _open_poll(client, admin)
    res = client.put(f"/api/polls/{pid}/close", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["poll"]["status"] == "CLOSED"


def test_admin_can_delete_a_poll(client, seed, admin):
    pid, _ = _open_poll(client, admin)
    assert client.delete(f"/api/polls/{pid}", headers=admin).status_code == 200
    assert client.get(f"/api/polls/{pid}", headers=admin).status_code == 404


# ── has_voted reporting ───────────────────────────────────────
def test_poll_list_reports_has_voted_per_user(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin)

    before = client.get("/api/polls/", headers=resident).get_json()[0]
    assert before["has_voted"] is False
    assert before["my_option_id"] is None

    client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id}, headers=resident)

    after = client.get("/api/polls/", headers=resident).get_json()[0]
    assert after["has_voted"] is True
    assert after["my_option_id"] == option_id

    # another user's view is unaffected
    other = client.get("/api/polls/", headers=admin).get_json()[0]
    assert other["has_voted"] is False


# ── business rules ────────────────────────────────────────────
def test_voting_twice_returns_409(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin)
    assert client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                       headers=resident).status_code == 200

    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 409
    assert res.get_json()["error"] == "You have already voted"


def test_voting_on_a_closed_poll_is_rejected(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin)
    client.put(f"/api/polls/{pid}/close", headers=admin)

    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Poll is not active"


def test_voting_before_the_window_opens_is_rejected(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin,
                                start_date=str(TOMORROW),
                                end_date=str(NEXT_WEEK))
    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("Voting opens on")


def test_voting_after_the_window_closes_is_rejected(client, seed, admin, resident):
    yesterday = TODAY - timedelta(days=1)
    pid, option_id = _open_poll(client, admin,
                                start_date=str(TODAY - timedelta(days=5)),
                                end_date=str(yesterday))
    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("Voting closed on")


def test_voting_for_an_option_of_another_poll_is_rejected(client, seed, admin, resident):
    _pid_a, option_a = _open_poll(client, admin, title="Poll A")
    pid_b, _option_b = _open_poll(client, admin, title="Poll B")

    res = client.post(f"/api/polls/{pid_b}/vote", json={"option_id": option_a},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Invalid option"


# ── validation ────────────────────────────────────────────────
def test_poll_requires_an_end_date(client, seed, admin):
    res = client.post("/api/polls/",
                      json={"title": "No deadline", "options": ["Yes", "No"]},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "end_date is required"


def test_poll_requires_a_title(client, seed, admin):
    res = client.post("/api/polls/",
                      json={"options": ["Yes", "No"], "end_date": str(NEXT_WEEK)},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"


def test_options_given_as_a_string_are_rejected(client, seed, admin):
    """"abc" used to be split into three single-letter options."""
    res = _create_poll(client, admin, options="abc")
    assert res.status_code == 400
    assert res.get_json()["error"] == "options must be a list"


def test_missing_options_are_rejected(client, seed, admin):
    res = client.post("/api/polls/",
                      json={"title": "No options", "end_date": str(NEXT_WEEK)},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "options must be a list"


def test_fewer_than_two_options_are_rejected(client, seed, admin):
    res = _create_poll(client, admin, options=["Only one"])
    assert res.status_code == 400
    assert res.get_json()["error"] == "At least 2 options required"


def test_blank_options_do_not_count_towards_the_minimum(client, seed, admin):
    res = _create_poll(client, admin, options=["Yes", "   ", None])
    assert res.status_code == 400
    assert res.get_json()["error"] == "At least 2 options required"


def test_unparseable_end_date_is_rejected(client, seed, admin):
    res = _create_poll(client, admin, end_date="31-12-2026")
    assert res.status_code == 400
    assert res.get_json()["error"] == "end_date must be a valid date (YYYY-MM-DD)"


def test_end_date_before_start_date_is_rejected(client, seed, admin):
    res = _create_poll(client, admin,
                       start_date=str(NEXT_WEEK), end_date=str(TODAY))
    assert res.status_code == 400
    assert res.get_json()["error"] == "end_date cannot be before start_date"


def test_unknown_status_is_rejected(client, seed, admin):
    res = _create_poll(client, admin, status="PENDING")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("vote_status must be one of:")


def test_vote_requires_an_option_id(client, seed, admin, resident):
    pid, _ = _open_poll(client, admin)
    res = client.post(f"/api/polls/{pid}/vote", json={}, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "option_id is required"


def test_non_numeric_option_id_is_rejected(client, seed, admin, resident):
    pid, _ = _open_poll(client, admin)
    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": "abc"}, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "option_id must be a whole number"


def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/polls/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"


def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/polls/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"


# ── authorization ─────────────────────────────────────────────
def test_polls_require_authentication(client, seed):
    assert client.get("/api/polls/").status_code == 401
    assert client.post("/api/polls/", json={"title": "x"}).status_code == 401


def test_resident_can_read_the_poll_list(client, seed, admin, resident):
    _create_poll(client, admin)
    res = client.get("/api/polls/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_resident_cannot_create_close_or_delete_a_poll(client, seed, admin, resident):
    pid, _ = _open_poll(client, admin)

    created = _create_poll(client, resident, title="Resident poll")
    assert created.status_code == 403
    assert created.get_json()["error"] == "You are not allowed to perform this action"

    assert client.put(f"/api/polls/{pid}/close", headers=resident).status_code == 403
    assert client.delete(f"/api/polls/{pid}", headers=resident).status_code == 403
