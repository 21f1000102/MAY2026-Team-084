# API Test Cases

Test cases for the SocietyEase REST API. For each case this records the **URL that was called**, the **exact request that was sent**, the **output that was expected**, and the **output that actually came back**.

> **Generated document.** `Backend/tests/report.py` runs the suite and writes this file. The *Actual Output* is captured live from each HTTP response; the *Expected Output* is read from the assertions in the test source. Neither column is written by hand.

## 1. Summary

| | |
|---|---|
| Generated | 02 August 2026, 12:01 UTC |
| Total test cases | **539** |
| Passed | **533** |
| Failed — known open defects | **6** (expected — see section 3) |
| Failed — regressions | **0** |
| Skipped | 0 |
| Duration | 201s |
| Base URL | `http://127.0.0.1:5000` |


> **6 tests fail on purpose.** They live in `tests/test_open_defects.py` and assert the behaviour the API *should* have. Each is a real defect we found and have not fixed yet — leaving the test red keeps it visible. Section 3 lists them with expected vs actual. **Regressions (unexpected failures): 0.**


### How to run

```bash
cd Backend
pip install -r requirements.txt
pytest -v                 # run every test case
python tests/report.py    # regenerate this document
```


### Coverage by module

| Module | Feature | User stories | Cases | Passed |
|---|---|---|---:|---:|
| `test_auth.py` | Authentication | US-08 | 52 | 52 |
| `test_members.py` | Members & Apartments | US-09, US-04 | 96 | 96 |
| `test_complaints.py` | Complaints | US-02, US-03, US-04 | 44 | 44 |
| `test_invoices.py` | Invoices & Payments | US-01, US-05, US-06 | 53 | 53 |
| `test_expenses.py` | Expenses | US-14 | 44 | 44 |
| `test_notices.py` | Notices | US-10 | 18 | 18 |
| `test_polls.py` | Polls & Voting | US-13 | 29 | 29 |
| `test_maintenance.py` | Maintenance Tasks | US-11 | 24 | 24 |
| `test_equipment.py` | Equipment / Maintenance Predictor | US-15 | 28 | 28 |
| `test_health.py` | Society Health Score | US-17 | 20 | 20 |
| `test_conflicts.py` | Neighbour Conflict Resolver | US-16 | 27 | 27 |
| `test_parking.py` | Visitor Parking | US-12 | 27 | 27 |
| `test_emergency.py` | Emergency Contacts | US-07 | 50 | 50 |
| `test_regressions.py` | Regression suite — defects already fixed | all | 21 | 21 |
| `test_open_defects.py` | Open defects — EXPECTED TO FAIL ⚠️ fails by design | all | 6 | 0 |
| | | **Total** | **539** | **533** |

Every module covers the same four axes: **happy path**, **validation** (missing fields, bad enums, bad dates, malformed bodies), **authorization** (401 unauthenticated, 403 wrong role) and **business rules** (duplicates, idempotency, state transitions).


---

## 2. Test cases


---

## Authentication

`Backend/tests/test_auth.py` · US-08 · **52/52 passed**


### TC-001 · Register returns 201 with token and user

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Nina Newcomer",
      "email": "nina@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "phone": "9000000001"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "message": "User registered successfully",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:41.271585",
        "email": "nina@test.com",
        "id": 1,
        "is_active": true,
        "name": "Nina Newcomer",
        "phone": "9000000001",
        "role": "OWNER"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_returns_201_with_token_and_user(client):
    res = client.post("/api/auth/register", json={
        "name": "Nina Newcomer",
        "email": "nina@test.com",
        "password": "Secret@123",
        "role": "OWNER",
        "phone": "9000000001",
    })
    assert res.status_code == 201
    body = res.get_json()
    assert body["message"] == "User registered successfully"
    assert body["token"]
    assert body["user"]["email"] == "nina@test.com"
    assert body["user"]["role"] == "OWNER"
    assert body["user"]["is_active"] is True
```
</details>


### TC-002 · Register lowercases and strips email

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "  Casey Case  ",
      "email": "  MiXeD@Test.COM  ",
      "password": "<hidden>",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "message": "User registered successfully",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:41.593671",
        "email": "mixed@test.com",
        "id": 1,
        "is_active": true,
        "name": "Casey Case",
        "phone": null,
        "role": "TENANT"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_lowercases_and_strips_email(client):
    res = client.post("/api/auth/register", json={
        "name": "  Casey Case  ",
        "email": "  MiXeD@Test.COM  ",
        "password": "Secret@123",
        "role": "TENANT",
    })
    assert res.status_code == 201
    assert res.get_json()["user"]["email"] == "mixed@test.com"
```
</details>


### TC-003 · Register issues a usable token

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/register` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `email` == "token@test.com"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "created_at": "2026-08-02 11:56:42.148697",
      "email": "token@test.com",
      "id": 1,
      "is_active": true,
      "name": "Token Tester",
      "phone": null,
      "role": "TENANT"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_issues_a_usable_token(client):
    token = client.post("/api/auth/register", json={
        "name": "Token Tester", "email": "token@test.com",
        "password": "Secret@123", "role": "TENANT",
    }).get_json()["token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["email"] == "token@test.com"
```
</details>


### TC-004 · Register missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "email": "nofield@test.com",
      "password": "<hidden>",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "name is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["name", "email", "password", "role"])
def test_register_missing_required_field_returns_400(client, missing):
    payload = {"name": "No Field", "email": "nofield@test.com",
               "password": "Secret@123", "role": "TENANT"}
    payload.pop(missing)

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-005 · Register missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "No Field",
      "password": "<hidden>",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "email is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["name", "email", "password", "role"])
def test_register_missing_required_field_returns_400(client, missing):
    payload = {"name": "No Field", "email": "nofield@test.com",
               "password": "Secret@123", "role": "TENANT"}
    payload.pop(missing)

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-006 · Register missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "No Field",
      "email": "nofield@test.com",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "password is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["name", "email", "password", "role"])
def test_register_missing_required_field_returns_400(client, missing):
    payload = {"name": "No Field", "email": "nofield@test.com",
               "password": "Secret@123", "role": "TENANT"}
    payload.pop(missing)

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-007 · Register missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "No Field",
      "email": "nofield@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "role is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["name", "email", "password", "role"])
def test_register_missing_required_field_returns_400(client, missing):
    payload = {"name": "No Field", "email": "nofield@test.com",
               "password": "Secret@123", "role": "TENANT"}
    payload.pop(missing)

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-008 · Register blank required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "",
      "email": "blank@test.com",
      "password": "<hidden>",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "name is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "name is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("blank", ["", "   "])
def test_register_blank_required_field_returns_400(client, blank):
    res = client.post("/api/auth/register", json={
        "name": blank, "email": "blank@test.com",
        "password": "Secret@123", "role": "TENANT",
    })
    assert res.status_code == 400
    assert res.get_json()["error"] == "name is required"
```
</details>


### TC-009 · Register blank required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "   ",
      "email": "blank@test.com",
      "password": "<hidden>",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "name is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "name is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("blank", ["", "   "])
def test_register_blank_required_field_returns_400(client, blank):
    res = client.post("/api/auth/register", json={
        "name": blank, "email": "blank@test.com",
        "password": "Secret@123", "role": "TENANT",
    })
    assert res.status_code == 400
    assert res.get_json()["error"] == "name is required"
```
</details>


### TC-010 · Register unknown role returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Wanda Wizard",
      "email": "wizard@test.com",
      "password": "<hidden>",
      "role": "WIZARD"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "role must be one of: ADMIN, TENANT, OWNER, TREASURER, WORKER, COMMITTEE_MEMBER, AUDITOR, SYSTEM_ADMIN"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_unknown_role_returns_400(client):
    res = client.post("/api/auth/register", json={
        "name": "Wanda Wizard", "email": "wizard@test.com",
        "password": "Secret@123", "role": "WIZARD",
    })
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("role must be one of:")
```
</details>


### TC-011 · Register malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    null
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_register_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/register", data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-012 · Register malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    []
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_register_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/register", data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-013 · Register malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    "str"
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_register_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/register", data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-014 · Register duplicate email returns 409

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Copycat",
      "email": "resident@test.com",
      "password": "<hidden>",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Email already registered"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Email already registered"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_duplicate_email_returns_409(client, seed):
    res = client.post("/api/auth/register", json={
        "name": "Copycat", "email": "resident@test.com",
        "password": "Secret@123", "role": "TENANT",
    })
    assert res.status_code == 409
    assert res.get_json()["error"] == "Email already registered"
```
</details>


### TC-015 · Register duplicate email is case insensitive

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Copycat",
      "email": "RESIDENT@TEST.COM",
      "password": "<hidden>",
      "role": "TENANT"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Email already registered"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Email already registered"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_duplicate_email_is_case_insensitive(client, seed):
    res = client.post("/api/auth/register", json={
        "name": "Copycat", "email": "RESIDENT@TEST.COM",
        "password": "Secret@123", "role": "TENANT",
    })
    assert res.status_code == 409
    assert res.get_json()["error"] == "Email already registered"
```
</details>


### TC-016 · Register duplicate phone returns 409

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Phone Two",
      "email": "phone2@test.com",
      "password": "<hidden>",
      "role": "TENANT",
      "phone": "9111111111"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (1): `POST /api/auth/register` → 201

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Phone number already registered"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Phone number already registered"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_duplicate_phone_returns_409(client):
    first = client.post("/api/auth/register", json={
        "name": "Phone One", "email": "phone1@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "9111111111",
    })
    assert first.status_code == 201

    second = client.post("/api/auth/register", json={
        "name": "Phone Two", "email": "phone2@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "9111111111",
    })
    assert second.status_code == 409
    assert second.get_json()["error"] == "Phone number already registered"
```
</details>


### TC-017 · Blank phone must normalise to NULL — users.phone is UNIQUE

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Blank Two",
      "email": "blank2@test.com",
      "password": "<hidden>",
      "role": "TENANT",
      "phone": ""
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (1): `POST /api/auth/register` → 201

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "message": "User registered successfully",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:48.881252",
        "email": "blank2@test.com",
        "id": 2,
        "is_active": true,
        "name": "Blank Two",
        "phone": null,
        "role": "TENANT"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_two_blank_phones_both_succeed(client):
    """Blank phone must normalise to NULL — users.phone is UNIQUE.

    This was a real bug: the second blank-phone signup collided with the first.
    """
    first = client.post("/api/auth/register", json={
        "name": "Blank One", "email": "blank1@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "",
    })
    second = client.post("/api/auth/register", json={
        "name": "Blank Two", "email": "blank2@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "",
    })
    assert (first.status_code, second.status_code) == (201, 201)
```
</details>


### TC-018 · Register blank phone is stored as null

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Blank Phone",
      "email": "blankphone@test.com",
      "password": "<hidden>",
      "role": "TENANT",
      "phone": "   "
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `phone` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "message": "User registered successfully",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:49.639816",
        "email": "blankphone@test.com",
        "id": 1,
        "is_active": true,
        "name": "Blank Phone",
        "phone": null,
        "role": "TENANT"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_register_blank_phone_is_stored_as_null(client):
    res = client.post("/api/auth/register", json={
        "name": "Blank Phone", "email": "blankphone@test.com",
        "password": "Secret@123", "role": "TENANT", "phone": "   ",
    })
    assert res.status_code == 201
    assert res.get_json()["user"]["phone"] is None
```
</details>


### TC-019 · Login succeeds for every seeded role

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "admin@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:49.958042",
        "email": "admin@test.com",
        "id": 1,
        "is_active": true,
        "name": "Priya Admin",
        "phone": null,
        "role": "ADMIN"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("email,role", [
    ("admin@test.com", "ADMIN"),
    ("treasurer@test.com", "TREASURER"),
    ("committee@test.com", "COMMITTEE_MEMBER"),
    ("resident@test.com", "TENANT"),
    ("owner@test.com", "OWNER"),
    ("worker@test.com", "WORKER"),
])
def test_login_succeeds_for_every_seeded_role(client, seed, email, role):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Login successful"
    assert body["token"]
    assert body["user"]["role"] == role
```
</details>


### TC-020 · Login succeeds for every seeded role

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "treasurer@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:50.502459",
        "email": "treasurer@test.com",
        "id": 2,
        "is_active": true,
        "name": "Tarun Treasurer",
        "phone": null,
        "role": "TREASURER"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("email,role", [
    ("admin@test.com", "ADMIN"),
    ("treasurer@test.com", "TREASURER"),
    ("committee@test.com", "COMMITTEE_MEMBER"),
    ("resident@test.com", "TENANT"),
    ("owner@test.com", "OWNER"),
    ("worker@test.com", "WORKER"),
])
def test_login_succeeds_for_every_seeded_role(client, seed, email, role):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Login successful"
    assert body["token"]
    assert body["user"]["role"] == role
```
</details>


### TC-021 · Login succeeds for every seeded role

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "committee@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:50.930694",
        "email": "committee@test.com",
        "id": 3,
        "is_active": true,
        "name": "Chitra Committee",
        "phone": null,
        "role": "COMMITTEE_MEMBER"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("email,role", [
    ("admin@test.com", "ADMIN"),
    ("treasurer@test.com", "TREASURER"),
    ("committee@test.com", "COMMITTEE_MEMBER"),
    ("resident@test.com", "TENANT"),
    ("owner@test.com", "OWNER"),
    ("worker@test.com", "WORKER"),
])
def test_login_succeeds_for_every_seeded_role(client, seed, email, role):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Login successful"
    assert body["token"]
    assert body["user"]["role"] == role
```
</details>


### TC-022 · Login succeeds for every seeded role

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "resident@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:51.459616",
        "email": "resident@test.com",
        "id": 4,
        "is_active": true,
        "name": "Ravi Resident",
        "phone": null,
        "role": "TENANT"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("email,role", [
    ("admin@test.com", "ADMIN"),
    ("treasurer@test.com", "TREASURER"),
    ("committee@test.com", "COMMITTEE_MEMBER"),
    ("resident@test.com", "TENANT"),
    ("owner@test.com", "OWNER"),
    ("worker@test.com", "WORKER"),
])
def test_login_succeeds_for_every_seeded_role(client, seed, email, role):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Login successful"
    assert body["token"]
    assert body["user"]["role"] == role
```
</details>


### TC-023 · Login succeeds for every seeded role

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "owner@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:51.797236",
        "email": "owner@test.com",
        "id": 5,
        "is_active": true,
        "name": "Ojas Owner",
        "phone": null,
        "role": "OWNER"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("email,role", [
    ("admin@test.com", "ADMIN"),
    ("treasurer@test.com", "TREASURER"),
    ("committee@test.com", "COMMITTEE_MEMBER"),
    ("resident@test.com", "TENANT"),
    ("owner@test.com", "OWNER"),
    ("worker@test.com", "WORKER"),
])
def test_login_succeeds_for_every_seeded_role(client, seed, email, role):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Login successful"
    assert body["token"]
    assert body["user"]["role"] == role
```
</details>


### TC-024 · Login succeeds for every seeded role

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "worker@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:52.321752",
        "email": "worker@test.com",
        "id": 6,
        "is_active": true,
        "name": "Ramesh Worker",
        "phone": null,
        "role": "WORKER"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("email,role", [
    ("admin@test.com", "ADMIN"),
    ("treasurer@test.com", "TREASURER"),
    ("committee@test.com", "COMMITTEE_MEMBER"),
    ("resident@test.com", "TENANT"),
    ("owner@test.com", "OWNER"),
    ("worker@test.com", "WORKER"),
])
def test_login_succeeds_for_every_seeded_role(client, seed, email, role):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Login successful"
    assert body["token"]
    assert body["user"]["role"] == role
```
</details>


### TC-025 · Login wrong password returns 401

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "resident@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`
- JSON: `error` == "Invalid email or password"

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "error": "Invalid email or password"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_login_wrong_password_returns_401(client, seed):
    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": "WrongPass1"})
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"
```
</details>


### TC-026 · Login unknown email returns 401

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "ghost@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`
- JSON: `error` == "Invalid email or password"

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "error": "Invalid email or password"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_login_unknown_email_returns_401(client, seed):
    res = client.post("/api/auth/login",
                      json={"email": "ghost@test.com", "password": PASSWORD})
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"
```
</details>


### TC-027 · Login missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "email is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["email", "password"])
def test_login_missing_required_field_returns_400(client, seed, missing):
    payload = {"email": "resident@test.com", "password": PASSWORD}
    payload.pop(missing)

    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-028 · Login missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "resident@test.com"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "password is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["email", "password"])
def test_login_missing_required_field_returns_400(client, seed, missing):
    payload = {"email": "resident@test.com", "password": PASSWORD}
    payload.pop(missing)

    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-029 · Login malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    null
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_login_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/login", data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-030 · Login malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    []
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_login_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/login", data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-031 · Login malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    "str"
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_login_malformed_body_returns_400(client, raw, expected):
    res = client.post("/api/auth/login", data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-032 · Login deactivated account returns 403

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "resident@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `POST /api/auth/login` → 200, `DELETE /api/members/1` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "Account is deactivated"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "Account is deactivated"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_login_deactivated_account_returns_403(client, seed, admin):
    client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)

    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": PASSWORD})
    assert res.status_code == 403
    assert res.get_json()["error"] == "Account is deactivated"
```
</details>


### TC-033 · Me returns the authenticated user

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "created_at": "2026-08-02 11:56:55.552923",
      "email": "resident@test.com",
      "id": 4,
      "is_active": true,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_me_returns_the_authenticated_user(client, seed, resident):
    res = client.get("/api/auth/me", headers=resident)
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == seed["resident_id"]
    assert body["email"] == "resident@test.com"
    assert body["role"] == "TENANT"
```
</details>


### TC-034 · Me is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "created_at": "2026-08-02 11:56:56.015860",
      "email": "admin@test.com",
      "id": 1,
      "is_active": true,
      "name": "Priya Admin",
      "phone": null,
      "role": "ADMIN"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_me_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
```
</details>


### TC-035 · Me is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "created_at": "2026-08-02 11:56:56.459714",
      "email": "treasurer@test.com",
      "id": 2,
      "is_active": true,
      "name": "Tarun Treasurer",
      "phone": null,
      "role": "TREASURER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_me_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
```
</details>


### TC-036 · Me is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "created_at": "2026-08-02 11:56:56.939179",
      "email": "resident@test.com",
      "id": 4,
      "is_active": true,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_me_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
```
</details>


### TC-037 · Me is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "created_at": "2026-08-02 11:56:57.263679",
      "email": "worker@test.com",
      "id": 6,
      "is_active": true,
      "name": "Ramesh Worker",
      "phone": null,
      "role": "WORKER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_me_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
```
</details>


### TC-038 · Me without token returns 401

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_me_without_token_returns_401(client):
    assert client.get("/api/auth/me").status_code == 401
```
</details>


### TC-039 · Me with garbage token returns 422

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`

**Expected Output:**

- HTTP Status Code: `401 or 422`

**Actual Output:**

- HTTP Status Code: `422`
- JSON:
    ```json
    {
      "msg": "Invalid header string: 'utf-8' codec can't decode byte 0x9e in position 0: invalid start byte"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_me_with_garbage_token_returns_422(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert res.status_code in (401, 422)
```
</details>


### TC-040 · Change password returns 200

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "Pass@123",
      "new_password": "Brand@New1"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Password changed successfully"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Password changed successfully"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_returns_200(client, seed, resident):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD, "new_password": "Brand@New1"})
    assert res.status_code == 200
    assert res.get_json()["message"] == "Password changed successfully"
```
</details>


### TC-041 · Change password old password stops working

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "resident@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `POST /api/auth/login` → 200, `PUT /api/auth/change-password` → 200

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "error": "Invalid email or password"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_old_password_stops_working(client, seed, resident):
    client.put("/api/auth/change-password", headers=resident,
               json={"old_password": PASSWORD, "new_password": "Brand@New1"})

    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": PASSWORD})
    assert res.status_code == 401
```
</details>


### TC-042 · Change password new password works

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "resident@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `POST /api/auth/login` → 200, `PUT /api/auth/change-password` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:56:59.886060",
        "email": "resident@test.com",
        "id": 4,
        "is_active": true,
        "name": "Ravi Resident",
        "phone": null,
        "role": "TENANT"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_new_password_works(client, seed, resident):
    client.put("/api/auth/change-password", headers=resident,
               json={"old_password": PASSWORD, "new_password": "Brand@New1"})

    res = client.post("/api/auth/login",
                      json={"email": "resident@test.com", "password": "Brand@New1"})
    assert res.status_code == 200
```
</details>


### TC-043 · Regression: this used to be a KeyError -> HTML 500

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "Pass@123"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "new_password is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "new_password is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_missing_new_password_returns_400(client, seed, resident):
    """Regression: this used to be a KeyError -> HTML 500."""
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD})
    assert res.status_code == 400
    assert res.get_json()["error"] == "new_password is required"
```
</details>


### TC-044 · Change password missing old password returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "new_password": "Brand@New1"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "old_password is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "old_password is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_missing_old_password_returns_400(client, seed, resident):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"new_password": "Brand@New1"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "old_password is required"
```
</details>


### TC-045 · Change password wrong old password returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "NotMyPassword",
      "new_password": "Brand@New1"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Old password is incorrect"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Old password is incorrect"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_wrong_old_password_returns_400(client, seed, resident):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": "NotMyPassword", "new_password": "Brand@New1"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "Old password is incorrect"
```
</details>


### TC-046 · Change password shorter than six chars returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "Pass@123",
      "new_password": "a"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "New password must be at least 6 characters"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "New password must be at least 6 characters"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("short", ["a", "abcde", "12345"])
def test_change_password_shorter_than_six_chars_returns_400(client, seed, resident, short):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD, "new_password": short})
    assert res.status_code == 400
    assert res.get_json()["error"] == "New password must be at least 6 characters"
```
</details>


### TC-047 · Change password shorter than six chars returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "Pass@123",
      "new_password": "abcde"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "New password must be at least 6 characters"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "New password must be at least 6 characters"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("short", ["a", "abcde", "12345"])
def test_change_password_shorter_than_six_chars_returns_400(client, seed, resident, short):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD, "new_password": short})
    assert res.status_code == 400
    assert res.get_json()["error"] == "New password must be at least 6 characters"
```
</details>


### TC-048 · Change password shorter than six chars returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "Pass@123",
      "new_password": "12345"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "New password must be at least 6 characters"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "New password must be at least 6 characters"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("short", ["a", "abcde", "12345"])
def test_change_password_shorter_than_six_chars_returns_400(client, seed, resident, short):
    res = client.put("/api/auth/change-password", headers=resident,
                     json={"old_password": PASSWORD, "new_password": short})
    assert res.status_code == 400
    assert res.get_json()["error"] == "New password must be at least 6 characters"
```
</details>


