"""
Shared pytest fixtures for the SocietyEase API test suite.

Each test gets a fresh, isolated SQLite database in a temp file, so tests never
touch instance/societyease.db and never leak state into one another.

Why a temp file and not sqlite:///:memory: — an in-memory SQLite database lives
for the lifetime of a single connection, so the tables created on one pooled
connection are invisible to the next one and every request fails with
"no such table: users".
"""
import io as _io
import json as _json
import os
import re as _re
import sys
import tempfile

import pytest
from flask.testing import FlaskClient

# Make the Backend package importable however pytest is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config                                  # noqa: E402
from app import create_app                                 # noqa: E402
from models import db, Apartment, User, Resident           # noqa: E402
from werkzeug.security import generate_password_hash       # noqa: E402

TEST_SECRET = "societyease-test-secret-key-long-enough-for-hs256"
# scrypt (the production default) costs ~100ms per call; with 6 seeded users and
# a login each, that dominated the suite runtime. Tests only need the hashing
# round-trip to work, not to be slow.
FAST_HASH = "pbkdf2:sha256:1"
PASSWORD = "Pass@123"


# ── application / database ────────────────────────────────────
@pytest.fixture()
def app():
    """A fresh app bound to its own throwaway database file."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="societyease-test-")
    os.close(fd)

    # create_app() reads Config at call time and calls db.create_all(), so the
    # URI has to be set *before* the app is built.
    original_uri = Config.SQLALCHEMY_DATABASE_URI
    original_secret = Config.JWT_SECRET_KEY
    Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{path}"
    Config.JWT_SECRET_KEY = TEST_SECRET
    try:
        application = create_app()
        application.config.update(TESTING=True)
        with application.app_context():
            db.create_all()
            yield application
            db.session.remove()
            db.engine.dispose()
    finally:
        Config.SQLALCHEMY_DATABASE_URI = original_uri
        Config.JWT_SECRET_KEY = original_secret
        try:
            os.unlink(path)
        except OSError:
            pass   # Windows may still hold the handle; the temp dir is cleaned anyway


# ── request/response recording ────────────────────────────────
# Every API call made through the test client is logged with its real request
# and real response, so docs/TEST_CASES.md can show what was actually sent and
# what actually came back instead of a hand-written "as expected".
API_LOG = []
_CURRENT = {"nodeid": None}
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_api_log.json")


def _shorten(value, limit=400):
    text = value if isinstance(value, str) else _json.dumps(value, default=str)
    # JWTs and password hashes are long and add nothing to the report.
    text = _re.sub(r'"(token)":\s*"eyJ[\w.\-]+"', r'"\1": "<jwt>"', text)
    text = _re.sub(r'"(password)":\s*"[^"]*"', r'"\1": "<hidden>"', text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


class RecordingClient(FlaskClient):
    """Flask test client that records each call for the test-case report."""

    def open(self, *args, **kwargs):
        method = (kwargs.get("method") or (args[1] if len(args) > 1 else "GET")).upper()
        path = kwargs.get("path") or (args[0] if args else "")

        if "json" in kwargs:
            body = _shorten(kwargs["json"])
        elif kwargs.get("data") is not None:
            body = _shorten(kwargs["data"])
        else:
            body = ""

        headers = kwargs.get("headers") or {}
        authed = bool(isinstance(headers, dict) and headers.get("Authorization"))

        response = super().open(*args, **kwargs)

        try:
            payload = response.get_json()
            out = "" if payload is None else _shorten(payload)
        except Exception:
            out = _shorten((response.data or b"")[:200].decode("utf-8", "replace"))

        API_LOG.append({
            "nodeid": _CURRENT["nodeid"],
            "method": method,
            "path": str(path),
            "request": body,
            "authenticated": authed,
            "status": response.status_code,
            "response": out,
        })
        return response


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    _CURRENT["nodeid"] = item.nodeid


def pytest_sessionfinish(session, exitstatus):
    """Persist the captured calls for tests/report.py."""
    try:
        with _io.open(LOG_PATH, "w", encoding="utf-8") as fh:
            _json.dump(API_LOG, fh, indent=1, default=str)
    except OSError:
        pass


@pytest.fixture()
def client(app):
    app.test_client_class = RecordingClient
    return app.test_client()


# ── seed data ─────────────────────────────────────────────────
ROLE_USERS = {
    "admin":     ("Priya Admin",      "admin@test.com",     "ADMIN"),
    "treasurer": ("Tarun Treasurer",  "treasurer@test.com", "TREASURER"),
    "committee": ("Chitra Committee", "committee@test.com", "COMMITTEE_MEMBER"),
    "resident":  ("Ravi Resident",    "resident@test.com",  "TENANT"),
    "owner":     ("Ojas Owner",       "owner@test.com",     "OWNER"),
    "worker":    ("Ramesh Worker",    "worker@test.com",    "WORKER"),
}


@pytest.fixture()
def seed(app):
    """Two flats and one user per role; the tenant lives in A-101.

    Returns a dict of ids so tests don't have to re-query.
    """
    with app.app_context():
        apartment = Apartment(flat_number="A-101", block="A", floor=1)
        second = Apartment(flat_number="B-202", block="B", floor=2)
        db.session.add_all([apartment, second])
        db.session.flush()

        ids = {"apartment_id": apartment.id, "other_apartment_id": second.id}
        for key, (name, email, role) in ROLE_USERS.items():
            user = User(
                name=name, email=email, role=role,
                password_hash=generate_password_hash(PASSWORD, method=FAST_HASH),
            )
            db.session.add(user)
            db.session.flush()
            ids[f"{key}_id"] = user.id

        resident = Resident(user_id=ids["resident_id"],
                            apartment_id=apartment.id, is_owner=False)
        db.session.add(resident)
        db.session.flush()
        ids["resident_record_id"] = resident.id

        db.session.commit()
        return ids


# ── auth helpers ──────────────────────────────────────────────
def login(client, email, password=PASSWORD):
    """Log in and return the raw JWT."""
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"login failed for {email}: {res.get_json()}"
    return res.get_json()["token"]


def auth(token):
    """Authorization header dict for a token."""
    return {"Authorization": f"Bearer {token}"}


def _role_header(client, key):
    return auth(login(client, ROLE_USERS[key][1]))


# One fixture per role. Each logs in only the role it needs, so a test that
# wants a single token doesn't pay for six.
@pytest.fixture()
def admin(client, seed):
    return _role_header(client, "admin")


@pytest.fixture()
def treasurer(client, seed):
    return _role_header(client, "treasurer")


@pytest.fixture()
def committee(client, seed):
    return _role_header(client, "committee")


@pytest.fixture()
def resident(client, seed):
    return _role_header(client, "resident")


@pytest.fixture()
def owner(client, seed):
    return _role_header(client, "owner")


@pytest.fixture()
def worker(client, seed):
    return _role_header(client, "worker")


@pytest.fixture()
def tokens(client, seed):
    """All six raw tokens, for tests that genuinely need several roles."""
    return {key: login(client, email) for key, (_n, email, _r) in ROLE_USERS.items()}
