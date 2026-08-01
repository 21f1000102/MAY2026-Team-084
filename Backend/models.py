from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from datetime import datetime

db = SQLAlchemy()

# NOTE: this module used to build its own second Flask app and run
# db.create_all() at import time, against a different relative DB path than the
# real app. Importing models for a script or test therefore created/opened a
# stray database. The app is created once in app.py via create_app().


# USER

 
class User(db.Model):
    __tablename__ = "users"
 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
 
    role = db.Column(
        db.Enum(
            "ADMIN",
            "TENANT",
            "OWNER",
            "TREASURER",
            "WORKER",
            "COMMITTEE_MEMBER",
            "AUDITOR",
            "SYSTEM_ADMIN",
            name="role_enum"
        ),
        nullable=False
    )
 
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    resident = db.relationship(
        "Resident",
        back_populates="user",
        uselist=False
    )
 
 

# APARTMENT

 
class Apartment(db.Model):
    __tablename__ = "apartments"
 
    id = db.Column(db.Integer, primary_key=True)
    block = db.Column(db.String(20))
    flat_number = db.Column(db.String(20), unique=True, nullable=False)
    floor = db.Column(db.Integer)
 
    residents = db.relationship(
        "Resident",
        back_populates="apartment",
        cascade="all, delete-orphan"
    )
 
    invoices = db.relationship(
        "Invoice",
        back_populates="apartment",
        cascade="all, delete-orphan"
    )
 
    complaints = db.relationship(
        "Complaint",
        back_populates="apartment",
        cascade="all, delete-orphan"
    )
 

# RESIDENT

 
class Resident(db.Model):
    __tablename__ = "residents"
 
    id = db.Column(db.Integer, primary_key=True)
 
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    apartment_id = db.Column(
        db.Integer,
        db.ForeignKey("apartments.id"),
        nullable=False
    )
 
    is_owner = db.Column(db.Boolean, default=False)
    move_in_date = db.Column(db.Date)
    move_out_date = db.Column(db.Date)
 
    user = db.relationship("User", back_populates="resident")
    apartment = db.relationship("Apartment", back_populates="residents")
 
    payments = db.relationship(
        "Payment",
        back_populates="resident",
        cascade="all, delete-orphan"
    )
 
 

# COMPLAINT

 
class Complaint(db.Model):
    __tablename__ = "complaints"
 
    id = db.Column(db.Integer, primary_key=True)
 
  
    raised_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    apartment_id = db.Column(
        db.Integer,
        db.ForeignKey("apartments.id"),
        nullable=False
    )
 
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    
    category = db.Column(
        db.Enum(
            "PLUMBING",
            "ELECTRICAL",
            "CLEANING",
            "SECURITY",
            "OTHER",
            name="complaint_category_enum"
        ),
        nullable=False
    )
 
    priority = db.Column(
        db.Enum(
            "LOW",
            "MEDIUM",
            "HIGH",
            name="priority_enum"
        ),
        default="MEDIUM"
    )
 
    status = db.Column(
        db.Enum(
            "OPEN",
            "ASSIGNED",
            "IN_PROGRESS",
            "COMPLETED",
            "CLOSED",
            name="complaint_status_enum"
        ),
        default="OPEN"
    )
 
    assigned_worker_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )
 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    resolved_at = db.Column(db.DateTime)
 
    raiser = db.relationship(
        "User",
        foreign_keys=[raised_by]
    )
 
    worker = db.relationship(
        "User",
        foreign_keys=[assigned_worker_id]
    )
 
    apartment = db.relationship(
        "Apartment",
        back_populates="complaints"
    )
 
    updates = db.relationship(
        "ComplaintUpdate",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )
 
 

# COMPLAINT UPDATE

 
class ComplaintUpdate(db.Model):
    __tablename__ = "complaint_updates"
 
    id = db.Column(db.Integer, primary_key=True)
 
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=False
    )
 
    updated_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )
    
    status = db.Column(db.String(30))
    remarks = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by_user = db.relationship(
        "User",
        foreign_keys=[updated_by]
    )
    
    complaint = db.relationship("Complaint", back_populates="updates")
 

# INVOICE

 
class Invoice(db.Model):
    __tablename__ = "invoices"
 
    id = db.Column(db.Integer, primary_key=True)
 
    apartment_id = db.Column(
        db.Integer,
        db.ForeignKey("apartments.id"),
        nullable=False
    )
 
    generated_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )
    generator = db.relationship(
        "User",
        foreign_keys=[generated_by]
    )
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(Numeric(10,2), nullable=False)
    due_date = db.Column(db.Date)
 
    status = db.Column(
        db.Enum(
            "PAID",
            "UNPAID",
            "OVERDUE",
            name="invoice_status_enum"
        ),
        default="UNPAID"
    )
 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    apartment = db.relationship("Apartment", back_populates="invoices")
 
    payments = db.relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
 
 