### TC-049 · Change password malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_change_password_malformed_body_returns_400(client, seed, resident, raw, expected):
    res = client.put("/api/auth/change-password", headers=resident,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-050 · Change password malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_change_password_malformed_body_returns_400(client, seed, resident, raw, expected):
    res = client.put("/api/auth/change-password", headers=resident,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-051 · Change password malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    "str"
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_change_password_malformed_body_returns_400(client, seed, resident, raw, expected):
    res = client.put("/api/auth/change-password", headers=resident,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-052 · Change password without token returns 401

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "Pass@123",
      "new_password": "Brand@New1"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_without_token_returns_401(client, seed):
    res = client.put("/api/auth/change-password",
                     json={"old_password": PASSWORD, "new_password": "Brand@New1"})
    assert res.status_code == 401
```
</details>


---

## Members & Apartments

`Backend/tests/test_members.py` · US-09, US-04 · **96/96 passed**


### TC-053 · List apartments returns seeded flats

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "block": "A",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1
      },
      {
        "block": "B",
        "flat_number": "B-202",
        "floor": 2,
        "id": 2
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_apartments_returns_seeded_flats(client, seed, admin):
    res = client.get("/api/members/apartments", headers=admin)
    assert res.status_code == 200
    assert {a["flat_number"] for a in res.get_json()} == {"A-101", "B-202"}
```
</details>


### TC-054 · List apartments exposes block and floor

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "block": "A",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1
      },
      {
        "block": "B",
        "flat_number": "B-202",
        "floor": 2,
        "id": 2
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_apartments_exposes_block_and_floor(client, seed, admin):
    body = client.get("/api/members/apartments", headers=admin).get_json()
    a101 = next(a for a in body if a["flat_number"] == "A-101")
    assert (a101["id"], a101["block"], a101["floor"]) == (seed["apartment_id"], "A", 1)
```
</details>


### TC-055 · List apartments is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "block": "A",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1
      },
      {
        "block": "B",
        "flat_number": "B-202",
        "floor": 2,
        "id": 2
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_apartments_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/members/apartments", headers=headers).status_code == 200
```
</details>


### TC-056 · List apartments is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "block": "A",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1
      },
      {
        "block": "B",
        "flat_number": "B-202",
        "floor": 2,
        "id": 2
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_apartments_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/members/apartments", headers=headers).status_code == 200
```
</details>


### TC-057 · List apartments is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "block": "A",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1
      },
      {
        "block": "B",
        "flat_number": "B-202",
        "floor": 2,
        "id": 2
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_apartments_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/members/apartments", headers=headers).status_code == 200
```
</details>


### TC-058 · List apartments is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "block": "A",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1
      },
      {
        "block": "B",
        "flat_number": "B-202",
        "floor": 2,
        "id": 2
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_apartments_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/members/apartments", headers=headers).status_code == 200
```
</details>


### TC-059 · List apartments without token returns 401

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_apartments_without_token_returns_401(client, seed):
    assert client.get("/api/members/apartments").status_code == 401
```
</details>


### TC-060 · Create apartment returns 201

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "C-303",
      "block": "C",
      "floor": 3
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "block": "C",
      "flat_number": "C-303",
      "floor": 3,
      "id": 3
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_returns_201(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "C-303", "block": "C", "floor": 3})
    assert res.status_code == 201
    body = res.get_json()
    assert body["flat_number"] == "C-303"
    assert body["block"] == "C"
    assert body["floor"] == 3
    assert body["id"]
```
</details>


### TC-061 · Create apartment accepts a numeric string floor

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "D-404",
      "floor": "4"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "block": null,
      "flat_number": "D-404",
      "floor": 4,
      "id": 3
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_accepts_a_numeric_string_floor(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "D-404", "floor": "4"})
    assert res.status_code == 201
    assert res.get_json()["floor"] == 4
```
</details>


### TC-062 · Create apartment missing flat number returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "block": "C"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "flat_number is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "flat_number is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_missing_flat_number_returns_400(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin, json={"block": "C"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "flat_number is required"
```
</details>


### TC-063 · Create apartment non numeric floor returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "E-505",
      "floor": "top"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "floor must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "floor must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_non_numeric_floor_returns_400(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "E-505", "floor": "top"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "floor must be a whole number"
```
</details>


### TC-064 · Create apartment malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_apartment_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/apartments", headers=admin,
                      data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-065 · Create apartment malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_apartment_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/apartments", headers=admin,
                      data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-066 · Create apartment malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    "str"
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_apartment_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/apartments", headers=admin,
                      data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-067 · Create apartment duplicate flat number returns 409

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "A-101"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Flat number already exists"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Flat number already exists"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_duplicate_flat_number_returns_409(client, seed, admin):
    res = client.post("/api/members/apartments", headers=admin,
                      json={"flat_number": "A-101"})
    assert res.status_code == 409
    assert res.get_json()["error"] == "Flat number already exists"
```
</details>


### TC-068 · Create apartment as resident returns 403

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "C-303"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_as_resident_returns_403(client, seed, resident):
    res = client.post("/api/members/apartments", headers=resident,
                      json={"flat_number": "C-303"})
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-069 · Create apartment as worker returns 403

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "C-303"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_as_worker_returns_403(client, seed, worker):
    res = client.post("/api/members/apartments", headers=worker,
                      json={"flat_number": "C-303"})
    assert res.status_code == 403
```
</details>


### TC-070 · Create apartment as treasurer returns 201

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "C-303"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "block": null,
      "flat_number": "C-303",
      "floor": null,
      "id": 3
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_as_treasurer_returns_201(client, seed, treasurer):
    res = client.post("/api/members/apartments", headers=treasurer,
                      json={"flat_number": "C-303"})
    assert res.status_code == 201
```
</details>


### TC-071 · Create apartment without token returns 401

**Page being tested:** `POST http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body:
    ```json
    {
      "flat_number": "C-303"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_apartment_without_token_returns_401(client, seed):
    res = client.post("/api/members/apartments", json={"flat_number": "C-303"})
    assert res.status_code == 401
```
</details>


### TC-072 · Update apartment renames the flat

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body:
    ```json
    {
      "flat_number": "B-999"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `flat_number` == "B-999"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "block": "B",
      "flat_number": "B-999",
      "floor": 2,
      "id": 2
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_renames_the_flat(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"flat_number": "B-999"})
    assert res.status_code == 200
    assert res.get_json()["flat_number"] == "B-999"
```
</details>


### TC-073 · Update apartment updates block and floor

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body:
    ```json
    {
      "block": "Z",
      "floor": 9
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "block": "Z",
      "flat_number": "B-202",
      "floor": 9,
      "id": 2
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_updates_block_and_floor(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"block": "Z", "floor": 9})
    assert res.status_code == 200
    assert (res.get_json()["block"], res.get_json()["floor"]) == ("Z", 9)
```
</details>


### TC-074 · Update apartment blank flat number returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body:
    ```json
    {
      "flat_number": "   "
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "flat_number is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "flat_number is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_blank_flat_number_returns_400(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"flat_number": "   "})
    assert res.status_code == 400
    assert res.get_json()["error"] == "flat_number is required"
```
</details>


### TC-075 · Update apartment bad floor returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body:
    ```json
    {
      "floor": "penthouse"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "floor must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "floor must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_bad_floor_returns_400(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"floor": "penthouse"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "floor must be a whole number"
```
</details>


### TC-076 · Update apartment duplicate flat number returns 409

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body:
    ```json
    {
      "flat_number": "A-101"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Flat number already exists"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Flat number already exists"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_duplicate_flat_number_returns_409(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=admin, json={"flat_number": "A-101"})
    assert res.status_code == 409
    assert res.get_json()["error"] == "Flat number already exists"
```
</details>


### TC-077 · Update apartment to its own flat number returns 200

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/1`
- JSON body:
    ```json
    {
      "flat_number": "A-101"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "block": "A",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_to_its_own_flat_number_returns_200(client, seed, admin):
    res = client.put(f"/api/members/apartments/{seed['apartment_id']}",
                     headers=admin, json={"flat_number": "A-101"})
    assert res.status_code == 200
```
</details>


### TC-078 · Update unknown apartment returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/9999`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/9999`
- JSON body:
    ```json
    {
      "flat_number": "X-000"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_unknown_apartment_returns_404(client, seed, admin):
    res = client.put("/api/members/apartments/9999", headers=admin,
                     json={"flat_number": "X-000"})
    assert res.status_code == 404
```
</details>


### TC-079 · Update apartment as resident returns 403

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body:
    ```json
    {
      "flat_number": "B-999"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_as_resident_returns_403(client, seed, resident):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     headers=resident, json={"flat_number": "B-999"})
    assert res.status_code == 403
```
</details>


### TC-080 · Update apartment without token returns 401

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body:
    ```json
    {
      "flat_number": "B-999"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_apartment_without_token_returns_401(client, seed):
    res = client.put(f"/api/members/apartments/{seed['other_apartment_id']}",
                     json={"flat_number": "B-999"})
    assert res.status_code == 401
```
</details>


### TC-081 · Delete empty apartment returns 200

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Apartment deleted"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Apartment deleted"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_empty_apartment_returns_200(client, seed, admin):
    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                        headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Apartment deleted"
```
</details>


### TC-082 · Delete apartment removes it from the list

**Page being tested:** `GET http://127.0.0.1:5000/api/members/apartments`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/apartments`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `DELETE /api/members/apartments/2` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "block": "A",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_apartment_removes_it_from_the_list(client, seed, admin):
    client.delete(f"/api/members/apartments/{seed['other_apartment_id']}", headers=admin)
    listing = client.get("/api/members/apartments", headers=admin).get_json()
    assert {a["flat_number"] for a in listing} == {"A-101"}
```
</details>


### TC-083 · Delete apartment with residents returns 409

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/apartments/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/apartments/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `409`

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Cannot delete a flat that still has residents or invoices"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_apartment_with_residents_returns_409(client, seed, admin):
    res = client.delete(f"/api/members/apartments/{seed['apartment_id']}", headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == \
        "Cannot delete a flat that still has residents or invoices"
```
</details>


### TC-084 · Delete apartment with invoices returns 409

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `409`

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Cannot delete a flat that still has residents or invoices"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_apartment_with_invoices_returns_409(client, app, seed, admin):
    with app.app_context():
        db.session.add(Invoice(apartment_id=seed["other_apartment_id"],
                               month=6, year=2026, amount=1500))
        db.session.commit()

    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                        headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == \
        "Cannot delete a flat that still has residents or invoices"
```
</details>


### TC-085 · Delete unknown apartment returns 404

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/apartments/9999`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/apartments/9999`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_unknown_apartment_returns_404(client, seed, admin):
    assert client.delete("/api/members/apartments/9999", headers=admin).status_code == 404
```
</details>


### TC-086 · Delete apartment as resident returns 403

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_apartment_as_resident_returns_403(client, seed, resident):
    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                        headers=resident)
    assert res.status_code == 403
```
</details>


### TC-087 · Delete apartment without token returns 401

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/apartments/2`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/apartments/2`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_apartment_without_token_returns_401(client, seed):
    res = client.delete(f"/api/members/apartments/{seed['other_apartment_id']}")
    assert res.status_code == 401
```
</details>


### TC-088 · List members returns the seeded resident

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "apartment_id": 1,
        "block": "A",
        "email": "resident@test.com",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1,
        "is_active": true,
        "is_owner": false,
        "move_in_date": null,
        "move_out_date": null,
        "name": "Ravi Resident",
        "phone": null,
        "role": "TENANT",
        "user_id": 4
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_members_returns_the_seeded_resident(client, seed, admin):
    res = client.get("/api/members/", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1
    assert body[0]["id"] == seed["resident_record_id"]
    assert body[0]["user_id"] == seed["resident_id"]
```
</details>


### TC-089 · List members includes flat details

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "apartment_id": 1,
        "block": "A",
        "email": "resident@test.com",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1,
        "is_active": true,
        "is_owner": false,
        "move_in_date": null,
        "move_out_date": null,
        "name": "Ravi Resident",
        "phone": null,
        "role": "TENANT",
        "user_id": 4
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_members_includes_flat_details(client, seed, admin):
    row = client.get("/api/members/", headers=admin).get_json()[0]
    assert row["flat_number"] == "A-101"
    assert row["block"] == "A"
    assert row["floor"] == 1
    assert row["is_owner"] is False
```
</details>


### TC-090 · List members as resident returns 403

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_members_as_resident_returns_403(client, seed, resident):
    res = client.get("/api/members/", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-091 · List members as worker returns 403

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_members_as_worker_returns_403(client, seed, worker):
    assert client.get("/api/members/", headers=worker).status_code == 403
```
</details>


### TC-092 · List members as treasurer returns 200

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "apartment_id": 1,
        "block": "A",
        "email": "resident@test.com",
        "flat_number": "A-101",
        "floor": 1,
        "id": 1,
        "is_active": true,
        "is_owner": false,
        "move_in_date": null,
        "move_out_date": null,
        "name": "Ravi Resident",
        "phone": null,
        "role": "TENANT",
        "user_id": 4
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_members_as_treasurer_returns_200(client, seed, treasurer):
    assert client.get("/api/members/", headers=treasurer).status_code == 200
```
</details>


### TC-093 · List members without token returns 401

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_members_without_token_returns_401(client, seed):
    assert client.get("/api/members/").status_code == 401
```
</details>


### TC-094 · Create member returns 201

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 2,
      "phone": "9222222222",
      "is_owner": true,
      "move_in_date": "2026-01-15"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "apartment_id": 2,
      "block": "B",
      "email": "manoj@test.com",
      "flat_number": "B-202",
      "floor": 2,
      "id": 2,
      "is_active": true,
      "is_owner": true,
      "move_in_date": "2026-01-15",
      "move_out_date": null,
      "name": "Manoj Member",
      "phone": "9222222222",
      "role": "OWNER",
      "user_id": 7
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_returns_201(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["other_apartment_id"], phone="9222222222",
        is_owner=True, move_in_date="2026-01-15",
    ))
    assert res.status_code == 201
    body = res.get_json()
    assert body["email"] == "manoj@test.com"
    assert body["role"] == "OWNER"
    assert body["apartment_id"] == seed["other_apartment_id"]
    assert body["flat_number"] == "B-202"
    assert body["is_owner"] is True
    assert body["move_in_date"] == "2026-01-15"
```
</details>


### TC-095 · Create member can log in afterwards

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    {
      "email": "manoj@test.com",
      "password": "<hidden>"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/members/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Login successful",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:58:57.221618",
        "email": "manoj@test.com",
        "id": 7,
        "is_active": true,
        "name": "Manoj Member",
        "phone": null,
        "role": "OWNER"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_can_log_in_afterwards(client, seed, admin):
    client.post("/api/members/", headers=admin,
                json=_member_payload(apartment_id=seed["apartment_id"]))
    res = client.post("/api/auth/login",
                      json={"email": "manoj@test.com", "password": "Secret@123"})
    assert res.status_code == 200
```
</details>


### TC-096 · Create member appears in the listing

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/members/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"apartment_id": 1, "block": "A", "email": "resident@test.com", "flat_number": "A-101", "floor": 1, "id": 1, "is_active": true, "is_owner": false, "move_in_date": null, "move_out_date": null, "name": "Ravi Resident", "phone": null, "role": "TENANT", "user_id": 4}, {"apartment_id": 1, "block": "A", "email": "manoj@test.com", "flat_number": "A-101", "floor": 1, "id": 2, "is_active": true, "is_owne…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_appears_in_the_listing(client, seed, admin):
    client.post("/api/members/", headers=admin,
                json=_member_payload(apartment_id=seed["apartment_id"]))
    body = client.get("/api/members/", headers=admin).get_json()
    assert len(body) == 2
```
</details>


### TC-097 · Create member missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "name is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing",
                         ["name", "email", "password", "role", "apartment_id"])
def test_create_member_missing_required_field_returns_400(client, seed, admin, missing):
    payload = _member_payload(apartment_id=seed["apartment_id"])
    payload.pop(missing)

    res = client.post("/api/members/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-098 · Create member missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "email is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing",
                         ["name", "email", "password", "role", "apartment_id"])
def test_create_member_missing_required_field_returns_400(client, seed, admin, missing):
    payload = _member_payload(apartment_id=seed["apartment_id"])
    payload.pop(missing)

    res = client.post("/api/members/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-099 · Create member missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "role": "OWNER",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "password is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing",
                         ["name", "email", "password", "role", "apartment_id"])
def test_create_member_missing_required_field_returns_400(client, seed, admin, missing):
    payload = _member_payload(apartment_id=seed["apartment_id"])
    payload.pop(missing)

    res = client.post("/api/members/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-100 · Create member missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "role is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing",
                         ["name", "email", "password", "role", "apartment_id"])
def test_create_member_missing_required_field_returns_400(client, seed, admin, missing):
    payload = _member_payload(apartment_id=seed["apartment_id"])
    payload.pop(missing)

    res = client.post("/api/members/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-101 · Create member missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "apartment_id is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing",
                         ["name", "email", "password", "role", "apartment_id"])
def test_create_member_missing_required_field_returns_400(client, seed, admin, missing):
    payload = _member_payload(apartment_id=seed["apartment_id"])
    payload.pop(missing)

    res = client.post("/api/members/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-102 · Create member unknown role returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "WIZARD",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "role must be one of: ADMIN, TENANT, OWNER, TREASURER, WORKER, COMMITTEE_MEMBER, AUDITOR, SYSTEM_ADMIN"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_unknown_role_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        role="WIZARD", apartment_id=seed["apartment_id"]))
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("role must be one of:")
```
</details>


### TC-103 · Create member bad move in date returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1,
      "move_in_date": "not-a-date"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "move_in_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "move_in_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_bad_move_in_date_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], move_in_date="not-a-date"))
    assert res.status_code == 400
    assert res.get_json()["error"] == "move_in_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-104 · Create member non numeric apartment id returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": "ground"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "apartment_id must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "apartment_id must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_non_numeric_apartment_id_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin,
                      json=_member_payload(apartment_id="ground"))
    assert res.status_code == 400
    assert res.get_json()["error"] == "apartment_id must be a whole number"
```
</details>


### TC-105 · Create member zero apartment id returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 0
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "apartment_id must be at least 1"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "apartment_id must be at least 1"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_zero_apartment_id_returns_400(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(apartment_id=0))
    assert res.status_code == 400
    assert res.get_json()["error"] == "apartment_id must be at least 1"
```
</details>


### TC-106 · Create member unknown apartment returns 404

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 9999
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`
- JSON: `error` == "Apartment not found"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "Apartment not found"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_unknown_apartment_returns_404(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(apartment_id=9999))
    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"
```
</details>


### TC-107 · Create member malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-108 · Create member malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-109 · Create member malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    "str"
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/members/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-110 · Create member duplicate email returns 409

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "resident@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Email already registered"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Email already registered"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_duplicate_email_returns_409(client, seed, admin):
    res = client.post("/api/members/", headers=admin, json=_member_payload(
        email="resident@test.com", apartment_id=seed["apartment_id"]))
    assert res.status_code == 409
    assert res.get_json()["error"] == "Email already registered"
```
</details>


### TC-111 · Create member duplicate phone returns 409

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "second@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1,
      "phone": "9333333333"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/members/` → 201

**Expected Output:**

- HTTP Status Code: `201 or 409`
- JSON: `error` == "Phone number already registered"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Phone number already registered"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_duplicate_phone_returns_409(client, seed, admin):
    first = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], phone="9333333333"))
    assert first.status_code == 201

    second = client.post("/api/members/", headers=admin, json=_member_payload(
        email="second@test.com", apartment_id=seed["apartment_id"], phone="9333333333"))
    assert second.status_code == 409
    assert second.get_json()["error"] == "Phone number already registered"
```
</details>


### TC-112 · Blank phone must normalise to NULL — users.phone is UNIQUE

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "second@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1,
      "phone": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/members/` → 201

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `phone` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "second@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 3,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Manoj Member",
      "phone": null,
      "role": "OWNER",
      "user_id": 8
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_two_members_with_blank_phone_both_succeed(client, seed, admin):
    """Blank phone must normalise to NULL — users.phone is UNIQUE."""
    first = client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], phone=""))
    second = client.post("/api/members/", headers=admin, json=_member_payload(
        email="second@test.com", apartment_id=seed["apartment_id"], phone=""))
    assert (first.status_code, second.status_code) == (201, 201)
    assert first.get_json()["phone"] is None
```
</details>


### TC-113 · Create member as resident returns 403

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_as_resident_returns_403(client, seed, resident):
    res = client.post("/api/members/", headers=resident,
                      json=_member_payload(apartment_id=seed["apartment_id"]))
    assert res.status_code == 403
```
</details>


### TC-114 · Create member without token returns 401

**Page being tested:** `POST http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body:
    ```json
    {
      "name": "Manoj Member",
      "email": "manoj@test.com",
      "password": "<hidden>",
      "role": "OWNER",
      "apartment_id": 1
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_member_without_token_returns_401(client, seed):
    res = client.post("/api/members/", json=_member_payload(apartment_id=seed["apartment_id"]))
    assert res.status_code == 401
```
</details>


### TC-115 · List workers returns only worker role users

**Page being tested:** `GET http://127.0.0.1:5000/api/members/workers`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/workers`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "email": "worker@test.com",
        "id": 6,
        "name": "Ramesh Worker"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_workers_returns_only_worker_role_users(client, seed, admin):
    res = client.get("/api/members/workers", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert [w["email"] for w in body] == ["worker@test.com"]
```
</details>


### TC-116 · complaints.assigned_worker_id points at users.id, never residents.id

**Page being tested:** `GET http://127.0.0.1:5000/api/members/workers`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/workers`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "email": "worker@test.com",
        "id": 6,
        "name": "Ramesh Worker"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_workers_id_is_the_users_id(client, seed, admin):
    """complaints.assigned_worker_id points at users.id, never residents.id."""
    body = client.get("/api/members/workers", headers=admin).get_json()
    assert body[0]["id"] == seed["worker_id"]
```
</details>


### TC-117 · List workers returns id name email only

**Page being tested:** `GET http://127.0.0.1:5000/api/members/workers`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/workers`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "email": "worker@test.com",
        "id": 6,
        "name": "Ramesh Worker"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_workers_returns_id_name_email_only(client, seed, admin):
    body = client.get("/api/members/workers", headers=admin).get_json()
    assert set(body[0]) == {"id", "name", "email"}
```
</details>


### TC-118 · List workers includes newly added workers

**Page being tested:** `GET http://127.0.0.1:5000/api/members/workers`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/workers`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/members/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "email": "anil@test.com",
        "id": 7,
        "name": "Anil Worker"
      },
      {
        "email": "worker@test.com",
        "id": 6,
        "name": "Ramesh Worker"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_workers_includes_newly_added_workers(client, seed, admin):
    client.post("/api/members/", headers=admin, json=_member_payload(
        name="Anil Worker", email="anil@test.com",
        role="WORKER", apartment_id=seed["apartment_id"]))

    body = client.get("/api/members/workers", headers=admin).get_json()
    assert [w["name"] for w in body] == ["Anil Worker", "Ramesh Worker"]
```
</details>


### TC-119 · List workers as resident returns 403

**Page being tested:** `GET http://127.0.0.1:5000/api/members/workers`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/workers`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_workers_as_resident_returns_403(client, seed, resident):
    assert client.get("/api/members/workers", headers=resident).status_code == 403
```
</details>


### TC-120 · List workers without token returns 401

**Page being tested:** `GET http://127.0.0.1:5000/api/members/workers`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/workers`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_workers_without_token_returns_401(client, seed):
    assert client.get("/api/members/workers").status_code == 401
```
</details>


### TC-121 · Get member returns 200

**Page being tested:** `GET http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_get_member_returns_200(client, seed, admin):
    res = client.get(f"/api/members/{seed['resident_record_id']}", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == seed["resident_record_id"]
    assert body["email"] == "resident@test.com"
    assert body["flat_number"] == "A-101"
```
</details>


### TC-122 · Get member is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_get_member_is_open_to_every_role(client, seed, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    res = client.get(f"/api/members/{seed['resident_record_id']}", headers=headers)
    assert res.status_code == 200
```
</details>


### TC-123 · Get member is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_get_member_is_open_to_every_role(client, seed, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    res = client.get(f"/api/members/{seed['resident_record_id']}", headers=headers)
    assert res.status_code == 200
```
</details>


### TC-124 · Get member is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_get_member_is_open_to_every_role(client, seed, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    res = client.get(f"/api/members/{seed['resident_record_id']}", headers=headers)
    assert res.status_code == 200
```
</details>


### TC-125 · Get member is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_get_member_is_open_to_every_role(client, seed, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    res = client.get(f"/api/members/{seed['resident_record_id']}", headers=headers)
    assert res.status_code == 200
```
</details>


### TC-126 · Get unknown member returns 404

**Page being tested:** `GET http://127.0.0.1:5000/api/members/9999`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/9999`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_get_unknown_member_returns_404(client, seed, admin):
    assert client.get("/api/members/9999", headers=admin).status_code == 404
```
</details>


### TC-127 · Get member without token returns 401

**Page being tested:** `GET http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_get_member_without_token_returns_401(client, seed):
    assert client.get(f"/api/members/{seed['resident_record_id']}").status_code == 401
```
</details>


### TC-128 · Update member changes name and role

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "name": "Ravi Renamed",
      "role": "OWNER"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Renamed",
      "phone": null,
      "role": "OWNER",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_changes_name_and_role(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"name": "Ravi Renamed", "role": "OWNER"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["name"] == "Ravi Renamed"
    assert body["role"] == "OWNER"
```
</details>


### TC-129 · Update member changes resident fields

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "is_owner": true,
      "move_in_date": "2025-03-01",
      "move_out_date": "2026-03-01"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": true,
      "move_in_date": "2025-03-01",
      "move_out_date": "2026-03-01",
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_changes_resident_fields(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"is_owner": True, "move_in_date": "2025-03-01",
                           "move_out_date": "2026-03-01"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["is_owner"] is True
    assert body["move_in_date"] == "2025-03-01"
    assert body["move_out_date"] == "2026-03-01"
```
</details>


### TC-130 · Update member blank phone clears it

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "phone": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `phone` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_blank_phone_clears_it(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"phone": ""})
    assert res.status_code == 200
    assert res.get_json()["phone"] is None
```
</details>


### TC-131 · Update member unknown role returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "role": "WIZARD"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "role must be one of: ADMIN, TENANT, OWNER, TREASURER, WORKER, COMMITTEE_MEMBER, AUDITOR, SYSTEM_ADMIN"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_unknown_role_returns_400(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"role": "WIZARD"})
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("role must be one of:")
```
</details>


### TC-132 · Update member bad move in date returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "move_in_date": "not-a-date"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "move_in_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "move_in_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_bad_move_in_date_returns_400(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"move_in_date": "not-a-date"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "move_in_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-133 · Update member bad move out date returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "move_out_date": "31-12-2026"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "move_out_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "move_out_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_bad_move_out_date_returns_400(client, seed, admin):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"move_out_date": "31-12-2026"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "move_out_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-134 · Update member duplicate phone returns 409

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "phone": "9444444444"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/members/` → 201

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Phone number already registered"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Phone number already registered"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_duplicate_phone_returns_409(client, seed, admin):
    client.post("/api/members/", headers=admin, json=_member_payload(
        apartment_id=seed["apartment_id"], phone="9444444444"))

    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"phone": "9444444444"})
    assert res.status_code == 409
    assert res.get_json()["error"] == "Phone number already registered"
```
</details>


### TC-135 · Update member keeping its own phone returns 200

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "phone": "9555555555"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `PUT /api/members/1` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": true,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": "9555555555",
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_keeping_its_own_phone_returns_200(client, seed, admin):
    client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
               json={"phone": "9555555555"})
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     json={"phone": "9555555555"})
    assert res.status_code == 200
```
</details>


### TC-136 · Update member malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-137 · Update member malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-138 · Update member malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    "str"
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_member_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=admin,
                     data=raw, content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-139 · Update unknown member returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/9999`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/9999`
- JSON body:
    ```json
    {
      "name": "Nobody"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_unknown_member_returns_404(client, seed, admin):
    res = client.put("/api/members/9999", headers=admin, json={"name": "Nobody"})
    assert res.status_code == 404
```
</details>


### TC-140 · Update member as resident returns 403

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "name": "Self Service"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_as_resident_returns_403(client, seed, resident):
    res = client.put(f"/api/members/{seed['resident_record_id']}", headers=resident,
                     json={"name": "Self Service"})
    assert res.status_code == 403
```
</details>


### TC-141 · Update member without token returns 401

**Page being tested:** `PUT http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body:
    ```json
    {
      "name": "X"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_member_without_token_returns_401(client, seed):
    res = client.put(f"/api/members/{seed['resident_record_id']}", json={"name": "X"})
    assert res.status_code == 401
```
</details>


### TC-142 · Deactivate member returns 200

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Member deactivated"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Member deactivated"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_deactivate_member_returns_200(client, seed, admin):
    res = client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Member deactivated"
```
</details>


### TC-143 · Deactivate member is a soft delete

**Page being tested:** `GET http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `DELETE /api/members/1` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "block": "A",
      "email": "resident@test.com",
      "flat_number": "A-101",
      "floor": 1,
      "id": 1,
      "is_active": false,
      "is_owner": false,
      "move_in_date": null,
      "move_out_date": null,
      "name": "Ravi Resident",
      "phone": null,
      "role": "TENANT",
      "user_id": 4
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_deactivate_member_is_a_soft_delete(client, seed, admin):
    client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)
    body = client.get(f"/api/members/{seed['resident_record_id']}", headers=admin).get_json()
    assert body["is_active"] is False
```
</details>


### TC-144 · Deactivate worker removes them from the worker list

**Page being tested:** `GET http://127.0.0.1:5000/api/members/workers`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/workers`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/members/` → 201, `DELETE /api/members/2` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "email": "worker@test.com",
        "id": 6,
        "name": "Ramesh Worker"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_deactivate_worker_removes_them_from_the_worker_list(client, seed, admin):
    created = client.post("/api/members/", headers=admin, json=_member_payload(
        name="Anil Worker", email="anil@test.com",
        role="WORKER", apartment_id=seed["apartment_id"])).get_json()

    client.delete(f"/api/members/{created['id']}", headers=admin)
    body = client.get("/api/members/workers", headers=admin).get_json()
    assert [w["email"] for w in body] == ["worker@test.com"]
```
</details>


### TC-145 · Deactivated member token returns 403

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `DELETE /api/members/1` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "Account is deactivated"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "Account is deactivated"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_deactivated_member_token_returns_403(client, seed, admin, resident):
    client.delete(f"/api/members/{seed['resident_record_id']}", headers=admin)
    res = client.get("/api/auth/me", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "Account is deactivated"
```
</details>


### TC-146 · Deactivate unknown member returns 404

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/9999`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/9999`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_deactivate_unknown_member_returns_404(client, seed, admin):
    assert client.delete("/api/members/9999", headers=admin).status_code == 404
```
</details>


### TC-147 · Deactivate member as resident returns 403

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_deactivate_member_as_resident_returns_403(client, seed, resident):
    res = client.delete(f"/api/members/{seed['resident_record_id']}", headers=resident)
    assert res.status_code == 403
```
</details>


### TC-148 · Deactivate member without token returns 401

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/1`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_deactivate_member_without_token_returns_401(client, seed):
    assert client.delete(f"/api/members/{seed['resident_record_id']}").status_code == 401
```
</details>


---

## Complaints

`Backend/tests/test_complaints.py` · US-02, US-03, US-04 · **44/44 passed**


### TC-149 · Resident can raise complaint

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "Lift is stuck",
      "description": "Lift stops between floors 1 and 2.",
      "category": "ELECTRICAL",
      "priority": "HIGH",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `assigned_worker_id` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "ELECTRICAL",
      "created_at": "2026-08-02 11:57:04.485026",
      "description": "Lift stops between floors 1 and 2.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "HIGH",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Lift is stuck"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_raise_complaint(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Lift is stuck",
        "description": "Lift stops between floors 1 and 2.",
        "category": "ELECTRICAL",
        "priority": "HIGH",
        "apartment_id": seed["apartment_id"],
    }, headers=resident)

    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Lift is stuck"
    assert body["category"] == "ELECTRICAL"
    assert body["priority"] == "HIGH"
    assert body["status"] == "OPEN"
    assert body["flat_number"] == "A-101"
    assert body["raised_by"] == seed["resident_id"]
    assert body["assigned_worker_id"] is None
```
</details>


### TC-150 · Priority defaults to medium

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "Leaking kitchen tap",
      "description": "Water drips continuously under the sink.",
      "category": "PLUMBING",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:04.817119",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Leaking kitchen tap"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_priority_defaults_to_medium(client, resident, seed):
    body = raise_complaint(client, resident, seed["apartment_id"])
    assert body["priority"] == "MEDIUM"
```
</details>


### TC-151 · Resident lists only own complaints

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "apartment_id": 1,
        "assigned_worker_id": null,
        "assigned_worker_name": null,
        "category": "PLUMBING",
        "created_at": "2026-08-02 11:57:05.224411",
        "description": "Water drips continuously under the sink.",
        "flat_number": "A-101",
        "id": 1,
        "priority": "MEDIUM",
        "raised_by": 4,
        "raised_by_name": "Ravi Resident",
        "resolved_at": null,
        "status": "OPEN",
        "title": "Leaking kitchen tap"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_lists_only_own_complaints(client, admin, resident, seed):
    mine = raise_complaint(client, resident, seed["apartment_id"])
    raise_complaint(client, admin, seed["other_apartment_id"],
                    title="Admin raised elsewhere")

    res = client.get("/api/complaints/", headers=resident)
    assert res.status_code == 200
    ids = [c["id"] for c in res.get_json()]
    assert ids == [mine["id"]]
```
</details>


### TC-152 · Admin lists all complaints

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"apartment_id": 2, "assigned_worker_id": null, "assigned_worker_name": null, "category": "PLUMBING", "created_at": "2026-08-02 11:57:05.616544", "description": "Water drips continuously under the sink.", "flat_number": "B-202", "id": 2, "priority": "MEDIUM", "raised_by": 1, "raised_by_name": "Priya Admin", "resolved_at": null, "status": "OPEN", "title": "Second"}, {"apartment_id": 1, "assigned_…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_lists_all_complaints(client, admin, resident, seed):
    raise_complaint(client, resident, seed["apartment_id"])
    raise_complaint(client, admin, seed["other_apartment_id"], title="Second")

    res = client.get("/api/complaints/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 2
```
</details>


### TC-153 · Get complaint detail includes updates

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/assign` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"apartment_id": 1, "assigned_worker_id": 6, "assigned_worker_name": "Ramesh Worker", "category": "PLUMBING", "created_at": "2026-08-02 11:57:06.022541", "description": "Water drips continuously under the sink.", "flat_number": "A-101", "id": 1, "priority": "MEDIUM", "raised_by": 4, "raised_by_name": "Ravi Resident", "resolved_at": null, "status": "ASSIGNED", "title": "Leaking kitchen tap", "upda…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_get_complaint_detail_includes_updates(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    client.put(f"/api/complaints/{complaint['id']}/assign",
               json={"worker_id": seed["worker_id"]}, headers=admin)

    res = client.get(f"/api/complaints/{complaint['id']}", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == complaint["id"]
    assert [u["status"] for u in body["updates"]] == ["ASSIGNED"]
```
</details>


### TC-154 · Admin can delete complaint

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `DELETE /api/complaints/1` → 200

**Expected Output:**

