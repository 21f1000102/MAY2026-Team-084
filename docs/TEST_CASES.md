# API Test Cases

Automated test cases for the SocietyEase REST API, with the **input**, the **expected output**, and the **actual output** observed in a real run.

> This document is **generated** by `Backend/tests/report.py` from a live `pytest` run — the Actual column is never written by hand. Re-run it to reproduce.

## 1. How to run

```bash
cd Backend
pip install -r requirements.txt
pytest -v                 # run the suite
python tests/report.py    # regenerate this document
```

### Run summary

| | |
|---|---|
| Generated | 2026-08-02 09:20 UTC |
| Total test cases | **534** |
| Passed | **533** |
| Failed | **0** |
| Skipped | 1 |
| Duration | 154.9s |
| pytest exit code | 0 |


The single skipped case is **FINDING-10**, a known open issue documented in section 3 — it is skipped deliberately rather than silently deleted.


### Coverage

| Module | Feature | User stories | Cases |
|---|---|---|---:|
| `test_auth.py` | Authentication | US-08 | 52 |
| `test_members.py` | Members & Apartments | US-09, US-04 | 96 |
| `test_complaints.py` | Complaints | US-02, US-03, US-04 | 44 |
| `test_invoices.py` | Invoices & Payments | US-01, US-05, US-06 | 53 |
| `test_expenses.py` | Expenses | US-14 | 44 |
| `test_notices.py` | Notices | US-10 | 18 |
| `test_polls.py` | Polls & Voting | US-13 | 29 |
| `test_maintenance.py` | Maintenance Tasks | US-11 | 24 |
| `test_equipment.py` | Equipment / Maintenance Predictor | US-15 | 28 |
| `test_health.py` | Society Health Score | US-17 | 20 |
| `test_conflicts.py` | Neighbour Conflict Resolver | US-16 | 27 |
| `test_parking.py` | Visitor Parking | US-12 | 27 |
| `test_emergency.py` | Emergency Contacts | US-07 | 50 |
| `test_regressions.py` | Regression suite — defects found by testing | all | 22 |
| | | **Total** | **534** |

Every module covers the same four axes: **happy path**, **validation** (missing fields, bad enums, bad dates, malformed bodies), **authorization** (401 unauthenticated, 403 wrong role), and **business rules** (duplicates, idempotency, state transitions).


## 2. Test cases

`Expected` is the behaviour asserted by the test; `Actual` is what the run produced. A case only passes when they match.


### Authentication  
`Backend/tests/test_auth.py` · US-08 · **52/52 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | register | returns 201 with token and user | as expected | ✅ PASS |
| 2 | register lowercases and strips email | behaves as specified | as expected | ✅ PASS |
| 3 | register issues a usable token | behaves as specified | as expected | ✅ PASS |
| 4 | register missing required field | returns 400 | as expected | ✅ PASS |
| 5 | register missing required field | returns 400 | as expected | ✅ PASS |
| 6 | register missing required field | returns 400 | as expected | ✅ PASS |
| 7 | register missing required field | returns 400 | as expected | ✅ PASS |
| 8 | register blank required field | returns 400 | as expected | ✅ PASS |
| 9 | register blank required field | returns 400 | as expected | ✅ PASS |
| 10 | register unknown role | returns 400 | as expected | ✅ PASS |
| 11 | register malformed body | returns 400 | as expected | ✅ PASS |
| 12 | register malformed body | returns 400 | as expected | ✅ PASS |
| 13 | register malformed body | returns 400 | as expected | ✅ PASS |
| 14 | register duplicate email | returns 409 | as expected | ✅ PASS |
| 15 | register duplicate email is case insensitive | behaves as specified | as expected | ✅ PASS |
| 16 | register duplicate phone | returns 409 | as expected | ✅ PASS |
| 17 | register two blank phones both succeed | behaves as specified | as expected | ✅ PASS |
| 18 | register blank phone is stored as null | behaves as specified | as expected | ✅ PASS |
| 19 | login | succeeds  for every seeded role | as expected | ✅ PASS |
| 20 | login | succeeds  for every seeded role | as expected | ✅ PASS |
| 21 | login | succeeds  for every seeded role | as expected | ✅ PASS |
| 22 | login | succeeds  for every seeded role | as expected | ✅ PASS |
| 23 | login | succeeds  for every seeded role | as expected | ✅ PASS |
| 24 | login | succeeds  for every seeded role | as expected | ✅ PASS |
| 25 | login wrong password | returns 401 | as expected | ✅ PASS |
| 26 | login unknown email | returns 401 | as expected | ✅ PASS |
| 27 | login missing required field | returns 400 | as expected | ✅ PASS |
| 28 | login missing required field | returns 400 | as expected | ✅ PASS |
| 29 | login malformed body | returns 400 | as expected | ✅ PASS |
| 30 | login malformed body | returns 400 | as expected | ✅ PASS |
| 31 | login malformed body | returns 400 | as expected | ✅ PASS |
| 32 | login deactivated account | returns 403 | as expected | ✅ PASS |
| 33 | me | returns the authenticated user | as expected | ✅ PASS |
| 34 | me is open to every role | behaves as specified | as expected | ✅ PASS |
| 35 | me is open to every role | behaves as specified | as expected | ✅ PASS |
| 36 | me is open to every role | behaves as specified | as expected | ✅ PASS |
| 37 | me is open to every role | behaves as specified | as expected | ✅ PASS |
| 38 | me without token | returns 401 | as expected | ✅ PASS |
| 39 | me with garbage token | returns 422 | as expected | ✅ PASS |
| 40 | change password | returns 200 | as expected | ✅ PASS |
| 41 | change password old password stops working | behaves as specified | as expected | ✅ PASS |
| 42 | change password new password works | behaves as specified | as expected | ✅ PASS |
| 43 | change password missing new password | returns 400 | as expected | ✅ PASS |
| 44 | change password missing old password | returns 400 | as expected | ✅ PASS |
| 45 | change password wrong old password | returns 400 | as expected | ✅ PASS |
| 46 | change password shorter than six chars | returns 400 | as expected | ✅ PASS |
| 47 | change password shorter than six chars | returns 400 | as expected | ✅ PASS |
| 48 | change password shorter than six chars | returns 400 | as expected | ✅ PASS |
| 49 | change password malformed body | returns 400 | as expected | ✅ PASS |
| 50 | change password malformed body | returns 400 | as expected | ✅ PASS |
| 51 | change password malformed body | returns 400 | as expected | ✅ PASS |
| 52 | change password without token | returns 401 | as expected | ✅ PASS |

