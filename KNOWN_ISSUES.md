# Known Issues

Deliberate gaps left in the current build. Everything here is a conscious decision,
not an undiscovered bug — close these before the app is used with real data.

**Five of these are covered by deliberately-failing tests** in
`Backend/tests/test_open_defects.py`, so they stay visible in every test run rather than
relying on someone reading this file. See `docs/TEST_CASES.md` section 3 for the
expected-vs-actual detail. (A sixth, #9 below, has since been fixed.)

---

## 1. Anyone can self-register as ADMIN or TREASURER  🔴 security

`POST /api/auth/register` is public and accepts a client-supplied `role`, and the
Register page offers **Admin / Secretary** and **Treasurer** in its dropdown. Any
visitor can therefore mint a full administrator account.

**Kept on purpose** so the team can create test accounts of any role while developing.

**Failing test:** `test_public_registration_cannot_grant_itself_admin` (OD-02) and
`test_admin_token_from_public_signup_cannot_reach_admin_endpoints` (OD-02b).

**To close it:** restrict the public endpoint to `TENANT`/`OWNER` and create staff
through the admin-only "Add Member" screen (which already supports every role).
- `Backend/auth/routes.py` → `register()` (see the NOTE comment on the role line)
- `Frontend/src/componenets/RegisterPage.vue` → the role `<select>`

## 2. JWTs never expire and there is no revocation list  🔴 security

`Backend/config.py` sets `JWT_ACCESS_TOKEN_EXPIRES = False`. A leaked token is valid
forever; logout only clears `localStorage`.

Partly mitigated: `@role_required` now re-checks `is_active` on **every** request, so
deactivating a user does take effect immediately even with a live token.

**To close it:** set a real expiry (e.g. 12 h), add refresh tokens, and keep a
revocation list (or a `token_version` column bumped on logout/password change).

## 3. Default JWT secret is hardcoded  🔴 security

`Backend/config.py` falls back to `"societyease-secret-key-change-in-production"`
when `JWT_SECRET_KEY` is unset — anyone with the repo can forge a token for any user.

**To close it:** require the env var and refuse to boot without it in production.

## 4. CORS is open to all origins  🟠 security

`Backend/app.py` calls `CORS(app)` with no origin restriction (it previously allowed
only `http://localhost:5173`).

**To close it:** `CORS(app, resources={r"/api/*": {"origins": [<frontend origin>]}})`.

## 5. Token is stored in `localStorage`  🟠 security

Readable by any script on the page, so it is exposed to XSS. An httpOnly, SameSite
cookie would be safer but requires CSRF handling.

## 6. No database migrations  🟠 operations

Schema comes from `db.create_all()`, which only ever *creates* tables — it never
alters an existing one. Any column change needs a manual migration or a DB reset.

**To close it:** adopt Flask-Migrate/Alembic.

## 7. SQLite foreign keys are not enforced  🟠 data integrity

SQLite ships with `PRAGMA foreign_keys=OFF`, so orphaned references are possible
(e.g. `ConflictReport.reported_apartment_id` after a flat is removed). Deleting a
flat that still has residents or invoices is now blocked, and the serializers
null-guard missing relations, so this does not currently crash anything.

**To close it:** enable the pragma on connect, or move to PostgreSQL.

## 8. Features with no UI  🟡 functionality

The API supports these but no screen calls them:
- **Conflict "respond"** — the reported flat can't answer a report yet
  (`conflictsAPI.respond` is unused), so the two-sided workflow is one-sided.
- **Edit member / notice / expense / task** — only create, deactivate and delete exist.
- **Change password** — `authAPI.changePassword` has no screen.
- **Re-activate a member** — deactivation is one-way in the UI.

## 9. `OVERDUE` invoices are never produced  — ✅ resolved

Previously the status existed and `due_date` was stored, but nothing compared the two,
so an invoice stayed `UNPAID` forever. Fixed while building the invoice search/filter
work (Feature 1): `_sweep_overdue_invoices()` in `Backend/api/invoices.py` runs a
scoped bulk `UPDATE` on every read of `/api/invoices/`, `/api/invoices/pending` and
`/api/invoices/summary`, promoting past-due `UNPAID` rows to `OVERDUE` *before* any
status/date filter is applied — running it after would have made `status=OVERDUE`
and `status=UNPAID` filters return stale rows.

Former failing test `test_unpaid_invoice_past_its_due_date_becomes_overdue` (was OD-03)
now passes and lives in `Backend/tests/test_regressions.py` as DEFECT-10.

## 10. Two component folders  🟡 maintainability

The live pages are in `Frontend/src/componenets/` (**misspelled**). The correctly
spelled `Frontend/src/components/` holds an older, dead flow, and
`Frontend/src/routes.js` + `Frontend/src/utils/auth.js` are orphaned.

**To close it:** delete the dead folder and files, then rename `componenets` →
`components` and update the 16 imports in `router/index.js`.

## 11. `openapi.yaml` — ✅ resolved

Previously out of date. It is now the single, consolidated spec (the duplicate
`openapi-final.yaml` was merged into it and removed) and is checked against the code:
all 84 live operations documented (21 user stories, US-01 through US-21), no stale
entries, and error-response coverage complete for every operation. Re-verify with the
parity script described in `docs/TEST_CASES.md`.

Remaining nit: response *schemas* for a few action endpoints are still inline
`type: object` rather than named components.

## 12. Emergency-contact service types are validated in two places  🟡 maintainability

`EmergencyContact.service_type` is a free-text `String(50)` in the database. The
allowed values are enforced at the application layer instead — `ENUMS["service_type"]`
in `Backend/utils.py` (validation) and `SERVICE_TYPES` in `Frontend/src/utils/format.js`
(labels and icons). **Adding a service type means editing both lists.**

This avoids a schema migration, which the project has no tooling for (see #6). If
Alembic is adopted later, promote the column to a real `Enum` and drop the duplication.

## 13. Auth errors use a different JSON envelope  🟡 contract

`flask-jwt-extended` returns `{"msg": "..."}` for a missing or invalid token, while every
other error in the API — and `openapi.yaml`'s `ErrorResponse` schema — uses `{"error": "..."}`.
The frontend's `errText()` reads `data.error`, so session-expiry messages fall back to
generic text.

**Failing test:** `test_unauthenticated_error_uses_the_documented_json_envelope` (OD-01).

**To close it:** add `@jwt.unauthorized_loader`, `@jwt.invalid_token_loader` and
`@jwt.expired_token_loader` in `create_app()`, each returning `{"error": <msg>}`. ~6 lines.

## 14. Validation errors name the internal enum, not the client's field  🟡 contract

`POST /api/maintenance/` with a bad category replies `"task_category must be one of: …"`
rather than `"category must be one of: …"`; equipment says `"equipment_category …"`. Notices
and conflicts get this right because they pass `field="category"` to `parse_enum`.

**Failing tests:** `test_validation_error_names_the_field_the_client_sent` (OD-04, OD-04b).

**To close it:** pass `field="category"` at the two call sites.
