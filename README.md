# SocietyEase — Apartment Association Management System

Software Engineering term project — **MAY 2026, Team 084**.

**SocietyEase** simplifies apartment association management with a centralized platform for
residents, association members, and administrators — reducing missed updates, improving
complaint tracking, managing dues efficiently, and maintaining proper records.

**Stack:** Flask · SQLAlchemy · Flask-JWT-Extended · SQLite (backend) — Vue 3 · Vite · Vue Router · Axios · Bootstrap 5 (frontend)

---

## Repository structure

| Path | Contents |
|------|----------|
| [`Backend/`](Backend/) | Flask API — `app.py`, `models.py`, `config.py`, `api/` (13 blueprints), `tests/`, `seed.py`, `auth/`, `openapi.yaml` |
| [`Frontend/`](Frontend/) | Vue 3 SPA — `src/` (pages, router, store, API client), `vite.config.js` |
| [`docs/`](docs/) | Design docs, [user stories](docs/USER_STORIES.md), [test cases](docs/TEST_CASES.md), [development plan](docs/DEVELOPMENT_PLAN.md) |
| [`diagrams/`](diagrams/) | Python generators (Graphviz + matplotlib) and rendered PNG/SVG diagrams |

---

## Running the app locally

Two processes: the Flask API on **port 5000** and the Vite dev server on **port 5173**.
Vite proxies `/api` → `http://localhost:5000`, so start the backend first.

### 1. Backend

```bash
cd Backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # -> http://127.0.0.1:5000
```

The SQLite database is created automatically on first run (it is git-ignored).
To load a demo society — one user per role, flats, notices, invoices and emergency contacts:

```bash
python seed.py          # safe to re-run; --reset wipes first
```

It prints the sign-in table; the admin account is `admin@apt.com` / `Admin@123`.

### 2. Frontend

In a second terminal:

```bash
cd Frontend
npm install
npm run dev                     # -> http://localhost:5173
```

Then open **http://localhost:5173**. Register an account from the UI, or sign in with an
existing one. Roles: `ADMIN`, `TREASURER`, `COMMITTEE_MEMBER` (admin views), `TENANT`/`OWNER`
(resident views), `WORKER` (task views) — each lands on its own dashboard.

---

## Core features

* Membership management (apartments, owners, tenants)
* Complaint and maintenance management
* Invoice and payment tracking, expenses and monthly summary
* Notices and community polls
* **Smart Maintenance Predictor** — equipment service forecasting
* **Society Health Score** — monthly composite score
* **Neighbour Conflict Resolver** — anonymous reporting
* **Live Visitor Parking** — slot availability
* **Emergency Contacts** — one-tap directory for plumbers, electricians, security and services

## API

All endpoints live under `/api/*` and (except register/login) require an
`Authorization: Bearer <JWT>` header. The full contract is in
[`Backend/openapi.yaml`](Backend/openapi.yaml).

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| `auth` | `/api/auth` | register, login, profile, change password |
| `members` | `/api/members` | apartments + residents |
| `complaints` | `/api/complaints` | raise, assign, status workflow |
| `invoices` | `/api/invoices` | invoices, bulk generation, payments, receipts |
| `expenses` | `/api/expenses` | expense log + monthly summary |
| `notices` | `/api/notices` | announcements |
| `polls` | `/api/polls` | polls, voting, results |
| `maintenance` | `/api/maintenance` | scheduled maintenance tasks |
| `equipment` | `/api/equipment` | smart maintenance predictor + forecast |
| `health` | `/api/health` | society health score |
| `conflicts` | `/api/conflicts` | anonymous neighbour-conflict resolver |
| `parking` | `/api/parking` | live visitor parking slots |
| `emergency` | `/api/emergency` | emergency contact directory (admin manages, all roles read) |

---

## Testing

539 automated API tests covering all 13 blueprints — happy paths, validation, role
authorization, and business rules, plus a regression suite for every defect testing has caught.

**6 of them fail on purpose.** `tests/test_open_defects.py` asserts the behaviour the API
*should* have; each failure is a real defect we found and have not fixed yet, so it stays
visible in every run instead of hiding in a document. A run is healthy when **regressions = 0**.

```bash
cd Backend
.\run_tests.ps1           # Windows: full suite with a per-module summary
run_tests.bat             #   (or this, if PowerShell blocks scripts)
pytest -v                 # any platform
python tests/report.py    # regenerate docs/TEST_CASES.md from a real run
```

**[docs/TEST_CASES.md](docs/TEST_CASES.md)** lists every case with its input, expected output and
actual output, and documents the defects testing uncovered.

## Development process

Work is split into feature verticals (*one blueprint ↔ one API group ↔ one page*), each taken
through a 6-stage contract-first loop. See **[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)**
for the loop, foundation tasks, and feature/ownership breakdown; use
**[docs/FEATURE_SPEC_TEMPLATE.md](docs/FEATURE_SPEC_TEMPLATE.md)** to spec a feature before building it.

### Team workflow

1. Each team member works on a separate branch.
2. Changes are pushed to the respective branch.
3. Pull Requests are created for review.
4. The Project Manager reviews the Pull Requests.
5. Approved changes are merged into `main`.
6. `main` is maintained as the stable version.

Tasks are tracked on a GitHub Projects Kanban board: **Backlog → To Do → In Progress → Review → Done**.

## Team members and responsibilities

| Team Member | Responsibility |
|-------------|----------------|
| Madhumathi J | Project coordination, documentation, MoM, Kanban tracking |
| Nikhilesh | Initial database schema, backend API integration |
| Mani Shankar | Database schema refinement, frontend dev and backend API dev |
| Pratik Ranjan Bishwal | Frontend development using Vue.js |
| Praket Pati Tiwari | Class diagram, component design, Gantt chart, testing and reviewing |

## Diagrams

Class diagram, component design, Gantt chart and Kanban board live in
[`diagrams/output/`](diagrams/output/) (PNG + SVG). Design documents are in [`docs/`](docs/).
To regenerate the diagrams:

```bash
cd diagrams
pip install -r requirements.txt     # graphviz + matplotlib
python generate_all.py
```

> Requires the Graphviz `dot` binary — `winget install Graphviz.Graphviz` (Windows),
> `brew install graphviz` (macOS), `apt-get install graphviz` (Linux).