### Members & Apartments  
`Backend/tests/test_members.py` · US-09, US-04 · **96/96 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | list apartments | returns seeded flats | as expected | ✅ PASS |
| 2 | list apartments exposes block and floor | behaves as specified | as expected | ✅ PASS |
| 3 | list apartments is open to every role | behaves as specified | as expected | ✅ PASS |
| 4 | list apartments is open to every role | behaves as specified | as expected | ✅ PASS |
| 5 | list apartments is open to every role | behaves as specified | as expected | ✅ PASS |
| 6 | list apartments is open to every role | behaves as specified | as expected | ✅ PASS |
| 7 | list apartments without token | returns 401 | as expected | ✅ PASS |
| 8 | create apartment | returns 201 | as expected | ✅ PASS |
| 9 | create apartment accepts a numeric string floor | behaves as specified | as expected | ✅ PASS |
| 10 | create apartment missing flat number | returns 400 | as expected | ✅ PASS |
| 11 | create apartment non numeric floor | returns 400 | as expected | ✅ PASS |
| 12 | create apartment malformed body | returns 400 | as expected | ✅ PASS |
| 13 | create apartment malformed body | returns 400 | as expected | ✅ PASS |
| 14 | create apartment malformed body | returns 400 | as expected | ✅ PASS |
| 15 | create apartment duplicate flat number | returns 409 | as expected | ✅ PASS |
| 16 | create apartment as resident | returns 403 | as expected | ✅ PASS |
| 17 | create apartment as worker | returns 403 | as expected | ✅ PASS |
| 18 | create apartment as treasurer | returns 201 | as expected | ✅ PASS |
| 19 | create apartment without token | returns 401 | as expected | ✅ PASS |
| 20 | update apartment renames the flat | behaves as specified | as expected | ✅ PASS |
| 21 | update apartment updates block and floor | behaves as specified | as expected | ✅ PASS |
| 22 | update apartment blank flat number | returns 400 | as expected | ✅ PASS |
| 23 | update apartment bad floor | returns 400 | as expected | ✅ PASS |
| 24 | update apartment duplicate flat number | returns 409 | as expected | ✅ PASS |
| 25 | update apartment to its own flat number | returns 200 | as expected | ✅ PASS |
| 26 | update unknown apartment | returns 404 | as expected | ✅ PASS |
| 27 | update apartment as resident | returns 403 | as expected | ✅ PASS |
| 28 | update apartment without token | returns 401 | as expected | ✅ PASS |
| 29 | delete empty apartment | returns 200 | as expected | ✅ PASS |
| 30 | delete apartment removes it from the list | behaves as specified | as expected | ✅ PASS |
| 31 | delete apartment with residents | returns 409 | as expected | ✅ PASS |
| 32 | delete apartment with invoices | returns 409 | as expected | ✅ PASS |
| 33 | delete unknown apartment | returns 404 | as expected | ✅ PASS |
| 34 | delete apartment as resident | returns 403 | as expected | ✅ PASS |
| 35 | delete apartment without token | returns 401 | as expected | ✅ PASS |
| 36 | list members | returns the seeded resident | as expected | ✅ PASS |
| 37 | list members includes flat details | behaves as specified | as expected | ✅ PASS |
| 38 | list members as resident | returns 403 | as expected | ✅ PASS |
| 39 | list members as worker | returns 403 | as expected | ✅ PASS |
| 40 | list members as treasurer | returns 200 | as expected | ✅ PASS |
| 41 | list members without token | returns 401 | as expected | ✅ PASS |
| 42 | create member | returns 201 | as expected | ✅ PASS |
| 43 | create member can log in afterwards | behaves as specified | as expected | ✅ PASS |
| 44 | create member appears in the listing | behaves as specified | as expected | ✅ PASS |
| 45 | create member missing required field | returns 400 | as expected | ✅ PASS |
| 46 | create member missing required field | returns 400 | as expected | ✅ PASS |
| 47 | create member missing required field | returns 400 | as expected | ✅ PASS |
| 48 | create member missing required field | returns 400 | as expected | ✅ PASS |
| 49 | create member missing required field | returns 400 | as expected | ✅ PASS |
| 50 | create member unknown role | returns 400 | as expected | ✅ PASS |
| 51 | create member bad move in date | returns 400 | as expected | ✅ PASS |
| 52 | create member non numeric apartment id | returns 400 | as expected | ✅ PASS |
| 53 | create member zero apartment id | returns 400 | as expected | ✅ PASS |
| 54 | create member unknown apartment | returns 404 | as expected | ✅ PASS |
| 55 | create member malformed body | returns 400 | as expected | ✅ PASS |
| 56 | create member malformed body | returns 400 | as expected | ✅ PASS |
| 57 | create member malformed body | returns 400 | as expected | ✅ PASS |
| 58 | create member duplicate email | returns 409 | as expected | ✅ PASS |
| 59 | create member duplicate phone | returns 409 | as expected | ✅ PASS |
| 60 | create two members with blank phone both succeed | behaves as specified | as expected | ✅ PASS |
| 61 | create member as resident | returns 403 | as expected | ✅ PASS |
| 62 | create member without token | returns 401 | as expected | ✅ PASS |
| 63 | list workers | returns only worker role users | as expected | ✅ PASS |
| 64 | list workers id is the users id | behaves as specified | as expected | ✅ PASS |
| 65 | list workers | returns id name email only | as expected | ✅ PASS |
| 66 | list workers includes newly added workers | behaves as specified | as expected | ✅ PASS |
| 67 | list workers as resident | returns 403 | as expected | ✅ PASS |
| 68 | list workers without token | returns 401 | as expected | ✅ PASS |
| 69 | get member | returns 200 | as expected | ✅ PASS |
| 70 | get member is open to every role | behaves as specified | as expected | ✅ PASS |
| 71 | get member is open to every role | behaves as specified | as expected | ✅ PASS |
| 72 | get member is open to every role | behaves as specified | as expected | ✅ PASS |
| 73 | get member is open to every role | behaves as specified | as expected | ✅ PASS |
| 74 | get unknown member | returns 404 | as expected | ✅ PASS |
| 75 | get member without token | returns 401 | as expected | ✅ PASS |
| 76 | update member changes name and role | behaves as specified | as expected | ✅ PASS |
| 77 | update member changes resident fields | behaves as specified | as expected | ✅ PASS |
| 78 | update member blank phone clears it | behaves as specified | as expected | ✅ PASS |
| 79 | update member unknown role | returns 400 | as expected | ✅ PASS |
| 80 | update member bad move in date | returns 400 | as expected | ✅ PASS |
| 81 | update member bad move out date | returns 400 | as expected | ✅ PASS |
| 82 | update member duplicate phone | returns 409 | as expected | ✅ PASS |
| 83 | update member keeping its own phone | returns 200 | as expected | ✅ PASS |
| 84 | update member malformed body | returns 400 | as expected | ✅ PASS |
| 85 | update member malformed body | returns 400 | as expected | ✅ PASS |
| 86 | update member malformed body | returns 400 | as expected | ✅ PASS |
| 87 | update unknown member | returns 404 | as expected | ✅ PASS |
| 88 | update member as resident | returns 403 | as expected | ✅ PASS |
| 89 | update member without token | returns 401 | as expected | ✅ PASS |
| 90 | deactivate member | returns 200 | as expected | ✅ PASS |
| 91 | deactivate member is a soft delete | behaves as specified | as expected | ✅ PASS |
| 92 | deactivate worker removes them from the worker list | behaves as specified | as expected | ✅ PASS |
| 93 | deactivated member token | returns 403 | as expected | ✅ PASS |
| 94 | deactivate unknown member | returns 404 | as expected | ✅ PASS |
| 95 | deactivate member as resident | returns 403 | as expected | ✅ PASS |
| 96 | deactivate member without token | returns 401 | as expected | ✅ PASS |

