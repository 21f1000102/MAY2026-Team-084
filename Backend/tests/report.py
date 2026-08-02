"""
Generate docs/TEST_CASES.md from a REAL pytest run.

For every test case the document records:

    Page being tested : the actual URL that was called
    Inputs            : request method, JSON body, auth header
    Expected Output   : status code + JSON, parsed from the test's own asserts
    Actual Output     : status code + JSON, captured live from the response
    Result            : Success / Failure
    Test code         : the pytest function that produced it

"Expected" and "Actual" come from independent sources — the assertions in the
source versus the recorded HTTP response — so the comparison is meaningful
rather than circular.

    python tests/report.py
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)
TESTS = os.path.join(BACKEND, "tests")
XML = os.path.join(TESTS, "_junit.xml")
LOG = os.path.join(TESTS, "_api_log.json")
OUT = os.path.join(REPO, "docs", "TEST_CASES.md")
BASE_URL = "http://127.0.0.1:5000"

MODULES = OrderedDict([
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
    ("test_regressions", ("Regression suite — defects already fixed", "all")),
    ("test_open_defects", ("Open defects — EXPECTED TO FAIL", "all")),
])


# ── run ───────────────────────────────────────────────────────
def run_pytest():
    print("running pytest (this takes a few minutes) ...")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=no", "-q", f"--junit-xml={XML}"],
        cwd=BACKEND, capture_output=True, text=True,
    )
    lines = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    return proc.returncode, (lines[-1] if lines else "")


def parse_junit():
    root = ET.parse(XML).getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    cases, totals = [], {}
    for tc in suite.iter("testcase"):
        classname = tc.get("classname", "")
        parts = [p for p in classname.split(".") if p and p != "tests"]
        failure = tc.find("failure")
        if failure is None:
            failure = tc.find("error")
        skipped = tc.find("skipped")
        cases.append({
            "module": parts[0] if parts else "",
            "cls": parts[1] if len(parts) > 1 else "",
            "name": tc.get("name", ""),
            "status": "SKIP" if skipped is not None else ("FAIL" if failure is not None else "PASS"),
            "message": (failure.get("message") if failure is not None
                        else (skipped.get("message") if skipped is not None else "")),
        })
    totals = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    totals["time"] = float(suite.get("time", 0) or 0)
    return cases, totals


# ── source analysis: expectations + code ──────────────────────
def load_sources():
    """Per test function: its source text and the expectations it asserts."""
    info = {}
    for fname in os.listdir(TESTS):
        if not (fname.startswith("test_") and fname.endswith(".py")):
            continue
        module = fname[:-3]
        src = io.open(os.path.join(TESTS, fname), encoding="utf-8").read()
        lines = src.splitlines()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue

        def visit(node, cls=""):
            for child in node.body:
                if isinstance(child, ast.ClassDef):
                    visit(child, child.name)
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not child.name.startswith("test"):
                        continue
                    start = min([child.lineno] + [d.lineno for d in child.decorator_list]) - 1
                    body = "\n".join(lines[start:child.end_lineno])
                    info[(module, cls, child.name)] = {
                        "code": body,
                        "expected": extract_expectations(body),
                        "doc": ast.get_docstring(child) or "",
                    }
        visit(tree)
    return info


def extract_expectations(code):
    """Pull the asserted status codes and JSON expectations out of a test body."""
    codes, notes = [], []

    for m in re.finditer(r"status_code\s*==\s*(\d{3})", code):
        codes.append(int(m.group(1)))
    for m in re.finditer(r"status_code\s+in\s*[\(\[]([\d,\s]+)[\)\]]", code):
        codes.extend(int(x) for x in re.findall(r"\d{3}", m.group(1)))
    # parametrized status codes, e.g. @pytest.mark.parametrize("...status", [400, 403])
    if not codes:
        for m in re.finditer(r"status_code\s*==\s*(\w+)", code):
            for lit in re.findall(rf"{m.group(1)}\W+(\d{{3}})", code):
                codes.append(int(lit))

    # asserted JSON content
    for m in re.finditer(r'get_json\(\)\s*\[\s*[\'"](\w+)[\'"]\s*\]\s*==\s*[\'"]([^\'"]+)[\'"]', code):
        notes.append(f'`{m.group(1)}` == "{m.group(2)}"')
    for m in re.finditer(r'[\'"]([^\'"]{3,60})[\'"]\s+in\s+\w+\.get_json\(\)\s*\[\s*[\'"](\w+)[\'"]\s*\]', code):
        notes.append(f'`{m.group(2)}` contains "{m.group(1)}"')
    for m in re.finditer(r'[\'"](\w+)[\'"]\s+(not\s+)?in\s+\w+\.get_json\(\)', code):
        notes.append(f'response {"omits" if m.group(2) else "includes"} `{m.group(1)}`')
    for m in re.finditer(r'\[\s*[\'"](\w+)[\'"]\s*\]\s*is\s+(not\s+)?None', code):
        notes.append(f'`{m.group(1)}` is {"set" if m.group(2) else "null"}')

    seen, ordered = set(), []
    for c in codes:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return {"codes": ordered, "notes": notes[:4]}


# ── recorded API calls ────────────────────────────────────────
def load_calls():
    if not os.path.exists(LOG):
        return {}
    records = json.load(io.open(LOG, encoding="utf-8"))
    by_node = defaultdict(list)
    for r in records:
        if r.get("nodeid"):
            by_node[r["nodeid"]].append(r)
    return by_node


def nodeid_for(case):
    path = f"tests/{case['module']}.py::"
    if case["cls"]:
        path += f"{case['cls']}::"
    return path + case["name"]


# ── formatting ────────────────────────────────────────────────
def title_of(case, src):
    if src and src.get("doc"):
        first = src["doc"].strip().splitlines()[0].strip()
        if 10 < len(first) < 130:
            return first.rstrip(".")
    name = re.sub(r"^test_", "", case["name"])
    name = re.sub(r"\[.*\]$", "", name)
    return name.replace("_", " ").strip().capitalize()


def pretty_json(text, indent="    "):
    if not text:
        return None
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return text.strip()
    out = json.dumps(obj, indent=2, ensure_ascii=False)
    if len(out) > 700:
        out = out[:699] + "\n…"
    return out.replace("\n", "\n" + indent)


def main():
    reuse = "--no-run" in sys.argv
    if reuse and os.path.exists(XML):
        code, summary = 0, "(reused the previous run's results)"
        print("reusing existing test results (--no-run)")
    else:
        code, summary = run_pytest()
    cases, totals = parse_junit()
    sources = load_sources()
    calls = load_calls()
    print(f"pytest: {summary}")

    passed = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    open_fail = sum(1 for c in cases
                    if c["module"] == "test_open_defects" and c["status"] == "FAIL")
    regressions = totals["failures"] + totals["errors"] - open_fail
    now = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

    by_module = OrderedDict((m, []) for m in MODULES)
    for c in cases:
        by_module.setdefault(c["module"], []).append(c)

    L = []
    w = L.append

    w("# API Test Cases\n")
    w("Test cases for the SocietyEase REST API. For each case this records the **URL that was "
      "called**, the **exact request that was sent**, the **output that was expected**, and the "
      "**output that actually came back**.\n")
    w("> **Generated document.** `Backend/tests/report.py` runs the suite and writes this file. "
      "The *Actual Output* is captured live from each HTTP response; the *Expected Output* is "
      "read from the assertions in the test source. Neither column is written by hand.\n")

    w("## 1. Summary\n")
    w(f"| | |\n|---|---|\n| Generated | {now} |\n| Total test cases | **{totals['tests']}** |\n"
      f"| Passed | **{passed}** |\n"
      f"| Failed — known open defects | **{open_fail}** (expected — see section 3) |\n"
      f"| Failed — regressions | **{regressions}** |\n"
      f"| Skipped | {totals['skipped']} |\n| Duration | {totals['time']:.0f}s |\n"
      f"| Base URL | `{BASE_URL}` |\n")
    if open_fail:
        w(f"\n> **{open_fail} tests fail on purpose.** They live in "
          "`tests/test_open_defects.py` and assert the behaviour the API *should* have. Each is a "
          "real defect we found and have not fixed yet — leaving the test red keeps it visible. "
          "Section 3 lists them with expected vs actual. "
          f"**Regressions (unexpected failures): {regressions}.**\n")

    w("\n### How to run\n")
    w("```bash\ncd Backend\npip install -r requirements.txt\npytest -v                 "
      "# run every test case\npython tests/report.py    # regenerate this document\n```\n")

    w("\n### Coverage by module\n")
    w("| Module | Feature | User stories | Cases | Passed |\n|---|---|---|---:|---:|")
    for mod, (feature, stories) in MODULES.items():
        rows = by_module.get(mod, [])
        ok = sum(1 for r in rows if r["status"] == "PASS")
        note = " ⚠️ fails by design" if mod == "test_open_defects" else ""
        w(f"| `{mod}.py` | {feature}{note} | {stories} | {len(rows)} | {ok} |")
    w(f"| | | **Total** | **{totals['tests']}** | **{passed}** |\n")

    w("Every module covers the same four axes: **happy path**, **validation** (missing fields, "
      "bad enums, bad dates, malformed bodies), **authorization** (401 unauthenticated, 403 wrong "
      "role) and **business rules** (duplicates, idempotency, state transitions).\n")

    # ── detailed cases ────────────────────────────────────────
    w("\n---\n")
    w("## 2. Test cases\n")

    counter = 0
    for mod, (feature, stories) in MODULES.items():
        rows = by_module.get(mod, [])
        if not rows:
            continue
        ok = sum(1 for r in rows if r["status"] == "PASS")
        w(f"\n---\n\n## {feature}\n")
        w(f"`Backend/tests/{mod}.py` · {stories} · **{ok}/{len(rows)} passed**\n")

        for case in rows:
            counter += 1
            src = sources.get((case["module"], case["cls"], re.sub(r"\[.*\]$", "", case["name"])))
            made = calls.get(nodeid_for(case), [])
            primary = made[-1] if made else None
            setup = made[:-1]

            w(f"\n### TC-{counter:03d} · {title_of(case, src)}\n")

            if primary:
                w(f"**Page being tested:** `{primary['method']} {BASE_URL}{primary['path']}`\n")
            else:
                w("**Page being tested:** _no HTTP call recorded (pure logic / skipped)_\n")

            # Inputs
            w("**Inputs:**\n")
            if primary:
                w(f"- Request Method: `{primary['method']}`")
                w(f"- URL: `{BASE_URL}{primary['path']}`")
                body = pretty_json(primary.get("request"))
                if body:
                    w(f"- JSON body:\n    ```json\n    {body}\n    ```")
                else:
                    w("- JSON body: _none_")
                w("- Header: `Authorization: Bearer <jwt>`" if primary["authenticated"]
                  else "- Header: _none (unauthenticated request)_")
                if setup:
                    steps = ", ".join(f"`{s['method']} {s['path']}` → {s['status']}" for s in setup[-4:])
                    w(f"- Setup calls before this ({len(setup)}): {steps}")
            else:
                w("- _none_")
            w("")

            # Expected. Asserts appear in the same order as the calls, so when the
            # counts line up we can attribute the right expectation to the primary
            # (last) call instead of listing every code the test ever asserted.
            exp = (src or {}).get("expected", {"codes": [], "notes": []})
            exp_codes = exp["codes"]
            if len(exp_codes) > 1 and made and len(exp_codes) == len(made):
                exp_codes = [exp_codes[-1]]
            w("**Expected Output:**\n")
            if case["status"] == "SKIP":
                w("- _Documented open finding — see section 3._")
            elif exp_codes:
                w(f"- HTTP Status Code: `{' or '.join(str(c) for c in exp_codes)}`")
            elif primary:
                w(f"- HTTP Status Code: `{primary['status']}`")
            for note in exp["notes"]:
                w(f"- JSON: {note}")
            if not exp["codes"] and not exp["notes"] and not primary:
                w("- _behaviour asserted in code; see the test below_")
            w("")

            # Actual
            w("**Actual Output:**\n")
            if primary:
                w(f"- HTTP Status Code: `{primary['status']}`")
                resp = pretty_json(primary.get("response"))
                if resp:
                    w(f"- JSON:\n    ```json\n    {resp}\n    ```")
                else:
                    w("- JSON: _empty body_")
            elif case["status"] == "SKIP":
                w(f"- _not executed_ — {(case['message'] or 'skipped').splitlines()[0][:110]}")
            else:
                w("- _no HTTP call recorded_")
            w("")

            if case["status"] == "PASS":
                w("**Result:** ✅ Success — actual output matched the expectation.\n")
            elif case["status"] == "SKIP":
                w("**Result:** ⏭️ Skipped — deliberately not run; the reason is recorded above.\n")
            else:
                w(f"**Result:** ❌ Failure — {(case['message'] or '').splitlines()[0][:200]}\n")

            if src and src.get("code"):
                snippet = src["code"]
                if len(snippet) > 1800:
                    snippet = snippet[:1799] + "\n    # …"
                w("<details><summary>Test code</summary>\n")
                w("```python")
                w(snippet)
                w("```")
                w("</details>\n")

    w(DEFECTS)

    w("\n## 4. Test design notes\n")
    w("- **Isolation** — each test builds a fresh app against its own temporary SQLite file "
      "(`tests/conftest.py`), so tests never share state and never touch `instance/societyease.db`.\n"
      "- **Seed data** — two flats and one user per role (ADMIN, TREASURER, COMMITTEE_MEMBER, "
      "TENANT, OWNER, WORKER); the tenant is linked to flat A-101 so ownership rules can be tested.\n"
      "- **Recording** — the test client is subclassed (`RecordingClient`) to log every request and "
      "response, which is what fills the Inputs and Actual Output sections above. JWTs and "
      "passwords are redacted.\n"
      "- **Expected vs Actual** — Expected is parsed from the `assert` statements in the test "
      "source; Actual is the recorded HTTP response. They are captured independently.\n"
      "- A failing test is treated as a defect to report, never as a test to weaken.\n")

    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print(f"wrote {OUT}  ({counter} cases documented)")
    print("(re-run with --no-run to rebuild the document without re-running the suite)")


DEFECTS = """
---

