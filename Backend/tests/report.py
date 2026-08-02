"""
Generate docs/TEST_CASES.md from a REAL pytest run.

The "Actual output" column is filled from the live run, never by hand:

    python tests/report.py

It shells out to `pytest --tb=no -q --junit-xml`, parses the JUnit XML, and
writes the Markdown. Re-running after a code change reproduces the document.
"""
import io
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime, timezone

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)
XML = os.path.join(BACKEND, "tests", "_junit.xml")
OUT = os.path.join(REPO, "docs", "TEST_CASES.md")

MODULE_TITLES = OrderedDict([
    ("test_auth", ("Authentication", "US-08")),
    ("test_members", ("Members & Apartments", "US-09, US-04")),
    ("test_complaints", ("Complaints", "US-02, US-03, US-04")),
    ("test_invoices", ("Invoices & Payments", "US-01, US-05, US-06")),
    ("test_expenses", ("Expenses", "US-14")),
    ("test_notices", ("Notices", "US-10")),
    ("test_polls", ("Polls & Voting", "US-13")),
    ("test_maintenance", ("Maintenance Tasks", "US-11")),
    ("test_equipment", ("Equipment / Maintenance Predictor", "US-15")),
    ("test_health", ("Society Health Score", "US-17")),
    ("test_conflicts", ("Neighbour Conflict Resolver", "US-16")),
    ("test_parking", ("Visitor Parking", "US-12")),
    ("test_emergency", ("Emergency Contacts", "US-07")),
    ("test_regressions", ("Regression suite — defects found by testing", "all")),
])


def humanise(name):
    """test_register_duplicate_phone_returns_409 -> readable input/expectation."""
    text = re.sub(r"^test_", "", name)
    text = re.sub(r"\[.*\]$", "", text)
    return text.replace("_", " ").strip()


def split_expectation(label):
    """Best-effort split of a test name into 'input' and 'expected'."""
    markers = [" returns ", " is rejected", " succeeds", " fails", " must ",
               " returns_", " -> ", " gives "]
    for m in markers:
        if m in label:
            head, _, tail = label.partition(m)
            return head.strip(), (m.strip() + " " + tail).strip()
    return label, "behaves as specified"


def run_pytest():
    print("running pytest ...")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=no", "-q", f"--junit-xml={XML}"],
        cwd=BACKEND, capture_output=True, text=True,
    )
    tail = [l for l in proc.stdout.strip().splitlines() if l.strip()][-1:]
    return proc.returncode, (tail[0] if tail else "")


def parse():
    tree = ET.parse(XML)
    root = tree.getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    cases = []
    for tc in suite.iter("testcase"):
        # pytest emits a dotted classname: "tests.test_auth" or
        # "tests.test_auth.TestRegistration".
        classname = tc.get("classname", "")
        parts = [p for p in classname.split(".") if p and p != "tests"]
        module = parts[0] if parts else ""
        failure = tc.find("failure") or tc.find("error")
        skipped = tc.find("skipped")
        cases.append({
            "module": module,
            "cls": parts[1] if len(parts) > 1 else "",
            "name": tc.get("name", ""),
            "time": float(tc.get("time", 0) or 0),
            "status": "SKIP" if skipped is not None else ("FAIL" if failure is not None else "PASS"),
            "message": (failure.get("message") if failure is not None
                        else (skipped.get("message") if skipped is not None else "")),
        })
    totals = {
        "tests": int(suite.get("tests", 0)),
        "failures": int(suite.get("failures", 0)),
        "errors": int(suite.get("errors", 0)),
        "skipped": int(suite.get("skipped", 0)),
        "time": float(suite.get("time", 0) or 0),
    }
    return cases, totals


