# User Stories

The canonical list of user stories for SocietyEase, and the API operations that implement each one.

Every operation in [`Backend/openapi.yaml`](../Backend/openapi.yaml) carries an `x-user-story`
extension holding one of these IDs, so the mapping between requirements and implementation is
machine-checkable. The same table is embedded in the spec's `info.description` and in the
`x-user-stories` block at its root.

> **Note for the team:** the wording below was reconstructed from the `x-user-story` mapping in the
> API spec and from what each endpoint actually does. Replace any line that differs from the
> canonical wording in the project charter — the **IDs and the endpoint mapping are correct** and
> should not be renumbered, since the spec references them.

---

| ID | User story | Endpoints |
|----|------------|-----------|
| **US-01** | As a **Treasurer**, I want to generate and track maintenance invoices for every flat, so that dues are billed consistently and I can see what is outstanding. | 4 |
| **US-02** | As a **Resident**, I want to raise a complaint about a problem in my flat or the building, so that the society has a record of it and someone is accountable for fixing it. | 1 |
| **US-03** | As a **Resident**, I want to track the status of my complaint from open to closed, so that I know whether it is being worked on without having to chase anyone. | 4 |
| **US-04** | As an **Association manager**, I want to assign a complaint to a maintenance worker, so that the right person is responsible and the job reaches their queue. | 2 |
| **US-05** | As an **Owner**, I want to see the invoices raised against the flat I own, so that I can keep track of what my tenant or I owe the society. | 1 |
| **US-06** | As a **Resident**, I want to view my invoices and download a receipt once paid, so that I have proof of payment for my records. | 2 |
| **US-07** | As a **Tenant**, I want to access emergency contact numbers for plumbers, electricians and security staff in one place, so that I can quickly reach them during emergencies. | 4 |
| **US-08** | As a **User**, I want to register, log in and manage my own account and password, so that my access to the portal is secure and under my control. | 4 |
| **US-09** | As an **Association manager**, I want to manage flats and the residents living in them, so that the society register stays accurate as people move in and out. | 9 |
| **US-10** | As a **Resident**, I want to read notices published by the association, so that I do not miss announcements about water, maintenance or emergencies. | 4 |
| **US-11** | As an **Association manager**, I want to schedule and track recurring maintenance tasks, so that routine upkeep happens on time and nothing is forgotten. | 5 |
| **US-12** | As a **Resident**, I want to see live visitor-parking availability and reserve a slot, so that my guests know where to park without blocking anyone. | 7 |
| **US-13** | As a **Resident**, I want to vote in society polls and see the results, so that I have a say in decisions that affect the community. | 6 |
| **US-14** | As a **Treasurer**, I want to record society expenses and view a monthly income-versus-expense summary, so that the committee can see where the society's money goes. | 5 |
| **US-15** | As an **Association manager**, I want to track equipment servicing and get a 30-day maintenance forecast, so that I can budget for and schedule servicing before something fails. | 6 |
| **US-16** | As a **Resident**, I want to report a conflict with a neighbour anonymously and let the secretary mediate, so that the issue is resolved without a direct confrontation. | 5 |
| **US-17** | As a **Committee member**, I want to see a monthly society health score across payments, complaints, notices, polls and maintenance, so that we can spot problems early and track whether things are improving. | 3 |
| **US-18** | As an **Association manager**, I want to search and filter members, complaints, invoices, expenses and maintenance tasks by common criteria, so that I can find a specific record quickly without scanning the whole list. | 6 |
| **US-19** | As a **Treasurer**, I want summary reports and exportable data for complaints and payments, so that I can review society performance without manually counting records. | 7 |
| **US-20** | As a **Resident**, I want to see upcoming rent due dates, society meetings and other deadlines in one place, so that I do not miss them. | 5 |
| **US-21** | As a **Maintenance worker**, I want a dashboard scoped to my own assigned complaints and tasks, with the ability to complete them and see my work history, so that I can do my job without seeing data that is not mine. | 3 |