### Complaints  
`Backend/tests/test_complaints.py` · US-02, US-03, US-04 · **44/44 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | resident can raise complaint | behaves as specified | as expected | ✅ PASS |
| 2 | priority defaults to medium | behaves as specified | as expected | ✅ PASS |
| 3 | resident lists only own complaints | behaves as specified | as expected | ✅ PASS |
| 4 | admin lists all complaints | behaves as specified | as expected | ✅ PASS |
| 5 | get complaint detail includes updates | behaves as specified | as expected | ✅ PASS |
| 6 | admin can delete complaint | behaves as specified | as expected | ✅ PASS |
| 7 | committee member may delete complaint | behaves as specified | as expected | ✅ PASS |
| 8 | raise complaint missing required field | returns 400 | as expected | ✅ PASS |
| 9 | raise complaint missing required field | returns 400 | as expected | ✅ PASS |
| 10 | raise complaint missing required field | returns 400 | as expected | ✅ PASS |
| 11 | raise complaint bad category | returns 400 | as expected | ✅ PASS |
| 12 | raise complaint bad priority | returns 400 | as expected | ✅ PASS |
| 13 | raise complaint non numeric apartment id | returns 400 | as expected | ✅ PASS |
| 14 | raise complaint unknown apartment | returns 404 | as expected | ✅ PASS |
| 15 | raise complaint malformed body | returns 400 | as expected | ✅ PASS |
| 16 | raise complaint malformed body | returns 400 | as expected | ✅ PASS |
| 17 | raise complaint malformed body | returns 400 | as expected | ✅ PASS |
| 18 | complaint endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 19 | complaint endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 20 | complaint endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 21 | complaint endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 22 | complaint endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 23 | complaint endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 24 | resident cannot delete complaint | behaves as specified | as expected | ✅ PASS |
| 25 | resident cannot assign a worker | behaves as specified | as expected | ✅ PASS |
| 26 | resident cannot read another flats complaint | behaves as specified | as expected | ✅ PASS |
| 27 | resident cannot update another flats complaint | behaves as specified | as expected | ✅ PASS |
| 28 | assign worker | returns 200 and populates worker name | as expected | ✅ PASS |
| 29 | assign without worker id | returns 400 | as expected | ✅ PASS |
| 30 | assign without worker id | returns 400 | as expected | ✅ PASS |
| 31 | assign without worker id | returns 400 | as expected | ✅ PASS |
| 32 | assign without worker id | returns 400 | as expected | ✅ PASS |
| 33 | assign to non worker user | returns 400 | as expected | ✅ PASS |
| 34 | assign to unknown user | returns 404 | as expected | ✅ PASS |
| 35 | worker sees complaint assigned to them | behaves as specified | as expected | ✅ PASS |
| 36 | worker does not see unassigned complaints | behaves as specified | as expected | ✅ PASS |
| 37 | assigned worker can read and update the complaint | behaves as specified | as expected | ✅ PASS |
| 38 | status flow open to completed sets resolved at | behaves as specified | as expected | ✅ PASS |
| 39 | reopening a closed complaint clears resolved at | behaves as specified | as expected | ✅ PASS |
| 40 | invalid status transition | returns 400 | as expected | ✅ PASS |
| 41 | status update requires status field | behaves as specified | as expected | ✅ PASS |
| 42 | status update bad enum | returns 400 | as expected | ✅ PASS |
| 43 | setting the same status is allowed | behaves as specified | as expected | ✅ PASS |
| 44 | unknown complaint id | returns 404 | as expected | ✅ PASS |

