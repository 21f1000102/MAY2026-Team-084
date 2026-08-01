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
| [`Backend/`](Backend/) | Flask API — `app.py`, `models.py`, `config.py`, `api/` (12 blueprints), `auth/`, `openapi.yaml` |
| [`Frontend/`](Frontend/) | Vue 3 SPA — `src/` (pages, router, store, API client), `vite.config.js` |
| [`docs/`](docs/) | Design docs + [development plan](docs/DEVELOPMENT_PLAN.md) + [feature spec template](docs/FEATURE_SPEC_TEMPLATE.md) |
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