# PAYMENT

 
class Payment(db.Model):
    __tablename__ = "payments"
 
    id = db.Column(db.Integer, primary_key=True)
 
    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoices.id"),
        nullable=False
    )
 
    resident_id = db.Column(
        db.Integer,
        db.ForeignKey("residents.id"),
        nullable=False
    )
 
    amount = db.Column(Numeric(10,2), nullable=False)
    payment_method = db.Column(db.String(50))
    transaction_reference = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
 
    invoice = db.relationship("Invoice", back_populates="payments")
    resident = db.relationship("Resident", back_populates="payments")
 
 

# EXPENSE

 
class Expense(db.Model):
    __tablename__ = "expenses"
 
    id = db.Column(db.Integer, primary_key=True)
 
    category = db.Column(
        db.Enum(
            "SALARY",        
            "MAINTENANCE",    
            "UTILITIES",      
            "CONSUMABLES",    
            "MISCELLANEOUS",
            name="expense_category_enum"
        ),
        nullable=False
    )
 
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(Numeric(10,2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
 
    
    paid_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    
    logged_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    receipt_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    payer = db.relationship("User", foreign_keys=[paid_by])
    logger = db.relationship("User", foreign_keys=[logged_by])
 
 

# MAINTENANCE TASK

 
class MaintenanceTask(db.Model):
    __tablename__ = "maintenance_tasks"
 
    id = db.Column(db.Integer, primary_key=True)
 
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
 
    category = db.Column(
        db.Enum(
            "GENERATOR",
            "WATER_TANK",
            "CLEANING",
            "ELECTRICAL",
            "PLUMBING",
            "OTHER",
            name="task_category_enum"
        ),
        nullable=False
    )
 
    scheduled_date = db.Column(db.Date, nullable=False)
 
    status = db.Column(
        db.Enum(
            "PENDING",
            "IN_PROGRESS",
            "COMPLETED",
            name="task_status_enum"
        ),
        default="PENDING"
    )
 
    
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )
 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
 
    creator = db.relationship("User", foreign_keys=[created_by])
    assignee = db.relationship("User", foreign_keys=[assigned_to])
 

# ANNOUNCEMENT

class Announcement(db.Model):
    __tablename__ = "announcements"
 
    id = db.Column(db.Integer, primary_key=True)
 
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
 
    category = db.Column(
        db.Enum(
            "GENERAL",
            "FINANCIAL",     
            "MAINTENANCE",   
            "EMERGENCY",
            name="announcement_category_enum"
        ),
        default="GENERAL"
    )
 
    published_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    publisher = db.relationship("User", foreign_keys=[published_by])
 

# VOTE

 
class Vote(db.Model):
    __tablename__ = "votes"
 
    id = db.Column(db.Integer, primary_key=True)
 
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
 
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
 
    status = db.Column(
        db.Enum(
            "DRAFT",
            "ACTIVE",
            "CLOSED",
            name="vote_status_enum"
        ),
        default="DRAFT"
    )
 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    creator = db.relationship("User", foreign_keys=[created_by])
 
    options = db.relationship(
        "VoteOption",
        back_populates="vote",
        cascade="all, delete-orphan"
    )
 
    responses = db.relationship(
        "VoteResponse",
        back_populates="vote",
        cascade="all, delete-orphan"
    )
 
 
# VOTE OPTION

 
class VoteOption(db.Model):
    __tablename__ = "vote_options"
 
    id = db.Column(db.Integer, primary_key=True)
 
    vote_id = db.Column(
        db.Integer,
        db.ForeignKey("votes.id"),
        nullable=False
    )
 
    option_text = db.Column(db.String(255), nullable=False)
 
    vote = db.relationship("Vote", back_populates="options")
 
    responses = db.relationship(
        "VoteResponse",
        back_populates="option",
        cascade="all, delete-orphan"
    )
 

# VOTE RESPONSE

 
class VoteResponse(db.Model):
    __tablename__ = "vote_responses"
 
    id = db.Column(db.Integer, primary_key=True)
 
    vote_id = db.Column(
        db.Integer,
        db.ForeignKey("votes.id"),
        nullable=False
    )
 
    option_id = db.Column(
        db.Integer,
        db.ForeignKey("vote_options.id"),
        nullable=False
    )
 
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    vote = db.relationship("Vote", back_populates="responses")
    option = db.relationship("VoteOption", back_populates="responses")
    user = db.relationship("User", foreign_keys=[user_id])
 
   
    __table_args__ = (
        db.UniqueConstraint("vote_id", "user_id", name="uq_vote_user"),
    )
 
 

# EMERGENCY CONTACT

 
class EmergencyContact(db.Model):
    __tablename__ = "emergency_contacts"
 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    availability = db.Column(db.String(100))


# ════════════════════════════════════════════════════════════
#  NEW FEATURE MODELS — added below, original models untouched
# ════════════════════════════════════════════════════════════


# ----------------------------------------------------------------
# FEATURE 1 — SMART MAINTENANCE PREDICTOR
# ----------------------------------------------------------------

class Equipment(db.Model):
    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    category = db.Column(
        db.Enum(
            "GENERATOR",
            "WATER_TANK",
            "LIFT",
            "PEST_CONTROL",
            "FIRE_SAFETY",
            "OTHER",
            name="equipment_category_enum"
        ),
        nullable=False
    )

    last_serviced_date = db.Column(db.Date, nullable=False)
    service_frequency_days = db.Column(db.Integer, nullable=False)  # e.g. 90 for quarterly
    estimated_service_cost = db.Column(Numeric(10, 2))

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])

    service_logs = db.relationship(
        "EquipmentServiceLog",
        back_populates="equipment",
        cascade="all, delete-orphan"
    )


