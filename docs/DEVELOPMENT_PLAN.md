# SocietyEase — Development Plan

**App:** SocietyEase (apartment-society management) · **Codebase:** `Updated_Prototype/`
**Stack:** Flask + SQLAlchemy + JWT + SQLite (backend) · Vue 3 + Vite + Bootstrap (frontend)
**Goal:** take the functional-but-unhardened prototype to **production**, split into
**parallel-ownable features**, each run through a repeatable **6-stage loop**, with
**~5 people owning one feature vertical each**.

---

## 1. How the code is organized (why parallelism is easy)

Every feature is a **vertical slice** with three matching layers:

```
one backend blueprint   ↔   one api/index.js group   ↔   one Vue page
Backend/api/<f>.py            authAPI/membersAPI/...       src/components/<F>Page.vue
```

Because a feature owns its own blueprint + API group + page, two people editing two
different features rarely touch the same file. The only shared surfaces are the
**foundation** (§3) and the **contracts** (§2.1) — which is exactly what we freeze first.

---

## 2. The development loop (6-stage, contract-first)

Each feature runs this loop. The contract is **frozen in Stage 1**, so backend and frontend
build at the same time and nobody waits on anybody.

```
1 SPEC  ─►  2 DESIGN  ─►  3 BUILD (BE ∥ FE)  ─►  4 TEST  ─►  5 REVIEW  ─►  6 INTEGRATE
                                   ▲                                            │
                                   └──────────── loop back on feedback ─────────┘
```

| # | Stage | The owner does | Gate to advance (exit criteria) |
|---|-------|----------------|---------------------------------|
| 1 | **SPEC** | Write a 1-page spec (use `FEATURE_SPEC_TEMPLATE.md`): scope, **user stories per role**, endpoints + request/response shapes added to `openapi.yaml`, enums/data, acceptance criteria. | Contract merged into `openapi.yaml`; matching method stubs in `api/index.js`; acceptance criteria agreed. |
| 2 | **DESIGN** | Wireframe/mock the page with the shared design system (`style.css` tokens + `DashboardLayout`). Define states: empty / loading / error, and role variants. | Static page renders with dummy data; design reviewed by one peer. |
| 3 | **BUILD** | **Backend and frontend in parallel.** BE: routes, input validation, **role authorization**, serializers. FE: page wired to its `api/index.js` group. Both code to the frozen contract. | Feature works end-to-end locally against the real backend. |
| 4 | **TEST** | BE: `pytest` for endpoints, **role enforcement**, edge cases. FE: manual e2e walk-through (+ optional component tests). Check every acceptance criterion. | Tests green; acceptance criteria met. |
| 5 | **REVIEW** | Open a PR (one PR = one feature). Get code review + design review + **security/role review** (authorization enforced; no data leaks — e.g. conflict anonymity). | ≥1 approval covering code **and** security. |
| 6 | **INTEGRATE** | Merge to `main` behind the frozen contract. Run the full app, **demo** the feature, write the feature's `readme.md`. | On `main`, demoed, docs updated. Feedback → loop back to the relevant stage. |

### 2.1 The contracts that decouple teams

| Contract | File | Frozen in | Lets you… |
|----------|------|-----------|-----------|
| Backend API | `Backend/openapi.yaml` | Stage 1 | build the page before the endpoint exists |
| Frontend API client | `Frontend/src/api/index.js` | Stage 1 | call the feature's endpoints uniformly |
| UI system | `Frontend/src/style.css` + `DashboardLayout.vue` | Wave 0 | pages look consistent without coordination |
| Sample data | `Backend/seed.py` | Wave 0 | every page has realistic data on first run |

### 2.2 Definition of Done (per feature)

- [ ] Contract in `openapi.yaml`, matching `api/index.js`
- [ ] **Role-based authorization enforced** on every mutating endpoint
- [ ] Input validated → clean `400`s (not raw DB errors); enum values checked
- [ ] Page handles **empty / loading / error** states
- [ ] `pytest` for the blueprint passes (incl. a role-denied test)
- [ ] Manual end-to-end pass across the affected roles
- [ ] Reviewed (code + security) → merged → demoed → feature `readme.md` written

---

## 3. Wave 0 — shared foundation (do FIRST, whole team, ~2–4 days)

Feature loops **cannot start** until the app builds, contracts exist, and auth/roles are real.
Split these among the five as a short pre-sprint.

| Area | Task | Files |
|------|------|-------|
| **Fix the build** | Consolidate the misspelled `componenets/` into `components/` (or repoint the 16 router imports); wire the **new** Login/Register; delete dead flow (`routes.js`, old `components/*`, `Home.vue`, `HelloWorld.vue`). | `Frontend/src/router/index.js`, `Frontend/src/componenets/*`, `Frontend/src/components/*`, `Frontend/src/routes.js` |
| **Authorization** | Add a reusable `@role_required(...)` / `@admin_required` decorator; apply the role matrix to every mutating endpoint. **Fix the conflict `/pending` anonymity leak.** | `Backend/auth/roles.py` (new), all `Backend/api/*.py`, `Backend/api/conflicts.py` |
| **Security/config** | Move `JWT_SECRET_KEY` to env (no hardcoded default in prod); set token expiry; restrict CORS to the frontend origin. | `Backend/config.py`, `Backend/app.py` |
| **Model/DB hygiene** | Remove `models.py` import-time app + `create_all()`; single DB-init path in `app.py`. | `Backend/models.py`, `Backend/app.py` |
| **Seed data** | Seed script: apartments, one user per role (incl. **WORKER**), sample complaints/invoices/notices/polls/equipment/parking. | `Backend/seed.py` (new) |
| **Missing primitive** | Add `GET /api/members/workers` so complaint assignment can target a real WORKER. | `Backend/api/members.py` |
| **Harness** | Reconcile `openapi.yaml` with actual routes (source of truth); stand up `pytest` scaffolding; tiny CI (lint + tests on PR). | `Backend/openapi.yaml`, `Backend/tests/` (new), CI config |

