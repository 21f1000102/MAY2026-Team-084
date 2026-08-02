"""
Seed the database with a demo society.

Gives a freshly cloned checkout a working, logged-in-able app: one user per
role, two flats, and a little data on every screen.

    python seed.py           # add anything missing (safe to re-run)
    python seed.py --reset   # wipe and recreate from scratch

Every account uses the password shown in the summary table printed at the end.
"""
import argparse
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from models import (db, User, Apartment, Resident, Announcement, Complaint,
                    Invoice, Expense, MaintenanceTask, Equipment, ParkingSlot,
                    EmergencyContact, Vote, VoteOption)

DEMO_PASSWORD = "Admin@123"
WORKER_PASSWORD = "Worker@123"
RESIDENT_PASSWORD = "Pass@123"

USERS = [
    ("Priya Admin",      "admin@apt.com",     "ADMIN",            "9990001111", DEMO_PASSWORD),
    ("Tarun Treasurer",  "treasurer@apt.com", "TREASURER",        "9990001112", DEMO_PASSWORD),
    ("Chitra Committee", "committee@apt.com", "COMMITTEE_MEMBER", "9990001113", DEMO_PASSWORD),
    ("Ramesh Worker",    "worker@apt.com",    "WORKER",           "9990002222", WORKER_PASSWORD),
    ("Ravi Tenant",      "tenant@apt.com",    "TENANT",           "9876500011", RESIDENT_PASSWORD),
    ("Ojas Owner",       "owner@apt.com",     "OWNER",            "9876543210", RESIDENT_PASSWORD),
]

FLATS = [("A-101", "A", 1), ("B-202", "B", 2), ("C-303", "C", 3)]

CONTACTS = [
    ("Ramesh Plumbing Services", "PLUMBER",     "9876543210", "24x7"),
    ("Suresh Electricals",       "ELECTRICIAN", "9876500022", "Mon-Sat 8am-8pm"),
    ("Gate Security Desk",       "SECURITY",    "9876500033", "24x7"),
    ("Fire Brigade",             "FIRE",        "101",        "24x7 emergency"),
    ("Ambulance",                "AMBULANCE",   "108",        "24x7 emergency"),
    ("Police Control Room",      "POLICE",      "100",        "24x7 emergency"),
    ("OTIS Lift Support",        "LIFT",        "9876500044", "Mon-Fri 9am-6pm"),
]


def get_or_create(model, defaults=None, **lookup):
    row = model.query.filter_by(**lookup).first()
    if row:
        return row, False
    row = model(**{**lookup, **(defaults or {})})
    db.session.add(row)
    db.session.flush()
    return row, True


def seed(reset=False):
    created = {}

    if reset:
        db.drop_all()
        db.create_all()
        print("database reset\n")

    # ── users ────────────────────────────────────────────────
    users = {}
    for name, email, role, phone, password in USERS:
        user, made = get_or_create(
            User, email=email,
            defaults=dict(name=name, role=role, phone=phone,
                          password_hash=generate_password_hash(password)),
        )
        users[role] = user
        created["users"] = created.get("users", 0) + int(made)

    # ── flats + one resident ─────────────────────────────────
    flats = {}
    for number, block, floor in FLATS:
        flat, made = get_or_create(Apartment, flat_number=number,
                                   defaults=dict(block=block, floor=floor))
        flats[number] = flat
        created["flats"] = created.get("flats", 0) + int(made)

    for role, flat_no, is_owner in [("TENANT", "A-101", False), ("OWNER", "B-202", True)]:
        _, made = get_or_create(
            Resident, user_id=users[role].id,
            defaults=dict(apartment_id=flats[flat_no].id, is_owner=is_owner,
                          move_in_date=date.today() - timedelta(days=365)),
        )
        created["residents"] = created.get("residents", 0) + int(made)

    admin = users["ADMIN"]

    # ── emergency contacts (User Story 7) ────────────────────
    for name, service, phone, availability in CONTACTS:
        _, made = get_or_create(EmergencyContact, name=name, phone=phone,
                                defaults=dict(service_type=service, availability=availability))
        created["emergency_contacts"] = created.get("emergency_contacts", 0) + int(made)

    # ── a little data on every other screen ──────────────────
    _, made = get_or_create(
        Announcement, title="Water tank cleaning on Saturday",
        defaults=dict(content="Supply will be off 10am-1pm in all blocks. Please store water.",
                      category="MAINTENANCE", published_by=admin.id))
    created["notices"] = int(made)

    _, made = get_or_create(
        Complaint, title="Corridor light not working",
        defaults=dict(description="Second floor corridor light has been out for two days.",
                      category="ELECTRICAL", priority="MEDIUM", status="OPEN",
                      raised_by=users["TENANT"].id, apartment_id=flats["A-101"].id))
    created["complaints"] = int(made)

    today = date.today()
    for flat in flats.values():
        _, made = get_or_create(
            Invoice, apartment_id=flat.id, month=today.month, year=today.year,
            defaults=dict(amount=1500, generated_by=admin.id, status="UNPAID",
                          due_date=today + timedelta(days=15)))
        created["invoices"] = created.get("invoices", 0) + int(made)

    _, made = get_or_create(
        Expense, description="Watchman salary",
        defaults=dict(category="SALARY", amount=18000, expense_date=today,
                      paid_by=admin.id, logged_by=admin.id))
    created["expenses"] = int(made)

    _, made = get_or_create(
        MaintenanceTask, title="Quarterly lift servicing",
        defaults=dict(description="Scheduled servicing for both lifts.",
                      category="OTHER", scheduled_date=today + timedelta(days=20),
                      status="PENDING", created_by=admin.id))
    created["maintenance_tasks"] = int(made)

    _, made = get_or_create(
        Equipment, name="Lift - A Block",
        defaults=dict(category="LIFT", last_serviced_date=today - timedelta(days=80),
                      service_frequency_days=90, estimated_service_cost=4500,
                      created_by=admin.id))
    created["equipment"] = int(made)

    for slot in ("P1", "P2", "P3", "P4"):
        _, made = get_or_create(ParkingSlot, slot_number=slot, defaults=dict(status="AVAILABLE"))
        created["parking_slots"] = created.get("parking_slots", 0) + int(made)

    poll, made = get_or_create(
        Vote, title="Should we install solar panels on the terrace?",
        defaults=dict(description="Estimated cost 8 lakh, payback in about 5 years.",
                      created_by=admin.id, status="ACTIVE",
                      start_date=today, end_date=today + timedelta(days=30)))
    if made:
        for option in ("Yes, go ahead", "No, not now", "Need more information"):
            db.session.add(VoteOption(vote_id=poll.id, option_text=option))
    created["polls"] = int(made)

    db.session.commit()
    return created


def main():
    parser = argparse.ArgumentParser(description="Seed the SocietyEase demo database.")
    parser.add_argument("--reset", action="store_true",
                        help="drop every table first (DESTRUCTIVE)")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        created = seed(reset=args.reset)

    print("Seeded:")
    for key, count in sorted(created.items()):
        print(f"  {key:20s} +{count}")

    print("\nSign in at http://localhost:5173 with:\n")
    print(f"  {'ROLE':18s} {'EMAIL':22s} PASSWORD")
    print(f"  {'-' * 18} {'-' * 22} {'-' * 12}")
    for name, email, role, _phone, password in USERS:
        print(f"  {role:18s} {email:22s} {password}")


if __name__ == "__main__":
    main()