### Invoices & Payments  
`Backend/tests/test_invoices.py` · US-01, US-05, US-06 · **53/53 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | admin creates invoice | behaves as specified | as expected | ✅ PASS |
| 2 | treasurer can create invoice | behaves as specified | as expected | ✅ PASS |
| 3 | admin lists all invoices | behaves as specified | as expected | ✅ PASS |
| 4 | pay invoice | returns receipt | as expected | ✅ PASS |
| 5 | payment method defaults to cash | behaves as specified | as expected | ✅ PASS |
| 6 | get receipt for paid invoice | behaves as specified | as expected | ✅ PASS |
| 7 | resident can read own receipt | behaves as specified | as expected | ✅ PASS |
| 8 | pending lists only unpaid | behaves as specified | as expected | ✅ PASS |
| 9 | bulk generate creates invoice for every flat | behaves as specified | as expected | ✅ PASS |
| 10 | bulk generate skips flats that already have that month | behaves as specified | as expected | ✅ PASS |
| 11 | create invoice missing required field | returns 400 | as expected | ✅ PASS |
| 12 | create invoice missing required field | returns 400 | as expected | ✅ PASS |
| 13 | create invoice missing required field | returns 400 | as expected | ✅ PASS |
| 14 | create invoice missing required field | returns 400 | as expected | ✅ PASS |
| 15 | create invoice month out of range | returns 400 | as expected | ✅ PASS |
| 16 | create invoice month out of range | returns 400 | as expected | ✅ PASS |
| 17 | create invoice month out of range | returns 400 | as expected | ✅ PASS |
| 18 | create invoice month out of range | returns 400 | as expected | ✅ PASS |
| 19 | bulk generate month out of range | returns 400 | as expected | ✅ PASS |
| 20 | create invoice year out of range | returns 400 | as expected | ✅ PASS |
| 21 | create invoice non numeric amount | returns 400 | as expected | ✅ PASS |
| 22 | create invoice negative amount | returns 400 | as expected | ✅ PASS |
| 23 | create invoice bad due date | returns 400 | as expected | ✅ PASS |
| 24 | blank due date is stored as null not rejected | behaves as specified | as expected | ✅ PASS |
| 25 | blank due date is stored as null not rejected | behaves as specified | as expected | ✅ PASS |
| 26 | blank due date is stored as null not rejected | behaves as specified | as expected | ✅ PASS |
| 27 | create invoice unknown apartment | returns 404 | as expected | ✅ PASS |
| 28 | invoice malformed body | returns 400 | as expected | ✅ PASS |
| 29 | invoice malformed body | returns 400 | as expected | ✅ PASS |
| 30 | invoice malformed body | returns 400 | as expected | ✅ PASS |
| 31 | invoice malformed body | returns 400 | as expected | ✅ PASS |
| 32 | invoice endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 33 | invoice endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 34 | invoice endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 35 | invoice endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 36 | invoice endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 37 | invoice endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 38 | resident cannot create invoice | behaves as specified | as expected | ✅ PASS |
| 39 | resident cannot mark invoice paid | behaves as specified | as expected | ✅ PASS |
| 40 | resident cannot bulk generate | behaves as specified | as expected | ✅ PASS |
| 41 | committee member is not finance | behaves as specified | as expected | ✅ PASS |
| 42 | committee member is not finance | behaves as specified | as expected | ✅ PASS |
| 43 | resident cannot read another flats receipt | behaves as specified | as expected | ✅ PASS |
| 44 | duplicate invoice for same flat month year | returns 409 | as expected | ✅ PASS |
| 45 | same month different flat is allowed | behaves as specified | as expected | ✅ PASS |
| 46 | pay invoice twice | returns 409 | as expected | ✅ PASS |
| 47 | receipt for unpaid invoice | returns 400 | as expected | ✅ PASS |
| 48 | pay invoice for flat without resident | returns 404 | as expected | ✅ PASS |
| 49 | unknown invoice | returns 404 | as expected | ✅ PASS |
| 50 | resident sees only own flat invoices | behaves as specified | as expected | ✅ PASS |
| 51 | resident pending is scoped to own flat | behaves as specified | as expected | ✅ PASS |
| 52 | user without a flat sees an empty list | behaves as specified | as expected | ✅ PASS |
| 53 | user without a flat sees an empty list | behaves as specified | as expected | ✅ PASS |

### Expenses  
`Backend/tests/test_expenses.py` · US-14 · **44/44 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | admin logs expense | behaves as specified | as expected | ✅ PASS |
| 2 | treasurer can log expense | behaves as specified | as expected | ✅ PASS |
| 3 | paid by defaults to the logged in user | behaves as specified | as expected | ✅ PASS |
| 4 | admin may attribute expense to another user | behaves as specified | as expected | ✅ PASS |
| 5 | paid by unknown user | returns 404 | as expected | ✅ PASS |
| 6 | list expenses | behaves as specified | as expected | ✅ PASS |
| 7 | update expense | behaves as specified | as expected | ✅ PASS |
| 8 | delete expense | behaves as specified | as expected | ✅ PASS |
| 9 | unknown expense | returns 404 | as expected | ✅ PASS |
| 10 | summary for a month | behaves as specified | as expected | ✅ PASS |
| 11 | summary without filters is all time | behaves as specified | as expected | ✅ PASS |
| 12 | summary with partial filter | returns 400 | as expected | ✅ PASS |
| 13 | summary with partial filter | returns 400 | as expected | ✅ PASS |
| 14 | summary with partial filter | returns 400 | as expected | ✅ PASS |
| 15 | summary with partial filter | returns 400 | as expected | ✅ PASS |
| 16 | summary month out of range | returns 400 | as expected | ✅ PASS |
| 17 | summary non numeric month | returns 400 | as expected | ✅ PASS |
| 18 | add expense missing required field | returns 400 | as expected | ✅ PASS |
| 19 | add expense missing required field | returns 400 | as expected | ✅ PASS |
| 20 | add expense missing required field | returns 400 | as expected | ✅ PASS |
| 21 | add expense missing required field | returns 400 | as expected | ✅ PASS |
| 22 | add expense bad category | returns 400 | as expected | ✅ PASS |
| 23 | add expense bad date | returns 400 | as expected | ✅ PASS |
| 24 | add expense bad date | returns 400 | as expected | ✅ PASS |
| 25 | add expense bad date | returns 400 | as expected | ✅ PASS |
| 26 | add expense blank date | returns 400 | as expected | ✅ PASS |
| 27 | add expense non numeric amount | returns 400 | as expected | ✅ PASS |
| 28 | add expense negative amount | returns 400 | as expected | ✅ PASS |
| 29 | update expense bad category | returns 400 | as expected | ✅ PASS |
| 30 | update expense non numeric amount | returns 400 | as expected | ✅ PASS |
| 31 | add expense malformed body | returns 400 | as expected | ✅ PASS |
| 32 | add expense malformed body | returns 400 | as expected | ✅ PASS |
| 33 | expense endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 34 | expense endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 35 | expense endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 36 | expense endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 37 | expense endpoints require a token | behaves as specified | as expected | ✅ PASS |
| 38 | resident cannot list expenses | behaves as specified | as expected | ✅ PASS |
| 39 | resident cannot add expense | behaves as specified | as expected | ✅ PASS |
| 40 | resident cannot delete expense | behaves as specified | as expected | ✅ PASS |
| 41 | worker cannot read the ledger | behaves as specified | as expected | ✅ PASS |
| 42 | committee member is not finance | behaves as specified | as expected | ✅ PASS |
| 43 | committee member is not finance | behaves as specified | as expected | ✅ PASS |
| 44 | committee member is not finance | behaves as specified | as expected | ✅ PASS |