class EquipmentServiceLog(db.Model):
    __tablename__ = "equipment_service_logs"

    id = db.Column(db.Integer, primary_key=True)

    equipment_id = db.Column(
        db.Integer,
        db.ForeignKey("equipment.id"),
        nullable=False
    )

    serviced_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    cost = db.Column(Numeric(10, 2))
    vendor_name = db.Column(db.String(150))
    notes = db.Column(db.Text)

    logged_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    equipment = db.relationship("Equipment", back_populates="service_logs")
    logger = db.relationship("User", foreign_keys=[logged_by])


# ----------------------------------------------------------------
# FEATURE 2 — SOCIETY HEALTH SCORE
# ----------------------------------------------------------------

class SocietyHealthScore(db.Model):
    __tablename__ = "society_health_scores"

    id = db.Column(db.Integer, primary_key=True)

    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    payment_score = db.Column(Numeric(5, 2), default=0)       # out of 30
    complaint_score = db.Column(Numeric(5, 2), default=0)     # out of 25
    notice_score = db.Column(Numeric(5, 2), default=0)        # out of 15
    poll_score = db.Column(Numeric(5, 2), default=0)          # out of 15
    maintenance_score = db.Column(Numeric(5, 2), default=0)   # out of 15

    total_score = db.Column(Numeric(5, 2), default=0)         # out of 100

    alert_reason = db.Column(db.Text)  # e.g. "3 complaints overdue, 2 invoices unpaid"

    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("month", "year", name="uq_health_score_month_year"),
    )


# ----------------------------------------------------------------
# FEATURE 3 — NEIGHBOUR CONFLICT RESOLVER
# ----------------------------------------------------------------

class ConflictReport(db.Model):
    __tablename__ = "conflict_reports"

    id = db.Column(db.Integer, primary_key=True)

    reported_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    reported_apartment_id = db.Column(
        db.Integer,
        db.ForeignKey("apartments.id"),
        nullable=False
    )

    category = db.Column(
        db.Enum(
            "NOISE",
            "PARKING",
            "GARBAGE",
            "COMMON_AREA_MISUSE",
            "PETS",
            "OTHER",
            name="conflict_category_enum"
        ),
        nullable=False
    )

    description = db.Column(db.Text, nullable=False)

    # Response from the reported flat — identity of reporter is
    # never shown to them, only the category + description
    reported_flat_response = db.Column(db.Text)
    response_submitted_at = db.Column(db.DateTime)

    status = db.Column(
        db.Enum(
            "OPEN",
            "UNDER_REVIEW",
            "RESOLVED",
            name="conflict_status_enum"
        ),
        default="OPEN"
    )

    resolution_note = db.Column(db.Text)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    resolved_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship("User", foreign_keys=[reported_by])
    reported_apartment = db.relationship("Apartment", foreign_keys=[reported_apartment_id])
    resolver = db.relationship("User", foreign_keys=[resolved_by])


# ----------------------------------------------------------------
# FEATURE 4 — LIVE VISITOR PARKING AVAILABILITY
# ----------------------------------------------------------------

class ParkingSlot(db.Model):
    __tablename__ = "parking_slots"

    id = db.Column(db.Integer, primary_key=True)

    slot_number = db.Column(db.String(20), unique=True, nullable=False)  # e.g. "P1"

    status = db.Column(
        db.Enum(
            "AVAILABLE",
            "OCCUPIED",
            "RESERVED",
            name="parking_status_enum"
        ),
        default="AVAILABLE"
    )

    occupied_by_apartment_id = db.Column(
        db.Integer,
        db.ForeignKey("apartments.id")
    )

    occupied_since = db.Column(db.DateTime)
    expected_arrival_time = db.Column(db.DateTime)  # used for "Reserved" pre-booking

    visitor_name = db.Column(db.String(100))
    visitor_vehicle_number = db.Column(db.String(20))

    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    occupied_by_apartment = db.relationship("Apartment", foreign_keys=[occupied_by_apartment_id])
    updater = db.relationship("User", foreign_keys=[updated_by])