**Wave 0 exit gate:** `cd Backend && python app.py` + `cd Frontend && npm run dev` →
**login works and every page loads with seed data**; `pytest` runs; `openapi.yaml` matches routes.

---

## 4. Feature breakdown → 5 owners

11 feature verticals + 3 role dashboards, grouped into **5 balanced, mostly-independent tracks**.
Each track = its blueprint(s) + `api/index.js` group(s) + page(s) + the 6-stage loop.

| Track | Owner | Features (blueprint ↔ page) | Dashboard | Key production work beyond wiring |
|-------|-------|-----------------------------|-----------|-----------------------------------|
| **A · Members & Access** | P1 (lead) | `members` ↔ MembersPage (Apartment + Resident CRUD); owns the shared `@role_required` layer + worker-listing | **SecretaryDashboard** | member edit UI, role enforcement, apartment management |
| **B · Complaints & Ops** | P2 | `complaints` ↔ ComplaintsPage; `maintenance` ↔ MaintenancePage | **WorkerDashboard** | worker picker on assign (fix `worker_id: null`), status workflow, worker "my tasks" scoping |
| **C · Finance** | P3 | `invoices` ↔ InvoicesPage; `expenses` ↔ ExpensesPage | — | receipts, bulk-generate, P&L summary, payment→resident correctness, OVERDUE handling |
| **D · Community & Governance** | P4 | `notices` ↔ NoticesPage; `polls` ↔ PollsPage; `conflicts` ↔ ConflictsPage | **ResidentDashboard** | persist poll vote-lock, **conflict anonymity fix** + reported-flat "respond" UI |
| **E · Smart Facilities** | P5 | `equipment` (predictor) ↔ EquipmentPage; `parking` ↔ ParkingPage; `health` (score) ↔ HealthScorePage | — | forecast/risk display, parking lifecycle, **health-score empty-denominator fix** + trend |

### 4.1 Dependencies & ordering

```
Foundation (Wave 0)
        │
        ▼
Track A (Members) owns Apartment + Resident
        │   FK'd into by ▼
   ┌────┴─────────────────────────────┐
   ▼            ▼            ▼          ▼
Track B      Track C      Track D    Track E(parking)
(complaints) (invoices)   (conflicts)
        │        │            │          │
        └────────┴─────┬──────┴──────────┘
                       ▼
               Track E · Health Score   (aggregates B+C+D+E+Members) → integrates LAST
```

**Because the loop is contract-first + Wave 0 ships seed data, all 5 tracks start immediately
after Wave 0** — they build against the *frozen Apartment/Resident contract*, not against
Track A's finished code. **Health Score** consumes read-shapes from B/C/D/E, all frozen in each
feature's Stage-1 SPEC, so it builds in parallel and just **integrates last**.

### 4.2 Atomic list (if you later prefer 1 person ↔ 1 blueprint)

`auth`, `members`, `complaints`, `invoices`, `expenses`, `notices`, `polls`,
`maintenance`, `equipment`, `health`, `conflicts`, `parking` (+ Secretary / Resident / Worker dashboards).

---

## 5. Roles reference (used for authorization in every feature)

| Bucket | Roles | Typical access |
|--------|-------|----------------|
| Admins | `ADMIN`, `TREASURER`, `COMMITTEE_MEMBER` | full management + all reads |
| Residents | `TENANT`, `OWNER` | own data + community features |
| Staff | `WORKER` | assigned tasks/complaints |
| (defined, unused) | `AUDITOR`, `SYSTEM_ADMIN` | reserved |

---

## 6. Verification

- **Process:** each feature's Definition-of-Done checklist is satisfied before merge; each PR maps 1:1 to a feature vertical.
- **App e2e:** after Wave 0, run backend + frontend, log in as each role, confirm every page loads with seed data.
- **Tests:** `pytest Backend/tests` green; per-feature acceptance criteria demoed.
- **Contract:** `openapi.yaml` matches live routes; `api/index.js` groups match; no page calls an undocumented endpoint.

---

## 7. Known issues this plan resolves (tracked as work items)

Broken frontend wiring · duplicate old/new UI flows · no authorization layer · hardcoded JWT
secret + non-expiring tokens · wide-open CORS · `models.py` import side-effects · no
worker-listing endpoint · conflict `/pending` anonymity leak · health-score inflation on empty
denominators · poll vote-lock not persisted · complaint assign sends `worker_id: null` ·
`openapi.yaml` drift · no tests/migrations · orphan `EmergencyContact` table.