- HTTP Status Code: `200 or 404`
- JSON: `message` == "Complaint deleted"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_delete_complaint(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.delete(f"/api/complaints/{complaint['id']}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Complaint deleted"
    assert client.get(f"/api/complaints/{complaint['id']}",
                      headers=admin).status_code == 404
```
</details>


### TC-155 · COMMITTEE_MEMBER is an admin role even though it is not a finance role

**Page being tested:** `DELETE http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (9): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Complaint deleted"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_committee_member_may_delete_complaint(client, admin, resident,
                                               tokens, seed):
    """COMMITTEE_MEMBER is an admin role even though it is not a finance role."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.delete(f"/api/complaints/{complaint['id']}",
                        headers=committee_headers(tokens))
    assert res.status_code == 200
```
</details>


### TC-156 · Raise complaint missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "category": "PLUMBING",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "title is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["title", "category", "apartment_id"])
def test_raise_complaint_missing_required_field_returns_400(
        client, resident, seed, missing):
    payload = {"title": "T", "category": "PLUMBING",
               "apartment_id": seed["apartment_id"]}
    payload.pop(missing)

    res = client.post("/api/complaints/", json=payload, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-157 · Raise complaint missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "T",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "category is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["title", "category", "apartment_id"])
def test_raise_complaint_missing_required_field_returns_400(
        client, resident, seed, missing):
    payload = {"title": "T", "category": "PLUMBING",
               "apartment_id": seed["apartment_id"]}
    payload.pop(missing)

    res = client.post("/api/complaints/", json=payload, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-158 · Raise complaint missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "T",
      "category": "PLUMBING"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "apartment_id is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["title", "category", "apartment_id"])
def test_raise_complaint_missing_required_field_returns_400(
        client, resident, seed, missing):
    payload = {"title": "T", "category": "PLUMBING",
               "apartment_id": seed["apartment_id"]}
    payload.pop(missing)

    res = client.post("/api/complaints/", json=payload, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-159 · Raise complaint bad category returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "Hungry",
      "category": "FOOD",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "category must be one of: PLUMBING, ELECTRICAL, CLEANING, SECURITY, OTHER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_raise_complaint_bad_category_returns_400(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Hungry", "category": "FOOD",
        "apartment_id": seed["apartment_id"],
    }, headers=resident)

    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")
```
</details>


### TC-160 · Raise complaint bad priority returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "Noisy",
      "category": "OTHER",
      "priority": "URGENT",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "priority must be one of: LOW, MEDIUM, HIGH"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_raise_complaint_bad_priority_returns_400(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Noisy", "category": "OTHER", "priority": "URGENT",
        "apartment_id": seed["apartment_id"],
    }, headers=resident)

    assert res.status_code == 400
    assert res.get_json()["error"].startswith("priority must be one of:")
```
</details>


### TC-161 · Raise complaint non numeric apartment id returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "Broken gate",
      "category": "SECURITY",
      "apartment_id": "the first one"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "apartment_id must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "apartment_id must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_raise_complaint_non_numeric_apartment_id_returns_400(
        client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Broken gate", "category": "SECURITY",
        "apartment_id": "the first one",
    }, headers=resident)

    assert res.status_code == 400
    assert res.get_json()["error"] == "apartment_id must be a whole number"
```
</details>


### TC-162 · Raise complaint unknown apartment returns 404

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "Ghost flat",
      "category": "OTHER",
      "apartment_id": 99999
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`
- JSON: `error` == "Apartment not found"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "Apartment not found"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_raise_complaint_unknown_apartment_returns_404(client, resident, seed):
    res = client.post("/api/complaints/", json={
        "title": "Ghost flat", "category": "OTHER", "apartment_id": 99999,
    }, headers=resident)

    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"
```
</details>


### TC-163 · Raise complaint malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"hello"', "Request body must be a JSON object"),
])
def test_raise_complaint_malformed_body_returns_400(
        client, resident, raw, expected_error):
    res = client.post("/api/complaints/", data=raw,
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-164 · Raise complaint malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"hello"', "Request body must be a JSON object"),
])
def test_raise_complaint_malformed_body_returns_400(
        client, resident, raw, expected_error):
    res = client.post("/api/complaints/", data=raw,
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-165 · Raise complaint malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    "hello"
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"hello"', "Request body must be a JSON object"),
])
def test_raise_complaint_malformed_body_returns_400(
        client, resident, raw, expected_error):
    res = client.post("/api/complaints/", data=raw,
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-166 · Complaint endpoints require a token

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/complaints/"),
    ("post", "/api/complaints/"),
    ("get", "/api/complaints/1"),
    ("put", "/api/complaints/1/assign"),
    ("put", "/api/complaints/1/status"),
    ("delete", "/api/complaints/1"),
])
def test_complaint_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-167 · Complaint endpoints require a token

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/complaints/"),
    ("post", "/api/complaints/"),
    ("get", "/api/complaints/1"),
    ("put", "/api/complaints/1/assign"),
    ("put", "/api/complaints/1/status"),
    ("delete", "/api/complaints/1"),
])
def test_complaint_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-168 · Complaint endpoints require a token

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/complaints/"),
    ("post", "/api/complaints/"),
    ("get", "/api/complaints/1"),
    ("put", "/api/complaints/1/assign"),
    ("put", "/api/complaints/1/status"),
    ("delete", "/api/complaints/1"),
])
def test_complaint_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-169 · Complaint endpoints require a token

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/assign`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/assign`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/complaints/"),
    ("post", "/api/complaints/"),
    ("get", "/api/complaints/1"),
    ("put", "/api/complaints/1/assign"),
    ("put", "/api/complaints/1/status"),
    ("delete", "/api/complaints/1"),
])
def test_complaint_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-170 · Complaint endpoints require a token

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/complaints/"),
    ("post", "/api/complaints/"),
    ("get", "/api/complaints/1"),
    ("put", "/api/complaints/1/assign"),
    ("put", "/api/complaints/1/status"),
    ("delete", "/api/complaints/1"),
])
def test_complaint_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-171 · Complaint endpoints require a token

**Page being tested:** `DELETE http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/complaints/"),
    ("post", "/api/complaints/"),
    ("get", "/api/complaints/1"),
    ("put", "/api/complaints/1/assign"),
    ("put", "/api/complaints/1/status"),
    ("delete", "/api/complaints/1"),
])
def test_complaint_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-172 · Resident cannot delete complaint

**Page being tested:** `DELETE http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_delete_complaint(client, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.delete(f"/api/complaints/{complaint['id']}", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-173 · Resident cannot assign a worker

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/assign`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/assign`
- JSON body:
    ```json
    {
      "worker_id": 6
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_assign_a_worker(client, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": seed["worker_id"]}, headers=resident)
    assert res.status_code == 403
```
</details>


### TC-174 · Resident cannot read another flats complaint

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to view this complaint"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to view this complaint"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_read_another_flats_complaint(
        client, admin, resident, seed):
    other = raise_complaint(client, admin, seed["other_apartment_id"],
                            title="B-202 seepage")

    res = client.get(f"/api/complaints/{other['id']}", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to view this complaint"
```
</details>


### TC-175 · Resident cannot update another flats complaint

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "status": "CLOSED"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to update this complaint"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to update this complaint"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_update_another_flats_complaint(
        client, admin, resident, seed):
    other = raise_complaint(client, admin, seed["other_apartment_id"])

    res = client.put(f"/api/complaints/{other['id']}/status",
                     json={"status": "CLOSED"}, headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to update this complaint"
```
</details>


### TC-176 · Assign worker returns 200 and populates worker name

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/assign`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/assign`
- JSON body:
    ```json
    {
      "worker_id": 6
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": 6,
      "assigned_worker_name": "Ramesh Worker",
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:15.118742",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "ASSIGNED",
      "title": "Leaking kitchen tap"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_assign_worker_returns_200_and_populates_worker_name(
        client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": seed["worker_id"]}, headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ASSIGNED"
    assert body["assigned_worker_id"] == seed["worker_id"]
    assert body["assigned_worker_name"] == "Ramesh Worker"
```
</details>


### TC-177 · Regression: a null worker_id used to flip the status to ASSIGNED anyway

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/assign` → 400

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "worker_id is required"
- JSON: `assigned_worker_id` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:15.624630",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Leaking kitchen tap",
      "updates": []
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("payload", [{}, {"worker_id": None},
                                     {"worker_id": ""}, {"remarks": "please fix"}])
def test_assign_without_worker_id_returns_400(client, admin, resident,
                                              seed, payload):
    """Regression: a null worker_id used to flip the status to ASSIGNED anyway."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "worker_id is required"

    after = client.get(f"/api/complaints/{complaint['id']}", headers=admin).get_json()
    assert after["status"] == "OPEN"
    assert after["assigned_worker_id"] is None
```
</details>


### TC-178 · Regression: a null worker_id used to flip the status to ASSIGNED anyway

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/assign` → 400

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "worker_id is required"
- JSON: `assigned_worker_id` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:16.485794",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Leaking kitchen tap",
      "updates": []
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("payload", [{}, {"worker_id": None},
                                     {"worker_id": ""}, {"remarks": "please fix"}])
def test_assign_without_worker_id_returns_400(client, admin, resident,
                                              seed, payload):
    """Regression: a null worker_id used to flip the status to ASSIGNED anyway."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "worker_id is required"

    after = client.get(f"/api/complaints/{complaint['id']}", headers=admin).get_json()
    assert after["status"] == "OPEN"
    assert after["assigned_worker_id"] is None
```
</details>


### TC-179 · Regression: a null worker_id used to flip the status to ASSIGNED anyway

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/assign` → 400

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "worker_id is required"
- JSON: `assigned_worker_id` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:17.100531",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Leaking kitchen tap",
      "updates": []
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("payload", [{}, {"worker_id": None},
                                     {"worker_id": ""}, {"remarks": "please fix"}])
def test_assign_without_worker_id_returns_400(client, admin, resident,
                                              seed, payload):
    """Regression: a null worker_id used to flip the status to ASSIGNED anyway."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "worker_id is required"

    after = client.get(f"/api/complaints/{complaint['id']}", headers=admin).get_json()
    assert after["status"] == "OPEN"
    assert after["assigned_worker_id"] is None
```
</details>


### TC-180 · Regression: a null worker_id used to flip the status to ASSIGNED anyway

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/assign` → 400

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "worker_id is required"
- JSON: `assigned_worker_id` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:17.550866",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Leaking kitchen tap",
      "updates": []
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("payload", [{}, {"worker_id": None},
                                     {"worker_id": ""}, {"remarks": "please fix"}])
def test_assign_without_worker_id_returns_400(client, admin, resident,
                                              seed, payload):
    """Regression: a null worker_id used to flip the status to ASSIGNED anyway."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "worker_id is required"

    after = client.get(f"/api/complaints/{complaint['id']}", headers=admin).get_json()
    assert after["status"] == "OPEN"
    assert after["assigned_worker_id"] is None
```
</details>


### TC-181 · Assign to non worker user returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/assign`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/assign`
- JSON body:
    ```json
    {
      "worker_id": 4
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Selected user is not a maintenance worker"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Selected user is not a maintenance worker"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_assign_to_non_worker_user_returns_400(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": seed["resident_id"]}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Selected user is not a maintenance worker"
```
</details>


### TC-182 · Assign to unknown user returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/assign`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/assign`
- JSON body:
    ```json
    {
      "worker_id": 99999
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `404`
- JSON: `error` == "Worker not found"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "Worker not found"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_assign_to_unknown_user_returns_404(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/assign",
                     json={"worker_id": 99999}, headers=admin)
    assert res.status_code == 404
    assert res.get_json()["error"] == "Worker not found"
```
</details>


### TC-183 · Regression: workers only ever saw complaints they had raised themselves

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `GET /api/complaints/` → 200, `PUT /api/complaints/1/assign` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "apartment_id": 1,
        "assigned_worker_id": 6,
        "assigned_worker_name": "Ramesh Worker",
        "category": "PLUMBING",
        "created_at": "2026-08-02 11:57:18.641511",
        "description": "Water drips continuously under the sink.",
        "flat_number": "A-101",
        "id": 1,
        "priority": "MEDIUM",
        "raised_by": 4,
        "raised_by_name": "Ravi Resident",
        "resolved_at": null,
        "status": "ASSIGNED",
        "title": "Leaking kitchen tap"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_worker_sees_complaint_assigned_to_them(client, admin, resident,
                                                worker, seed):
    """Regression: workers only ever saw complaints they had raised themselves."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    assert client.get("/api/complaints/", headers=worker).get_json() == []

    client.put(f"/api/complaints/{complaint['id']}/assign",
               json={"worker_id": seed["worker_id"]}, headers=admin)

    res = client.get("/api/complaints/", headers=worker)
    assert res.status_code == 200
    assert [c["id"] for c in res.get_json()] == [complaint["id"]]
```
</details>


### TC-184 · Worker does not see unassigned complaints

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_worker_does_not_see_unassigned_complaints(client, resident,
                                                   worker, seed):
    raise_complaint(client, resident, seed["apartment_id"])

    res = client.get("/api/complaints/", headers=worker)
    assert res.status_code == 200
    assert res.get_json() == []
```
</details>


### TC-185 · Assigned worker can read and update the complaint

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "status": "IN_PROGRESS"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/assign` → 200, `GET /api/complaints/1` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `status` == "IN_PROGRESS"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": 6,
      "assigned_worker_name": "Ramesh Worker",
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:19.459455",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "IN_PROGRESS",
      "title": "Leaking kitchen tap"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_assigned_worker_can_read_and_update_the_complaint(
        client, admin, resident, worker, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    client.put(f"/api/complaints/{complaint['id']}/assign",
               json={"worker_id": seed["worker_id"]}, headers=admin)

    assert client.get(f"/api/complaints/{complaint['id']}",
                      headers=worker).status_code == 200

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": "IN_PROGRESS"}, headers=worker)
    assert res.status_code == 200
    assert res.get_json()["status"] == "IN_PROGRESS"
```
</details>


### TC-186 · Status flow open to completed sets resolved at

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "status": "COMPLETED",
      "remarks": "Washer replaced"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/status` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `status` == "COMPLETED"
- JSON: `resolved_at` is set

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"apartment_id": 1, "assigned_worker_id": null, "assigned_worker_name": null, "category": "PLUMBING", "created_at": "2026-08-02 11:57:20.045278", "description": "Water drips continuously under the sink.", "flat_number": "A-101", "id": 1, "priority": "MEDIUM", "raised_by": 4, "raised_by_name": "Ravi Resident", "resolved_at": "2026-08-02 11:57:20.102242", "status": "COMPLETED", "title": "Leaking ki…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_status_flow_open_to_completed_sets_resolved_at(
        client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    cid = complaint["id"]

    assert client.put(f"/api/complaints/{cid}/status",
                      json={"status": "IN_PROGRESS"},
                      headers=admin).status_code == 200
    res = client.put(f"/api/complaints/{cid}/status",
                     json={"status": "COMPLETED", "remarks": "Washer replaced"},
                     headers=admin)
    assert res.status_code == 200
    assert res.get_json()["status"] == "COMPLETED"
    assert res.get_json()["resolved_at"] is not None
```
</details>


### TC-187 · Regression: resolved_at used to survive a reopen

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "status": "OPEN"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/status` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `resolved_at` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:20.579144",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Leaking kitchen tap"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_reopening_a_closed_complaint_clears_resolved_at(
        client, admin, resident, seed):
    """Regression: resolved_at used to survive a reopen."""
    complaint = raise_complaint(client, resident, seed["apartment_id"])
    cid = complaint["id"]

    client.put(f"/api/complaints/{cid}/status", json={"status": "CLOSED"},
               headers=admin)
    res = client.put(f"/api/complaints/{cid}/status", json={"status": "OPEN"},
                     headers=admin)
    assert res.status_code == 200
    assert res.get_json()["resolved_at"] is None
```
</details>


### TC-188 · Invalid status transition returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "status": "COMPLETED"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Cannot change status from OPEN to COMPLETED"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("new_status", ["COMPLETED"])
def test_invalid_status_transition_returns_400(client, admin, resident,
                                               seed, new_status):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": new_status}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"Cannot change status from OPEN to {new_status}"
```
</details>


### TC-189 · Status update requires status field

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "remarks": "no status"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "status is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "status is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_status_update_requires_status_field(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"remarks": "no status"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "status is required"
```
</details>


### TC-190 · Status update bad enum returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "status": "DONE"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "status must be one of: OPEN, ASSIGNED, IN_PROGRESS, COMPLETED, CLOSED"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_status_update_bad_enum_returns_400(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": "DONE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("status must be one of:")
```
</details>


### TC-191 · Setting the same status is allowed

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/status`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/status`
- JSON body:
    ```json
    {
      "status": "OPEN"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `status` == "OPEN"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "apartment_id": 1,
      "assigned_worker_id": null,
      "assigned_worker_name": null,
      "category": "PLUMBING",
      "created_at": "2026-08-02 11:57:22.519850",
      "description": "Water drips continuously under the sink.",
      "flat_number": "A-101",
      "id": 1,
      "priority": "MEDIUM",
      "raised_by": 4,
      "raised_by_name": "Ravi Resident",
      "resolved_at": null,
      "status": "OPEN",
      "title": "Leaking kitchen tap"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_setting_the_same_status_is_allowed(client, admin, resident, seed):
    complaint = raise_complaint(client, resident, seed["apartment_id"])

    res = client.put(f"/api/complaints/{complaint['id']}/status",
                     json={"status": "OPEN"}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["status"] == "OPEN"
```
</details>


### TC-192 · Unknown complaint id returns 404

**Page being tested:** `DELETE http://127.0.0.1:5000/api/complaints/99999`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/complaints/99999`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `GET /api/complaints/99999` → 404

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_complaint_id_returns_404(client, admin, seed):
    assert client.get("/api/complaints/99999", headers=admin).status_code == 404
    assert client.delete("/api/complaints/99999", headers=admin).status_code == 404
```
</details>


---

## Invoices & Payments

`Backend/tests/test_invoices.py` · US-01, US-05, US-06 · **53/53 passed**


### TC-193 · Admin creates invoice

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500.5,
      "due_date": "2026-07-15"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 2500.5,
      "apartment_id": 1,
      "created_at": "2026-08-02 11:58:24.113963",
      "due_date": "2026-07-15",
      "flat_number": "A-101",
      "id": 1,
      "month": 7,
      "status": "UNPAID",
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_creates_invoice(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500.50, "due_date": "2026-07-15",
    }, headers=admin)

    assert res.status_code == 201
    body = res.get_json()
    assert body["apartment_id"] == seed["apartment_id"]
    assert body["flat_number"] == "A-101"
    assert body["month"] == 7 and body["year"] == 2026
    assert body["amount"] == 2500.50
    assert body["due_date"] == "2026-07-15"
    assert body["status"] == "UNPAID"
```
</details>


### TC-194 · Treasurer can create invoice

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 2500.0,
      "apartment_id": 1,
      "created_at": "2026-08-02 11:58:24.334206",
      "due_date": null,
      "flat_number": "A-101",
      "id": 1,
      "month": 7,
      "status": "UNPAID",
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_treasurer_can_create_invoice(client, treasurer, seed):
    body = create_invoice(client, treasurer, seed["apartment_id"])
    assert body["status"] == "UNPAID"
```
</details>


### TC-195 · Admin lists all invoices

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 2500.0,
        "apartment_id": 2,
        "created_at": "2026-08-02 11:58:24.666524",
        "due_date": null,
        "flat_number": "B-202",
        "id": 2,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      },
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:24.647570",
        "due_date": null,
        "flat_number": "A-101",
        "id": 1,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_lists_all_invoices(client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"])
    create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get("/api/invoices/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 2
```
</details>


### TC-196 · Pay invoice returns receipt

**Page being tested:** `PUT http://127.0.0.1:5000/api/invoices/1/pay`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/invoices/1/pay`
- JSON body:
    ```json
    {
      "payment_method": "UPI",
      "transaction_reference": "TXN-9001"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"invoice": {"amount": 2500.0, "apartment_id": 1, "created_at": "2026-08-02 11:58:25.027333", "due_date": null, "flat_number": "A-101", "id": 1, "month": 7, "status": "PAID", "year": 2026}, "message": "Invoice marked as paid", "receipt": {"amount": 2500.0, "flat_number": "A-101", "month": 7, "payment_date": "2026-08-02 11:58:25.063252", "payment_method": "UPI", "receipt_number": "RCP-0001", "tran…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_pay_invoice_returns_receipt(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = pay(client, admin, invoice["id"],
              payment_method="UPI", transaction_reference="TXN-9001")
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Invoice marked as paid"
    assert body["invoice"]["status"] == "PAID"
    assert body["receipt"]["receipt_number"].startswith("RCP-")
    assert body["receipt"]["payment_method"] == "UPI"
    assert body["receipt"]["transaction_reference"] == "TXN-9001"
    assert body["receipt"]["amount"] == 2500.0
```
</details>


### TC-197 · Payment method defaults to cash

**Page being tested:** `PUT http://127.0.0.1:5000/api/invoices/1/pay`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/invoices/1/pay`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"invoice": {"amount": 2500.0, "apartment_id": 1, "created_at": "2026-08-02 11:58:25.403806", "due_date": null, "flat_number": "A-101", "id": 1, "month": 7, "status": "PAID", "year": 2026}, "message": "Invoice marked as paid", "receipt": {"amount": 2500.0, "flat_number": "A-101", "month": 7, "payment_date": "2026-08-02 11:58:25.432014", "payment_method": "CASH", "receipt_number": "RCP-0001", "tra…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_payment_method_defaults_to_cash(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = client.put(f"/api/invoices/{invoice['id']}/pay", json={}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["receipt"]["payment_method"] == "CASH"
```
</details>


### TC-198 · Get receipt for paid invoice

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/1/receipt`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/1/receipt`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `PUT /api/invoices/1/pay` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "amount": 2500.0,
      "flat_number": "A-101",
      "month": 7,
      "payment_date": "2026-08-02 11:58:25.864732",
      "payment_method": "UPI",
      "receipt_number": "RCP-0001",
      "transaction_reference": null,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_get_receipt_for_paid_invoice(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])
    pay(client, admin, invoice["id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["flat_number"] == "A-101"
    assert body["month"] == 7 and body["year"] == 2026
    assert body["amount"] == 2500.0
```
</details>


### TC-199 · Resident can read own receipt

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/1/receipt`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/1/receipt`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `PUT /api/invoices/1/pay` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `flat_number` == "A-101"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "amount": 2500.0,
      "flat_number": "A-101",
      "month": 7,
      "payment_date": "2026-08-02 11:58:26.258465",
      "payment_method": "UPI",
      "receipt_number": "RCP-0001",
      "transaction_reference": null,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_read_own_receipt(client, admin, resident, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])
    pay(client, admin, invoice["id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=resident)
    assert res.status_code == 200
    assert res.get_json()["flat_number"] == "A-101"
```
</details>


### TC-200 · Pending lists only unpaid

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/pending`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/pending`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `POST /api/invoices/` → 201, `PUT /api/invoices/1/pay` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:26.632730",
        "due_date": null,
        "flat_number": "A-101",
        "id": 2,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_pending_lists_only_unpaid(client, admin, seed):
    paid = create_invoice(client, admin, seed["apartment_id"], month=6)
    unpaid = create_invoice(client, admin, seed["apartment_id"], month=7)
    pay(client, admin, paid["id"])

    res = client.get("/api/invoices/pending", headers=admin)
    assert res.status_code == 200
    assert [i["id"] for i in res.get_json()] == [unpaid["id"]]
```
</details>


### TC-201 · Bulk generate creates invoice for every flat

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/bulk`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/bulk`
- JSON body:
    ```json
    {
      "month": 8,
      "year": 2026,
      "amount": 3000,
      "due_date": "2026-08-10"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "flats": [
        "A-101",
        "B-202"
      ],
      "message": "Invoices generated for 2 flats"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_bulk_generate_creates_invoice_for_every_flat(client, admin, seed):
    res = client.post("/api/invoices/bulk", json={
        "month": 8, "year": 2026, "amount": 3000, "due_date": "2026-08-10",
    }, headers=admin)

    assert res.status_code == 201
    body = res.get_json()
    assert body["message"] == "Invoices generated for 2 flats"
    assert sorted(body["flats"]) == ["A-101", "B-202"]
```
</details>


### TC-202 · Bulk generate skips flats that already have that month

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `POST /api/invoices/bulk` → 201

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 3000.0,
        "apartment_id": 2,
        "created_at": "2026-08-02 11:58:27.178889",
        "due_date": null,
        "flat_number": "B-202",
        "id": 2,
        "month": 8,
        "status": "UNPAID",
        "year": 2026
      },
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:27.161623",
        "due_date": null,
        "flat_number": "A-101",
        "id": 1,
        "month": 8,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_bulk_generate_skips_flats_that_already_have_that_month(
        client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"], month=8, year=2026)

    res = client.post("/api/invoices/bulk",
                      json={"month": 8, "year": 2026, "amount": 3000},
                      headers=admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["flats"] == ["B-202"]
    assert body["message"] == "Invoices generated for 1 flats"

    all_invoices = client.get("/api/invoices/", headers=admin).get_json()
    assert len(all_invoices) == 2
```
</details>


### TC-203 · Create invoice missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "month": 7,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "apartment_id is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["apartment_id", "month", "year", "amount"])
def test_create_invoice_missing_required_field_returns_400(
        client, admin, seed, missing):
    payload = {"apartment_id": seed["apartment_id"], "month": 7,
               "year": 2026, "amount": 2500}
    payload.pop(missing)

    res = client.post("/api/invoices/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-204 · Create invoice missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["apartment_id", "month", "year", "amount"])
def test_create_invoice_missing_required_field_returns_400(
        client, admin, seed, missing):
    payload = {"apartment_id": seed["apartment_id"], "month": 7,
               "year": 2026, "amount": 2500}
    payload.pop(missing)

    res = client.post("/api/invoices/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-205 · Create invoice missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "year is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["apartment_id", "month", "year", "amount"])
def test_create_invoice_missing_required_field_returns_400(
        client, admin, seed, missing):
    payload = {"apartment_id": seed["apartment_id"], "month": 7,
               "year": 2026, "amount": 2500}
    payload.pop(missing)

    res = client.post("/api/invoices/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-206 · Create invoice missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "amount is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["apartment_id", "month", "year", "amount"])
def test_create_invoice_missing_required_field_returns_400(
        client, admin, seed, missing):
    payload = {"apartment_id": seed["apartment_id"], "month": 7,
               "year": 2026, "amount": 2500}
    payload.pop(missing)

    res = client.post("/api/invoices/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-207 · Create invoice month out of range returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 0,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at least 1"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("month", [0, 13, 99, -1])
def test_create_invoice_month_out_of_range_returns_400(client, admin, seed, month):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": month,
        "year": 2026, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] in ("month must be at least 1",
                                       "month must be at most 12")
```
</details>


### TC-208 · Create invoice month out of range returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 13,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at most 12"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("month", [0, 13, 99, -1])
def test_create_invoice_month_out_of_range_returns_400(client, admin, seed, month):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": month,
        "year": 2026, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] in ("month must be at least 1",
                                       "month must be at most 12")
```
</details>


### TC-209 · Create invoice month out of range returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 99,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at most 12"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("month", [0, 13, 99, -1])
def test_create_invoice_month_out_of_range_returns_400(client, admin, seed, month):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": month,
        "year": 2026, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] in ("month must be at least 1",
                                       "month must be at most 12")
```
</details>


### TC-210 · Create invoice month out of range returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": -1,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at least 1"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("month", [0, 13, 99, -1])
def test_create_invoice_month_out_of_range_returns_400(client, admin, seed, month):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": month,
        "year": 2026, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] in ("month must be at least 1",
                                       "month must be at most 12")
```
</details>


### TC-211 · Bulk generate month out of range returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/bulk`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/bulk`
- JSON body:
    ```json
    {
      "month": 99,
      "year": 2026,
      "amount": 3000
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "month must be at most 12"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at most 12"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_bulk_generate_month_out_of_range_returns_400(client, admin, seed):
    res = client.post("/api/invoices/bulk",
                      json={"month": 99, "year": 2026, "amount": 3000},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at most 12"
```
</details>


### TC-212 · Create invoice year out of range returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 1899,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "year must be at least 2000"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "year must be at least 2000"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_invoice_year_out_of_range_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 1899, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "year must be at least 2000"
```
</details>


### TC-213 · Create invoice non numeric amount returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": "one thousand"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "amount must be a number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "amount must be a number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_invoice_non_numeric_amount_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": "one thousand",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be a number"
```
</details>


### TC-214 · Create invoice negative amount returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": -5
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "amount must be at least 0"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "amount must be at least 0"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_invoice_negative_amount_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": -5,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be at least 0"
```
</details>


### TC-215 · Create invoice bad due date returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500,
      "due_date": "yesterday"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "due_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "due_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_invoice_bad_due_date_returns_400(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500, "due_date": "yesterday",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "due_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-216 · Regression: an empty due_date from the form used to 400 (or crash)

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500,
      "due_date": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `due_date` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 2500.0,
      "apartment_id": 1,
      "created_at": "2026-08-02 11:58:30.695743",
      "due_date": null,
      "flat_number": "A-101",
      "id": 1,
      "month": 7,
      "status": "UNPAID",
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("due_date", ["", "   ", None])
def test_blank_due_date_is_stored_as_null_not_rejected(client, admin,
                                                       seed, due_date):
    """Regression: an empty due_date from the form used to 400 (or crash)."""
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500, "due_date": due_date,
    }, headers=admin)

    assert res.status_code == 201, res.get_json()
    assert res.get_json()["due_date"] is None
```
</details>


### TC-217 · Regression: an empty due_date from the form used to 400 (or crash)

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500,
      "due_date": "   "
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `due_date` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 2500.0,
      "apartment_id": 1,
      "created_at": "2026-08-02 11:58:31.024569",
      "due_date": null,
      "flat_number": "A-101",
      "id": 1,
      "month": 7,
      "status": "UNPAID",
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("due_date", ["", "   ", None])
def test_blank_due_date_is_stored_as_null_not_rejected(client, admin,
                                                       seed, due_date):
    """Regression: an empty due_date from the form used to 400 (or crash)."""
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500, "due_date": due_date,
    }, headers=admin)

    assert res.status_code == 201, res.get_json()
    assert res.get_json()["due_date"] is None
```
</details>


### TC-218 · Regression: an empty due_date from the form used to 400 (or crash)

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500,
      "due_date": null
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `due_date` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 2500.0,
      "apartment_id": 1,
      "created_at": "2026-08-02 11:58:31.186472",
      "due_date": null,
      "flat_number": "A-101",
      "id": 1,
      "month": 7,
      "status": "UNPAID",
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("due_date", ["", "   ", None])
def test_blank_due_date_is_stored_as_null_not_rejected(client, admin,
                                                       seed, due_date):
    """Regression: an empty due_date from the form used to 400 (or crash)."""
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7, "year": 2026,
        "amount": 2500, "due_date": due_date,
    }, headers=admin)

    assert res.status_code == 201, res.get_json()
    assert res.get_json()["due_date"] is None
```
</details>


### TC-219 · Create invoice unknown apartment returns 404

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 99999,
      "month": 7,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`
- JSON: `error` == "Apartment not found"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "Apartment not found"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_invoice_unknown_apartment_returns_404(client, admin, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": 99999, "month": 7, "year": 2026, "amount": 2500,
    }, headers=admin)

    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"
```
</details>


### TC-220 · Invoice malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_invoice_malformed_body_returns_400(client, admin, seed, path,
                                            raw, expected_error):
    res = client.post(path, data=raw, content_type="application/json",
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-221 · Invoice malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_invoice_malformed_body_returns_400(client, admin, seed, path,
                                            raw, expected_error):
    res = client.post(path, data=raw, content_type="application/json",
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-222 · Invoice malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/bulk`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/bulk`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_invoice_malformed_body_returns_400(client, admin, seed, path,
                                            raw, expected_error):
    res = client.post(path, data=raw, content_type="application/json",
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-223 · Invoice malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/bulk`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/bulk`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_invoice_malformed_body_returns_400(client, admin, seed, path,
                                            raw, expected_error):
    res = client.post(path, data=raw, content_type="application/json",
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-224 · Invoice endpoints require a token

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/invoices/"),
    ("post", "/api/invoices/"),
    ("post", "/api/invoices/bulk"),
    ("put", "/api/invoices/1/pay"),
    ("get", "/api/invoices/1/receipt"),
    ("get", "/api/invoices/pending"),
])
def test_invoice_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-225 · Invoice endpoints require a token

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/invoices/"),
    ("post", "/api/invoices/"),
    ("post", "/api/invoices/bulk"),
    ("put", "/api/invoices/1/pay"),
    ("get", "/api/invoices/1/receipt"),
    ("get", "/api/invoices/pending"),
])
def test_invoice_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-226 · Invoice endpoints require a token

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/bulk`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/bulk`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/invoices/"),
    ("post", "/api/invoices/"),
    ("post", "/api/invoices/bulk"),
    ("put", "/api/invoices/1/pay"),
    ("get", "/api/invoices/1/receipt"),
    ("get", "/api/invoices/pending"),
])
def test_invoice_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-227 · Invoice endpoints require a token

**Page being tested:** `PUT http://127.0.0.1:5000/api/invoices/1/pay`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/invoices/1/pay`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/invoices/"),
    ("post", "/api/invoices/"),
    ("post", "/api/invoices/bulk"),
    ("put", "/api/invoices/1/pay"),
    ("get", "/api/invoices/1/receipt"),
    ("get", "/api/invoices/pending"),
])
def test_invoice_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-228 · Invoice endpoints require a token

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/1/receipt`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/1/receipt`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/invoices/"),
    ("post", "/api/invoices/"),
    ("post", "/api/invoices/bulk"),
    ("put", "/api/invoices/1/pay"),
    ("get", "/api/invoices/1/receipt"),
    ("get", "/api/invoices/pending"),
])
def test_invoice_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-229 · Invoice endpoints require a token

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/pending`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/pending`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/invoices/"),
    ("post", "/api/invoices/"),
    ("post", "/api/invoices/bulk"),
    ("put", "/api/invoices/1/pay"),
    ("get", "/api/invoices/1/receipt"),
    ("get", "/api/invoices/pending"),
])
def test_invoice_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-230 · Resident cannot create invoice

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_create_invoice(client, resident, seed):
    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": 2500,
    }, headers=resident)

    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-231 · Resident cannot mark invoice paid

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `PUT /api/invoices/1/pay` → 403

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:33.996767",
        "due_date": null,
        "flat_number": "A-101",
        "id": 1,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_mark_invoice_paid(client, admin, resident, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = pay(client, resident, invoice["id"])
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
    assert client.get("/api/invoices/",
                      headers=admin).get_json()[0]["status"] == "UNPAID"
```
</details>


### TC-232 · Resident cannot bulk generate

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/bulk`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/bulk`
- JSON body:
    ```json
    {
      "month": 8,
      "year": 2026,
      "amount": 3000
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_bulk_generate(client, resident, seed):
    res = client.post("/api/invoices/bulk",
                      json={"month": 8, "year": 2026, "amount": 3000},
                      headers=resident)
    assert res.status_code == 403
```
</details>


### TC-233 · COMMITTEE_MEMBER manages the society but must not touch money

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_committee_member_is_not_finance(client, tokens, seed, path):
    """COMMITTEE_MEMBER manages the society but must not touch money."""
    res = client.post(path, json={"apartment_id": seed["apartment_id"],
                                  "month": 7, "year": 2026, "amount": 2500},
                      headers=committee_headers(tokens))
    assert res.status_code == 403
```
</details>


### TC-234 · COMMITTEE_MEMBER manages the society but must not touch money

**Page being tested:** `POST http://127.0.0.1:5000/api/invoices/bulk`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/invoices/bulk`
- JSON body:
    ```json
    {
      "apartment_id": 1,
      "month": 7,
      "year": 2026,
      "amount": 2500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/bulk"])
def test_committee_member_is_not_finance(client, tokens, seed, path):
    """COMMITTEE_MEMBER manages the society but must not touch money."""
    res = client.post(path, json={"apartment_id": seed["apartment_id"],
                                  "month": 7, "year": 2026, "amount": 2500},
                      headers=committee_headers(tokens))
    assert res.status_code == 403
```
</details>


### TC-235 · Resident cannot read another flats receipt

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/1/receipt`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/1/receipt`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to view this receipt"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to view this receipt"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_read_another_flats_receipt(client, admin,
                                                    resident, seed):
    invoice = create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to view this receipt"
```
</details>


### TC-236 · Duplicate invoice for same flat month year returns 409

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `POST /api/invoices/` → 409

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "An invoice already exists for this flat and month"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:35.249295",
        "due_date": null,
        "flat_number": "A-101",
        "id": 1,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_duplicate_invoice_for_same_flat_month_year_returns_409(
        client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"], month=7, year=2026)

    res = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 7,
        "year": 2026, "amount": 9999,
    }, headers=admin)

    assert res.status_code == 409
    assert res.get_json()["error"] == "An invoice already exists for this flat and month"
    assert len(client.get("/api/invoices/", headers=admin).get_json()) == 1
```
</details>


### TC-237 · Same month different flat is allowed

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 2500.0,
        "apartment_id": 2,
        "created_at": "2026-08-02 11:58:35.444930",
        "due_date": null,
        "flat_number": "B-202",
        "id": 2,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      },
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:35.434731",
        "due_date": null,
        "flat_number": "A-101",
        "id": 1,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_same_month_different_flat_is_allowed(client, admin, seed):
    create_invoice(client, admin, seed["apartment_id"], month=7, year=2026)
    create_invoice(client, admin, seed["other_apartment_id"], month=7, year=2026)

    assert len(client.get("/api/invoices/", headers=admin).get_json()) == 2
```
</details>


### TC-238 · Regression: the second payment used to insert a duplicate Payment row

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/1/receipt`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/1/receipt`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `PUT /api/invoices/1/pay` → 200, `PUT /api/invoices/1/pay` → 409

**Expected Output:**

- HTTP Status Code: `200 or 409`
- JSON: `error` == "This invoice is already paid"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "amount": 2500.0,
      "flat_number": "A-101",
      "month": 7,
      "payment_date": "2026-08-02 11:58:35.613346",
      "payment_method": "UPI",
      "receipt_number": "RCP-0001",
      "transaction_reference": "TXN-1",
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_pay_invoice_twice_returns_409(client, admin, seed):
    """Regression: the second payment used to insert a duplicate Payment row."""
    invoice = create_invoice(client, admin, seed["apartment_id"])
    first = pay(client, admin, invoice["id"], payment_method="UPI",
                transaction_reference="TXN-1")
    assert first.status_code == 200
    first_receipt = first.get_json()["receipt"]["receipt_number"]

    second = pay(client, admin, invoice["id"], payment_method="CARD",
                 transaction_reference="TXN-2")
    assert second.status_code == 409
    assert second.get_json()["error"] == "This invoice is already paid"

    receipt = client.get(f"/api/invoices/{invoice['id']}/receipt",
                         headers=admin).get_json()
    assert receipt["receipt_number"] == first_receipt
    assert receipt["transaction_reference"] == "TXN-1"
```
</details>


### TC-239 · Receipt for unpaid invoice returns 400

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/1/receipt`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/1/receipt`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Invoice not paid yet"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Invoice not paid yet"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_receipt_for_unpaid_invoice_returns_400(client, admin, seed):
    invoice = create_invoice(client, admin, seed["apartment_id"])

    res = client.get(f"/api/invoices/{invoice['id']}/receipt", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Invoice not paid yet"
```
</details>


### TC-240 · Pay invoice for flat without resident returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/invoices/1/pay`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/invoices/1/pay`
- JSON body:
    ```json
    {
      "payment_method": "UPI"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `404`
- JSON: `error` == "No resident found for this apartment"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "No resident found for this apartment"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_pay_invoice_for_flat_without_resident_returns_404(client, admin, seed):
    invoice = create_invoice(client, admin, seed["other_apartment_id"])

    res = pay(client, admin, invoice["id"])
    assert res.status_code == 404
    assert res.get_json()["error"] == "No resident found for this apartment"
```
</details>


### TC-241 · Unknown invoice returns 404

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/99999/receipt`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/99999/receipt`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `PUT /api/invoices/99999/pay` → 404

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_invoice_returns_404(client, admin, seed):
    assert pay(client, admin, 99999).status_code == 404
    assert client.get("/api/invoices/99999/receipt",
                      headers=admin).status_code == 404
```
</details>


### TC-242 · Resident sees only own flat invoices

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:36.229258",
        "due_date": null,
        "flat_number": "A-101",
        "id": 1,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_sees_only_own_flat_invoices(client, admin, resident, seed):
    mine = create_invoice(client, admin, seed["apartment_id"])
    create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get("/api/invoices/", headers=resident)
    assert res.status_code == 200
    assert [i["id"] for i in res.get_json()] == [mine["id"]]
```
</details>


### TC-243 · Regression: /pending used to leak every flat's outstanding dues

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/pending`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/pending`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 2500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:58:36.412799",
        "due_date": null,
        "flat_number": "A-101",
        "id": 1,
        "month": 7,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_pending_is_scoped_to_own_flat(client, admin, resident, seed):
    """Regression: /pending used to leak every flat's outstanding dues."""
    mine = create_invoice(client, admin, seed["apartment_id"])
    create_invoice(client, admin, seed["other_apartment_id"])

    res = client.get("/api/invoices/pending", headers=resident)
    assert res.status_code == 200
    body = res.get_json()
    assert [i["id"] for i in body] == [mine["id"]]
    assert all(i["flat_number"] == "A-101" for i in body)
```
</details>


### TC-244 · User without a flat sees an empty list

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/pending"])
def test_user_without_a_flat_sees_an_empty_list(client, admin, worker,
                                                seed, path):
    create_invoice(client, admin, seed["apartment_id"])

    res = client.get(path, headers=worker)
    assert res.status_code == 200
    assert res.get_json() == []
```
</details>


### TC-245 · User without a flat sees an empty list

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/pending`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/pending`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/invoices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("path", ["/api/invoices/", "/api/invoices/pending"])
def test_user_without_a_flat_sees_an_empty_list(client, admin, worker,
                                                seed, path):
    create_invoice(client, admin, seed["apartment_id"])

    res = client.get(path, headers=worker)
    assert res.status_code == 200
    assert res.get_json() == []
```
</details>


---

## Expenses

`Backend/tests/test_expenses.py` · US-14 · **44/44 passed**


### TC-246 · Admin logs expense

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "utilities",
      "description": "Common area electricity bill",
      "amount": 12750.25,
      "expense_date": "2026-08-05",
      "receipt_url": "https://example.com/bill.pdf"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 12750.25,
      "category": "UTILITIES",
      "created_at": "2026-08-02 11:58:08.530211",
      "description": "Common area electricity bill",
      "expense_date": "2026-08-05",
      "id": 1,
      "paid_by": 1,
      "paid_by_name": "Priya Admin",
      "receipt_url": "https://example.com/bill.pdf"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_logs_expense(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "utilities",
        "description": "Common area electricity bill",
        "amount": 12750.25,
        "expense_date": "2026-08-05",
        "receipt_url": "https://example.com/bill.pdf",
    }, headers=admin)

    assert res.status_code == 201
    body = res.get_json()
    assert body["category"] == "UTILITIES"          # normalised to upper case
    assert body["description"] == "Common area electricity bill"
    assert body["amount"] == 12750.25
    assert body["expense_date"] == "2026-08-05"
    assert body["receipt_url"] == "https://example.com/bill.pdf"
    assert body["paid_by"] == seed["admin_id"]
    assert body["paid_by_name"] == "Priya Admin"
```
</details>


### TC-247 · Treasurer can log expense

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Lift annual servicing",
      "amount": 4500,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 4500.0,
      "category": "MAINTENANCE",
      "created_at": "2026-08-02 11:58:08.730124",
      "description": "Lift annual servicing",
      "expense_date": "2026-08-05",
      "id": 1,
      "paid_by": 2,
      "paid_by_name": "Tarun Treasurer",
      "receipt_url": null
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_treasurer_can_log_expense(client, treasurer, seed):
    body = create_expense(client, treasurer)
    assert body["paid_by"] == seed["treasurer_id"]
```
</details>


### TC-248 · Paid by defaults to the logged in user

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Lift annual servicing",
      "amount": 4500,
      "expense_date": "2026-08-05",
      "paid_by": null
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 4500.0,
      "category": "MAINTENANCE",
      "created_at": "2026-08-02 11:58:08.906531",
      "description": "Lift annual servicing",
      "expense_date": "2026-08-05",
      "id": 1,
      "paid_by": 2,
      "paid_by_name": "Tarun Treasurer",
      "receipt_url": null
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_paid_by_defaults_to_the_logged_in_user(client, treasurer, seed):
    body = create_expense(client, treasurer, paid_by=None)
    assert body["paid_by"] == seed["treasurer_id"]
```
</details>


### TC-249 · Admin may attribute expense to another user

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Lift annual servicing",
      "amount": 4500,
      "expense_date": "2026-08-05",
      "paid_by": 6
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 4500.0,
      "category": "MAINTENANCE",
      "created_at": "2026-08-02 11:58:09.062159",
      "description": "Lift annual servicing",
      "expense_date": "2026-08-05",
      "id": 1,
      "paid_by": 6,
      "paid_by_name": "Ramesh Worker",
      "receipt_url": null
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_may_attribute_expense_to_another_user(client, admin, seed):
    body = create_expense(client, admin, paid_by=seed["worker_id"])
    assert body["paid_by"] == seed["worker_id"]
    assert body["paid_by_name"] == "Ramesh Worker"
```
</details>


### TC-250 · Paid by unknown user returns 404

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "SALARY",
      "description": "Guard salary",
      "amount": 15000,
      "expense_date": "2026-08-01",
      "paid_by": 99999
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`
- JSON: `error` == "paid_by user not found"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "paid_by user not found"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_paid_by_unknown_user_returns_404(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "SALARY", "description": "Guard salary",
        "amount": 15000, "expense_date": "2026-08-01", "paid_by": 99999,
    }, headers=admin)

    assert res.status_code == 404
    assert res.get_json()["error"] == "paid_by user not found"
```
</details>


### TC-251 · List expenses

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/expenses/` → 201, `POST /api/expenses/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"amount": 4500.0, "category": "MAINTENANCE", "created_at": "2026-08-02 11:58:09.353414", "description": "Second", "expense_date": "2026-08-20", "id": 2, "paid_by": 1, "paid_by_name": "Priya Admin", "receipt_url": null}, {"amount": 4500.0, "category": "MAINTENANCE", "created_at": "2026-08-02 11:58:09.346237", "description": "First", "expense_date": "2026-08-01", "id": 1, "paid_by": 1, "paid_by_n…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_expenses(client, admin, seed):
    create_expense(client, admin, description="First", expense_date="2026-08-01")
    create_expense(client, admin, description="Second", expense_date="2026-08-20")

    res = client.get("/api/expenses/", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 2
    assert body[0]["description"] == "Second"       # newest expense_date first
```
</details>


### TC-252 · Update expense

**Page being tested:** `PUT http://127.0.0.1:5000/api/expenses/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/expenses/1`
- JSON body:
    ```json
    {
      "description": "Lift servicing (revised)",
      "amount": 5200,
      "category": "CONSUMABLES",
      "receipt_url": "https://example.com/new.pdf"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/expenses/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "amount": 5200.0,
      "category": "CONSUMABLES",
      "created_at": "2026-08-02 11:58:09.513586",
      "description": "Lift servicing (revised)",
      "expense_date": "2026-08-05",
      "id": 1,
      "paid_by": 1,
      "paid_by_name": "Priya Admin",
      "receipt_url": "https://example.com/new.pdf"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_expense(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.put(f"/api/expenses/{expense['id']}", json={
        "description": "Lift servicing (revised)",
        "amount": 5200,
        "category": "CONSUMABLES",
        "receipt_url": "https://example.com/new.pdf",
    }, headers=admin)

    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == expense["id"]
    assert body["description"] == "Lift servicing (revised)"
    assert body["amount"] == 5200.0
    assert body["category"] == "CONSUMABLES"
    assert body["receipt_url"] == "https://example.com/new.pdf"
```
</details>


### TC-253 · Delete expense

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/expenses/` → 201, `DELETE /api/expenses/1` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Expense deleted"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_expense(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.delete(f"/api/expenses/{expense['id']}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Expense deleted"
    assert client.get("/api/expenses/", headers=admin).get_json() == []
```
</details>


### TC-254 · Unknown expense returns 404

**Page being tested:** `DELETE http://127.0.0.1:5000/api/expenses/99999`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/expenses/99999`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `PUT /api/expenses/99999` → 404

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_expense_returns_404(client, admin, seed):
    assert client.put("/api/expenses/99999", json={"amount": 1},
                      headers=admin).status_code == 404
    assert client.delete("/api/expenses/99999", headers=admin).status_code == 404
```
</details>


### TC-255 · Summary for a month

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary?month=8&year=2026`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary?month=8&year=2026`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/expenses/` → 201, `POST /api/expenses/` → 201, `POST /api/invoices/` → 201, `PUT /api/invoices/1/pay` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "by_category": {
        "SALARY": 15000.0,
        "UTILITIES": 2500.0
      },
      "net_balance": -14500.0,
      "total_expense": 17500.0,
      "total_income": 3000.0
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_summary_for_a_month(client, admin, seed):
    create_expense(client, admin, category="SALARY", amount=15000,
                   expense_date="2026-08-01")
    create_expense(client, admin, category="UTILITIES", amount=2500,
                   expense_date="2026-08-20")
    create_expense(client, admin, category="SALARY", amount=999,
                   expense_date="2026-09-01")   # different month, excluded

    invoice = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"], "month": 8,
        "year": 2026, "amount": 3000,
    }, headers=admin).get_json()
    client.put(f"/api/invoices/{invoice['id']}/pay", json={}, headers=admin)

    res = client.get("/api/expenses/summary?month=8&year=2026", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["total_expense"] == 17500.0
    assert body["total_income"] == 3000.0
    assert body["net_balance"] == -14500.0
    assert body["by_category"] == {"SALARY": 15000.0, "UTILITIES": 2500.0}
```
</details>


### TC-256 · Summary without filters is all time

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/expenses/` → 201, `POST /api/expenses/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "by_category": {
        "MAINTENANCE": 350.0
      },
      "net_balance": -350.0,
      "total_expense": 350.0,
      "total_income": 0
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_summary_without_filters_is_all_time(client, admin, seed):
    create_expense(client, admin, amount=100, expense_date="2026-08-01")
    create_expense(client, admin, amount=250, expense_date="2025-01-01")

    res = client.get("/api/expenses/summary", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["total_expense"] == 350.0
```
</details>


### TC-257 · Regression: half a filter silently fell through to all-time totals

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary?month=8`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary?month=8`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Provide both month and year"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Provide both month and year"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("query", ["?month=8", "?year=2026",
                                   "?month=8&year=", "?month=&year=2026"])
def test_summary_with_partial_filter_returns_400(client, admin, seed, query):
    """Regression: half a filter silently fell through to all-time totals."""
    res = client.get(f"/api/expenses/summary{query}", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Provide both month and year"
```
</details>


### TC-258 · Regression: half a filter silently fell through to all-time totals

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary?year=2026`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary?year=2026`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Provide both month and year"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Provide both month and year"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("query", ["?month=8", "?year=2026",
                                   "?month=8&year=", "?month=&year=2026"])
def test_summary_with_partial_filter_returns_400(client, admin, seed, query):
    """Regression: half a filter silently fell through to all-time totals."""
    res = client.get(f"/api/expenses/summary{query}", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Provide both month and year"
```
</details>


### TC-259 · Regression: half a filter silently fell through to all-time totals

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary?month=8&year=`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary?month=8&year=`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Provide both month and year"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Provide both month and year"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("query", ["?month=8", "?year=2026",
                                   "?month=8&year=", "?month=&year=2026"])
def test_summary_with_partial_filter_returns_400(client, admin, seed, query):
    """Regression: half a filter silently fell through to all-time totals."""
    res = client.get(f"/api/expenses/summary{query}", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Provide both month and year"
```
</details>


### TC-260 · Regression: half a filter silently fell through to all-time totals

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary?month=&year=2026`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary?month=&year=2026`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Provide both month and year"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Provide both month and year"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("query", ["?month=8", "?year=2026",
                                   "?month=8&year=", "?month=&year=2026"])
def test_summary_with_partial_filter_returns_400(client, admin, seed, query):
    """Regression: half a filter silently fell through to all-time totals."""
    res = client.get(f"/api/expenses/summary{query}", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Provide both month and year"
```
</details>


### TC-261 · Summary month out of range returns 400

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary?month=99&year=2026`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary?month=99&year=2026`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "month must be at most 12"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at most 12"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_summary_month_out_of_range_returns_400(client, admin, seed):
    res = client.get("/api/expenses/summary?month=99&year=2026", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at most 12"
```
</details>


### TC-262 · Summary non numeric month returns 400

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary?month=August&year=2026`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary?month=August&year=2026`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "month must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_summary_non_numeric_month_returns_400(client, admin, seed):
    res = client.get("/api/expenses/summary?month=August&year=2026",
                     headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be a whole number"
```
</details>


### TC-263 · Add expense missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "description": "Painting",
      "amount": 1000,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "category is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["category", "description",
                                     "amount", "expense_date"])
def test_add_expense_missing_required_field_returns_400(client, admin,
                                                        seed, missing):
    payload = {"category": "MAINTENANCE", "description": "Painting",
               "amount": 1000, "expense_date": "2026-08-05"}
    payload.pop(missing)

    res = client.post("/api/expenses/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-264 · Add expense missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "amount": 1000,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "description is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["category", "description",
                                     "amount", "expense_date"])
def test_add_expense_missing_required_field_returns_400(client, admin,
                                                        seed, missing):
    payload = {"category": "MAINTENANCE", "description": "Painting",
               "amount": 1000, "expense_date": "2026-08-05"}
    payload.pop(missing)

    res = client.post("/api/expenses/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-265 · Add expense missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "amount is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["category", "description",
                                     "amount", "expense_date"])
def test_add_expense_missing_required_field_returns_400(client, admin,
                                                        seed, missing):
    payload = {"category": "MAINTENANCE", "description": "Painting",
               "amount": 1000, "expense_date": "2026-08-05"}
    payload.pop(missing)

    res = client.post("/api/expenses/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-266 · Add expense missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_date is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["category", "description",
                                     "amount", "expense_date"])
def test_add_expense_missing_required_field_returns_400(client, admin,
                                                        seed, missing):
    payload = {"category": "MAINTENANCE", "description": "Painting",
               "amount": 1000, "expense_date": "2026-08-05"}
    payload.pop(missing)

    res = client.post("/api/expenses/", json=payload, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-267 · Add expense bad category returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "PIZZA",
      "description": "Team lunch",
      "amount": 1000,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_category must be one of: SALARY, MAINTENANCE, UTILITIES, CONSUMABLES, MISCELLANEOUS"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_add_expense_bad_category_returns_400(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "PIZZA", "description": "Team lunch",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"].startswith("expense_category must be one of:")
```
</details>


### TC-268 · Regression: raw strings used to reach the Date column and 500

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": "yesterday"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "expense_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("bad_date", ["yesterday", "05-08-2026", "2026-13-01"])
def test_add_expense_bad_date_returns_400(client, admin, seed, bad_date):
    """Regression: raw strings used to reach the Date column and 500."""
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": bad_date,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "expense_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-269 · Regression: raw strings used to reach the Date column and 500

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": "05-08-2026"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "expense_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("bad_date", ["yesterday", "05-08-2026", "2026-13-01"])
def test_add_expense_bad_date_returns_400(client, admin, seed, bad_date):
    """Regression: raw strings used to reach the Date column and 500."""
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": bad_date,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "expense_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-270 · Regression: raw strings used to reach the Date column and 500

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": "2026-13-01"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "expense_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("bad_date", ["yesterday", "05-08-2026", "2026-13-01"])
def test_add_expense_bad_date_returns_400(client, admin, seed, bad_date):
    """Regression: raw strings used to reach the Date column and 500."""
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": bad_date,
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "expense_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-271 · expense_date is required, so a blank one is rejected by require()

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "expense_date is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_date is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_add_expense_blank_date_returns_400(client, admin, seed):
    """expense_date is required, so a blank one is rejected by require()."""
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "expense_date is required"
```
</details>


### TC-272 · Add expense non numeric amount returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": "one thousand",
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "amount must be a number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "amount must be a number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_add_expense_non_numeric_amount_returns_400(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": "one thousand", "expense_date": "2026-08-05",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be a number"
```
</details>


### TC-273 · Add expense negative amount returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": -1,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "amount must be at least 0"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "amount must be at least 0"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_add_expense_negative_amount_returns_400(client, admin, seed):
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": -1, "expense_date": "2026-08-05",
    }, headers=admin)

    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be at least 0"
```
</details>


### TC-274 · Update expense bad category returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/expenses/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/expenses/1`
- JSON body:
    ```json
    {
      "category": "PIZZA"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/expenses/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_category must be one of: SALARY, MAINTENANCE, UTILITIES, CONSUMABLES, MISCELLANEOUS"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_expense_bad_category_returns_400(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.put(f"/api/expenses/{expense['id']}",
                     json={"category": "PIZZA"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("expense_category must be one of:")
```
</details>


### TC-275 · Update expense non numeric amount returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/expenses/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/expenses/1`
- JSON body:
    ```json
    {
      "amount": "one thousand"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/expenses/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "amount must be a number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "amount must be a number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_expense_non_numeric_amount_returns_400(client, admin, seed):
    expense = create_expense(client, admin)

    res = client.put(f"/api/expenses/{expense['id']}",
                     json={"amount": "one thousand"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "amount must be a number"
```
</details>


### TC-276 · Add expense malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
def test_add_expense_malformed_body_returns_400(client, admin, seed,
                                                raw, expected_error):
    res = client.post("/api/expenses/", data=raw,
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-277 · Add expense malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw, expected_error", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
])
def test_add_expense_malformed_body_returns_400(client, admin, seed,
                                                raw, expected_error):
    res = client.post("/api/expenses/", data=raw,
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == expected_error
```
</details>


### TC-278 · Expense endpoints require a token

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("put", "/api/expenses/1"),
    ("delete", "/api/expenses/1"),
    ("get", "/api/expenses/summary"),
])
def test_expense_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-279 · Expense endpoints require a token

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("put", "/api/expenses/1"),
    ("delete", "/api/expenses/1"),
    ("get", "/api/expenses/summary"),
])
def test_expense_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-280 · Expense endpoints require a token

**Page being tested:** `PUT http://127.0.0.1:5000/api/expenses/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/expenses/1`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("put", "/api/expenses/1"),
    ("delete", "/api/expenses/1"),
    ("get", "/api/expenses/summary"),
])
def test_expense_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-281 · Expense endpoints require a token

**Page being tested:** `DELETE http://127.0.0.1:5000/api/expenses/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/expenses/1`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("put", "/api/expenses/1"),
    ("delete", "/api/expenses/1"),
    ("get", "/api/expenses/summary"),
])
def test_expense_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-282 · Expense endpoints require a token

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("put", "/api/expenses/1"),
    ("delete", "/api/expenses/1"),
    ("get", "/api/expenses/summary"),
])
def test_expense_endpoints_require_a_token(client, seed, method, path):
    res = getattr(client, method)(path, json={})
    assert res.status_code == 401
