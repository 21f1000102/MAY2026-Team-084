# Known Issues

Deliberate gaps left in the current build. Everything here is a conscious decision,
not an undiscovered bug — close these before the app is used with real data.

---

## 1. Anyone can self-register as ADMIN or TREASURER  🔴 security

`POST /api/auth/register` is public and accepts a client-supplied `role`, and the
Register page offers **Admin / Secretary** and **Treasurer** in its dropdown. Any
visitor can therefore mint a full administrator account.

**Kept on purpose** so the team can create test accounts of any role while developing.

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

## 9. `OVERDUE` invoices are never produced  🟡 functionality

The status exists and `due_date` is stored, but nothing compares the two, so an
invoice stays `UNPAID` forever.

**To close it:** a scheduled job (or a check on read) that flips past-due unpaid
invoices to `OVERDUE`.

## 10. Two component folders  🟡 maintainability

The live pages are in `Frontend/src/componenets/` (**misspelled**). The correctly
spelled `Frontend/src/components/` holds an older, dead flow, and
`Frontend/src/routes.js` + `Frontend/src/utils/auth.js` are orphaned.

**To close it:** delete the dead folder and files, then rename `componenets` →
`components` and update the 16 imports in `router/index.js`.

## 11. `openapi.yaml` is out of date  🟡 docs

It predates the recent work and does not document `GET /api/members/workers`, the
`/api/emergency` endpoints, the new `has_voted`/`my_option_id` poll fields, or the
403/409 responses added by the role and validation layers.

## 12. Emergency-contact service types are validated in two places  🟡 maintainability

`EmergencyContact.service_type` is a free-text `String(50)` in the database. The
allowed values are enforced at the application layer instead — `ENUMS["service_type"]`
in `Backend/utils.py` (validation) and `SERVICE_TYPES` in `Frontend/src/utils/format.js`
(labels and icons). **Adding a service type means editing both lists.**

This avoids a schema migration, which the project has no tooling for (see #6). If
Alembic is adopted later, promote the column to a real `Enum` and drop the duplication.
