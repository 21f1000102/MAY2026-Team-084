# Feature Spec — `<FEATURE NAME>`

> Fill this out in **Stage 1 (SPEC)** of the development loop, before writing code.
> Copy this file to `docs/specs/<feature>.md`. Once the **Contract** section is merged into
> `openapi.yaml` + `api/index.js`, backend and frontend can build in parallel.
> See `DEVELOPMENT_PLAN.md` for the full loop.

| | |
|---|---|
| **Feature / track** | e.g. Complaints & Ops |
| **Owner** | your name |
| **Backend blueprint** | `Backend/api/<feature>.py` |
| **Frontend page(s)** | `Frontend/src/components/<Feature>Page.vue` |
| **api/index.js group** | `<feature>API` |
| **Status** | Spec / Design / Build / Test / Review / Integrate |

---

## 1. Scope

**In scope:** what this feature does (2–4 bullets).

**Out of scope:** explicitly what it does *not* do (so it doesn't creep into other tracks).

**Depends on:** upstream contracts you rely on (e.g. `Apartment` shape from Members). List the
*contract*, not the person — you build against the frozen shape, not their finished code.

---

## 2. User stories (per role)

Cover every role that touches the feature. Use the role buckets from `DEVELOPMENT_PLAN.md §5`.

- **As an ADMIN/TREASURER/COMMITTEE_MEMBER**, I can … so that …
- **As a TENANT/OWNER (resident)**, I can … so that …
- **As a WORKER**, I can … so that …

---

## 3. Contract (freeze this, then unblock parallel build)

### 3.1 Endpoints (add these to `openapi.yaml`)

| Method | Path | Purpose | Allowed roles | Request body | Response |
|--------|------|---------|---------------|--------------|----------|
| GET | `/api/<feature>/` | list | … | — | `[ {…} ]` |
| POST | `/api/<feature>/` | create | ADMIN… | `{…}` | `{…}` (201) |
| PUT | `/api/<feature>/{id}` | update | … | `{…}` | `{…}` |
| DELETE | `/api/<feature>/{id}` | delete | ADMIN… | — | `{message}` |

### 3.2 `api/index.js` group (add matching stubs)

```js
export const <feature>API = {
  getAll: () => api.get('/<feature>/'),
  add:    (data) => api.post('/<feature>/', data),
  update: (id, data) => api.put(`/<feature>/${id}`, data),
  remove: (id) => api.delete(`/<feature>/${id}`),
}
```

### 3.3 Data / response shape (the object a page renders)

```json
{
  "id": 1,
  "field": "value",
  "status": "OPEN"
}
```

### 3.4 Enums used

List each enum + allowed values (validate these on the backend → clean `400`).

---

## 4. UI design (Stage 2)

- **Layout:** which parts of the page (filters, list/table/cards, modals).
- **States:** empty / loading / error copy.
- **Role variations:** what admins see/can-do vs residents vs workers.
- **Design system:** use `style.css` tokens + classes; page lives inside `DashboardLayout`.
- Attach wireframe/screenshot or link.

---

## 5. Acceptance criteria (Stage 4 checks these)

- [ ] …happy-path works for each role
- [ ] …unauthorized role is **denied** (403) on mutating endpoints
- [ ] …invalid input returns a clean 400 (no raw DB error)
- [ ] …empty / loading / error states render
- [ ] …(feature-specific rule, e.g. "one vote per user", "reporter identity hidden from accused")

---

## 6. Tests (Stage 4)

- **Backend (`pytest`):** happy path per endpoint · role-denied case · validation/edge cases.
- **Frontend:** manual e2e steps to reproduce, listed here; optional component tests.

---

## 7. Definition of Done (Stage 6)

- [ ] Contract in `openapi.yaml` + `api/index.js`
- [ ] Role authorization enforced
- [ ] Input validated (clean 400s)
- [ ] Empty/loading/error states
- [ ] `pytest` passes (incl. role-denied)
- [ ] Manual e2e passes across roles
- [ ] Reviewed (code + security) → merged → demoed → this spec + feature `readme.md` updated