### Notices  
`Backend/tests/test_notices.py` · US-10 · **18/18 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | admin can publish a notice | behaves as specified | as expected | ✅ PASS |
| 2 | category defaults to general when omitted | behaves as specified | as expected | ✅ PASS |
| 3 | treasurer is also allowed to publish | behaves as specified | as expected | ✅ PASS |
| 4 | notice list | returns newest notices | as expected | ✅ PASS |
| 5 | admin can update a notice | behaves as specified | as expected | ✅ PASS |
| 6 | delete soft deletes and hides the notice from the list | behaves as specified | as expected | ✅ PASS |
| 7 | updating a missing notice | returns 404 | as expected | ✅ PASS |
| 8 | notice without title | is rejected | as expected | ✅ PASS |
| 9 | notice without content | is rejected | as expected | ✅ PASS |
| 10 | blank title | is rejected | as expected | ✅ PASS |
| 11 | unknown category | is rejected  instead of being stored | as expected | ✅ PASS |
| 12 | unknown category on update | is rejected | as expected | ✅ PASS |
| 13 | null body | is rejected | as expected | ✅ PASS |
| 14 | list body | is rejected | as expected | ✅ PASS |
| 15 | notices require authentication | behaves as specified | as expected | ✅ PASS |
| 16 | resident can read notices | behaves as specified | as expected | ✅ PASS |
| 17 | resident cannot publish a notice | behaves as specified | as expected | ✅ PASS |
| 18 | resident cannot update or delete a notice | behaves as specified | as expected | ✅ PASS |

### Polls & Voting  
`Backend/tests/test_polls.py` · US-13 · **29/29 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | admin can create a poll with options | behaves as specified | as expected | ✅ PASS |
| 2 | start date defaults to today when omitted | behaves as specified | as expected | ✅ PASS |
| 3 | explicit start date is kept | behaves as specified | as expected | ✅ PASS |
| 4 | single poll can be fetched | behaves as specified | as expected | ✅ PASS |
| 5 | resident can vote and results are tallied | behaves as specified | as expected | ✅ PASS |
| 6 | admin can close a poll | behaves as specified | as expected | ✅ PASS |
| 7 | admin can delete a poll | behaves as specified | as expected | ✅ PASS |
| 8 | poll list reports has voted per user | behaves as specified | as expected | ✅ PASS |
| 9 | voting twice | returns 409 | as expected | ✅ PASS |
| 10 | voting on a closed poll | is rejected | as expected | ✅ PASS |
| 11 | voting before the window opens | is rejected | as expected | ✅ PASS |
| 12 | voting after the window closes | is rejected | as expected | ✅ PASS |
| 13 | voting for an option of another poll | is rejected | as expected | ✅ PASS |
| 14 | poll requires an end date | behaves as specified | as expected | ✅ PASS |
| 15 | poll requires a title | behaves as specified | as expected | ✅ PASS |
| 16 | options given as a string are rejected | behaves as specified | as expected | ✅ PASS |
| 17 | missing options are rejected | behaves as specified | as expected | ✅ PASS |
| 18 | fewer than two options are rejected | behaves as specified | as expected | ✅ PASS |
| 19 | blank options do not count towards the minimum | behaves as specified | as expected | ✅ PASS |
| 20 | unparseable end date | is rejected | as expected | ✅ PASS |
| 21 | end date before start date | is rejected | as expected | ✅ PASS |
| 22 | unknown status | is rejected | as expected | ✅ PASS |
| 23 | vote requires an option id | behaves as specified | as expected | ✅ PASS |
| 24 | non numeric option id | is rejected | as expected | ✅ PASS |
| 25 | null body | is rejected | as expected | ✅ PASS |
| 26 | list body | is rejected | as expected | ✅ PASS |
| 27 | polls require authentication | behaves as specified | as expected | ✅ PASS |
| 28 | resident can read the poll list | behaves as specified | as expected | ✅ PASS |
| 29 | resident cannot create close or delete a poll | behaves as specified | as expected | ✅ PASS |