DEFECTS = """
## 3. Defects found through testing — where actual differed from expected

The milestone invites us to show cases where the actual output differed from the expected output.
Every entry below is a **real defect that testing caught in our own code**, with the failing
behaviour we observed and the fix. Each now has a permanent regression test in
`Backend/tests/test_regressions.py`, so it cannot come back unnoticed.

| # | API | Input | Expected | **Actual (before fix)** | Root cause | Status |
|---|-----|-------|----------|--------------------------|------------|--------|
| D-01 | `POST /api/auth/register` | `phone` already used by another user | `409 Phone number already registered` | **`500`** — HTML error page, `IntegrityError: UNIQUE constraint failed: users.phone` | `users.phone` is UNIQUE but only `email` was pre-checked | ✅ Fixed |
| D-02 | `POST /api/auth/register` | two sign-ups with `phone: ""` | both `201` | first `201`, second **`500`** | `''` is not `NULL`, so the second blank collided | ✅ Fixed |
| D-03 | `POST /api/expenses/` | `expense_date: "2026-08-01"` | `201` | **`500`** — `TypeError: SQLite Date type only accepts Python date objects` | date strings assigned straight to `db.Date`; no parser existed anywhere | ✅ Fixed |
| D-04 | `POST /api/maintenance/` | `scheduled_date: "2026-08-10"` | `201` | **`500`** (same cause as D-03) | endpoint was 100% unusable | ✅ Fixed |
| D-05 | `POST /api/equipment/` | `last_serviced_date: "2026-06-01"` | `201` | **`500`** (same cause as D-03) | endpoint was 100% unusable | ✅ Fixed |
| D-06 | `POST /api/polls/` | title + 2 options | `201` | **`500`** | `start_date`/`end_date` are `NOT NULL` but neither required nor parsed | ✅ Fixed |
| D-07 | `GET /api/conflicts/pending` | called by a TENANT | `403` | **`200`** + `reported_by_name` for every open report | no role check, and `reveal_reporter=True` — broke the feature's anonymity guarantee | ✅ Fixed |
| D-08 | `PUT /api/complaints/{id}/assign` | `{}` (no `worker_id`) | `400` | **`200`** — status flipped to `ASSIGNED` with `assigned_worker_id = NULL` | no validation; the complaint reached no worker's queue | ✅ Fixed |
| D-09 | `GET /api/complaints/` | called by the assigned WORKER | the assigned job is listed | **`[]`** — always empty | the query filtered on `raised_by` only, so the whole WORKER role was unusable | ✅ Fixed |
| D-10 | `PUT /api/invoices/{id}/pay` | called twice on one invoice | `409` on the second | **`200`** + a second `Payment` row | no idempotency guard; ledger and receipt then disagreed permanently | ✅ Fixed |
| D-11 | `POST /api/equipment/` | `service_frequency_days: "0"` | `400` | **`201`**, then every later `GET /api/equipment/` returned **`500`** | `not "0"` is `False` in Python, so 0 passed validation and caused `ZeroDivisionError` forever | ✅ Fixed |
| D-12 | any endpoint | body `null`, `[]` or `"str"` | `400` | **`500`** — `AttributeError: 'NoneType' object has no attribute 'get'` | `request.get_json()` result used without a type check | ✅ Fixed |
| D-13 | `PUT /api/auth/change-password` | `new_password` omitted | `400` | **`500`** — `KeyError: 'new_password'` | read with `data["..."]` instead of `.get()` | ✅ Fixed |
| D-14 | `POST /api/invoices/` (as TENANT) | any valid body | `403` | **`200`** — invoice created | every mutating endpoint was bare `@jwt_required()`; residents could also mark invoices paid and delete flats | ✅ Fixed |
| D-15 | `DELETE /api/members/apartments/{id}` | flat still has residents | `409` | **`200`** — cascade silently deleted its residents, invoices, payments and complaints | destructive cascade with no guard | ✅ Fixed |

### Still open

| # | API | Expected | Actual | Assessment |
|---|-----|----------|--------|------------|
| **FINDING-10** | any protected endpoint without a token | `{"error": "..."}` — the envelope `openapi.yaml` documents | `{"msg": "Missing Authorization Header"}` | **Open, low severity.** `flask-jwt-extended` emits its own envelope for auth failures, so 401 bodies differ from every other error. The frontend reads `data.error`, so a session-expiry message falls back to generic text. The fix is a few `@jwt.unauthorized_loader`-style handlers in `create_app()`. Left unfixed pending team sign-off; documented in the spec so the contract is not misleading. Test: `test_jwt_401_uses_a_different_error_envelope_than_the_rest_of_the_api` (skipped, with the reason recorded). |

### What testing bought us

Six endpoints (`POST` expenses, maintenance, equipment, polls; plus registration in two ways) were
**completely unusable** — every call returned 500. The empty `expenses`, `maintenance_tasks`,
`equipment` and `votes` tables in the shipped database confirm no user ever succeeded in creating
one. Three defects were security issues: the conflict-anonymity leak (D-07), unrestricted privileged
actions (D-14), and the destructive cascade (D-15). None of these were visible from the UI, because
the frontend swallowed errors — they were only found by asserting on status codes.
"""