**84 operations across 21 user stories** — every operation is mapped, and every ID used resolves to
an entry above (verified automatically). `GET /api/maintenance/summary` and
`PUT /api/maintenance/{tid}/complete` are each mapped to two stories, so the per-story counts above
sum to more than 84.

---

## Story → endpoint detail

| Story | Method | Endpoint |
|---|---|---|
| US-01 | POST · POST · GET · PUT | `/api/invoices/` · `/api/invoices/bulk` · `/api/invoices/pending` · `/api/invoices/{inv_id}/pay` |
| US-02 | POST | `/api/complaints/` |
| US-03 | GET · GET · PUT · DELETE | `/api/complaints/` · `/api/complaints/{cid}` · `/api/complaints/{cid}/status` · `/api/complaints/{cid}` |
| US-04 | PUT · GET | `/api/complaints/{cid}/assign` · `/api/members/workers` |
| US-05, US-06 | GET | `/api/invoices/` |
| US-06 | GET | `/api/invoices/{inv_id}/receipt` |
| US-07 | GET · POST · PUT · DELETE | `/api/emergency/` · `/api/emergency/` · `/api/emergency/{cid}` · `/api/emergency/{cid}` |
| US-08 | POST · POST · GET · PUT | `/api/auth/register` · `/api/auth/login` · `/api/auth/me` · `/api/auth/change-password` |
| US-09 | GET/POST/PUT/DELETE | `/api/members/apartments`… and `/api/members/`… (9 operations) |
| US-10 | GET · POST · PUT · DELETE | `/api/notices/` and `/api/notices/{nid}` |
| US-11 | GET · POST · PUT · PUT · DELETE | `/api/maintenance/`, `/api/maintenance/{tid}`, `/api/maintenance/{tid}/complete` |
| US-12 | GET · GET · POST · PUT ×3 · DELETE | `/api/parking/`, `/api/parking/available`, `/api/parking/{sid}/reserve\|occupy\|release` |
| US-13 | GET · POST · GET · POST · PUT · DELETE | `/api/polls/`, `/api/polls/{pid}`, `/api/polls/{pid}/vote`, `/api/polls/{pid}/close` |
| US-14 | GET · POST · PUT · DELETE · GET | `/api/expenses/`, `/api/expenses/{exp_id}`, `/api/expenses/summary` |
| US-15 | GET · POST · PUT · GET · GET · DELETE | `/api/equipment/`, `/api/equipment/{eid}/service`, `/api/equipment/forecast`, `/api/equipment/{eid}/history` |
| US-16 | GET · POST · PUT · PUT · GET | `/api/conflicts/`, `/api/conflicts/{rid}/respond\|resolve`, `/api/conflicts/pending` |
| US-17 | GET · POST · GET | `/api/health/calculate` (GET and POST) · `/api/health/history` |
| US-18 | GET ×6 | `/api/members/`, `/api/complaints/`, `/api/invoices/`, `/api/invoices/pending`, `/api/expenses/`, `/api/maintenance/` — query filters added to each existing list endpoint |
| US-19 | GET ×7 | `/api/members/export`, `/api/complaints/summary`, `/api/complaints/export`, `/api/invoices/summary`, `/api/invoices/export`, `/api/expenses/export`, `/api/maintenance/summary` |
| US-20 | GET · POST · PUT · DELETE · GET | `/api/events/` and `/api/events/{eid}` · `/api/events/upcoming` (merged, role-aware feed) |
| US-21 | GET · PUT · GET | `/api/maintenance/summary` · `/api/maintenance/{tid}/complete` (now worker-or-admin) · `/api/members/workers/{user_id}/work-history` |

## Verifying the mapping

```bash
python - <<'EOF'
import yaml
spec = yaml.safe_load(open('Backend/openapi.yaml', encoding='utf-8'))
legend = set(spec['x-user-stories'])
used = set()
for path in spec['paths'].values():
    for method, op in path.items():
        if method in ('get','post','put','delete'):
            us = op['x-user-story']
            used.update(us if isinstance(us, list) else [us])
print('stories used:', len(used), '| in legend:', len(legend), '| unmapped:', used - legend)
EOF
```