```
</details>


### TC-283 · Resident cannot list expenses

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_list_expenses(client, resident, seed):
    res = client.get("/api/expenses/", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-284 · Resident cannot add expense

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_add_expense(client, resident, seed):
    res = client.post("/api/expenses/", json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=resident)

    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-285 · Resident cannot delete expense

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/expenses/` → 201, `DELETE /api/expenses/1` → 403

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 4500.0,
        "category": "MAINTENANCE",
        "created_at": "2026-08-02 11:58:15.979480",
        "description": "Lift annual servicing",
        "expense_date": "2026-08-05",
        "id": 1,
        "paid_by": 1,
        "paid_by_name": "Priya Admin",
        "receipt_url": null
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_delete_expense(client, admin, resident, seed):
    expense = create_expense(client, admin)

    res = client.delete(f"/api/expenses/{expense['id']}", headers=resident)
    assert res.status_code == 403
    assert len(client.get("/api/expenses/", headers=admin).get_json()) == 1
```
</details>


### TC-286 · Worker cannot read the ledger

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `GET /api/expenses/` → 403

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_worker_cannot_read_the_ledger(client, worker, seed):
    assert client.get("/api/expenses/", headers=worker).status_code == 403
    assert client.get("/api/expenses/summary", headers=worker).status_code == 403
```
</details>


### TC-287 · COMMITTEE_MEMBER is an admin role but must not reach the ledger

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("get", "/api/expenses/summary"),
])
def test_committee_member_is_not_finance(client, tokens, seed, method, path):
    """COMMITTEE_MEMBER is an admin role but must not reach the ledger."""
    res = getattr(client, method)(path, json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=committee_headers(tokens))

    assert res.status_code == 403
```
</details>


### TC-288 · COMMITTEE_MEMBER is an admin role but must not reach the ledger

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("get", "/api/expenses/summary"),
])
def test_committee_member_is_not_finance(client, tokens, seed, method, path):
    """COMMITTEE_MEMBER is an admin role but must not reach the ledger."""
    res = getattr(client, method)(path, json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=committee_headers(tokens))

    assert res.status_code == 403
```
</details>


### TC-289 · COMMITTEE_MEMBER is an admin role but must not reach the ledger

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/summary`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/summary`
- JSON body:
    ```json
    {
      "category": "MAINTENANCE",
      "description": "Painting",
      "amount": 1000,
      "expense_date": "2026-08-05"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("method, path", [
    ("get", "/api/expenses/"),
    ("post", "/api/expenses/"),
    ("get", "/api/expenses/summary"),
])
def test_committee_member_is_not_finance(client, tokens, seed, method, path):
    """COMMITTEE_MEMBER is an admin role but must not reach the ledger."""
    res = getattr(client, method)(path, json={
        "category": "MAINTENANCE", "description": "Painting",
        "amount": 1000, "expense_date": "2026-08-05",
    }, headers=committee_headers(tokens))

    assert res.status_code == 403
```
</details>


---

## Notices

`Backend/tests/test_notices.py` · US-10 · **18/18 passed**


### TC-290 · Admin can publish a notice

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "Water shutdown",
      "content": "No water 9am-1pm on Friday.",
      "category": "MAINTENANCE"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "category": "MAINTENANCE",
      "content": "No water 9am-1pm on Friday.",
      "created_at": "2026-08-02 11:59:17.610994",
      "id": 1,
      "is_active": true,
      "published_by": 1,
      "published_by_name": "Priya Admin",
      "title": "Water shutdown"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_publish_a_notice(client, seed, admin):
    res = _create_notice(client, admin, category="MAINTENANCE")
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Water shutdown"
    assert body["category"] == "MAINTENANCE"
    assert body["is_active"] is True
    assert body["published_by_name"] == "Priya Admin"
```
</details>


### TC-291 · Category defaults to general when omitted

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "Water shutdown",
      "content": "No water 9am-1pm on Friday."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "category": "GENERAL",
      "content": "No water 9am-1pm on Friday.",
      "created_at": "2026-08-02 11:59:18.021720",
      "id": 1,
      "is_active": true,
      "published_by": 1,
      "published_by_name": "Priya Admin",
      "title": "Water shutdown"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_category_defaults_to_general_when_omitted(client, seed, admin):
    body = _create_notice(client, admin).get_json()
    assert body["category"] == "GENERAL"
```
</details>


### TC-292 · Treasurer is also allowed to publish

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "Water shutdown",
      "content": "No water 9am-1pm on Friday."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "category": "GENERAL",
      "content": "No water 9am-1pm on Friday.",
      "created_at": "2026-08-02 11:59:18.309329",
      "id": 1,
      "is_active": true,
      "published_by": 2,
      "published_by_name": "Tarun Treasurer",
      "title": "Water shutdown"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_treasurer_is_also_allowed_to_publish(client, seed, treasurer):
    assert _create_notice(client, treasurer).status_code == 201