### Maintenance Tasks  
`Backend/tests/test_maintenance.py` · US-11 · **24/24 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | admin can create a task | behaves as specified | as expected | ✅ PASS |
| 2 | task can be assigned to a worker | behaves as specified | as expected | ✅ PASS |
| 3 | task list is returned | behaves as specified | as expected | ✅ PASS |
| 4 | admin can update a task | behaves as specified | as expected | ✅ PASS |
| 5 | admin can complete a task | behaves as specified | as expected | ✅ PASS |
| 6 | admin can delete a task | behaves as specified | as expected | ✅ PASS |
| 7 | completing a missing task | returns 404 | as expected | ✅ PASS |
| 8 | completing an already completed task | returns 409 | as expected | ✅ PASS |
| 9 | updating status to completed stamps completed at | behaves as specified | as expected | ✅ PASS |
| 10 | reopening a completed task clears completed at | behaves as specified | as expected | ✅ PASS |
| 11 | task requires a title | behaves as specified | as expected | ✅ PASS |
| 12 | task requires a scheduled date | behaves as specified | as expected | ✅ PASS |
| 13 | blank scheduled date | is rejected | as expected | ✅ PASS |
| 14 | day first scheduled date | is rejected | as expected | ✅ PASS |
| 15 | unknown category | is rejected | as expected | ✅ PASS |
| 16 | unknown status on update | is rejected | as expected | ✅ PASS |
| 17 | bad scheduled date on update | is rejected | as expected | ✅ PASS |
| 18 | non numeric assignee | is rejected | as expected | ✅ PASS |
| 19 | null body | is rejected | as expected | ✅ PASS |
| 20 | list body | is rejected | as expected | ✅ PASS |
| 21 | maintenance requires authentication | behaves as specified | as expected | ✅ PASS |
| 22 | resident can read the task list | behaves as specified | as expected | ✅ PASS |
| 23 | worker cannot create a task | behaves as specified | as expected | ✅ PASS |
| 24 | resident cannot update complete or delete a task | behaves as specified | as expected | ✅ PASS |

### Equipment / Maintenance Predictor  
`Backend/tests/test_equipment.py` · US-15 · **28/28 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | admin can add equipment | behaves as specified | as expected | ✅ PASS |
| 2 | equipment list is readable | behaves as specified | as expected | ✅ PASS |
| 3 | overdue equipment reports negative days and high risk | behaves as specified | as expected | ✅ PASS |
| 4 | equipment nearing its due date is medium risk | behaves as specified | as expected | ✅ PASS |
| 5 | marking serviced updates the last serviced date | behaves as specified | as expected | ✅ PASS |
| 6 | service can be backdated | behaves as specified | as expected | ✅ PASS |
| 7 | service history lists logged services | behaves as specified | as expected | ✅ PASS |
| 8 | history of unserviced equipment is empty | behaves as specified | as expected | ✅ PASS |
| 9 | forecast | returns items due within 30 days | as expected | ✅ PASS |
| 10 | forecast works with no equipment | behaves as specified | as expected | ✅ PASS |
| 11 | admin can delete equipment | behaves as specified | as expected | ✅ PASS |
| 12 | history of missing equipment | returns 404 | as expected | ✅ PASS |
| 13 | equipment requires a name | behaves as specified | as expected | ✅ PASS |
| 14 | equipment requires a last serviced date | behaves as specified | as expected | ✅ PASS |
| 15 | blank last serviced date | is rejected | as expected | ✅ PASS |
| 16 | bad last serviced date | is rejected | as expected | ✅ PASS |
| 17 | zero service frequency | is rejected | as expected | ✅ PASS |
| 18 | zero service frequency as a string | is rejected | as expected | ✅ PASS |
| 19 | missing service frequency | is rejected | as expected | ✅ PASS |
| 20 | negative estimated cost | is rejected | as expected | ✅ PASS |
| 21 | unknown category | is rejected | as expected | ✅ PASS |
| 22 | blank cost when marking serviced is accepted | behaves as specified | as expected | ✅ PASS |
| 23 | non numeric cost when marking serviced | is rejected | as expected | ✅ PASS |
| 24 | null body | is rejected | as expected | ✅ PASS |
| 25 | list body | is rejected | as expected | ✅ PASS |
| 26 | equipment requires authentication | behaves as specified | as expected | ✅ PASS |
| 27 | resident can read equipment and forecast | behaves as specified | as expected | ✅ PASS |
| 28 | resident cannot add service or delete equipment | behaves as specified | as expected | ✅ PASS |

### Society Health Score  
`Backend/tests/test_health.py` · US-17 · **20/20 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | get calculate | returns the full score shape | as expected | ✅ PASS |
| 2 | post calculate uses the same view as get | behaves as specified | as expected | ✅ PASS |
| 3 | calculate accepts explicit month and year | behaves as specified | as expected | ✅ PASS |
| 4 | calculate is an upsert for the month | behaves as specified | as expected | ✅ PASS |
| 5 | history is empty before anything is calculated | behaves as specified | as expected | ✅ PASS |
| 6 | history | returns the saved score | as expected | ✅ PASS |
| 7 | empty society is not awarded a perfect score | behaves as specified | as expected | ✅ PASS |
| 8 | empty society does not report nonsense invoice alerts | behaves as specified | as expected | ✅ PASS |
| 9 | components without data are named as not scored | behaves as specified | as expected | ✅ PASS |
| 10 | missing notices are flagged | behaves as specified | as expected | ✅ PASS |
| 11 | total is scaled over applicable components only | behaves as specified | as expected | ✅ PASS |
| 12 | month above twelve | is rejected | as expected | ✅ PASS |
| 13 | month below one | is rejected | as expected | ✅ PASS |
| 14 | non numeric month | is rejected | as expected | ✅ PASS |
| 15 | year before 2000 | is rejected | as expected | ✅ PASS |
| 16 | health endpoints require authentication | behaves as specified | as expected | ✅ PASS |
| 17 | resident cannot calculate the score | behaves as specified | as expected | ✅ PASS |
| 18 | worker cannot calculate the score | behaves as specified | as expected | ✅ PASS |
| 19 | treasurer can calculate the score | behaves as specified | as expected | ✅ PASS |
| 20 | any authenticated user can read the history | behaves as specified | as expected | ✅ PASS |