def main():
    code, summary = run_pytest()
    cases, totals = parse()
    print(f"pytest: {summary}")

    by_module = OrderedDict((m, []) for m in MODULE_TITLES)
    for c in cases:
        by_module.setdefault(c["module"], []).append(c)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]

    L = []
    w = L.append
    w("# API Test Cases\n")
    w("Automated test cases for the SocietyEase REST API, with the **input**, the **expected "
      "output**, and the **actual output** observed in a real run.\n")
    w("> This document is **generated** by `Backend/tests/report.py` from a live `pytest` run — "
      "the Actual column is never written by hand. Re-run it to reproduce.\n")

    w("## 1. How to run\n")
    w("```bash\ncd Backend\npip install -r requirements.txt\npytest -v                 "
      "# run the suite\npython tests/report.py    # regenerate this document\n```\n")

    w("### Run summary\n")
    w(f"| | |\n|---|---|\n| Generated | {now} |\n| Total test cases | **{totals['tests']}** |\n"
      f"| Passed | **{passed}** |\n| Failed | **{totals['failures'] + totals['errors']}** |\n"
      f"| Skipped | {totals['skipped']} |\n| Duration | {totals['time']:.1f}s |\n"
      f"| pytest exit code | {code} |\n")
    if totals["skipped"]:
        w("\nThe single skipped case is **FINDING-10**, a known open issue documented in "
          "section 3 — it is skipped deliberately rather than silently deleted.\n")

    w("\n### Coverage\n")
    w("| Module | Feature | User stories | Cases |\n|---|---|---|---:|")
    for mod, (title, stories) in MODULE_TITLES.items():
        w(f"| `{mod}.py` | {title} | {stories} | {len(by_module.get(mod, []))} |")
    w(f"| | | **Total** | **{totals['tests']}** |\n")

    w("Every module covers the same four axes: **happy path**, **validation** (missing fields, bad "
      "enums, bad dates, malformed bodies), **authorization** (401 unauthenticated, 403 wrong role), "
      "and **business rules** (duplicates, idempotency, state transitions).\n")

    w("\n## 2. Test cases\n")
    w("`Expected` is the behaviour asserted by the test; `Actual` is what the run produced. "
      "A case only passes when they match.\n")

    for mod, (title, stories) in MODULE_TITLES.items():
        rows = by_module.get(mod, [])
        if not rows:
            continue
        mod_pass = sum(1 for r in rows if r["status"] == "PASS")
        w(f"\n### {title}  \n"
          f"`Backend/tests/{mod}.py` · {stories} · **{mod_pass}/{len(rows)} passed**\n")
        w("| # | Test case (input) | Expected | Actual | Result |")
        w("|---|---|---|---|---|")
        for i, r in enumerate(rows, 1):
            label = humanise(r["name"])
            given, expected = split_expectation(label)
            if r["status"] == "PASS":
                actual, mark = "as expected", "✅ PASS"
            elif r["status"] == "SKIP":
                actual = (r["message"] or "skipped").split("\n")[0][:70]
                expected = "documented open finding"
                mark = "⏭️ SKIP"
            else:
                actual = (r["message"] or "assertion failed").split("\n")[0][:70]
                mark = "❌ FAIL"
            cls = f"{r['cls']}: " if r["cls"] else ""
            w(f"| {i} | {cls}{given} | {expected} | {actual} | {mark} |")

    w(DEFECTS)

    w("\n## 4. Test design notes\n")
    w("- **Isolation** — every test builds a fresh app against its own temporary SQLite file "
      "(`tests/conftest.py`), so tests never share state and never touch `instance/societyease.db`.\n"
      "- **Seed fixture** — two flats and one user per role (ADMIN, TREASURER, COMMITTEE_MEMBER, "
      "TENANT, OWNER, WORKER); the tenant is linked to flat A-101 so ownership rules can be tested.\n"
      "- **Role fixtures** — `admin`, `treasurer`, `resident`, `worker` yield ready-made "
      "`Authorization` headers, so a test that needs one role does not pay to log in six.\n"
      "- **Regression tests are named after the defect** they prevent, and their docstrings record "
      "the expected/actual pair, so the evidence lives next to the code.\n"
      "- A test that fails is treated as a finding to report, never as a test to weaken.\n")

    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print(f"wrote {OUT}  ({len(cases)} cases)")
    try:
        os.unlink(XML)
    except OSError:
        pass


if __name__ == "__main__":
    main()