```
</details>


### TC-293 · Notice list returns newest notices

**Page being tested:** `GET http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/notices/` → 201, `POST /api/notices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"category": "GENERAL", "content": "No water 9am-1pm on Friday.", "created_at": "2026-08-02 11:59:18.670347", "id": 2, "is_active": true, "published_by": 1, "published_by_name": "Priya Admin", "title": "Second"}, {"category": "GENERAL", "content": "No water 9am-1pm on Friday.", "created_at": "2026-08-02 11:59:18.608110", "id": 1, "is_active": true, "published_by": 1, "published_by_name": "Priya …
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_notice_list_returns_newest_notices(client, seed, admin):
    _create_notice(client, admin, title="First")
    _create_notice(client, admin, title="Second")

    res = client.get("/api/notices/", headers=admin)
    assert res.status_code == 200
    titles = [n["title"] for n in res.get_json()]
    assert {"First", "Second"} <= set(titles)
```
</details>


### TC-294 · Admin can update a notice

**Page being tested:** `PUT http://127.0.0.1:5000/api/notices/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/notices/1`
- JSON body:
    ```json
    {
      "title": "Water shutdown (revised)",
      "category": "EMERGENCY"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/notices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "category": "EMERGENCY",
      "content": "No water 9am-1pm on Friday.",
      "created_at": "2026-08-02 11:59:19.399435",
      "id": 1,
      "is_active": true,
      "published_by": 1,
      "published_by_name": "Priya Admin",
      "title": "Water shutdown (revised)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_update_a_notice(client, seed, admin):
    nid = _create_notice(client, admin).get_json()["id"]

    res = client.put(f"/api/notices/{nid}",
                     json={"title": "Water shutdown (revised)", "category": "EMERGENCY"},
                     headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["title"] == "Water shutdown (revised)"
    assert body["category"] == "EMERGENCY"
```
</details>


### TC-295 · Delete soft deletes and hides the notice from the list

**Page being tested:** `GET http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/notices/` → 201, `DELETE /api/notices/1` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Notice removed"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_soft_deletes_and_hides_the_notice_from_the_list(client, seed, admin):
    nid = _create_notice(client, admin, title="Temporary").get_json()["id"]

    res = client.delete(f"/api/notices/{nid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Notice removed"

    titles = [n["title"] for n in client.get("/api/notices/", headers=admin).get_json()]
    assert "Temporary" not in titles
```
</details>


### TC-296 · Updating a missing notice returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/notices/9999`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/notices/9999`
- JSON body:
    ```json
    {
      "title": "x"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_updating_a_missing_notice_returns_404(client, seed, admin):
    assert client.put("/api/notices/9999", json={"title": "x"}, headers=admin).status_code == 404
```
</details>


### TC-297 · Notice without title is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "content": "body only"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "title is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "title is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_notice_without_title_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", json={"content": "body only"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"
```
</details>


### TC-298 · Notice without content is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "title only"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "content is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "content is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_notice_without_content_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", json={"title": "title only"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "content is required"
```
</details>


### TC-299 · Blank title is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "   ",
      "content": "No water 9am-1pm on Friday."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "title is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "title is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_blank_title_is_rejected(client, seed, admin):
    res = _create_notice(client, admin, title="   ")
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"
```
</details>


### TC-300 · Unknown category is rejected instead of being stored

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "Water shutdown",
      "content": "No water 9am-1pm on Friday.",
      "category": "SPAM"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "category must be one of: GENERAL, FINANCIAL, MAINTENANCE, EMERGENCY"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_category_is_rejected_instead_of_being_stored(client, seed, admin):
    res = _create_notice(client, admin, category="SPAM")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")
```
</details>


### TC-301 · Unknown category on update is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/notices/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/notices/1`
- JSON body:
    ```json
    {
      "category": "NONSENSE"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/notices/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "category must be one of: GENERAL, FINANCIAL, MAINTENANCE, EMERGENCY"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_category_on_update_is_rejected(client, seed, admin):
    nid = _create_notice(client, admin).get_json()["id"]
    res = client.put(f"/api/notices/{nid}", json={"category": "NONSENSE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")
```
</details>


### TC-302 · Null body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be valid JSON"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"
```
</details>


### TC-303 · List body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be a JSON object"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/notices/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"
```
</details>


### TC-304 · Notices require authentication

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "a",
      "content": "b"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (1): `GET /api/notices/` → 401

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_notices_require_authentication(client, seed):
    assert client.get("/api/notices/").status_code == 401
    assert client.post("/api/notices/", json={"title": "a", "content": "b"}).status_code == 401
```
</details>


### TC-305 · Resident can read notices

**Page being tested:** `GET http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/notices/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "category": "GENERAL",
        "content": "No water 9am-1pm on Friday.",
        "created_at": "2026-08-02 11:59:23.269768",
        "id": 1,
        "is_active": true,
        "published_by": 1,
        "published_by_name": "Priya Admin",
        "title": "Water shutdown"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_read_notices(client, seed, admin, resident):
    _create_notice(client, admin)
    res = client.get("/api/notices/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1
```
</details>


### TC-306 · Resident cannot publish a notice

**Page being tested:** `POST http://127.0.0.1:5000/api/notices/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/notices/`
- JSON body:
    ```json
    {
      "title": "Water shutdown",
      "content": "No water 9am-1pm on Friday."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_publish_a_notice(client, seed, resident):
    res = _create_notice(client, resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-307 · Resident cannot update or delete a notice

**Page being tested:** `DELETE http://127.0.0.1:5000/api/notices/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/notices/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/notices/` → 201, `PUT /api/notices/1` → 403

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_update_or_delete_a_notice(client, seed, admin, resident):
    nid = _create_notice(client, admin).get_json()["id"]
    assert client.put(f"/api/notices/{nid}", json={"title": "hacked"},
                      headers=resident).status_code == 403
    assert client.delete(f"/api/notices/{nid}", headers=resident).status_code == 403
```
</details>


---

## Polls & Voting

`Backend/tests/test_polls.py` · US-13 · **29/29 passed**


### TC-308 · Admin can create a poll with options

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {"created_at": "2026-08-02 11:59:36.807447", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": false, "id": 1, "my_option_id": null, "options": [{"id": 1, "percentage": 0, "text": "Yes", "votes": 0}, {"id": 2, "percentage": 0, "text": "No", "votes": 0}], "start_date": "2026-08-02", "status": "ACTIVE", "title": "New gym equipment?", "total_votes":…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_create_a_poll_with_options(client, seed, admin):
    res = _create_poll(client, admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "New gym equipment?"
    assert body["status"] == "ACTIVE"
    assert [o["text"] for o in body["options"]] == ["Yes", "No"]
    assert body["total_votes"] == 0
    assert body["has_voted"] is False
```
</details>


### TC-309 · Start date defaults to today when omitted

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {"created_at": "2026-08-02 11:59:38.455876", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": false, "id": 1, "my_option_id": null, "options": [{"id": 1, "percentage": 0, "text": "Yes", "votes": 0}, {"id": 2, "percentage": 0, "text": "No", "votes": 0}], "start_date": "2026-08-02", "status": "ACTIVE", "title": "New gym equipment?", "total_votes":…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_start_date_defaults_to_today_when_omitted(client, seed, admin):
    body = _create_poll(client, admin).get_json()
    assert body["start_date"] == str(TODAY)
    assert body["end_date"] == str(NEXT_WEEK)
```
</details>


### TC-310 · Explicit start date is kept

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "2026-08-09",
      "start_date": "2026-07-31"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {"created_at": "2026-08-02 11:59:40.302834", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": false, "id": 1, "my_option_id": null, "options": [{"id": 1, "percentage": 0, "text": "Yes", "votes": 0}, {"id": 2, "percentage": 0, "text": "No", "votes": 0}], "start_date": "2026-07-31", "status": "ACTIVE", "title": "New gym equipment?", "total_votes":…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_explicit_start_date_is_kept(client, seed, admin):
    body = _create_poll(client, admin, start_date=str(TODAY - timedelta(days=2))).get_json()
    assert body["start_date"] == str(TODAY - timedelta(days=2))
```
</details>


### TC-311 · Single poll can be fetched

**Page being tested:** `GET http://127.0.0.1:5000/api/polls/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/polls/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"created_at": "2026-08-02 11:59:42.038583", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": false, "id": 1, "my_option_id": null, "options": [{"id": 1, "percentage": 0, "text": "Yes", "votes": 0}, {"id": 2, "percentage": 0, "text": "No", "votes": 0}], "start_date": "2026-08-02", "status": "ACTIVE", "title": "New gym equipment?", "total_votes":…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_single_poll_can_be_fetched(client, seed, admin):
    pid, _ = _open_poll(client, admin)
    res = client.get(f"/api/polls/{pid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["id"] == pid
```
</details>


### TC-312 · Resident can vote and results are tallied

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/1/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/1/vote`
- JSON body:
    ```json
    {
      "option_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"message": "Vote cast successfully", "poll": {"created_at": "2026-08-02 11:59:43.894699", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": true, "id": 1, "my_option_id": 1, "options": [{"id": 1, "percentage": 100.0, "text": "Yes", "votes": 1}, {"id": 2, "percentage": 0.0, "text": "No", "votes": 0}], "start_date": "2026-08-02", "status": "ACTIVE…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-313 · Admin can close a poll

**Page being tested:** `PUT http://127.0.0.1:5000/api/polls/1/close`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/polls/1/close`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"message": "Poll closed", "poll": {"created_at": "2026-08-02 11:59:44.589351", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": false, "id": 1, "my_option_id": null, "options": [{"id": 1, "percentage": 0, "text": "Yes", "votes": 0}, {"id": 2, "percentage": 0, "text": "No", "votes": 0}], "start_date": "2026-08-02", "status": "CLOSED", "title": "…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_close_a_poll(client, seed, admin):
    pid, _ = _open_poll(client, admin)
    res = client.put(f"/api/polls/{pid}/close", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["poll"]["status"] == "CLOSED"
```
</details>


### TC-314 · Admin can delete a poll

**Page being tested:** `GET http://127.0.0.1:5000/api/polls/1`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/polls/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/polls/` → 201, `DELETE /api/polls/1` → 200

**Expected Output:**

- HTTP Status Code: `200 or 404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_delete_a_poll(client, seed, admin):
    pid, _ = _open_poll(client, admin)
    assert client.delete(f"/api/polls/{pid}", headers=admin).status_code == 200
    assert client.get(f"/api/polls/{pid}", headers=admin).status_code == 404
```
</details>


### TC-315 · Poll list reports has voted per user

**Page being tested:** `GET http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/polls/` → 201, `GET /api/polls/` → 200, `POST /api/polls/1/vote` → 200, `GET /api/polls/` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `my_option_id` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"created_at": "2026-08-02 11:59:46.284225", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": false, "id": 1, "my_option_id": null, "options": [{"id": 1, "percentage": 100.0, "text": "Yes", "votes": 1}, {"id": 2, "percentage": 0.0, "text": "No", "votes": 0}], "start_date": "2026-08-02", "status": "ACTIVE", "title": "New gym equipment?", "total_…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-316 · Voting twice returns 409

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/1/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/1/vote`
- JSON body:
    ```json
    {
      "option_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201, `POST /api/polls/1/vote` → 200

**Expected Output:**

- HTTP Status Code: `200 or 409`
- JSON: `error` == "You have already voted"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "You have already voted"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_voting_twice_returns_409(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin)
    assert client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                       headers=resident).status_code == 200

    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 409
    assert res.get_json()["error"] == "You have already voted"
```
</details>


### TC-317 · Voting on a closed poll is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/1/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/1/vote`
- JSON body:
    ```json
    {
      "option_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201, `PUT /api/polls/1/close` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Poll is not active"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Poll is not active"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_voting_on_a_closed_poll_is_rejected(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin)
    client.put(f"/api/polls/{pid}/close", headers=admin)

    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Poll is not active"
```
</details>


### TC-318 · Voting before the window opens is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/1/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/1/vote`
- JSON body:
    ```json
    {
      "option_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Voting opens on 2026-08-03"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_voting_before_the_window_opens_is_rejected(client, seed, admin, resident):
    pid, option_id = _open_poll(client, admin,
                                start_date=str(TOMORROW),
                                end_date=str(NEXT_WEEK))
    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("Voting opens on")
```
</details>


### TC-319 · Voting after the window closes is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/1/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/1/vote`
- JSON body:
    ```json
    {
      "option_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Voting closed on 2026-08-01"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_voting_after_the_window_closes_is_rejected(client, seed, admin, resident):
    yesterday = TODAY - timedelta(days=1)
    pid, option_id = _open_poll(client, admin,
                                start_date=str(TODAY - timedelta(days=5)),
                                end_date=str(yesterday))
    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": option_id},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("Voting closed on")
```
</details>


### TC-320 · Voting for an option of another poll is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/2/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/2/vote`
- JSON body:
    ```json
    {
      "option_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Invalid option"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Invalid option"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_voting_for_an_option_of_another_poll_is_rejected(client, seed, admin, resident):
    _pid_a, option_a = _open_poll(client, admin, title="Poll A")
    pid_b, _option_b = _open_poll(client, admin, title="Poll B")

    res = client.post(f"/api/polls/{pid_b}/vote", json={"option_id": option_a},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Invalid option"
```
</details>


### TC-321 · Poll requires an end date

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "No deadline",
      "options": [
        "Yes",
        "No"
      ]
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "end_date is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "end_date is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_poll_requires_an_end_date(client, seed, admin):
    res = client.post("/api/polls/",
                      json={"title": "No deadline", "options": ["Yes", "No"]},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "end_date is required"
```
</details>


### TC-322 · Poll requires a title

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "title is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "title is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_poll_requires_a_title(client, seed, admin):
    res = client.post("/api/polls/",
                      json={"options": ["Yes", "No"], "end_date": str(NEXT_WEEK)},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"
```
</details>


### TC-323 · "abc" used to be split into three single-letter options

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": "abc",
      "end_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "options must be a list"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "options must be a list"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_options_given_as_a_string_are_rejected(client, seed, admin):
    """"abc" used to be split into three single-letter options."""
    res = _create_poll(client, admin, options="abc")
    assert res.status_code == 400
    assert res.get_json()["error"] == "options must be a list"
```
</details>


### TC-324 · Missing options are rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "No options",
      "end_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "options must be a list"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "options must be a list"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_missing_options_are_rejected(client, seed, admin):
    res = client.post("/api/polls/",
                      json={"title": "No options", "end_date": str(NEXT_WEEK)},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "options must be a list"
```
</details>


### TC-325 · Fewer than two options are rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Only one"
      ],
      "end_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "At least 2 options required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "At least 2 options required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_fewer_than_two_options_are_rejected(client, seed, admin):
    res = _create_poll(client, admin, options=["Only one"])
    assert res.status_code == 400
    assert res.get_json()["error"] == "At least 2 options required"
```
</details>


### TC-326 · Blank options do not count towards the minimum

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Yes",
        "   ",
        null
      ],
      "end_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "At least 2 options required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "At least 2 options required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_blank_options_do_not_count_towards_the_minimum(client, seed, admin):
    res = _create_poll(client, admin, options=["Yes", "   ", None])
    assert res.status_code == 400
    assert res.get_json()["error"] == "At least 2 options required"
```
</details>


### TC-327 · Unparseable end date is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "31-12-2026"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "end_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "end_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unparseable_end_date_is_rejected(client, seed, admin):
    res = _create_poll(client, admin, end_date="31-12-2026")
    assert res.status_code == 400
    assert res.get_json()["error"] == "end_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-328 · End date before start date is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "2026-08-02",
      "start_date": "2026-08-09"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "end_date cannot be before start_date"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "end_date cannot be before start_date"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_end_date_before_start_date_is_rejected(client, seed, admin):
    res = _create_poll(client, admin,
                       start_date=str(NEXT_WEEK), end_date=str(TODAY))
    assert res.status_code == 400
    assert res.get_json()["error"] == "end_date cannot be before start_date"
```
</details>


### TC-329 · Unknown status is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "New gym equipment?",
      "description": "Should we buy a treadmill?",
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "2026-08-09",
      "status": "PENDING"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "vote_status must be one of: DRAFT, ACTIVE, CLOSED"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_status_is_rejected(client, seed, admin):
    res = _create_poll(client, admin, status="PENDING")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("vote_status must be one of:")
```
</details>


### TC-330 · Vote requires an option id

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/1/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/1/vote`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "option_id is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "option_id is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_vote_requires_an_option_id(client, seed, admin, resident):
    pid, _ = _open_poll(client, admin)
    res = client.post(f"/api/polls/{pid}/vote", json={}, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "option_id is required"
```
</details>


### TC-331 · Non numeric option id is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/1/vote`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/1/vote`
- JSON body:
    ```json
    {
      "option_id": "abc"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "option_id must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "option_id must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_non_numeric_option_id_is_rejected(client, seed, admin, resident):
    pid, _ = _open_poll(client, admin)
    res = client.post(f"/api/polls/{pid}/vote", json={"option_id": "abc"}, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "option_id must be a whole number"
```
</details>


### TC-332 · Null body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be valid JSON"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/polls/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"
```
</details>


### TC-333 · List body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be a JSON object"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/polls/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"
```
</details>


### TC-334 · Polls require authentication

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "x"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (1): `GET /api/polls/` → 401

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_polls_require_authentication(client, seed):
    assert client.get("/api/polls/").status_code == 401
    assert client.post("/api/polls/", json={"title": "x"}).status_code == 401
```
</details>


### TC-335 · Resident can read the poll list

**Page being tested:** `GET http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/polls/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"created_at": "2026-08-02 11:59:53.301701", "created_by": 1, "description": "Should we buy a treadmill?", "end_date": "2026-08-09", "has_voted": false, "id": 1, "my_option_id": null, "options": [{"id": 1, "percentage": 0, "text": "Yes", "votes": 0}, {"id": 2, "percentage": 0, "text": "No", "votes": 0}], "start_date": "2026-08-02", "status": "ACTIVE", "title": "New gym equipment?", "total_votes"…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_read_the_poll_list(client, seed, admin, resident):
    _create_poll(client, admin)
    res = client.get("/api/polls/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1
```
</details>


### TC-336 · Resident cannot create close or delete a poll

**Page being tested:** `DELETE http://127.0.0.1:5000/api/polls/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/polls/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/auth/login` → 200, `POST /api/polls/` → 201, `POST /api/polls/` → 403, `PUT /api/polls/1/close` → 403

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_create_close_or_delete_a_poll(client, seed, admin, resident):
    pid, _ = _open_poll(client, admin)

    created = _create_poll(client, resident, title="Resident poll")
    assert created.status_code == 403
    assert created.get_json()["error"] == "You are not allowed to perform this action"

    assert client.put(f"/api/polls/{pid}/close", headers=resident).status_code == 403
    assert client.delete(f"/api/polls/{pid}", headers=resident).status_code == 403
```
</details>


---

## Maintenance Tasks

`Backend/tests/test_maintenance.py` · US-11 · **24/24 passed**


### TC-337 · Admin can create a task

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Generator servicing",
      "description": "Quarterly diesel generator service",
      "category": "GENERATOR",
      "scheduled_date": "2026-08-12"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `completed_at` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "assigned_to": null,
      "assigned_to_name": null,
      "category": "GENERATOR",
      "completed_at": null,
      "created_by": 1,
      "description": "Quarterly diesel generator service",
      "id": 1,
      "scheduled_date": "2026-08-12",
      "status": "PENDING",
      "title": "Generator servicing"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_create_a_task(client, seed, admin):
    res = _create_task(client, admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Generator servicing"
    assert body["category"] == "GENERATOR"
    assert body["scheduled_date"] == SCHEDULED
    assert body["status"] == "PENDING"
    assert body["completed_at"] is None
```
</details>


### TC-338 · Task can be assigned to a worker

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Generator servicing",
      "description": "Quarterly diesel generator service",
      "category": "GENERATOR",
      "scheduled_date": "2026-08-12",
      "assigned_to": 6
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "assigned_to": 6,
      "assigned_to_name": "Ramesh Worker",
      "category": "GENERATOR",
      "completed_at": null,
      "created_by": 1,
      "description": "Quarterly diesel generator service",
      "id": 1,
      "scheduled_date": "2026-08-12",
      "status": "PENDING",
      "title": "Generator servicing"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_task_can_be_assigned_to_a_worker(client, seed, admin):
    body = _create_task(client, admin, assigned_to=seed["worker_id"]).get_json()
    assert body["assigned_to"] == seed["worker_id"]
    assert body["assigned_to_name"] == "Ramesh Worker"
```
</details>


### TC-339 · Task list is returned

**Page being tested:** `GET http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "assigned_to": null,
        "assigned_to_name": null,
        "category": "WATER_TANK",
        "completed_at": null,
        "created_by": 1,
        "description": "Quarterly diesel generator service",
        "id": 1,
        "scheduled_date": "2026-08-12",
        "status": "PENDING",
        "title": "Tank cleaning"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_task_list_is_returned(client, seed, admin):
    _create_task(client, admin, title="Tank cleaning", category="WATER_TANK")
    res = client.get("/api/maintenance/", headers=admin)
    assert res.status_code == 200
    assert [t["title"] for t in res.get_json()] == ["Tank cleaning"]
```
</details>


### TC-340 · Admin can update a task

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/1`
- JSON body:
    ```json
    {
      "title": "Generator servicing (rescheduled)",
      "category": "ELECTRICAL",
      "scheduled_date": "2026-08-22",
      "status": "IN_PROGRESS"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "assigned_to": null,
      "assigned_to_name": null,
      "category": "ELECTRICAL",
      "completed_at": null,
      "created_by": 1,
      "description": "Quarterly diesel generator service",
      "id": 1,
      "scheduled_date": "2026-08-22",
      "status": "IN_PROGRESS",
      "title": "Generator servicing (rescheduled)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_update_a_task(client, seed, admin):
    tid = _task_id(client, admin)
    new_date = str(date.today() + timedelta(days=20))

    res = client.put(f"/api/maintenance/{tid}",
                     json={"title": "Generator servicing (rescheduled)",
                           "category": "ELECTRICAL",
                           "scheduled_date": new_date,
                           "status": "IN_PROGRESS"},
                     headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["title"] == "Generator servicing (rescheduled)"
    assert body["category"] == "ELECTRICAL"
    assert body["scheduled_date"] == new_date
    assert body["status"] == "IN_PROGRESS"
```
</details>


### TC-341 · Admin can complete a task

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/1/complete`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/1/complete`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `completed_at` is set

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "assigned_to": null,
      "assigned_to_name": null,
      "category": "GENERATOR",
      "completed_at": "2026-08-02 11:58:38.718598",
      "created_by": 1,
      "description": "Quarterly diesel generator service",
      "id": 1,
      "scheduled_date": "2026-08-12",
      "status": "COMPLETED",
      "title": "Generator servicing"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_complete_a_task(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}/complete", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None
```
</details>


### TC-342 · Admin can delete a task

**Page being tested:** `GET http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201, `DELETE /api/maintenance/1` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Task deleted"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_delete_a_task(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.delete(f"/api/maintenance/{tid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Task deleted"
    assert client.get("/api/maintenance/", headers=admin).get_json() == []
```
</details>


### TC-343 · Completing a missing task returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/9999/complete`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/9999/complete`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_completing_a_missing_task_returns_404(client, seed, admin):
    assert client.put("/api/maintenance/9999/complete", headers=admin).status_code == 404
```
</details>


### TC-344 · Completing an already completed task returns 409

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/1/complete`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/1/complete`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201, `PUT /api/maintenance/1/complete` → 200

**Expected Output:**

- HTTP Status Code: `200 or 409`
- JSON: `error` == "Task is already completed"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Task is already completed"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_completing_an_already_completed_task_returns_409(client, seed, admin):
    tid = _task_id(client, admin)
    assert client.put(f"/api/maintenance/{tid}/complete", headers=admin).status_code == 200

    res = client.put(f"/api/maintenance/{tid}/complete", headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == "Task is already completed"
```
</details>


### TC-345 · Updating status to completed stamps completed at

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/1`
- JSON body:
    ```json
    {
      "status": "COMPLETED"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `completed_at` is set

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "assigned_to": null,
      "assigned_to_name": null,
      "category": "GENERATOR",
      "completed_at": "2026-08-02 11:58:39.935211",
      "created_by": 1,
      "description": "Quarterly diesel generator service",
      "id": 1,
      "scheduled_date": "2026-08-12",
      "status": "COMPLETED",
      "title": "Generator servicing"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_updating_status_to_completed_stamps_completed_at(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}", json={"status": "COMPLETED"}, headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None
```
</details>


### TC-346 · Reopening a completed task clears completed at

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/1`
- JSON body:
    ```json
    {
      "status": "PENDING"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201, `PUT /api/maintenance/1/complete` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `completed_at` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "assigned_to": null,
      "assigned_to_name": null,
      "category": "GENERATOR",
      "completed_at": null,
      "created_by": 1,
      "description": "Quarterly diesel generator service",
      "id": 1,
      "scheduled_date": "2026-08-12",
      "status": "PENDING",
      "title": "Generator servicing"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_reopening_a_completed_task_clears_completed_at(client, seed, admin):
    tid = _task_id(client, admin)
    client.put(f"/api/maintenance/{tid}/complete", headers=admin)

    res = client.put(f"/api/maintenance/{tid}", json={"status": "PENDING"}, headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "PENDING"
    assert body["completed_at"] is None
```
</details>


### TC-347 · Task requires a title

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "category": "GENERATOR",
      "scheduled_date": "2026-08-12"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "title is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "title is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_task_requires_a_title(client, seed, admin):
    res = client.post("/api/maintenance/",
                      json={"category": "GENERATOR", "scheduled_date": SCHEDULED},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "title is required"
```
</details>


### TC-348 · Task requires a scheduled date

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "No date",
      "category": "GENERATOR"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "scheduled_date is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "scheduled_date is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_task_requires_a_scheduled_date(client, seed, admin):
    res = client.post("/api/maintenance/",
                      json={"title": "No date", "category": "GENERATOR"},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date is required"
```
</details>


### TC-349 · Blank scheduled date is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Generator servicing",
      "description": "Quarterly diesel generator service",
      "category": "GENERATOR",
      "scheduled_date": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "scheduled_date is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "scheduled_date is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_blank_scheduled_date_is_rejected(client, seed, admin):
    res = _create_task(client, admin, scheduled_date="")
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date is required"
```
</details>


### TC-350 · Day first scheduled date is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Generator servicing",
      "description": "Quarterly diesel generator service",
      "category": "GENERATOR",
      "scheduled_date": "10/08/2026"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "scheduled_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "scheduled_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_day_first_scheduled_date_is_rejected(client, seed, admin):
    res = _create_task(client, admin, scheduled_date="10/08/2026")
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-351 · Unknown category is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Generator servicing",
      "description": "Quarterly diesel generator service",
      "category": "ROOFING",
      "scheduled_date": "2026-08-12"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "task_category must be one of: GENERATOR, WATER_TANK, CLEANING, ELECTRICAL, PLUMBING, OTHER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_category_is_rejected(client, seed, admin):
    res = _create_task(client, admin, category="ROOFING")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("task_category must be one of:")
```
</details>


### TC-352 · Unknown status on update is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/1`
- JSON body:
    ```json
    {
      "status": "DONE"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "task_status must be one of: PENDING, IN_PROGRESS, COMPLETED"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_status_on_update_is_rejected(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}", json={"status": "DONE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("task_status must be one of:")
```
</details>


### TC-353 · Bad scheduled date on update is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/maintenance/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/maintenance/1`
- JSON body:
    ```json
    {
      "scheduled_date": "not-a-date"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "scheduled_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "scheduled_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_bad_scheduled_date_on_update_is_rejected(client, seed, admin):
    tid = _task_id(client, admin)
    res = client.put(f"/api/maintenance/{tid}",
                     json={"scheduled_date": "not-a-date"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "scheduled_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-354 · Non numeric assignee is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Generator servicing",
      "description": "Quarterly diesel generator service",
      "category": "GENERATOR",
      "scheduled_date": "2026-08-12",
      "assigned_to": "ramesh"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "assigned_to must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "assigned_to must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_non_numeric_assignee_is_rejected(client, seed, admin):
    res = _create_task(client, admin, assigned_to="ramesh")
    assert res.status_code == 400
    assert res.get_json()["error"] == "assigned_to must be a whole number"
```
</details>


### TC-355 · Null body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be valid JSON"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/maintenance/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"
```
</details>


### TC-356 · List body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be a JSON object"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/maintenance/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"
```
</details>


### TC-357 · Maintenance requires authentication

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "x"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (1): `GET /api/maintenance/` → 401

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_maintenance_requires_authentication(client, seed):
    assert client.get("/api/maintenance/").status_code == 401
    assert client.post("/api/maintenance/", json={"title": "x"}).status_code == 401
```
</details>


### TC-358 · Resident can read the task list

**Page being tested:** `GET http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "assigned_to": null,
        "assigned_to_name": null,
        "category": "GENERATOR",
        "completed_at": null,
        "created_by": 1,
        "description": "Quarterly diesel generator service",
        "id": 1,
        "scheduled_date": "2026-08-12",
        "status": "PENDING",
        "title": "Generator servicing"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_read_the_task_list(client, seed, admin, resident):
    _create_task(client, admin)
    res = client.get("/api/maintenance/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1
```
</details>


### TC-359 · Worker cannot create a task

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Generator servicing",
      "description": "Quarterly diesel generator service",
      "category": "GENERATOR",
      "scheduled_date": "2026-08-12"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_worker_cannot_create_a_task(client, seed, worker):
    res = _create_task(client, worker)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-360 · Resident cannot update complete or delete a task

**Page being tested:** `DELETE http://127.0.0.1:5000/api/maintenance/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/maintenance/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/auth/login` → 200, `POST /api/maintenance/` → 201, `PUT /api/maintenance/1` → 403, `PUT /api/maintenance/1/complete` → 403

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_update_complete_or_delete_a_task(client, seed, admin, resident):
    tid = _task_id(client, admin)
    assert client.put(f"/api/maintenance/{tid}", json={"title": "x"},
                      headers=resident).status_code == 403
    assert client.put(f"/api/maintenance/{tid}/complete", headers=resident).status_code == 403
    assert client.delete(f"/api/maintenance/{tid}", headers=resident).status_code == 403
```
</details>


---

## Equipment / Maintenance Predictor

`Backend/tests/test_equipment.py` · US-15 · **28/28 passed**


### TC-361 · Admin can add equipment

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "2026-07-23",
      "service_frequency_days": 90,
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "category": "GENERATOR",
      "created_at": "2026-08-02 11:58:00.124545",
      "days_until_due": 80,
      "estimated_service_cost": 4500.0,
      "id": 1,
      "last_serviced_date": "2026-07-23",
      "name": "Diesel Generator",
      "risk_level": "LOW",
      "service_frequency_days": 90
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-362 · Equipment list is readable

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "category": "GENERATOR",
        "created_at": "2026-08-02 11:58:00.631333",
        "days_until_due": 80,
        "estimated_service_cost": 4500.0,
        "id": 1,
        "last_serviced_date": "2026-07-23",
        "name": "Diesel Generator",
        "risk_level": "LOW",
        "service_frequency_days": 90
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_equipment_list_is_readable(client, seed, admin):
    _create_equipment(client, admin)
    res = client.get("/api/equipment/", headers=admin)
    assert res.status_code == 200
    assert len(res.get_json()) == 1
```
</details>


### TC-363 · Overdue equipment reports negative days and high risk

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "2026-04-04",
      "service_frequency_days": 90,
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "category": "GENERATOR",
      "created_at": "2026-08-02 11:58:01.335203",
      "days_until_due": -30,
      "estimated_service_cost": 4500.0,
      "id": 1,
      "last_serviced_date": "2026-04-04",
      "name": "Diesel Generator",
      "risk_level": "HIGH",
      "service_frequency_days": 90
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_overdue_equipment_reports_negative_days_and_high_risk(client, seed, admin):
    body = _create_equipment(
        client, admin,
        last_serviced_date=str(date.today() - timedelta(days=120)),
        service_frequency_days=90,
    ).get_json()
    assert body["days_until_due"] == -30
    assert body["risk_level"] == "HIGH"
```
</details>


### TC-364 · Equipment nearing its due date is medium risk

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "2026-05-09",
      "service_frequency_days": 100,
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "category": "GENERATOR",
      "created_at": "2026-08-02 11:58:02.137726",
      "days_until_due": 15,
      "estimated_service_cost": 4500.0,
      "id": 1,
      "last_serviced_date": "2026-05-09",
      "name": "Diesel Generator",
      "risk_level": "MEDIUM",
      "service_frequency_days": 100
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_equipment_nearing_its_due_date_is_medium_risk(client, seed, admin):
    body = _create_equipment(
        client, admin,
        last_serviced_date=str(date.today() - timedelta(days=85)),
        service_frequency_days=100,
    ).get_json()
    assert body["risk_level"] == "MEDIUM"
```
</details>


### TC-365 · Marking serviced updates the last serviced date

**Page being tested:** `PUT http://127.0.0.1:5000/api/equipment/1/service`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/equipment/1/service`
- JSON body:
    ```json
    {
      "cost": 5000,
      "vendor_name": "PowerCare",
      "notes": "Oil and filter changed"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "equipment": {
        "category": "GENERATOR",
        "created_at": "2026-08-02 11:58:02.488363",
        "days_until_due": 90,
        "estimated_service_cost": 4500.0,
        "id": 1,
        "last_serviced_date": "2026-08-02",
        "name": "Diesel Generator",
        "risk_level": "LOW",
        "service_frequency_days": 90
      },
      "message": "Equipment marked as serviced"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-366 · Service can be backdated

**Page being tested:** `PUT http://127.0.0.1:5000/api/equipment/1/service`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/equipment/1/service`
- JSON body:
    ```json
    {
      "serviced_date": "2026-07-28"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "equipment": {
        "category": "GENERATOR",
        "created_at": "2026-08-02 11:58:02.756118",
        "days_until_due": 85,
        "estimated_service_cost": 4500.0,
        "id": 1,
        "last_serviced_date": "2026-07-28",
        "name": "Diesel Generator",
        "risk_level": "LOW",
        "service_frequency_days": 90
      },
      "message": "Equipment marked as serviced"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_service_can_be_backdated(client, seed, admin):
    eid = _equipment_id(client, admin)
    backdate = str(date.today() - timedelta(days=5))
    res = client.put(f"/api/equipment/{eid}/service",
                     json={"serviced_date": backdate}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["equipment"]["last_serviced_date"] == backdate
```
</details>


### TC-367 · Service history lists logged services

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/1/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/1/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201, `PUT /api/equipment/1/service` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "cost": 5000.0,
        "id": 1,
        "logged_by_name": "Priya Admin",
        "notes": null,
        "serviced_date": "2026-08-02",
        "vendor_name": "PowerCare"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-368 · History of unserviced equipment is empty

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/1/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/1/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_history_of_unserviced_equipment_is_empty(client, seed, admin):
    eid = _equipment_id(client, admin)
    assert client.get(f"/api/equipment/{eid}/history", headers=admin).get_json() == []
```
</details>


### TC-369 · Forecast returns items due within 30 days

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/forecast`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/forecast`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201, `POST /api/equipment/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "count": 1,
      "due_in_30_days": [
        {
          "category": "LIFT",
          "days_until_due": 10,
          "estimated_cost": 2000.0,
          "id": 1,
          "name": "Lift",
          "risk_level": "MEDIUM"
        }
      ],
      "total_estimated_cost": 2000.0
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-370 · Forecast works with no equipment

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/forecast`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/forecast`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "count": 0,
      "due_in_30_days": [],
      "total_estimated_cost": 0
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_forecast_works_with_no_equipment(client, seed, admin):
    res = client.get("/api/equipment/forecast", headers=admin)
    assert res.status_code == 200
    assert res.get_json() == {"due_in_30_days": [], "total_estimated_cost": 0, "count": 0}
```
</details>


### TC-371 · Admin can delete equipment

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201, `DELETE /api/equipment/1` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Equipment deleted"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_delete_equipment(client, seed, admin):
    eid = _equipment_id(client, admin)
    res = client.delete(f"/api/equipment/{eid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Equipment deleted"
    assert client.get("/api/equipment/", headers=admin).get_json() == []
```
</details>


### TC-372 · History of missing equipment returns 404

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/9999/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/9999/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_history_of_missing_equipment_returns_404(client, seed, admin):
    assert client.get("/api/equipment/9999/history", headers=admin).status_code == 404
```
</details>


### TC-373 · Equipment requires a name

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "category": "GENERATOR",
      "last_serviced_date": "2026-08-02",
      "service_frequency_days": 90
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "name is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "name is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_equipment_requires_a_name(client, seed, admin):
    res = client.post("/api/equipment/",
                      json={"category": "GENERATOR",
                            "last_serviced_date": str(date.today()),
                            "service_frequency_days": 90},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "name is required"
```
</details>


### TC-374 · Equipment requires a last serviced date

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Pump",
      "category": "OTHER",
      "service_frequency_days": 30
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "last_serviced_date is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "last_serviced_date is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_equipment_requires_a_last_serviced_date(client, seed, admin):
    res = client.post("/api/equipment/",
                      json={"name": "Pump", "category": "OTHER",
                            "service_frequency_days": 30},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "last_serviced_date is required"
```
</details>


### TC-375 · Blank last serviced date is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "",
      "service_frequency_days": 90,
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "last_serviced_date is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "last_serviced_date is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_blank_last_serviced_date_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, last_serviced_date="")
    assert res.status_code == 400
    assert res.get_json()["error"] == "last_serviced_date is required"
```
</details>


### TC-376 · Bad last serviced date is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "10/08/2026",
      "service_frequency_days": 90,
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "last_serviced_date must be a valid date (YYYY-MM-DD)"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "last_serviced_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_bad_last_serviced_date_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, last_serviced_date="10/08/2026")
    assert res.status_code == 400
    assert res.get_json()["error"] == "last_serviced_date must be a valid date (YYYY-MM-DD)"
```
</details>


### TC-377 · A 0 frequency used to be stored and then divided by on every GET

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "2026-07-23",
      "service_frequency_days": 0,
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "service_frequency_days must be at least 1"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "service_frequency_days must be at least 1"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_zero_service_frequency_is_rejected(client, seed, admin):
    """A 0 frequency used to be stored and then divided by on every GET."""
    res = _create_equipment(client, admin, service_frequency_days=0)
    assert res.status_code == 400
    assert res.get_json()["error"] == "service_frequency_days must be at least 1"
```
</details>


### TC-378 · Zero service frequency as a string is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "2026-07-23",
      "service_frequency_days": "0",
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "service_frequency_days must be at least 1"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "service_frequency_days must be at least 1"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_zero_service_frequency_as_a_string_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, service_frequency_days="0")
    assert res.status_code == 400
    assert res.get_json()["error"] == "service_frequency_days must be at least 1"
```
</details>


### TC-379 · Missing service frequency is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Pump",
      "category": "OTHER",
      "last_serviced_date": "2026-08-02"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "service_frequency_days is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "service_frequency_days is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_missing_service_frequency_is_rejected(client, seed, admin):
    res = client.post("/api/equipment/",
                      json={"name": "Pump", "category": "OTHER",
                            "last_serviced_date": str(date.today())},
                      headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "service_frequency_days is required"
```
</details>


### TC-380 · Negative estimated cost is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "GENERATOR",
      "last_serviced_date": "2026-07-23",
      "service_frequency_days": 90,
      "estimated_service_cost": -1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "estimated_service_cost must be at least 0"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "estimated_service_cost must be at least 0"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_negative_estimated_cost_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, estimated_service_cost=-1)
    assert res.status_code == 400
    assert res.get_json()["error"] == "estimated_service_cost must be at least 0"
```
</details>


### TC-381 · Unknown category is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Diesel Generator",
      "category": "ROBOT",
      "last_serviced_date": "2026-07-23",
      "service_frequency_days": 90,
      "estimated_service_cost": 4500
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "equipment_category must be one of: GENERATOR, WATER_TANK, LIFT, PEST_CONTROL, FIRE_SAFETY, OTHER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_category_is_rejected(client, seed, admin):
    res = _create_equipment(client, admin, category="ROBOT")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("equipment_category must be one of:")
```
</details>


### TC-382 · An empty cost box in the UI must mean "not recorded", not an error

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/1/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/1/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201, `PUT /api/equipment/1/service` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `cost` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "cost": null,
        "id": 1,
        "logged_by_name": "Priya Admin",
        "notes": null,
        "serviced_date": "2026-08-02",
        "vendor_name": null
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_blank_cost_when_marking_serviced_is_accepted(client, seed, admin):
    """An empty cost box in the UI must mean "not recorded", not an error."""
    eid = _equipment_id(client, admin)
    res = client.put(f"/api/equipment/{eid}/service", json={"cost": ""}, headers=admin)
    assert res.status_code == 200

    logs = client.get(f"/api/equipment/{eid}/history", headers=admin).get_json()
    assert logs[0]["cost"] is None
```
</details>


### TC-383 · Non numeric cost when marking serviced is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/equipment/1/service`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/equipment/1/service`
- JSON body:
    ```json
    {
      "cost": "five"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "cost must be a number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "cost must be a number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_non_numeric_cost_when_marking_serviced_is_rejected(client, seed, admin):
    eid = _equipment_id(client, admin)
    res = client.put(f"/api/equipment/{eid}/service", json={"cost": "five"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "cost must be a number"
```
</details>


### TC-384 · Null body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be valid JSON"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/equipment/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"
```
</details>


### TC-385 · List body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be a JSON object"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/equipment/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"
```
</details>


### TC-386 · Equipment requires authentication

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "x"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `GET /api/equipment/` → 401, `GET /api/equipment/forecast` → 401

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_equipment_requires_authentication(client, seed):
    assert client.get("/api/equipment/").status_code == 401
    assert client.get("/api/equipment/forecast").status_code == 401
    assert client.post("/api/equipment/", json={"name": "x"}).status_code == 401
```
</details>


### TC-387 · Resident can read equipment and forecast

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/forecast`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/forecast`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/equipment/` → 201, `GET /api/equipment/` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "count": 0,
      "due_in_30_days": [],
      "total_estimated_cost": 0
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_read_equipment_and_forecast(client, seed, admin, resident):
    _create_equipment(client, admin)
    assert client.get("/api/equipment/", headers=resident).status_code == 200
    assert client.get("/api/equipment/forecast", headers=resident).status_code == 200
```
</details>


### TC-388 · Resident cannot add service or delete equipment

**Page being tested:** `DELETE http://127.0.0.1:5000/api/equipment/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/equipment/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/auth/login` → 200, `POST /api/equipment/` → 201, `POST /api/equipment/` → 403, `PUT /api/equipment/1/service` → 403

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_add_service_or_delete_equipment(client, seed, admin, resident):
    eid = _equipment_id(client, admin)

    created = _create_equipment(client, resident, name="Sneaky pump")
    assert created.status_code == 403
    assert created.get_json()["error"] == "You are not allowed to perform this action"

    assert client.put(f"/api/equipment/{eid}/service", json={},
                      headers=resident).status_code == 403
    assert client.delete(f"/api/equipment/{eid}", headers=resident).status_code == 403
```
</details>


---

## Society Health Score

`Backend/tests/test_health.py` · US-17 · **20/20 passed**


### TC-389 · Get calculate returns the full score shape

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_get_calculate_returns_the_full_score_shape(client, seed, admin):
    res = client.get("/api/health/calculate", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert SHAPE_KEYS <= set(body)
    assert isinstance(body["total_score"], (int, float))
    assert body["grade"] in ("GREEN", "YELLOW", "RED")
```
</details>


### TC-390 · Post calculate uses the same view as get

**Page being tested:** `POST http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `GET /api/health/calculate` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_post_calculate_uses_the_same_view_as_get(client, seed, admin):
    get_body = client.get("/api/health/calculate", headers=admin).get_json()
    res = client.post("/api/health/calculate", headers=admin)
    assert res.status_code == 200
    post_body = res.get_json()
    assert post_body["month"] == get_body["month"]
    assert post_body["total_score"] == get_body["total_score"]
```
</details>


### TC-391 · Calculate accepts explicit month and year

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate?month=3&year=2025`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate?month=3&year=2025`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 3,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2025
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_calculate_accepts_explicit_month_and_year(client, seed, admin):
    res = client.get("/api/health/calculate?month=3&year=2025", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert body["month"] == 3
    assert body["year"] == 2025
```
</details>


### TC-392 · Calculate is an upsert for the month

**Page being tested:** `GET http://127.0.0.1:5000/api/health/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `GET /api/health/calculate?month=5&year=2026` → 200, `GET /api/health/calculate?month=5&year=2026` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
        "calculated_at": "2026-08-02 11:58:17.893675",
        "complaint_score": 0.0,
        "grade": "RED",
        "id": 1,
        "maintenance_score": 0.0,
        "month": 5,
        "notice_score": 0.0,
        "payment_score": 0.0,
        "poll_score": 0.0,
        "total_score": 0.0,
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_calculate_is_an_upsert_for_the_month(client, seed, admin):
    client.get("/api/health/calculate?month=5&year=2026", headers=admin)
    client.get("/api/health/calculate?month=5&year=2026", headers=admin)

    history = client.get("/api/health/history", headers=admin).get_json()
    assert len([s for s in history if (s["month"], s["year"]) == (5, 2026)]) == 1
```
</details>


### TC-393 · History is empty before anything is calculated

**Page being tested:** `GET http://127.0.0.1:5000/api/health/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_history_is_empty_before_anything_is_calculated(client, seed, admin):
    res = client.get("/api/health/history", headers=admin)
    assert res.status_code == 200
    assert res.get_json() == []
```
</details>


### TC-394 · History returns the saved score

**Page being tested:** `GET http://127.0.0.1:5000/api/health/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `GET /api/health/calculate?month=4&year=2026` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
        "calculated_at": "2026-08-02 11:58:18.309043",
        "complaint_score": 0.0,
        "grade": "RED",
        "id": 1,
        "maintenance_score": 0.0,
        "month": 4,
        "notice_score": 0.0,
        "payment_score": 0.0,
        "poll_score": 0.0,
        "total_score": 0.0,
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-395 · Empty society is not awarded a perfect score

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_empty_society_is_not_awarded_a_perfect_score(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert body["total_score"] < 100
    assert body["grade"] == "RED"
```
</details>


### TC-396 · Empty society does not report nonsense invoice alerts

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_empty_society_does_not_report_nonsense_invoice_alerts(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert "0 invoices unpaid" not in body["alert_reason"]
    assert "0 complaints unresolved" not in body["alert_reason"]
```
</details>


### TC-397 · Components without data are named as not scored

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_components_without_data_are_named_as_not_scored(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert "not scored (no data)" in body["alert_reason"]
    for component in ("payment", "complaint", "poll", "maintenance"):
        assert component in body["alert_reason"]
```
</details>


### TC-398 · Missing notices are flagged

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_missing_notices_are_flagged(client, seed, admin):
    body = client.get("/api/health/calculate", headers=admin).get_json()
    assert body["notice_score"] == 0.0
    assert "No notices posted this month" in body["alert_reason"]
```
</details>


### TC-399 · Only the notice component has data, so a posted notice is a full score

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate?month=8&year=2026`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate?month=8&year=2026`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/notices/` → 201

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "GREEN",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 15.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 100.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-400 · Month above twelve is rejected

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate?month=13`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate?month=13`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "month must be at most 12"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at most 12"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_month_above_twelve_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?month=13", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at most 12"
```
</details>


### TC-401 · Month below one is rejected

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate?month=0`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate?month=0`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "month must be at least 1"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be at least 1"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_month_below_one_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?month=0", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be at least 1"
```
</details>


### TC-402 · Non numeric month is rejected

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate?month=june`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate?month=june`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "month must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "month must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_non_numeric_month_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?month=june", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "month must be a whole number"
```
</details>


### TC-403 · Year before 2000 is rejected

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate?year=1999`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate?year=1999`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "year must be at least 2000"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "year must be at least 2000"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_year_before_2000_is_rejected(client, seed, admin):
    res = client.get("/api/health/calculate?year=1999", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "year must be at least 2000"
```
</details>


### TC-404 · Health endpoints require authentication

**Page being tested:** `GET http://127.0.0.1:5000/api/health/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/history`
- JSON body: _none_
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `GET /api/health/calculate` → 401, `POST /api/health/calculate` → 401

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_health_endpoints_require_authentication(client, seed):
    assert client.get("/api/health/calculate").status_code == 401
    assert client.post("/api/health/calculate").status_code == 401
    assert client.get("/api/health/history").status_code == 401
```
</details>


### TC-405 · Resident cannot calculate the score

**Page being tested:** `POST http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `GET /api/health/calculate` → 403

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_calculate_the_score(client, seed, resident):
    for call in (client.get, client.post):
        res = call("/api/health/calculate", headers=resident)
        assert res.status_code == 403
        assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-406 · Worker cannot calculate the score

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_worker_cannot_calculate_the_score(client, seed, worker):
    assert client.get("/api/health/calculate", headers=worker).status_code == 403
```
</details>


### TC-407 · Treasurer can calculate the score

**Page being tested:** `GET http://127.0.0.1:5000/api/health/calculate`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/calculate`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
      "complaint_score": 0.0,
      "grade": "RED",
      "has_data": true,
      "maintenance_score": 0.0,
      "month": 8,
      "notice_score": 0.0,
      "payment_score": 0.0,
      "poll_score": 0.0,
      "total_score": 0.0,
      "year": 2026
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_treasurer_can_calculate_the_score(client, seed, treasurer):
    assert client.get("/api/health/calculate", headers=treasurer).status_code == 200
```
</details>


### TC-408 · Any authenticated user can read the history

**Page being tested:** `GET http://127.0.0.1:5000/api/health/history`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/health/history`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `GET /api/health/calculate` → 200, `GET /api/health/history` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "alert_reason": "No notices posted this month | not scored (no data): complaint, maintenance, payment, poll",
        "calculated_at": "2026-08-02 11:58:23.866767",
        "complaint_score": 0.0,
        "grade": "RED",
        "id": 1,
        "maintenance_score": 0.0,
        "month": 8,
        "notice_score": 0.0,
        "payment_score": 0.0,
        "poll_score": 0.0,
        "total_score": 0.0,
        "year": 2026
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_any_authenticated_user_can_read_the_history(client, seed, admin, resident, worker):
    client.get("/api/health/calculate", headers=admin)
    assert client.get("/api/health/history", headers=resident).status_code == 200
    assert client.get("/api/health/history", headers=worker).status_code == 200
```
</details>


---

## Neighbour Conflict Resolver

`Backend/tests/test_conflicts.py` · US-16 · **27/27 passed**


### TC-409 · Resident can raise a conflict against another flat

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    {
      "reported_apartment_id": 2,
      "category": "NOISE",
      "description": "Loud music after 11pm on weekdays."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "message": "Conflict report submitted. The concerned flat will be notified anonymously.",
      "report_id": 1
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_raise_a_conflict_against_another_flat(client, seed, resident):
    res = _raise_conflict(client, resident, seed["other_apartment_id"])
    assert res.status_code == 201
    body = res.get_json()
    assert body["report_id"] > 0
    assert "anonymously" in body["message"]
```
</details>


### TC-410 · Admin sees every report with the reporter named

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "category": "NOISE",
        "created_at": "2026-08-02 11:57:23.852717",
        "description": "Loud music after 11pm on weekdays.",
        "id": 1,
        "reported_apartment_id": 2,
        "reported_by": 4,
        "reported_by_name": "Ravi Resident",
        "reported_flat": "B-202",
        "reported_flat_response": null,
        "resolution_note": null,
        "resolved_at": null,
        "response_submitted_at": null,
        "status": "OPEN"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_sees_every_report_with_the_reporter_named(client, seed, resident, admin):
    _raise_conflict(client, resident, seed["other_apartment_id"])

    res = client.get("/api/conflicts/", headers=admin)
    assert res.status_code == 200
    report = res.get_json()[0]
    assert report["reported_by"] == seed["resident_id"]
    assert report["reported_by_name"] == "Ravi Resident"
    assert report["reported_flat"] == "B-202"
    assert report["status"] == "OPEN"
```
</details>


### TC-411 · Reported flat can submit its side

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201, `PUT /api/conflicts/1/respond` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `response_submitted_at` is set

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "category": "NOISE",
        "created_at": "2026-08-02 11:57:24.221126",
        "description": "Loud music after 11pm on weekdays.",
        "id": 1,
        "reported_apartment_id": 1,
        "reported_flat": "A-101",
        "reported_flat_response": "The music was for a birthday, sorry.",
        "resolution_note": null,
        "resolved_at": null,
        "response_submitted_at": "2026-08-02 11:57:24.249054",
        "status": "UNDER_REVIEW"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-412 · Admin can resolve a report

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/resolve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/resolve`
- JSON body:
    ```json
    {
      "resolution_note": "Both parties agreed on quiet hours."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `resolved_at` is set

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"message": "Conflict resolved", "report": {"category": "NOISE", "created_at": "2026-08-02 11:57:24.761949", "description": "Loud music after 11pm on weekdays.", "id": 1, "reported_apartment_id": 2, "reported_by": 4, "reported_by_name": "Ravi Resident", "reported_flat": "B-202", "reported_flat_response": null, "resolution_note": "Both parties agreed on quiet hours.", "resolved_at": "2026-08-02 11…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-413 · Resolution note defaults when not supplied

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/resolve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/resolve`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {"message": "Conflict resolved", "report": {"category": "NOISE", "created_at": "2026-08-02 11:57:25.277445", "description": "Loud music after 11pm on weekdays.", "id": 1, "reported_apartment_id": 2, "reported_by": 4, "reported_by_name": "Ravi Resident", "reported_flat": "B-202", "reported_flat_response": null, "resolution_note": "Resolved by secretary", "resolved_at": "2026-08-02 11:57:25.314688"…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resolution_note_defaults_when_not_supplied(client, seed, resident, admin):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    body = client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin).get_json()
    assert body["report"]["resolution_note"] == "Resolved by secretary"
```
</details>


### TC-414 · Pending lists open and under review reports for admin

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/pending`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/pending`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (8): `POST /api/conflicts/` → 201, `PUT /api/conflicts/2/respond` → 200, `POST /api/conflicts/` → 201, `PUT /api/conflicts/3/resolve` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"category": "NOISE", "created_at": "2026-08-02 11:57:25.724734", "description": "Loud music after 11pm on weekdays.", "id": 1, "reported_apartment_id": 2, "reported_by": 4, "reported_by_name": "Ravi Resident", "reported_flat": "B-202", "reported_flat_response": null, "resolution_note": null, "resolved_at": null, "response_submitted_at": null, "status": "OPEN"}, {"category": "NOISE", "created_at…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-415 · Responding to a missing report returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/9999/respond`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/9999/respond`
- JSON body:
    ```json
    {
      "response": "hi"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_responding_to_a_missing_report_returns_404(client, seed, admin):
    assert client.put("/api/conflicts/9999/respond", json={"response": "hi"},
                      headers=admin).status_code == 404
```
</details>


### TC-416 · The accused flat must not learn who reported them

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "category": "NOISE",
        "created_at": "2026-08-02 11:57:26.724874",
        "description": "Loud music after 11pm on weekdays.",
        "id": 1,
        "reported_apartment_id": 1,
        "reported_flat": "A-101",
        "reported_flat_response": null,
        "resolution_note": null,
        "resolved_at": null,
        "response_submitted_at": null,
        "status": "OPEN"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
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
```
</details>


### TC-417 · Reporter own report is also returned without identity fields

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "category": "NOISE",
        "created_at": "2026-08-02 11:57:27.148961",
        "description": "Loud music after 11pm on weekdays.",
        "id": 1,
        "reported_apartment_id": 2,
        "reported_flat": "B-202",
        "reported_flat_response": null,
        "resolution_note": null,
        "resolved_at": null,
        "response_submitted_at": null,
        "status": "OPEN"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_reporter_own_report_is_also_returned_without_identity_fields(client, seed, resident):
    _raise_conflict(client, resident, seed["other_apartment_id"])

    report = client.get("/api/conflicts/", headers=resident).get_json()[0]
    assert "reported_by" not in report
    assert "reported_by_name" not in report
```
</details>


### TC-418 · Resident cannot see unrelated reports

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_see_unrelated_reports(client, seed, worker, resident):
    _raise_conflict(client, worker, seed["other_apartment_id"])
    assert client.get("/api/conflicts/", headers=resident).get_json() == []
```
</details>


### TC-419 · This endpoint reveals reporter identities, so residents get a 403

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/pending`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/pending`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `GET /api/conflicts/pending` → 403

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_pending_is_admin_only(client, seed, resident, worker):
    """This endpoint reveals reporter identities, so residents get a 403."""
    res = client.get("/api/conflicts/pending", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
    assert client.get("/api/conflicts/pending", headers=worker).status_code == 403
```
</details>


### TC-420 · Reporting your own flat is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    {
      "reported_apartment_id": 1,
      "category": "NOISE",
      "description": "Loud music after 11pm on weekdays."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "You cannot raise a conflict against your own flat"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "You cannot raise a conflict against your own flat"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_reporting_your_own_flat_is_rejected(client, seed, resident):
    res = _raise_conflict(client, resident, seed["apartment_id"])
    assert res.status_code == 400
    assert res.get_json()["error"] == "You cannot raise a conflict against your own flat"
```
</details>


### TC-421 · Reporting an unknown flat returns 404

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    {
      "reported_apartment_id": 9999,
      "category": "NOISE",
      "description": "Loud music after 11pm on weekdays."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`
- JSON: `error` == "Apartment not found"

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "Apartment not found"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_reporting_an_unknown_flat_returns_404(client, seed, resident):
    res = _raise_conflict(client, resident, 9999)
    assert res.status_code == 404
    assert res.get_json()["error"] == "Apartment not found"
```
</details>


### TC-422 · A user from another flat cannot respond

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/respond`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/respond`
- JSON body:
    ```json
    {
      "response": "Not my problem"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "Only the reported flat can respond to this report"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "Only the reported flat can respond to this report"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_a_user_from_another_flat_cannot_respond(client, seed, resident):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]

    res = client.put(f"/api/conflicts/{rid}/respond",
                     json={"response": "Not my problem"}, headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "Only the reported flat can respond to this report"
```
</details>


### TC-423 · A user with no flat cannot respond

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/respond`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/respond`
- JSON body:
    ```json
    {
      "response": "x"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "Only the reported flat can respond to this report"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_a_user_with_no_flat_cannot_respond(client, seed, worker, resident):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    assert client.put(f"/api/conflicts/{rid}/respond", json={"response": "x"},
                      headers=worker).status_code == 403
```
</details>


### TC-424 · Responding twice returns 409

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/respond`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/respond`
- JSON body:
    ```json
    {
      "response": "Second"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201, `PUT /api/conflicts/1/respond` → 200

**Expected Output:**

- HTTP Status Code: `200 or 409`
- JSON: `error` == "A response has already been submitted for this report"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "A response has already been submitted for this report"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_responding_twice_returns_409(client, seed, worker, resident):
    rid = _report_against_resident_flat(client, seed, worker)
    assert client.put(f"/api/conflicts/{rid}/respond", json={"response": "First"},
                      headers=resident).status_code == 200

    res = client.put(f"/api/conflicts/{rid}/respond", json={"response": "Second"},
                     headers=resident)
    assert res.status_code == 409
    assert res.get_json()["error"] == "A response has already been submitted for this report"
```
</details>


### TC-425 · Responding to a resolved report returns 409

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/respond`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/respond`
- JSON body:
    ```json
    {
      "response": "Too late"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201, `PUT /api/conflicts/1/resolve` → 200

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "This report has already been resolved"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "This report has already been resolved"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_responding_to_a_resolved_report_returns_409(client, seed, worker, resident, admin):
    rid = _report_against_resident_flat(client, seed, worker)
    client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin)

    res = client.put(f"/api/conflicts/{rid}/respond", json={"response": "Too late"},
                     headers=resident)
    assert res.status_code == 409
    assert res.get_json()["error"] == "This report has already been resolved"
```
</details>


### TC-426 · Resolving twice returns 409

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/resolve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/resolve`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201, `PUT /api/conflicts/1/resolve` → 200

**Expected Output:**

- HTTP Status Code: `200 or 409`
- JSON: `error` == "This report is already resolved"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "This report is already resolved"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resolving_twice_returns_409(client, seed, resident, admin):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    assert client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin).status_code == 200

    res = client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=admin)
    assert res.status_code == 409
    assert res.get_json()["error"] == "This report is already resolved"
```
</details>


### TC-427 · Conflict requires a description

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    {
      "reported_apartment_id": 2,
      "category": "NOISE"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "description is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "description is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_conflict_requires_a_description(client, seed, resident):
    res = client.post("/api/conflicts/",
                      json={"reported_apartment_id": seed["other_apartment_id"],
                            "category": "NOISE"},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "description is required"
```
</details>


### TC-428 · Conflict requires a reported apartment

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    {
      "category": "NOISE",
      "description": "Noisy"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "reported_apartment_id is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "reported_apartment_id is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_conflict_requires_a_reported_apartment(client, seed, resident):
    res = client.post("/api/conflicts/",
                      json={"category": "NOISE", "description": "Noisy"},
                      headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "reported_apartment_id is required"
```
</details>


### TC-429 · Unknown category is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    {
      "reported_apartment_id": 2,
      "category": "SHOUTING",
      "description": "Loud music after 11pm on weekdays."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "category must be one of: NOISE, PARKING, GARBAGE, COMMON_AREA_MISUSE, PETS, OTHER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_category_is_rejected(client, seed, resident):
    res = _raise_conflict(client, resident, seed["other_apartment_id"], category="SHOUTING")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("category must be one of:")
```
</details>


### TC-430 · Non numeric apartment id is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    {
      "reported_apartment_id": "B-202",
      "category": "NOISE",
      "description": "Loud music after 11pm on weekdays."
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "reported_apartment_id must be a whole number"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "reported_apartment_id must be a whole number"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_non_numeric_apartment_id_is_rejected(client, seed, resident):
    res = _raise_conflict(client, resident, "B-202")
    assert res.status_code == 400
    assert res.get_json()["error"] == "reported_apartment_id must be a whole number"
```
</details>


### TC-431 · Response text is required

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/respond`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/respond`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "response is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "response is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_response_text_is_required(client, seed, worker, resident):
    rid = _report_against_resident_flat(client, seed, worker)
    res = client.put(f"/api/conflicts/{rid}/respond", json={}, headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "response is required"
```
</details>


### TC-432 · Null body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be valid JSON"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_null_body_is_rejected(client, seed, resident):
    res = client.post("/api/conflicts/", data="null",
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"
```
</details>


### TC-433 · List body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be a JSON object"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_body_is_rejected(client, seed, resident):
    res = client.post("/api/conflicts/", data="[]",
                      content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"
```
</details>


### TC-434 · Conflicts require authentication

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/resolve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/resolve`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (3): `GET /api/conflicts/` → 401, `POST /api/conflicts/` → 401, `GET /api/conflicts/pending` → 401

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_conflicts_require_authentication(client, seed):
    assert client.get("/api/conflicts/").status_code == 401
    assert client.post("/api/conflicts/", json={}).status_code == 401
    assert client.get("/api/conflicts/pending").status_code == 401
    assert client.put("/api/conflicts/1/resolve", json={}).status_code == 401
```
</details>


### TC-435 · Resident cannot resolve a report

**Page being tested:** `PUT http://127.0.0.1:5000/api/conflicts/1/resolve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/conflicts/1/resolve`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_resolve_a_report(client, seed, resident):
    rid = _raise_conflict(client, resident,
                          seed["other_apartment_id"]).get_json()["report_id"]
    res = client.put(f"/api/conflicts/{rid}/resolve", json={}, headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


---

## Visitor Parking

`Backend/tests/test_parking.py` · US-12 · **27/27 passed**


### TC-436 · Admin can add a slot

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    {
      "slot_number": "P1"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `occupied_by_apartment_id` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "expected_arrival_time": null,
      "flat_number": null,
      "id": 1,
      "occupied_by_apartment_id": null,
      "occupied_since": null,
      "slot_number": "P1",
      "status": "AVAILABLE",
      "visitor_name": null,
      "visitor_vehicle_number": null
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_add_a_slot(client, seed, admin):
    res = _add_slot(client, admin)
    assert res.status_code == 201
    body = res.get_json()
    assert body["slot_number"] == "P1"
    assert body["status"] == "AVAILABLE"
    assert body["occupied_by_apartment_id"] is None
```
</details>


### TC-437 · Slot can be created with an explicit status

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    {
      "slot_number": "P9",
      "status": "OCCUPIED"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "expected_arrival_time": null,
      "flat_number": null,
      "id": 1,
      "occupied_by_apartment_id": null,
      "occupied_since": null,
      "slot_number": "P9",
      "status": "OCCUPIED",
      "visitor_name": null,
      "visitor_vehicle_number": null
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_slot_can_be_created_with_an_explicit_status(client, seed, admin):
    body = _add_slot(client, admin, "P9", status="OCCUPIED").get_json()
    assert body["status"] == "OCCUPIED"
```
</details>


### TC-438 · Slot list is ordered by slot number

**Page being tested:** `GET http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"expected_arrival_time": null, "flat_number": null, "id": 2, "occupied_by_apartment_id": null, "occupied_since": null, "slot_number": "P1", "status": "AVAILABLE", "visitor_name": null, "visitor_vehicle_number": null}, {"expected_arrival_time": null, "flat_number": null, "id": 1, "occupied_by_apartment_id": null, "occupied_since": null, "slot_number": "P2", "status": "AVAILABLE", "visitor_name":…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_slot_list_is_ordered_by_slot_number(client, seed, admin):
    _add_slot(client, admin, "P2")
    _add_slot(client, admin, "P1")

    res = client.get("/api/parking/", headers=admin)
    assert res.status_code == 200
    assert [s["slot_number"] for s in res.get_json()] == ["P1", "P2"]
```
</details>


### TC-439 · Available returns only free slots

**Page being tested:** `GET http://127.0.0.1:5000/api/parking/available`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/parking/available`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `POST /api/parking/` → 201, `PUT /api/parking/2/reserve` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "expected_arrival_time": null,
        "flat_number": null,
        "id": 1,
        "occupied_by_apartment_id": null,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "AVAILABLE",
        "visitor_name": null,
        "visitor_vehicle_number": null
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_available_returns_only_free_slots(client, seed, admin, resident):
    free = _slot_id(client, admin, "P1")
    taken = _slot_id(client, admin, "P2")
    _reserve(client, resident, taken)

    res = client.get("/api/parking/available", headers=resident)
    assert res.status_code == 200
    assert [s["id"] for s in res.get_json()] == [free]
```
</details>


### TC-440 · Resident can reserve a slot for a visitor

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/reserve`
- JSON body:
    ```json
    {
      "visitor_name": "Anil Kumar",
      "visitor_vehicle_number": "KA01AB1234",
      "expected_arrival_time": "2026-09-15T18:30:00"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `occupied_since` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Slot P1 reserved successfully",
      "slot": {
        "expected_arrival_time": "2026-09-15 18:30:00",
        "flat_number": "A-101",
        "id": 1,
        "occupied_by_apartment_id": 1,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "RESERVED",
        "visitor_name": "Anil Kumar",
        "visitor_vehicle_number": "KA01AB1234"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_reserve_a_slot_for_a_visitor(client, seed, resident, admin):
    sid = _slot_id(client, admin)

    res = _reserve(client, resident, sid, expected_arrival_time="2026-09-15T18:30:00")
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Slot P1 reserved successfully"
    slot = body["slot"]
    assert slot["status"] == "RESERVED"
    assert slot["visitor_name"] == "Anil Kumar"
    assert slot["expected_arrival_time"] == "2026-09-15 18:30:00"
    assert slot["occupied_by_apartment_id"] == seed["apartment_id"]
    assert slot["flat_number"] == "A-101"
    # a reservation is not an arrival
    assert slot["occupied_since"] is None
```
</details>


### TC-441 · Occupying a reserved slot keeps the reserving flat

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/occupy`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/occupy`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `PUT /api/parking/1/reserve` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `occupied_since` is set

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Slot P1 marked occupied",
      "slot": {
        "expected_arrival_time": null,
        "flat_number": "A-101",
        "id": 1,
        "occupied_by_apartment_id": 1,
        "occupied_since": "2026-08-02 11:59:28.845233",
        "slot_number": "P1",
        "status": "OCCUPIED",
        "visitor_name": "Anil Kumar",
        "visitor_vehicle_number": "KA01AB1234"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_occupying_a_reserved_slot_keeps_the_reserving_flat(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)

    res = client.put(f"/api/parking/{sid}/occupy", json={}, headers=admin)
    assert res.status_code == 200
    slot = res.get_json()["slot"]
    assert slot["status"] == "OCCUPIED"
    assert slot["occupied_by_apartment_id"] == seed["apartment_id"]
    assert slot["occupied_since"] is not None
    assert slot["visitor_name"] == "Anil Kumar"
```
</details>


### TC-442 · Occupying a free slot attributes it to the caller

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/occupy`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/occupy`
- JSON body:
    ```json
    {
      "visitor_name": "Walk-in"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Slot P1 marked occupied",
      "slot": {
        "expected_arrival_time": null,
        "flat_number": "A-101",
        "id": 1,
        "occupied_by_apartment_id": 1,
        "occupied_since": "2026-08-02 11:59:29.124086",
        "slot_number": "P1",
        "status": "OCCUPIED",
        "visitor_name": "Walk-in",
        "visitor_vehicle_number": null
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_occupying_a_free_slot_attributes_it_to_the_caller(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = client.put(f"/api/parking/{sid}/occupy",
                     json={"visitor_name": "Walk-in"}, headers=resident)
    assert res.status_code == 200
    slot = res.get_json()["slot"]
    assert slot["occupied_by_apartment_id"] == seed["apartment_id"]
    assert slot["visitor_name"] == "Walk-in"
```
</details>


### TC-443 · Resident can release their own reservation

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/release`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/release`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `PUT /api/parking/1/reserve` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `occupied_by_apartment_id` is null
- JSON: `visitor_name` is null
- JSON: `expected_arrival_time` is null
- JSON: `occupied_since` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Slot P1 released",
      "slot": {
        "expected_arrival_time": null,
        "flat_number": null,
        "id": 1,
        "occupied_by_apartment_id": null,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "AVAILABLE",
        "visitor_name": null,
        "visitor_vehicle_number": null
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_release_their_own_reservation(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid, expected_arrival_time="2026-09-15T18:30:00")

    res = client.put(f"/api/parking/{sid}/release", json={}, headers=resident)
    assert res.status_code == 200
    slot = res.get_json()["slot"]
    assert slot["status"] == "AVAILABLE"
    assert slot["occupied_by_apartment_id"] is None
    assert slot["visitor_name"] is None
    assert slot["expected_arrival_time"] is None
    assert slot["occupied_since"] is None
```
</details>


### TC-444 · Admin can release any slot

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/release`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/release`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `PUT /api/parking/1/reserve` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Slot P1 released",
      "slot": {
        "expected_arrival_time": null,
        "flat_number": null,
        "id": 1,
        "occupied_by_apartment_id": null,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "AVAILABLE",
        "visitor_name": null,
        "visitor_vehicle_number": null
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_release_any_slot(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)
    res = client.put(f"/api/parking/{sid}/release", json={}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["slot"]["status"] == "AVAILABLE"
```
</details>


### TC-445 · Admin can delete a slot

**Page being tested:** `GET http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `DELETE /api/parking/1` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Slot removed"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_admin_can_delete_a_slot(client, seed, admin):
    sid = _slot_id(client, admin)
    res = client.delete(f"/api/parking/{sid}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Slot removed"
    assert client.get("/api/parking/", headers=admin).get_json() == []
```
</details>


### TC-446 · Reserving a missing slot returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/9999/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/9999/reserve`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_reserving_a_missing_slot_returns_404(client, seed, resident):
    assert client.put("/api/parking/9999/reserve", json={},
                      headers=resident).status_code == 404
```
</details>


### TC-447 · Reserving an already reserved slot is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/reserve`
- JSON body:
    ```json
    {
      "visitor_name": "Anil Kumar",
      "visitor_vehicle_number": "KA01AB1234"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `PUT /api/parking/1/reserve` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Slot is already RESERVED"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Slot is already RESERVED"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_reserving_an_already_reserved_slot_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)

    res = _reserve(client, admin, sid)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Slot is already RESERVED"
```
</details>


### TC-448 · Occupying an already occupied slot is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/occupy`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/occupy`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `PUT /api/parking/1/occupy` → 200

**Expected Output:**

- HTTP Status Code: `200 or 400`
- JSON: `error` == "Slot is already OCCUPIED"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Slot is already OCCUPIED"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_occupying_an_already_occupied_slot_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    assert client.put(f"/api/parking/{sid}/occupy", json={},
                      headers=resident).status_code == 200

    res = client.put(f"/api/parking/{sid}/occupy", json={}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Slot is already OCCUPIED"
```
</details>


### TC-449 · Releasing someone elses reservation is forbidden

**Page being tested:** `GET http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (6): `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `PUT /api/parking/1/reserve` → 200, `PUT /api/parking/1/release` → 403

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You can only release your own reservation"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "expected_arrival_time": null,
        "flat_number": "A-101",
        "id": 1,
        "occupied_by_apartment_id": 1,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "RESERVED",
        "visitor_name": "Anil Kumar",
        "visitor_vehicle_number": "KA01AB1234"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_releasing_someone_elses_reservation_is_forbidden(client, seed, resident,
                                                          admin, worker):
    sid = _slot_id(client, admin)
    _reserve(client, resident, sid)

    res = client.put(f"/api/parking/{sid}/release", json={}, headers=worker)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You can only release your own reservation"

    # the reservation survived the failed attempt
    assert client.get("/api/parking/", headers=admin).get_json()[0]["status"] == "RESERVED"
```
</details>


### TC-450 · Duplicate slot number returns 409

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    {
      "slot_number": "P1"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` == "Slot already exists"

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Slot already exists"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_duplicate_slot_number_returns_409(client, seed, admin):
    _add_slot(client, admin, "P1")
    res = _add_slot(client, admin, "P1")
    assert res.status_code == 409
    assert res.get_json()["error"] == "Slot already exists"
```
</details>


### TC-451 · The UI sends "" when the arrival time box is left empty

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/reserve`
- JSON body:
    ```json
    {
      "visitor_name": "Anil Kumar",
      "visitor_vehicle_number": "KA01AB1234",
      "expected_arrival_time": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `expected_arrival_time` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Slot P1 reserved successfully",
      "slot": {
        "expected_arrival_time": null,
        "flat_number": "A-101",
        "id": 1,
        "occupied_by_apartment_id": 1,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "RESERVED",
        "visitor_name": "Anil Kumar",
        "visitor_vehicle_number": "KA01AB1234"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_blank_expected_arrival_time_is_accepted(client, seed, resident, admin):
    """The UI sends "" when the arrival time box is left empty."""
    sid = _slot_id(client, admin)
    res = _reserve(client, resident, sid, expected_arrival_time="")
    assert res.status_code == 200
    assert res.get_json()["slot"]["expected_arrival_time"] is None
```
</details>


### TC-452 · Date only expected arrival time is accepted

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/reserve`
- JSON body:
    ```json
    {
      "visitor_name": "Anil Kumar",
      "visitor_vehicle_number": "KA01AB1234",
      "expected_arrival_time": "2026-09-15"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Slot P1 reserved successfully",
      "slot": {
        "expected_arrival_time": "2026-09-15 00:00:00",
        "flat_number": "A-101",
        "id": 1,
        "occupied_by_apartment_id": 1,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "RESERVED",
        "visitor_name": "Anil Kumar",
        "visitor_vehicle_number": "KA01AB1234"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_date_only_expected_arrival_time_is_accepted(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = _reserve(client, resident, sid, expected_arrival_time="2026-09-15")
    assert res.status_code == 200
    assert res.get_json()["slot"]["expected_arrival_time"] == "2026-09-15 00:00:00"
```
</details>


### TC-453 · Unparseable expected arrival time is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/reserve`
- JSON body:
    ```json
    {
      "visitor_name": "Anil Kumar",
      "visitor_vehicle_number": "KA01AB1234",
      "expected_arrival_time": "tomorrow evening"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "expected_arrival_time must be a valid date/time"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expected_arrival_time must be a valid date/time"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unparseable_expected_arrival_time_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = _reserve(client, resident, sid, expected_arrival_time="tomorrow evening")
    assert res.status_code == 400
    assert res.get_json()["error"] == "expected_arrival_time must be a valid date/time"
```
</details>


### TC-454 · Slot number is required

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    {
      "status": "AVAILABLE"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "slot_number is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "slot_number is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_slot_number_is_required(client, seed, admin):
    res = client.post("/api/parking/", json={"status": "AVAILABLE"}, headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "slot_number is required"
```
</details>


### TC-455 · Blank slot number is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    {
      "slot_number": "   "
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "slot_number is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "slot_number is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_blank_slot_number_is_rejected(client, seed, admin):
    res = _add_slot(client, admin, "   ")
    assert res.status_code == 400
    assert res.get_json()["error"] == "slot_number is required"
```
</details>


### TC-456 · Unknown status is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    {
      "slot_number": "P3",
      "status": "BOOKED"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "parking_status must be one of: AVAILABLE, OCCUPIED, RESERVED"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_unknown_status_is_rejected(client, seed, admin):
    res = _add_slot(client, admin, "P3", status="BOOKED")
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("parking_status must be one of:")
```
</details>


### TC-457 · Null body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be valid JSON"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_null_body_is_rejected(client, seed, admin):
    res = client.post("/api/parking/", data="null",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"
```
</details>


### TC-458 · List body is rejected

**Page being tested:** `POST http://127.0.0.1:5000/api/parking/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/parking/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be a JSON object"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_body_is_rejected(client, seed, admin):
    res = client.post("/api/parking/", data="[]",
                      content_type="application/json", headers=admin)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be a JSON object"
```
</details>


### TC-459 · Null body on reserve is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/reserve`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "Request body must be valid JSON"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_null_body_on_reserve_is_rejected(client, seed, resident, admin):
    sid = _slot_id(client, admin)
    res = client.put(f"/api/parking/{sid}/reserve", data="null",
                     content_type="application/json", headers=resident)
    assert res.status_code == 400
    assert res.get_json()["error"] == "Request body must be valid JSON"
```
</details>


### TC-460 · Parking requires authentication

**Page being tested:** `PUT http://127.0.0.1:5000/api/parking/1/reserve`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/parking/1/reserve`
- JSON body:
    ```json
    {}
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (3): `GET /api/parking/` → 401, `GET /api/parking/available` → 401, `POST /api/parking/` → 401

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_parking_requires_authentication(client, seed):
    assert client.get("/api/parking/").status_code == 401
    assert client.get("/api/parking/available").status_code == 401
    assert client.post("/api/parking/", json={"slot_number": "P1"}).status_code == 401
    assert client.put("/api/parking/1/reserve", json={}).status_code == 401
```
</details>


### TC-461 · Resident can read slots

**Page being tested:** `GET http://127.0.0.1:5000/api/parking/available`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/parking/available`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `GET /api/parking/` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "expected_arrival_time": null,
        "flat_number": null,
        "id": 1,
        "occupied_by_apartment_id": null,
        "occupied_since": null,
        "slot_number": "P1",
        "status": "AVAILABLE",
        "visitor_name": null,
        "visitor_vehicle_number": null
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_can_read_slots(client, seed, admin, resident):
    _add_slot(client, admin)
    assert client.get("/api/parking/", headers=resident).status_code == 200
    assert client.get("/api/parking/available", headers=resident).status_code == 200
```
</details>


### TC-462 · Resident cannot add or delete slots

**Page being tested:** `DELETE http://127.0.0.1:5000/api/parking/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/parking/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/parking/` → 201, `POST /api/parking/` → 403

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_resident_cannot_add_or_delete_slots(client, seed, admin, resident):
    sid = _slot_id(client, admin)

    created = _add_slot(client, resident, "P5")
    assert created.status_code == 403
    assert created.get_json()["error"] == "You are not allowed to perform this action"

    assert client.delete(f"/api/parking/{sid}", headers=resident).status_code == 403
```
</details>


---

## Emergency Contacts

`Backend/tests/test_emergency.py` · US-07 · **50/50 passed**


### TC-463 · Create contact returns 201

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "availability": "24x7",
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_returns_201(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin, json=CONTACT)
    assert res.status_code == 201
    body = res.get_json()
    assert body["name"] == "City Ambulance"
    assert body["service_type"] == "AMBULANCE"
    assert body["phone"] == "108"
    assert body["availability"] == "24x7"
    assert body["id"]
```
</details>


### TC-464 · Create contact returns only real columns

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "availability": "24x7",
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_returns_only_real_columns(client, seed, admin):
    body = client.post("/api/emergency/", headers=admin, json=CONTACT).get_json()
    assert set(body) == {"id", "name", "service_type", "phone", "availability"}
```
</details>


### TC-465 · Create contact uppercases the service type

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "plumber",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `service_type` == "PLUMBER"

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "availability": "24x7",
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "PLUMBER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_uppercases_the_service_type(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "service_type": "plumber"})
    assert res.status_code == 201
    assert res.get_json()["service_type"] == "PLUMBER"
```
</details>


### TC-466 · Create contact blank availability becomes null

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "   "
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `availability` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "availability": null,
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_blank_availability_becomes_null(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "availability": "   "})
    assert res.status_code == 201
    assert res.get_json()["availability"] is None
```
</details>


### TC-467 · Create contact omitted availability is null

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`
- JSON: `availability` is null

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "availability": null,
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_omitted_availability_is_null(client, seed, admin):
    payload = {k: v for k, v in CONTACT.items() if k != "availability"}
    res = client.post("/api/emergency/", headers=admin, json=payload)
    assert res.status_code == 201
    assert res.get_json()["availability"] is None
```
</details>


### TC-468 · phone has no UNIQUE constraint — two services can share a number

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "Backup Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "availability": "24x7",
      "id": 2,
      "name": "Backup Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_two_contacts_may_share_a_phone(client, seed, admin):
    """phone has no UNIQUE constraint — two services can share a number."""
    first = client.post("/api/emergency/", headers=admin, json=CONTACT)
    second = client.post("/api/emergency/", headers=admin,
                         json={**CONTACT, "name": "Backup Ambulance"})
    assert (first.status_code, second.status_code) == (201, 201)
```
</details>


### TC-469 · Create contact missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "name is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["name", "service_type", "phone"])
def test_create_contact_missing_required_field_returns_400(client, seed, admin, missing):
    payload = {k: v for k, v in CONTACT.items() if k != missing}
    res = client.post("/api/emergency/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-470 · Create contact missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "service_type is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["name", "service_type", "phone"])
def test_create_contact_missing_required_field_returns_400(client, seed, admin, missing):
    payload = {k: v for k, v in CONTACT.items() if k != missing}
    res = client.post("/api/emergency/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-471 · Create contact missing required field returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "phone is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("missing", ["name", "service_type", "phone"])
def test_create_contact_missing_required_field_returns_400(client, seed, admin, missing):
    payload = {k: v for k, v in CONTACT.items() if k != missing}
    res = client.post("/api/emergency/", headers=admin, json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == f"{missing} is required"
```
</details>


### TC-472 · Create contact unknown service type returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "ASTRONAUT",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "service_type must be one of: PLUMBER, ELECTRICIAN, SECURITY, FIRE, AMBULANCE, POLICE, LIFT, WATER, OTHER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_unknown_service_type_returns_400(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "service_type": "ASTRONAUT"})
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("service_type must be one of:")
```
</details>


### TC-473 · Create contact phone without digits returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "call-us",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "phone must contain digits"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "phone must contain digits"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_phone_without_digits_returns_400(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "phone": "call-us"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must contain digits"
```
</details>


### TC-474 · Create contact phone longer than 15 chars returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "1234567890123456",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "phone must be 15 characters or fewer"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "phone must be 15 characters or fewer"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_phone_longer_than_15_chars_returns_400(client, seed, admin):
    res = client.post("/api/emergency/", headers=admin,
                      json={**CONTACT, "phone": "1234567890123456"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must be 15 characters or fewer"
```
</details>


### TC-475 · Create contact malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_contact_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/emergency/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-476 · Create contact malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_contact_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/emergency/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-477 · Create contact malformed body returns 400

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    "str"
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_create_contact_malformed_body_returns_400(client, seed, admin, raw, expected):
    res = client.post("/api/emergency/", headers=admin, data=raw,
                      content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-478 · Create contact as resident returns 403

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_as_resident_returns_403(client, seed, resident):
    res = client.post("/api/emergency/", headers=resident, json=CONTACT)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-479 · Create contact as worker returns 403

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_as_worker_returns_403(client, seed, worker):
    assert client.post("/api/emergency/", headers=worker, json=CONTACT).status_code == 403
```
</details>


### TC-480 · Create contact as treasurer returns 201

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "availability": "24x7",
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_as_treasurer_returns_201(client, seed, treasurer):
    assert client.post("/api/emergency/", headers=treasurer, json=CONTACT).status_code == 201
```
</details>


### TC-481 · Create contact without token returns 401

**Page being tested:** `POST http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body:
    ```json
    {
      "name": "City Ambulance",
      "service_type": "AMBULANCE",
      "phone": "108",
      "availability": "24x7"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_create_contact_without_token_returns_401(client, seed):
    assert client.post("/api/emergency/", json=CONTACT).status_code == 401
```
</details>


### TC-482 · List contacts empty directory returns empty list

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_contacts_empty_directory_returns_empty_list(client, seed, admin):
    res = client.get("/api/emergency/", headers=admin)
    assert res.status_code == 200
    assert res.get_json() == []
```
</details>


### TC-483 · List contacts returns the created contact

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "availability": "24x7",
        "id": 1,
        "name": "City Ambulance",
        "phone": "108",
        "service_type": "AMBULANCE"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_contacts_returns_the_created_contact(client, seed, admin, contact_id):
    res = client.get("/api/emergency/", headers=admin)
    assert res.status_code == 200
    body = res.get_json()
    assert [c["id"] for c in body] == [contact_id]
    assert body[0]["name"] == "City Ambulance"
```
</details>


### TC-484 · List contacts is ordered by service type then name

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/emergency/` → 201, `POST /api/emergency/` → 201, `POST /api/emergency/` → 201, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [{"availability": null, "id": 2, "name": "Amit Sparks", "phone": "9990001111", "service_type": "ELECTRICIAN"}, {"availability": null, "id": 1, "name": "Zed Sparks", "phone": "9990001111", "service_type": "ELECTRICIAN"}, {"availability": null, "id": 4, "name": "Fire HQ", "phone": "9990001111", "service_type": "FIRE"}, {"availability": null, "id": 3, "name": "Nita Pipes", "phone": "9990001111", "se…
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_contacts_is_ordered_by_service_type_then_name(client, seed, admin):
    for name, service in [("Zed Sparks", "ELECTRICIAN"), ("Amit Sparks", "ELECTRICIAN"),
                          ("Nita Pipes", "PLUMBER"), ("Fire HQ", "FIRE")]:
        client.post("/api/emergency/", headers=admin,
                    json={"name": name, "service_type": service, "phone": "9990001111"})

    body = client.get("/api/emergency/", headers=admin).get_json()
    assert [(c["service_type"], c["name"]) for c in body] == [
        ("ELECTRICIAN", "Amit Sparks"),
        ("ELECTRICIAN", "Zed Sparks"),
        ("FIRE", "Fire HQ"),
        ("PLUMBER", "Nita Pipes"),
    ]
```
</details>


### TC-485 · Every role may read the emergency directory

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "availability": "24x7",
        "id": 1,
        "name": "City Ambulance",
        "phone": "108",
        "service_type": "AMBULANCE"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_contacts_as_resident_returns_200(client, seed, resident, contact_id):
    """Every role may read the emergency directory."""
    res = client.get("/api/emergency/", headers=resident)
    assert res.status_code == 200
    assert len(res.get_json()) == 1
```
</details>


### TC-486 · List contacts is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_contacts_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/emergency/", headers=headers).status_code == 200
```
</details>


### TC-487 · List contacts is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_contacts_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/emergency/", headers=headers).status_code == 200
```
</details>


### TC-488 · List contacts is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_contacts_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/emergency/", headers=headers).status_code == 200
```
</details>


### TC-489 · List contacts is open to every role

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("role_fixture", ["admin", "treasurer", "resident", "worker"])
def test_list_contacts_is_open_to_every_role(client, request, role_fixture):
    headers = request.getfixturevalue(role_fixture)
    assert client.get("/api/emergency/", headers=headers).status_code == 200
```
</details>


### TC-490 · List contacts without token returns 401

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_list_contacts_without_token_returns_401(client, seed):
    assert client.get("/api/emergency/").status_code == 401
```
</details>


### TC-491 · Update contact returns 200

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "name": "State Ambulance",
      "phone": "102",
      "service_type": "FIRE",
      "availability": "Mon-Fri"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "availability": "Mon-Fri",
      "id": 1,
      "name": "State Ambulance",
      "phone": "102",
      "service_type": "FIRE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_returns_200(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"name": "State Ambulance", "phone": "102",
                           "service_type": "FIRE", "availability": "Mon-Fri"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["id"] == contact_id
    assert body["name"] == "State Ambulance"
    assert body["phone"] == "102"
    assert body["service_type"] == "FIRE"
    assert body["availability"] == "Mon-Fri"
```
</details>


### TC-492 · Update contact leaves omitted fields untouched

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "name": "Renamed Ambulance"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "availability": "24x7",
      "id": 1,
      "name": "Renamed Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_leaves_omitted_fields_untouched(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"name": "Renamed Ambulance"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["name"] == "Renamed Ambulance"
    assert body["service_type"] == "AMBULANCE"
    assert body["phone"] == "108"
    assert body["availability"] == "24x7"
```
</details>


### TC-493 · Update contact blank service type keeps the current one

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "service_type": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `service_type` == "AMBULANCE"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "availability": "24x7",
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_blank_service_type_keeps_the_current_one(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"service_type": ""})
    assert res.status_code == 200
    assert res.get_json()["service_type"] == "AMBULANCE"
```
</details>


### TC-494 · Update contact blank availability clears it

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "availability": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `availability` is null

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "availability": null,
      "id": 1,
      "name": "City Ambulance",
      "phone": "108",
      "service_type": "AMBULANCE"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_blank_availability_clears_it(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"availability": ""})
    assert res.status_code == 200
    assert res.get_json()["availability"] is None
```
</details>


### TC-495 · Update contact unknown service type returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "service_type": "ASTRONAUT"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "service_type must be one of: PLUMBER, ELECTRICIAN, SECURITY, FIRE, AMBULANCE, POLICE, LIFT, WATER, OTHER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_unknown_service_type_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"service_type": "ASTRONAUT"})
    assert res.status_code == 400
    assert res.get_json()["error"].startswith("service_type must be one of:")
```
</details>


### TC-496 · Update contact blank phone returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "phone": ""
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "phone is required"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "phone is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_blank_phone_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, json={"phone": ""})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone is required"
```
</details>


### TC-497 · Update contact phone without digits returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "phone": "ring-us"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "phone must contain digits"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "phone must contain digits"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_phone_without_digits_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, json={"phone": "ring-us"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must contain digits"
```
</details>


### TC-498 · Update contact phone longer than 15 chars returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "phone": "1234567890123456"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` == "phone must be 15 characters or fewer"

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "phone must be 15 characters or fewer"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_phone_longer_than_15_chars_returns_400(client, seed, admin, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin,
                     json={"phone": "1234567890123456"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "phone must be 15 characters or fewer"
```
</details>


### TC-499 · Update contact malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    null
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_contact_malformed_body_returns_400(client, seed, admin, contact_id,
                                                   raw, expected):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, data=raw,
                     content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-500 · Update contact malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    []
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_contact_malformed_body_returns_400(client, seed, admin, contact_id,
                                                   raw, expected):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, data=raw,
                     content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-501 · Update contact malformed body returns 400

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    "str"
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("raw,expected", [
    ("null", "Request body must be valid JSON"),
    ("[]", "Request body must be a JSON object"),
    ('"str"', "Request body must be a JSON object"),
])
def test_update_contact_malformed_body_returns_400(client, seed, admin, contact_id,
                                                   raw, expected):
    res = client.put(f"/api/emergency/{contact_id}", headers=admin, data=raw,
                     content_type="application/json")
    assert res.status_code == 400
    assert res.get_json()["error"] == expected
```
</details>


### TC-502 · Update unknown contact returns 404

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/9999`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/9999`
- JSON body:
    ```json
    {
      "name": "Ghost"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_unknown_contact_returns_404(client, seed, admin):
    res = client.put("/api/emergency/9999", headers=admin, json={"name": "Ghost"})
    assert res.status_code == 404
```
</details>


### TC-503 · Update contact as resident returns 403

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "name": "Hijacked"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_as_resident_returns_403(client, seed, resident, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=resident,
                     json={"name": "Hijacked"})
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-504 · Update contact as worker returns 403

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "name": "Nope"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_as_worker_returns_403(client, seed, worker, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", headers=worker, json={"name": "Nope"})
    assert res.status_code == 403
```
</details>


### TC-505 · Update contact without token returns 401

**Page being tested:** `PUT http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body:
    ```json
    {
      "name": "Anonymous"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_update_contact_without_token_returns_401(client, seed, contact_id):
    res = client.put(f"/api/emergency/{contact_id}", json={"name": "Anonymous"})
    assert res.status_code == 401
```
</details>


### TC-506 · Delete contact returns 200

**Page being tested:** `DELETE http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `message` == "Contact removed"

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    {
      "message": "Contact removed"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_contact_returns_200(client, seed, admin, contact_id):
    res = client.delete(f"/api/emergency/{contact_id}", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Contact removed"
```
</details>


### TC-507 · Delete contact is a hard delete

**Page being tested:** `GET http://127.0.0.1:5000/api/emergency/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/emergency/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201, `DELETE /api/emergency/1` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_contact_is_a_hard_delete(client, seed, admin, contact_id):
    client.delete(f"/api/emergency/{contact_id}", headers=admin)
    assert client.get("/api/emergency/", headers=admin).get_json() == []
```
</details>


### TC-508 · Delete contact twice returns 404

**Page being tested:** `DELETE http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201, `DELETE /api/emergency/1` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_contact_twice_returns_404(client, seed, admin, contact_id):
    client.delete(f"/api/emergency/{contact_id}", headers=admin)
    assert client.delete(f"/api/emergency/{contact_id}", headers=admin).status_code == 404
```
</details>


### TC-509 · Delete unknown contact returns 404

**Page being tested:** `DELETE http://127.0.0.1:5000/api/emergency/9999`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/emergency/9999`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `404`

**Actual Output:**

- HTTP Status Code: `404`
- JSON:
    ```json
    {
      "error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_unknown_contact_returns_404(client, seed, admin):
    assert client.delete("/api/emergency/9999", headers=admin).status_code == 404
```
</details>


### TC-510 · Delete contact as resident returns 403

**Page being tested:** `DELETE http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `403`
- JSON: `error` == "You are not allowed to perform this action"

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_contact_as_resident_returns_403(client, seed, resident, contact_id):
    res = client.delete(f"/api/emergency/{contact_id}", headers=resident)
    assert res.status_code == 403
    assert res.get_json()["error"] == "You are not allowed to perform this action"
```
</details>


### TC-511 · Delete contact as worker returns 403

**Page being tested:** `DELETE http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_contact_as_worker_returns_403(client, seed, worker, contact_id):
    assert client.delete(f"/api/emergency/{contact_id}", headers=worker).status_code == 403
```
</details>


### TC-512 · Delete contact without token returns 401

**Page being tested:** `DELETE http://127.0.0.1:5000/api/emergency/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/emergency/1`
- JSON body: _none_
- Header: _none (unauthenticated request)_
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/emergency/` → 201

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_delete_contact_without_token_returns_401(client, seed, contact_id):
    assert client.delete(f"/api/emergency/{contact_id}").status_code == 401
```
</details>


---

## Regression suite — defects already fixed

`Backend/tests/test_regressions.py` · all · **21/21 passed**


### TC-513 · Duplicate phone returns 409 not 500

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Second",
      "email": "second@x.com",
      "password": "<hidden>",
      "role": "TENANT",
      "phone": "9876543210"
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (1): `POST /api/auth/register` → 201

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` contains "phone"
- JSON: response includes `phone`

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Phone number already registered"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
    def test_duplicate_phone_returns_409_not_500(self, client, seed):
        first = client.post("/api/auth/register", json={
            "name": "First", "email": "first@x.com",
            "password": "Pass@123", "role": "TENANT", "phone": "9876543210",
        })
        assert first.status_code == 201

        second = client.post("/api/auth/register", json={
            "name": "Second", "email": "second@x.com",
            "password": "Pass@123", "role": "TENANT", "phone": "9876543210",
        })
        assert second.status_code == 409, "duplicate phone must not 500"
        assert "phone" in second.get_json()["error"].lower()
```
</details>


### TC-514 · The same bug in its nastier form: '' is not NULL, so the SECOND

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Blank 2",
      "email": "blank2@x.com",
      "password": "<hidden>",
      "role": "TENANT",
      "phone": ""
    }
    ```
- Header: _none (unauthenticated request)_
- Setup calls before this (1): `POST /api/auth/register` → 201

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "message": "User registered successfully",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:59:55.217412",
        "email": "blank2@x.com",
        "id": 8,
        "is_active": true,
        "name": "Blank 2",
        "phone": null,
        "role": "TENANT"
      }
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
    def test_two_blank_phone_registrations_both_succeed(self, client, seed):
        """The same bug in its nastier form: '' is not NULL, so the SECOND
        blank-phone signup collided with the first and 500'd. Blank must
        normalise to NULL, and SQLite allows many NULLs in a UNIQUE column."""
        for i in (1, 2):
            res = client.post("/api/auth/register", json={
                "name": f"Blank {i}", "email": f"blank{i}@x.com",
                "password": "Pass@123", "role": "TENANT", "phone": "",
            })
            assert res.status_code == 201, f"blank-phone signup #{i} failed: {res.get_json()}"
```
</details>


### TC-515 · DEFECT-02  Four endpoints were 100% dead

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "UTILITIES",
      "description": "Water bill",
      "amount": 500,
      "expense_date": "2026-08-01"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "amount": 500.0,
      "category": "UTILITIES",
      "created_at": "2026-08-02 11:59:55.495137",
      "description": "Water bill",
      "expense_date": "2026-08-01",
      "id": 1,
      "paid_by": 1,
      "paid_by_name": "Priya Admin",
      "receipt_url": null
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("label,url,payload", [
    ("expense", "/api/expenses/", {
        "category": "UTILITIES", "description": "Water bill",
        "amount": 500, "expense_date": "2026-08-01"}),
    ("maintenance task", "/api/maintenance/", {
        "title": "Tank cleaning", "category": "WATER_TANK",
        "scheduled_date": "2026-08-10"}),
    ("equipment", "/api/equipment/", {
        "name": "Lift A", "category": "LIFT",
        "last_serviced_date": "2026-06-01", "service_frequency_days": 90}),
    ("poll", "/api/polls/", {
        "title": "Paint the lobby?", "options": ["Yes", "No"],
        "end_date": "2026-12-31"}),
])
def test_date_accepting_endpoints_create_successfully(client, admin, label, url, payload):
    """DEFECT-02  Four endpoints were 100% dead.

    Client date strings were assigned straight into db.Date columns; there was
    not a single date parser in the backend. Every single call failed at flush.
        expected: 201 Created
        actual  : 500 (TypeError: SQLite Date type only accepts Python date objects)
    Fixed: utils.parse_date/parse_datetime applied at all 10 date sites.

    Evidence this was total, not intermittent: expenses, maintenance_tasks,
    equipment and votes were all empty in the shipped database, because no user
    had ever managed to create one.
    """
    res = client.post(url, json=payload, headers=admin)
    assert res.status_code == 201, f"creating a {label} failed: {res.get_json()}"
```
</details>


### TC-516 · DEFECT-02  Four endpoints were 100% dead

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "Tank cleaning",
      "category": "WATER_TANK",
      "scheduled_date": "2026-08-10"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "assigned_to": null,
      "assigned_to_name": null,
      "category": "WATER_TANK",
      "completed_at": null,
      "created_by": 1,
      "description": null,
      "id": 1,
      "scheduled_date": "2026-08-10",
      "status": "PENDING",
      "title": "Tank cleaning"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("label,url,payload", [
    ("expense", "/api/expenses/", {
        "category": "UTILITIES", "description": "Water bill",
        "amount": 500, "expense_date": "2026-08-01"}),
    ("maintenance task", "/api/maintenance/", {
        "title": "Tank cleaning", "category": "WATER_TANK",
        "scheduled_date": "2026-08-10"}),
    ("equipment", "/api/equipment/", {
        "name": "Lift A", "category": "LIFT",
        "last_serviced_date": "2026-06-01", "service_frequency_days": 90}),
    ("poll", "/api/polls/", {
        "title": "Paint the lobby?", "options": ["Yes", "No"],
        "end_date": "2026-12-31"}),
])
def test_date_accepting_endpoints_create_successfully(client, admin, label, url, payload):
    """DEFECT-02  Four endpoints were 100% dead.

    Client date strings were assigned straight into db.Date columns; there was
    not a single date parser in the backend. Every single call failed at flush.
        expected: 201 Created
        actual  : 500 (TypeError: SQLite Date type only accepts Python date objects)
    Fixed: utils.parse_date/parse_datetime applied at all 10 date sites.

    Evidence this was total, not intermittent: expenses, maintenance_tasks,
    equipment and votes were all empty in the shipped database, because no user
    had ever managed to create one.
    """
    res = client.post(url, json=payload, headers=admin)
    assert res.status_code == 201, f"creating a {label} failed: {res.get_json()}"
```
</details>


### TC-517 · DEFECT-02  Four endpoints were 100% dead

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "Lift A",
      "category": "LIFT",
      "last_serviced_date": "2026-06-01",
      "service_frequency_days": 90
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "category": "LIFT",
      "created_at": "2026-08-02 11:59:56.200107",
      "days_until_due": 28,
      "estimated_service_cost": null,
      "id": 1,
      "last_serviced_date": "2026-06-01",
      "name": "Lift A",
      "risk_level": "LOW",
      "service_frequency_days": 90
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("label,url,payload", [
    ("expense", "/api/expenses/", {
        "category": "UTILITIES", "description": "Water bill",
        "amount": 500, "expense_date": "2026-08-01"}),
    ("maintenance task", "/api/maintenance/", {
        "title": "Tank cleaning", "category": "WATER_TANK",
        "scheduled_date": "2026-08-10"}),
    ("equipment", "/api/equipment/", {
        "name": "Lift A", "category": "LIFT",
        "last_serviced_date": "2026-06-01", "service_frequency_days": 90}),
    ("poll", "/api/polls/", {
        "title": "Paint the lobby?", "options": ["Yes", "No"],
        "end_date": "2026-12-31"}),
])
def test_date_accepting_endpoints_create_successfully(client, admin, label, url, payload):
    """DEFECT-02  Four endpoints were 100% dead.

    Client date strings were assigned straight into db.Date columns; there was
    not a single date parser in the backend. Every single call failed at flush.
        expected: 201 Created
        actual  : 500 (TypeError: SQLite Date type only accepts Python date objects)
    Fixed: utils.parse_date/parse_datetime applied at all 10 date sites.

    Evidence this was total, not intermittent: expenses, maintenance_tasks,
    equipment and votes were all empty in the shipped database, because no user
    had ever managed to create one.
    """
    res = client.post(url, json=payload, headers=admin)
    assert res.status_code == 201, f"creating a {label} failed: {res.get_json()}"
```
</details>


### TC-518 · DEFECT-02  Four endpoints were 100% dead

**Page being tested:** `POST http://127.0.0.1:5000/api/polls/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/polls/`
- JSON body:
    ```json
    {
      "title": "Paint the lobby?",
      "options": [
        "Yes",
        "No"
      ],
      "end_date": "2026-12-31"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `201`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "created_at": "2026-08-02 11:59:56.589315",
      "created_by": 1,
      "description": null,
      "end_date": "2026-12-31",
      "has_voted": false,
      "id": 1,
      "my_option_id": null,
      "options": [
        {
          "id": 1,
          "percentage": 0,
          "text": "Yes",
          "votes": 0
        },
        {
          "id": 2,
          "percentage": 0,
          "text": "No",
          "votes": 0
        }
      ],
      "start_date": "2026-08-02",
      "status": "ACTIVE",
      "title": "Paint the lobby?",
      "total_votes": 0
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("label,url,payload", [
    ("expense", "/api/expenses/", {
        "category": "UTILITIES", "description": "Water bill",
        "amount": 500, "expense_date": "2026-08-01"}),
    ("maintenance task", "/api/maintenance/", {
        "title": "Tank cleaning", "category": "WATER_TANK",
        "scheduled_date": "2026-08-10"}),
    ("equipment", "/api/equipment/", {
        "name": "Lift A", "category": "LIFT",
        "last_serviced_date": "2026-06-01", "service_frequency_days": 90}),
    ("poll", "/api/polls/", {
        "title": "Paint the lobby?", "options": ["Yes", "No"],
        "end_date": "2026-12-31"}),
])
def test_date_accepting_endpoints_create_successfully(client, admin, label, url, payload):
    """DEFECT-02  Four endpoints were 100% dead.

    Client date strings were assigned straight into db.Date columns; there was
    not a single date parser in the backend. Every single call failed at flush.
        expected: 201 Created
        actual  : 500 (TypeError: SQLite Date type only accepts Python date objects)
    Fixed: utils.parse_date/parse_datetime applied at all 10 date sites.

    Evidence this was total, not intermittent: expenses, maintenance_tasks,
    equipment and votes were all empty in the shipped database, because no user
    had ever managed to create one.
    """
    res = client.post(url, json=payload, headers=admin)
    assert res.status_code == 201, f"creating a {label} failed: {res.get_json()}"
```
</details>


### TC-519 · The flip side: a genuinely bad date must be a 400, not a 500

**Page being tested:** `POST http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body:
    ```json
    {
      "category": "UTILITIES",
      "description": "x",
      "amount": 5,
      "expense_date": "yesterday"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` contains "date"
- JSON: response includes `date`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "expense_date must be a valid date (YYYY-MM-DD)"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_invalid_date_is_a_clean_400(client, admin):
    """The flip side: a genuinely bad date must be a 400, not a 500."""
    res = client.post("/api/expenses/", json={
        "category": "UTILITIES", "description": "x",
        "amount": 5, "expense_date": "yesterday",
    }, headers=admin)
    assert res.status_code == 400
    assert "date" in res.get_json()["error"].lower()
```
</details>


### TC-520 · Pending is admin only

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/pending`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/pending`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
    def test_pending_is_admin_only(self, client, resident, seed):
        self._raise_conflict(client, resident, seed)
        res = client.get("/api/conflicts/pending", headers=resident)
        assert res.status_code == 403, "tenants must not read the pending queue"
```
</details>


### TC-521 · Resident listing never exposes the reporter

**Page being tested:** `GET http://127.0.0.1:5000/api/conflicts/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/conflicts/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (2): `POST /api/auth/login` → 200, `POST /api/conflicts/` → 201

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "category": "NOISE",
        "created_at": "2026-08-02 11:59:57.718519",
        "description": "Loud music after midnight",
        "id": 1,
        "reported_apartment_id": 2,
        "reported_flat": "B-202",
        "reported_flat_response": null,
        "resolution_note": null,
        "resolved_at": null,
        "response_submitted_at": null,
        "status": "OPEN"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
    def test_resident_listing_never_exposes_the_reporter(self, client, resident, seed):
        self._raise_conflict(client, resident, seed)
        res = client.get("/api/conflicts/", headers=resident)
        assert res.status_code == 200
        for report in res.get_json():
            assert "reported_by" not in report
            assert "reported_by_name" not in report
```
</details>


### TC-522 · Assign without worker is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/assign`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/assign`
- JSON body:
    ```json
    {}
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "worker_id is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
    def test_assign_without_worker_is_rejected(self, client, admin, resident, seed):
        cid = self._complaint(client, resident, seed)
        res = client.put(f"/api/complaints/{cid}/assign", json={}, headers=admin)
        assert res.status_code == 400, "assigning to nobody must be rejected"
```
</details>


### TC-523 · Assign to non worker is rejected

**Page being tested:** `PUT http://127.0.0.1:5000/api/complaints/1/assign`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/complaints/1/assign`
- JSON body:
    ```json
    {
      "worker_id": 4
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201

**Expected Output:**

- HTTP Status Code: `400`
- JSON: `error` contains "worker"
- JSON: response includes `worker`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Selected user is not a maintenance worker"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
    def test_assign_to_non_worker_is_rejected(self, client, admin, resident, seed):
        cid = self._complaint(client, resident, seed)
        res = client.put(f"/api/complaints/{cid}/assign",
                         json={"worker_id": seed["resident_id"]}, headers=admin)
        assert res.status_code == 400
        assert "worker" in res.get_json()["error"].lower()
```
</details>


### TC-524 · Assigned worker sees the job

**Page being tested:** `GET http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/auth/login` → 200, `POST /api/auth/login` → 200, `POST /api/complaints/` → 201, `PUT /api/complaints/1/assign` → 200

**Expected Output:**

- HTTP Status Code: `200`
- JSON: `assigned_worker_name` is set

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "apartment_id": 1,
        "assigned_worker_id": 6,
        "assigned_worker_name": "Ramesh Worker",
        "category": "ELECTRICAL",
        "created_at": "2026-08-02 11:59:58.669712",
        "description": null,
        "flat_number": "A-101",
        "id": 1,
        "priority": "MEDIUM",
        "raised_by": 4,
        "raised_by_name": "Ravi Resident",
        "resolved_at": null,
        "status": "ASSIGNED",
        "title": "Corridor light out"
      }
    ]
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
    def test_assigned_worker_sees_the_job(self, client, admin, resident, worker, seed):
        cid = self._complaint(client, resident, seed)
        assigned = client.put(f"/api/complaints/{cid}/assign",
                              json={"worker_id": seed["worker_id"]}, headers=admin)
        assert assigned.status_code == 200
        assert assigned.get_json()["assigned_worker_name"] is not None

        queue = client.get("/api/complaints/", headers=worker)
        assert queue.status_code == 200
        assert any(c["id"] == cid for c in queue.get_json()), \
            "the assigned worker must see the complaint in their queue"
```
</details>


### TC-525 · DEFECT-05  PUT /api/invoices/<id>/pay was not idempotent

**Page being tested:** `PUT http://127.0.0.1:5000/api/invoices/1/pay`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/invoices/1/pay`
- JSON body:
    ```json
    {
      "payment_method": "UPI"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (3): `POST /api/auth/login` → 200, `POST /api/invoices/` → 201, `PUT /api/invoices/1/pay` → 200

**Expected Output:**

- HTTP Status Code: `201 or 200 or 409`

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "This invoice is already paid"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_paying_an_invoice_twice_is_rejected(client, admin, seed):
    """DEFECT-05  PUT /api/invoices/<id>/pay was not idempotent.

    Paying twice inserted a SECOND Payment row while the receipt kept showing
    the first, so the ledger and the receipt disagreed permanently.
        expected: 409 on the second call
        actual  : 200 and a duplicate Payment row
    Fixed: reject when the invoice is already PAID.
    """
    created = client.post("/api/invoices/", json={
        "apartment_id": seed["apartment_id"],
        "month": 7, "year": 2026, "amount": 1500,
    }, headers=admin)
    assert created.status_code == 201
    inv_id = created.get_json()["id"]

    first = client.put(f"/api/invoices/{inv_id}/pay",
                       json={"payment_method": "UPI"}, headers=admin)
    assert first.status_code == 200

    second = client.put(f"/api/invoices/{inv_id}/pay",
                        json={"payment_method": "UPI"}, headers=admin)
    assert second.status_code == 409, "an invoice must not be payable twice"
```
</details>


### TC-526 · DEFECT-06  POST /api/equipment with service_frequency_days = 0

**Page being tested:** `GET http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/equipment/` → 400, `POST /api/equipment/` → 400, `POST /api/equipment/` → 400

**Expected Output:**

- HTTP Status Code: `400 or 200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_zero_service_frequency_is_rejected(client, admin):
    """DEFECT-06  POST /api/equipment with service_frequency_days = 0.

    Validation was `if not data.get(f)`, and the STRING "0" is truthy in Python,
    so it passed. Every later GET then evaluated days_since / 0.
        expected: 400
        actual  : 201, after which GET /api/equipment, /forecast and the whole
                  Equipment page 500'd forever (ZeroDivisionError) with no way
                  to delete the offending row through the UI.
    Fixed: parse_int(min_value=1).
    """
    for value in (0, "0", -5):
        res = client.post("/api/equipment/", json={
            "name": "Bad Lift", "category": "LIFT",
            "last_serviced_date": "2026-06-01", "service_frequency_days": value,
        }, headers=admin)
        assert res.status_code == 400, f"service_frequency_days={value!r} must be rejected"

    # and the listing still works
    assert client.get("/api/equipment/", headers=admin).status_code == 200
```
</details>


### TC-527 · DEFECT-07  Any endpoint, with a body of null / [] / "str"

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    null
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be valid JSON"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("body", ["null", "[]", '"a string"'])
def test_malformed_json_bodies_return_400(client, body):
    """DEFECT-07  Any endpoint, with a body of null / [] / "str".

    request.get_json() returns None, a list or a str for these, and the code
    immediately called data.get(...).
        expected: 400
        actual  : 500 (AttributeError: 'NoneType' object has no attribute 'get')
    Fixed: utils.get_body() rejects anything that is not a JSON object.
    """
    res = client.post("/api/auth/login", data=body, content_type="application/json")
    assert res.status_code == 400
```
</details>


### TC-528 · DEFECT-07  Any endpoint, with a body of null / [] / "str"

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    []
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("body", ["null", "[]", '"a string"'])
def test_malformed_json_bodies_return_400(client, body):
    """DEFECT-07  Any endpoint, with a body of null / [] / "str".

    request.get_json() returns None, a list or a str for these, and the code
    immediately called data.get(...).
        expected: 400
        actual  : 500 (AttributeError: 'NoneType' object has no attribute 'get')
    Fixed: utils.get_body() rejects anything that is not a JSON object.
    """
    res = client.post("/api/auth/login", data=body, content_type="application/json")
    assert res.status_code == 400
```
</details>


### TC-529 · DEFECT-07  Any endpoint, with a body of null / [] / "str"

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/login`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/login`
- JSON body:
    ```json
    "a string"
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "Request body must be a JSON object"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("body", ["null", "[]", '"a string"'])
def test_malformed_json_bodies_return_400(client, body):
    """DEFECT-07  Any endpoint, with a body of null / [] / "str".

    request.get_json() returns None, a list or a str for these, and the code
    immediately called data.get(...).
        expected: 400
        actual  : 500 (AttributeError: 'NoneType' object has no attribute 'get')
    Fixed: utils.get_body() rejects anything that is not a JSON object.
    """
    res = client.post("/api/auth/login", data=body, content_type="application/json")
    assert res.status_code == 400
```
</details>


### TC-530 · DEFECT-07b  PUT /api/auth/change-password

**Page being tested:** `PUT http://127.0.0.1:5000/api/auth/change-password`

**Inputs:**

- Request Method: `PUT`
- URL: `http://127.0.0.1:5000/api/auth/change-password`
- JSON body:
    ```json
    {
      "old_password": "Pass@123"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "new_password is required"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_change_password_without_new_password_returns_400(client, admin):
    """DEFECT-07b  PUT /api/auth/change-password

    old_password was read with .get() but new_password with a raw subscript.
        expected: 400
        actual  : 500 (KeyError: 'new_password')
    """
    res = client.put("/api/auth/change-password",
                     json={"old_password": "Pass@123"}, headers=admin)
    assert res.status_code == 400
```
</details>


### TC-531 · DEFECT-08  There was not a single `except` block in api/ or auth/

**Page being tested:** `POST http://127.0.0.1:5000/api/complaints/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/complaints/`
- JSON body:
    ```json
    {
      "title": "x",
      "category": "NOPE",
      "apartment_id": 1
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (4): `POST /api/auth/login` → 200, `POST /api/auth/login` → 400, `GET /api/auth/me` → 401, `GET /api/emergency/9999999` → 405

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "category must be one of: PLUMBING, ELECTRICAL, CLEANING, SECURITY, OTHER"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_errors_are_always_json_never_html(client, admin, seed):
    """DEFECT-08  There was not a single `except` block in api/ or auth/.

    Every DB violation or unexpected error produced Flask's HTML error page,
    which the SPA rendered as `undefined` — the user saw nothing happen.
        expected: a JSON body {"error": "..."} on every failure
        actual  : text/html
    Fixed: global ApiError / IntegrityError / HTTPException / Exception
    handlers in app.py.
    """
    failures = [
        client.post("/api/auth/login", json={}),                       # 400
        client.get("/api/auth/me"),                                    # 401
        client.get("/api/emergency/9999999", headers=admin),           # 404/405
        client.post("/api/complaints/", json={"title": "x", "category": "NOPE",
                                              "apartment_id": seed["apartment_id"]},
                    headers=admin),                                    # 400 bad enum
    ]
    for res in failures:
        assert res.status_code >= 400
        assert res.content_type.startswith("application/json"), \
            f"error response was {res.content_type}, not JSON"
        body = res.get_json()
        # FINDING-10 (open): the envelope is not consistent. Our own handlers
        # return {"error": ...}, but flask-jwt-extended's built-in 401s return
        # {"msg": ...}. openapi.yaml documents ErrorResponse {error} for every
        # failure, so the 401 contract is currently inaccurate, and the
        # frontend's errText() falls back to a generic message on auth errors.
        # Asserting reality here; the aspiration is enforced by
        # tests/test_open_defects.py::test_unauthenticated_error_uses_the_documented_json_envelope,
        # which fails on purpos
    # …
```
</details>


### TC-532 · DEFECT-09  Every mutating endpoint was bare @jwt_required()

**Page being tested:** `GET http://127.0.0.1:5000/api/expenses/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/expenses/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (5): `POST /api/invoices/` → 403, `DELETE /api/members/apartments/2` → 403, `POST /api/notices/` → 403, `POST /api/emergency/` → 403

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `403`
- JSON:
    ```json
    {
      "error": "You are not allowed to perform this action"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_residents_cannot_perform_privileged_actions(client, resident, seed):
    """DEFECT-09  Every mutating endpoint was bare @jwt_required().

    Role was consulted in only 3 read filters, so any logged-in resident could
    mark invoices paid, delete a flat (cascading away its residents, invoices,
    payments and complaints), publish notices or close polls.
        expected: 403
        actual  : 200 — the action succeeded
    Fixed: @role_required / @admin_required / @finance_required.
    """
    forbidden = [
        client.post("/api/invoices/", json={"apartment_id": seed["apartment_id"],
                                            "month": 1, "year": 2026, "amount": 100},
                    headers=resident),
        client.delete(f"/api/members/apartments/{seed['other_apartment_id']}",
                      headers=resident),
        client.post("/api/notices/", json={"title": "hack", "content": "hack"},
                    headers=resident),
        client.post("/api/emergency/", json={"name": "x", "service_type": "OTHER",
                                             "phone": "999"}, headers=resident),
        client.get("/api/expenses/", headers=resident),
    ]
    for res in forbidden:
        assert res.status_code == 403, \
            f"a resident was allowed a privileged action (got {res.status_code})"
```
</details>


### TC-533 · DEFECT-09b  DELETE /api/members/apartments/<id>

**Page being tested:** `DELETE http://127.0.0.1:5000/api/members/apartments/1`

**Inputs:**

- Request Method: `DELETE`
- URL: `http://127.0.0.1:5000/api/members/apartments/1`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `409`
- JSON: `error` contains "resident"
- JSON: response includes `resident`

**Actual Output:**

- HTTP Status Code: `409`
- JSON:
    ```json
    {
      "error": "Cannot delete a flat that still has residents or invoices"
    }
    ```

**Result:** ✅ Success — actual output matched the expectation.

<details><summary>Test code</summary>

```python
def test_apartment_delete_no_longer_cascades_away_residents(client, admin, seed):
    """DEFECT-09b  DELETE /api/members/apartments/<id>

    The cascade silently destroyed every resident, invoice, payment and
    complaint for the flat.
        expected: 409 while the flat is still occupied
        actual  : 200 {"message": "Apartment deleted"} and the data was gone
    """
    res = client.delete(f"/api/members/apartments/{seed['apartment_id']}", headers=admin)
    assert res.status_code == 409
    assert "resident" in res.get_json()["error"].lower()
```
</details>


---

## Open defects — EXPECTED TO FAIL

`Backend/tests/test_open_defects.py` · all · **0/6 passed**


### TC-534 · OD-01 · Auth errors use a different JSON envelope from the rest of the API

**Page being tested:** `GET http://127.0.0.1:5000/api/auth/me`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/auth/me`
- JSON body: _none_
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `401`

**Actual Output:**

- HTTP Status Code: `401`
- JSON:
    ```json
    {
      "msg": "Missing Authorization Header"
    }
    ```

**Result:** ❌ Failure — AssertionError: openapi.yaml documents every error as {'error': ...}, but this returned {'msg': 'Missing Authorization Header'}

<details><summary>Test code</summary>

```python
def test_unauthenticated_error_uses_the_documented_json_envelope(client):
    """OD-01 · Auth errors use a different JSON envelope from the rest of the API.

    Endpoint  : any protected endpoint, called without a token
    Expected  : {"error": "..."} — the ErrorResponse schema that openapi.yaml
                declares for every single operation
    Actual    : {"msg": "Missing Authorization Header"}

    Cause     : flask-jwt-extended emits its own error envelope, and we never
                overrode it. Our own handlers in app.py all use "error".
    Impact    : the documented contract is wrong for all 67 protected
                operations, and the frontend's errText() reads `data.error`, so
                a session-expiry shows a generic fallback instead of the real
                message.
    Severity  : low — cosmetic to a human, but a contract violation for any
                client generated from the spec.
    Fix       : add @jwt.unauthorized_loader / @jwt.invalid_token_loader /
                @jwt.expired_token_loader in create_app() returning
                {"error": <msg>} with the same status code. ~6 lines.
    """
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    body = response.get_json()
    assert "error" in body, (
        f"openapi.yaml documents every error as {{'error': ...}}, "
        f"but this returned {body}"
    )
```
</details>


### TC-535 · OD-02 · Anyone on the internet can create an ADMIN account.  [SECURITY]

**Page being tested:** `POST http://127.0.0.1:5000/api/auth/register`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/auth/register`
- JSON body:
    ```json
    {
      "name": "Self Promoted",
      "email": "escalate@test.com",
      "password": "<hidden>",
      "role": "ADMIN"
    }
    ```
- Header: _none (unauthenticated request)_

**Expected Output:**

- HTTP Status Code: `400 or 403`

**Actual Output:**

- HTTP Status Code: `201`
- JSON:
    ```json
    {
      "message": "User registered successfully",
      "token": "<jwt>",
      "user": {
        "created_at": "2026-08-02 11:59:25.171972",
        "email": "escalate@test.com",
        "id": 1,
        "is_active": true,
        "name": "Self Promoted",
        "phone": null,
        "role": "ADMIN"
      }
    }
    ```

**Result:** ❌ Failure — AssertionError: public registration granted an ADMIN account (status 201, role ADMIN)

<details><summary>Test code</summary>

```python
def test_public_registration_cannot_grant_itself_admin(client):
    """OD-02 · Anyone on the internet can create an ADMIN account.  [SECURITY]

    Endpoint  : POST /api/auth/register  (public, unauthenticated)
    Input     : {"name": ..., "email": ..., "password": ..., "role": "ADMIN"}
    Expected  : 400 or 403 — public signup must only create residents
    Actual    : 201 Created, with a working ADMIN token

    Verified  : the returned token successfully calls GET /api/members/, an
                admin-only endpoint, so this is real privilege escalation and
                not just a mislabelled record.
    Cause     : register() validates that `role` is a *valid enum value* but
                never that the caller is *allowed* to request it. Every one of
                the 8 roles, including SYSTEM_ADMIN, is accepted.
    Impact    : defeats every role check in the application. An attacker can
                read the full member directory, mark invoices paid, delete
                flats and publish emergency notices.
    Severity  : HIGH.
    Known     : deliberately left open so the team can self-serve test accounts
                (KNOWN_ISSUES.md #1) — but it must be closed before the app is
                used with real data.
    Fix       : restrict the public endpoint to TENANT/OWNER and create staff
                through the existing admin-only POST /api/members/.
    """
    response = client.post("/api/auth/register", json={
        "name": "Self Promoted", "email": "escalate@test.com",
        "password": "Pass@123", "role": "ADMIN",
    })
    assert response.status_code in (400, 403), (
        "public registration granted an ADMIN account "
        f"(status {response.status_code}, role "
        f"{(response.get_json() or {}).get('user', {})
    # …
```
</details>


### TC-536 · OD-02b · Proves the escalation above is exploitable, not cosmetic

**Page being tested:** `GET http://127.0.0.1:5000/api/members/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/members/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/register` → 201

**Expected Output:**

- HTTP Status Code: `403`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    []
    ```

**Result:** ❌ Failure — AssertionError: an account created through public signup was able to read the admin-only member directory (status 200)

<details><summary>Test code</summary>

```python
def test_admin_token_from_public_signup_cannot_reach_admin_endpoints(client):
    """OD-02b · Proves the escalation above is exploitable, not cosmetic.

    Expected : the self-registered account cannot list the member directory
    Actual   : 200 OK with every resident's name, email, phone and role
    """
    signup = client.post("/api/auth/register", json={
        "name": "Self Promoted 2", "email": "escalate2@test.com",
        "password": "Pass@123", "role": "ADMIN",
    })
    token = (signup.get_json() or {}).get("token")
    listing = client.get("/api/members/", headers={"Authorization": f"Bearer {token}"})
    assert listing.status_code == 403, (
        "an account created through public signup was able to read the "
        f"admin-only member directory (status {listing.status_code})"
    )
```
</details>


### TC-537 · OD-03 · Invoices never become OVERDUE

**Page being tested:** `GET http://127.0.0.1:5000/api/invoices/`

**Inputs:**

- Request Method: `GET`
- URL: `http://127.0.0.1:5000/api/invoices/`
- JSON body: _none_
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `200`

**Actual Output:**

- HTTP Status Code: `200`
- JSON:
    ```json
    [
      {
        "amount": 1500.0,
        "apartment_id": 1,
        "created_at": "2026-08-02 11:59:26.064039",
        "due_date": "2026-06-03",
        "flat_number": "A-101",
        "id": 1,
        "month": 1,
        "status": "UNPAID",
        "year": 2026
      }
    ]
    ```

**Result:** ❌ Failure — AssertionError: an invoice due 2026-06-03 (60 days ago) is still reported as UNPAID

<details><summary>Test code</summary>

```python
def test_unpaid_invoice_past_its_due_date_becomes_overdue(client, admin, seed, app):
    """OD-03 · Invoices never become OVERDUE.

    Endpoint  : GET /api/invoices/
    Setup     : an UNPAID invoice whose due_date was 60 days ago
    Expected  : status "OVERDUE"
    Actual    : status "UNPAID" — forever

    Cause     : the OVERDUE value exists in invoice_status_enum and due_date is
                stored, but nothing in the codebase ever compares the two. No
                scheduled job, and no check on read.
    Impact    : the treasurer cannot distinguish "due next week" from "unpaid
                since March". The Society Health Score's payment component is
                also blind to lateness, so a society that never pays on time
                still scores well as long as the invoices are eventually paid.
    Severity  : medium — a real functional gap in a headline feature.
    Known     : KNOWN_ISSUES.md #9.
    Fix       : either flip past-due UNPAID invoices on read, or add a small
                scheduled task. Reading is simpler and has no infrastructure
                cost.
    """
    with app.app_context():
        overdue = Invoice(
            apartment_id=seed["apartment_id"], generated_by=seed["admin_id"],
            month=1, year=date.today().year, amount=1500, status="UNPAID",
            due_date=date.today() - timedelta(days=60),
        )
        db.session.add(overdue)
        db.session.commit()
        invoice_id = overdue.id

    listing = client.get("/api/invoices/", headers=admin)
    assert listing.status_code == 200
    invoice = next(i for i in listing.get_json() if i["id"] == invoice_id)
    assert invoice["status"] == "OVERDUE", (
        f"an invoice due {invoice['due_date']} (60 days ago) is still reported "
        f"as {
    # …
```
</details>


### TC-538 · OD-04 · Validation errors name the internal enum, not the client's field

**Page being tested:** `POST http://127.0.0.1:5000/api/maintenance/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/maintenance/`
- JSON body:
    ```json
    {
      "title": "x",
      "category": "BOGUS",
      "scheduled_date": "2026-09-01"
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "task_category must be one of: GENERATOR, WATER_TANK, CLEANING, ELECTRICAL, PLUMBING, OTHER"
    }
    ```

**Result:** ❌ Failure — AssertionError: error names the internal enum rather than the client's field: 'task_category must be one of: GENERATOR, WATER_TANK, CLEANING, ELECTRICAL, PLUMBING, OTHER'

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("endpoint,payload,field", [
    ("/api/maintenance/",
     {"title": "x", "category": "BOGUS", "scheduled_date": "2026-09-01"}, "category"),
    ("/api/equipment/",
     {"name": "x", "category": "BOGUS", "last_serviced_date": "2026-06-01",
      "service_frequency_days": 30}, "category"),
])
def test_validation_error_names_the_field_the_client_sent(client, admin, endpoint, payload, field):
    """OD-04 · Validation errors name the internal enum, not the client's field.

    Endpoint  : POST /api/maintenance/ and POST /api/equipment/
    Input     : {"category": "BOGUS", ...}
    Expected  : "category must be one of: ..." — naming the field the client sent
    Actual    : "task_category must be one of: ..."  (maintenance)
                "equipment_category must be one of: ..."  (equipment)

    Cause     : parse_enum() falls back to the enum's internal name when the
                caller omits field=. Notices and conflicts pass field="category"
                and so report it correctly; maintenance and equipment do not.
    Impact    : a frontend that maps error messages back to form fields cannot
                match these, so the message cannot be shown against the offending
                input. It also leaks internal naming into the public contract.
    Severity  : low.
    Fix       : pass field="category" at the two call sites — a one-word change
                each.
    """
    response = client.post(endpoint, json=payload, headers=admin)
    assert response.status_code == 400
    message = response.get_json()["error"]
    assert message.startswith(f"{field} must be one of"), (
        f"error names the internal enum rather than the client's field: {message!r}"
    )
```
</details>


### TC-539 · OD-04 · Validation errors name the internal enum, not the client's field

**Page being tested:** `POST http://127.0.0.1:5000/api/equipment/`

**Inputs:**

- Request Method: `POST`
- URL: `http://127.0.0.1:5000/api/equipment/`
- JSON body:
    ```json
    {
      "name": "x",
      "category": "BOGUS",
      "last_serviced_date": "2026-06-01",
      "service_frequency_days": 30
    }
    ```
- Header: `Authorization: Bearer <jwt>`
- Setup calls before this (1): `POST /api/auth/login` → 200

**Expected Output:**

- HTTP Status Code: `400`

**Actual Output:**

- HTTP Status Code: `400`
- JSON:
    ```json
    {
      "error": "equipment_category must be one of: GENERATOR, WATER_TANK, LIFT, PEST_CONTROL, FIRE_SAFETY, OTHER"
    }
    ```

**Result:** ❌ Failure — AssertionError: error names the internal enum rather than the client's field: 'equipment_category must be one of: GENERATOR, WATER_TANK, LIFT, PEST_CONTROL, FIRE_SAFETY, OTHER'

<details><summary>Test code</summary>

```python
@pytest.mark.parametrize("endpoint,payload,field", [
    ("/api/maintenance/",
     {"title": "x", "category": "BOGUS", "scheduled_date": "2026-09-01"}, "category"),
    ("/api/equipment/",
     {"name": "x", "category": "BOGUS", "last_serviced_date": "2026-06-01",
      "service_frequency_days": 30}, "category"),
])
def test_validation_error_names_the_field_the_client_sent(client, admin, endpoint, payload, field):
    """OD-04 · Validation errors name the internal enum, not the client's field.

    Endpoint  : POST /api/maintenance/ and POST /api/equipment/
    Input     : {"category": "BOGUS", ...}
    Expected  : "category must be one of: ..." — naming the field the client sent
    Actual    : "task_category must be one of: ..."  (maintenance)
                "equipment_category must be one of: ..."  (equipment)

    Cause     : parse_enum() falls back to the enum's internal name when the
                caller omits field=. Notices and conflicts pass field="category"
                and so report it correctly; maintenance and equipment do not.
    Impact    : a frontend that maps error messages back to form fields cannot
                match these, so the message cannot be shown against the offending
                input. It also leaks internal naming into the public contract.
    Severity  : low.
    Fix       : pass field="category" at the two call sites — a one-word change
                each.
    """
    response = client.post(endpoint, json=payload, headers=admin)
    assert response.status_code == 400
    message = response.get_json()["error"]
    assert message.startswith(f"{field} must be one of"), (
        f"error names the internal enum rather than the client's field: {message!r}"
    )
```
</details>


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


## 4. Test design notes

- **Isolation** — each test builds a fresh app against its own temporary SQLite file (`tests/conftest.py`), so tests never share state and never touch `instance/societyease.db`.
- **Seed data** — two flats and one user per role (ADMIN, TREASURER, COMMITTEE_MEMBER, TENANT, OWNER, WORKER); the tenant is linked to flat A-101 so ownership rules can be tested.
- **Recording** — the test client is subclassed (`RecordingClient`) to log every request and response, which is what fills the Inputs and Actual Output sections above. JWTs and passwords are redacted.
- **Expected vs Actual** — Expected is parsed from the `assert` statements in the test source; Actual is the recorded HTTP response. They are captured independently.
- A failing test is treated as a defect to report, never as a test to weaken.