### Neighbour Conflict Resolver  
`Backend/tests/test_conflicts.py` · US-16 · **27/27 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | resident can raise a conflict against another flat | behaves as specified | as expected | ✅ PASS |
| 2 | admin sees every report with the reporter named | behaves as specified | as expected | ✅ PASS |
| 3 | reported flat can submit its side | behaves as specified | as expected | ✅ PASS |
| 4 | admin can resolve a report | behaves as specified | as expected | ✅ PASS |
| 5 | resolution note defaults when not supplied | behaves as specified | as expected | ✅ PASS |
| 6 | pending lists open and under review reports for admin | behaves as specified | as expected | ✅ PASS |
| 7 | responding to a missing report | returns 404 | as expected | ✅ PASS |
| 8 | resident view never exposes the reporter | behaves as specified | as expected | ✅ PASS |
| 9 | reporter own report is also returned without identity fields | behaves as specified | as expected | ✅ PASS |
| 10 | resident cannot see unrelated reports | behaves as specified | as expected | ✅ PASS |
| 11 | pending is admin only | behaves as specified | as expected | ✅ PASS |
| 12 | reporting your own flat | is rejected | as expected | ✅ PASS |
| 13 | reporting an unknown flat | returns 404 | as expected | ✅ PASS |
| 14 | a user from another flat cannot respond | behaves as specified | as expected | ✅ PASS |
| 15 | a user with no flat cannot respond | behaves as specified | as expected | ✅ PASS |
| 16 | responding twice | returns 409 | as expected | ✅ PASS |
| 17 | responding to a resolved report | returns 409 | as expected | ✅ PASS |
| 18 | resolving twice | returns 409 | as expected | ✅ PASS |
| 19 | conflict requires a description | behaves as specified | as expected | ✅ PASS |
| 20 | conflict requires a reported apartment | behaves as specified | as expected | ✅ PASS |
| 21 | unknown category | is rejected | as expected | ✅ PASS |
| 22 | non numeric apartment id | is rejected | as expected | ✅ PASS |
| 23 | response text is required | behaves as specified | as expected | ✅ PASS |
| 24 | null body | is rejected | as expected | ✅ PASS |
| 25 | list body | is rejected | as expected | ✅ PASS |
| 26 | conflicts require authentication | behaves as specified | as expected | ✅ PASS |
| 27 | resident cannot resolve a report | behaves as specified | as expected | ✅ PASS |

### Visitor Parking  
`Backend/tests/test_parking.py` · US-12 · **27/27 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | admin can add a slot | behaves as specified | as expected | ✅ PASS |
| 2 | slot can be created with an explicit status | behaves as specified | as expected | ✅ PASS |
| 3 | slot list is ordered by slot number | behaves as specified | as expected | ✅ PASS |
| 4 | available | returns only free slots | as expected | ✅ PASS |
| 5 | resident can reserve a slot for a visitor | behaves as specified | as expected | ✅ PASS |
| 6 | occupying a reserved slot keeps the reserving flat | behaves as specified | as expected | ✅ PASS |
| 7 | occupying a free slot attributes it to the caller | behaves as specified | as expected | ✅ PASS |
| 8 | resident can release their own reservation | behaves as specified | as expected | ✅ PASS |
| 9 | admin can release any slot | behaves as specified | as expected | ✅ PASS |
| 10 | admin can delete a slot | behaves as specified | as expected | ✅ PASS |
| 11 | reserving a missing slot | returns 404 | as expected | ✅ PASS |
| 12 | reserving an already reserved slot | is rejected | as expected | ✅ PASS |
| 13 | occupying an already occupied slot | is rejected | as expected | ✅ PASS |
| 14 | releasing someone elses reservation is forbidden | behaves as specified | as expected | ✅ PASS |
| 15 | duplicate slot number | returns 409 | as expected | ✅ PASS |
| 16 | blank expected arrival time is accepted | behaves as specified | as expected | ✅ PASS |
| 17 | date only expected arrival time is accepted | behaves as specified | as expected | ✅ PASS |
| 18 | unparseable expected arrival time | is rejected | as expected | ✅ PASS |
| 19 | slot number is required | behaves as specified | as expected | ✅ PASS |
| 20 | blank slot number | is rejected | as expected | ✅ PASS |
| 21 | unknown status | is rejected | as expected | ✅ PASS |
| 22 | null body | is rejected | as expected | ✅ PASS |
| 23 | list body | is rejected | as expected | ✅ PASS |
| 24 | null body on reserve | is rejected | as expected | ✅ PASS |
| 25 | parking requires authentication | behaves as specified | as expected | ✅ PASS |
| 26 | resident can read slots | behaves as specified | as expected | ✅ PASS |
| 27 | resident cannot add or delete slots | behaves as specified | as expected | ✅ PASS |