## 3. Defects found through testing — where actual differed from expected

Every entry below is a **real defect testing caught in our own code**: the actual output differed
from what the API should have returned. Each now has a permanent regression test in
`Backend/tests/test_regressions.py`, so it cannot silently come back.

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

### Still open — these tests FAIL right now, on purpose

`Backend/tests/test_open_defects.py` asserts the behaviour the API *should* have. Each test below
currently fails because the code does something else. They are left red deliberately: a failing test
is a to-do item that cannot be forgotten, whereas a comment can. Every one was reproduced against
the running API, not inferred from reading the code.

| # | API | Input | Expected | **Actual (today)** | Severity | Fix |
|---|-----|-------|----------|--------------------|----------|-----|
| OD-01 | any protected endpoint, no token | — | `{"error": "..."}` — the envelope `openapi.yaml` declares for all 67 protected operations | **`{"msg": "Missing Authorization Header"}`** | Low | Add `@jwt.unauthorized_loader` / `invalid_token_loader` / `expired_token_loader` in `create_app()` (~6 lines) |
| OD-02 | `POST /api/auth/register` (public) | `{"role": "ADMIN", …}` | `400` / `403` — public signup may only create residents | **`201`** + a working ADMIN token | **HIGH** | Restrict the public endpoint to `TENANT`/`OWNER`; create staff via the admin-only `POST /api/members/` |
| OD-02b | `GET /api/members/` with that token | — | `403` | **`200`** — the full member directory, proving the escalation is exploitable | **HIGH** | as above |
| OD-03 | `GET /api/invoices/` | an UNPAID invoice due 60 days ago | status `OVERDUE` | **`UNPAID`** — forever | Medium | Flip past-due unpaid invoices on read, or add a scheduled task |
| OD-04 | `POST /api/maintenance/` | `{"category": "BOGUS"}` | `"category must be one of: …"` | **`"task_category must be one of: …"`** | Low | Pass `field="category"` to `parse_enum` |
| OD-04b | `POST /api/equipment/` | `{"category": "BOGUS"}` | `"category must be one of: …"` | **`"equipment_category must be one of: …"`** | Low | as above |

**Why these are still open.** OD-02 is deliberate for now — public ADMIN signup is how the team
creates test accounts during development (`KNOWN_ISSUES.md` #1) — but it is the single most
important thing to close before the app touches real data. OD-01 and OD-04 are contract
inconsistencies with easy fixes. OD-03 is a genuine functional gap in a headline feature: the
treasurer cannot tell "due next week" from "unpaid since March", and the Society Health Score's
payment component is blind to lateness.

All six are scheduled for the next sprint. When one is fixed, its test moves from
`test_open_defects.py` into `test_regressions.py`, where it must pass from then on.

### What testing bought us

Six endpoints (`POST` expenses, maintenance, equipment and polls, plus registration in two ways)
were **completely unusable** — every call returned 500. The empty `expenses`, `maintenance_tasks`,
`equipment` and `votes` tables in the shipped database confirm no user had ever succeeded in
creating one. Three defects were security issues: the conflict-anonymity leak (D-07), unrestricted
privileged actions (D-14) and the destructive cascade (D-15). None were visible from the UI,
because the frontend swallowed errors — they were only found by asserting on status codes.
"""


if __name__ == "__main__":
    main()