### Emergency Contacts  
`Backend/tests/test_emergency.py` · US-07 · **50/50 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | create contact | returns 201 | as expected | ✅ PASS |
| 2 | create contact | returns only real columns | as expected | ✅ PASS |
| 3 | create contact uppercases the service type | behaves as specified | as expected | ✅ PASS |
| 4 | create contact blank availability becomes null | behaves as specified | as expected | ✅ PASS |
| 5 | create contact omitted availability is null | behaves as specified | as expected | ✅ PASS |
| 6 | create two contacts may share a phone | behaves as specified | as expected | ✅ PASS |
| 7 | create contact missing required field | returns 400 | as expected | ✅ PASS |
| 8 | create contact missing required field | returns 400 | as expected | ✅ PASS |
| 9 | create contact missing required field | returns 400 | as expected | ✅ PASS |
| 10 | create contact unknown service type | returns 400 | as expected | ✅ PASS |
| 11 | create contact phone without digits | returns 400 | as expected | ✅ PASS |
| 12 | create contact phone longer than 15 chars | returns 400 | as expected | ✅ PASS |
| 13 | create contact malformed body | returns 400 | as expected | ✅ PASS |
| 14 | create contact malformed body | returns 400 | as expected | ✅ PASS |
| 15 | create contact malformed body | returns 400 | as expected | ✅ PASS |
| 16 | create contact as resident | returns 403 | as expected | ✅ PASS |
| 17 | create contact as worker | returns 403 | as expected | ✅ PASS |
| 18 | create contact as treasurer | returns 201 | as expected | ✅ PASS |
| 19 | create contact without token | returns 401 | as expected | ✅ PASS |
| 20 | list contacts empty directory | returns empty list | as expected | ✅ PASS |
| 21 | list contacts | returns the created contact | as expected | ✅ PASS |
| 22 | list contacts is ordered by service type then name | behaves as specified | as expected | ✅ PASS |
| 23 | list contacts as resident | returns 200 | as expected | ✅ PASS |
| 24 | list contacts is open to every role | behaves as specified | as expected | ✅ PASS |
| 25 | list contacts is open to every role | behaves as specified | as expected | ✅ PASS |
| 26 | list contacts is open to every role | behaves as specified | as expected | ✅ PASS |
| 27 | list contacts is open to every role | behaves as specified | as expected | ✅ PASS |
| 28 | list contacts without token | returns 401 | as expected | ✅ PASS |
| 29 | update contact | returns 200 | as expected | ✅ PASS |
| 30 | update contact leaves omitted fields untouched | behaves as specified | as expected | ✅ PASS |
| 31 | update contact blank service type keeps the current one | behaves as specified | as expected | ✅ PASS |
| 32 | update contact blank availability clears it | behaves as specified | as expected | ✅ PASS |
| 33 | update contact unknown service type | returns 400 | as expected | ✅ PASS |
| 34 | update contact blank phone | returns 400 | as expected | ✅ PASS |
| 35 | update contact phone without digits | returns 400 | as expected | ✅ PASS |
| 36 | update contact phone longer than 15 chars | returns 400 | as expected | ✅ PASS |
| 37 | update contact malformed body | returns 400 | as expected | ✅ PASS |
| 38 | update contact malformed body | returns 400 | as expected | ✅ PASS |
| 39 | update contact malformed body | returns 400 | as expected | ✅ PASS |
| 40 | update unknown contact | returns 404 | as expected | ✅ PASS |
| 41 | update contact as resident | returns 403 | as expected | ✅ PASS |
| 42 | update contact as worker | returns 403 | as expected | ✅ PASS |
| 43 | update contact without token | returns 401 | as expected | ✅ PASS |
| 44 | delete contact | returns 200 | as expected | ✅ PASS |
| 45 | delete contact is a hard delete | behaves as specified | as expected | ✅ PASS |
| 46 | delete contact twice | returns 404 | as expected | ✅ PASS |
| 47 | delete unknown contact | returns 404 | as expected | ✅ PASS |
| 48 | delete contact as resident | returns 403 | as expected | ✅ PASS |
| 49 | delete contact as worker | returns 403 | as expected | ✅ PASS |
| 50 | delete contact without token | returns 401 | as expected | ✅ PASS |

### Regression suite — defects found by testing  
`Backend/tests/test_regressions.py` · all · **21/22 passed**

| # | Test case (input) | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | TestDuplicatePhoneRegistration: duplicate phone | returns 409 not 500 | as expected | ✅ PASS |
| 2 | TestDuplicatePhoneRegistration: two blank phone registrations both succeed | behaves as specified | as expected | ✅ PASS |
| 3 | date accepting endpoints create successfully | behaves as specified | as expected | ✅ PASS |
| 4 | date accepting endpoints create successfully | behaves as specified | as expected | ✅ PASS |
| 5 | date accepting endpoints create successfully | behaves as specified | as expected | ✅ PASS |
| 6 | date accepting endpoints create successfully | behaves as specified | as expected | ✅ PASS |
| 7 | invalid date is a clean 400 | behaves as specified | as expected | ✅ PASS |
| 8 | TestConflictAnonymity: pending is admin only | behaves as specified | as expected | ✅ PASS |
| 9 | TestConflictAnonymity: resident listing never exposes the reporter | behaves as specified | as expected | ✅ PASS |
| 10 | TestComplaintAssignment: assign without worker | is rejected | as expected | ✅ PASS |
| 11 | TestComplaintAssignment: assign to non worker | is rejected | as expected | ✅ PASS |
| 12 | TestComplaintAssignment: assigned worker sees the job | behaves as specified | as expected | ✅ PASS |
| 13 | paying an invoice twice | is rejected | as expected | ✅ PASS |
| 14 | zero service frequency | is rejected | as expected | ✅ PASS |
| 15 | malformed json bodies return 400 | behaves as specified | as expected | ✅ PASS |
| 16 | malformed json bodies return 400 | behaves as specified | as expected | ✅ PASS |
| 17 | malformed json bodies return 400 | behaves as specified | as expected | ✅ PASS |
| 18 | change password without new password | returns 400 | as expected | ✅ PASS |
| 19 | errors are always json never html | behaves as specified | as expected | ✅ PASS |
| 20 | jwt 401 uses a different error envelope than the rest of the api | documented open finding | Known open finding — see docs/TEST_CASES.md FINDING-10 | ⏭️ SKIP |
| 21 | residents cannot perform privileged actions | behaves as specified | as expected | ✅ PASS |
| 22 | apartment delete no longer cascades away residents | behaves as specified | as expected | ✅ PASS |

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


## 4. Test design notes

- **Isolation** — every test builds a fresh app against its own temporary SQLite file (`tests/conftest.py`), so tests never share state and never touch `instance/societyease.db`.
- **Seed fixture** — two flats and one user per role (ADMIN, TREASURER, COMMITTEE_MEMBER, TENANT, OWNER, WORKER); the tenant is linked to flat A-101 so ownership rules can be tested.
- **Role fixtures** — `admin`, `treasurer`, `resident`, `worker` yield ready-made `Authorization` headers, so a test that needs one role does not pay to log in six.
- **Regression tests are named after the defect** they prevent, and their docstrings record the expected/actual pair, so the evidence lives next to the code.
- A test that fails is treated as a finding to report, never as a test to weaken.
