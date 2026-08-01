"""
Shared request-validation helpers.

The API previously assigned raw client strings straight into typed SQLAlchemy
columns, which raised at flush time and surfaced as HTML 500s. Everything here
raises ApiError, which app.py turns into a clean JSON 4xx response.
"""
from datetime import datetime


class ApiError(Exception):
    """Raised for bad client input. Handled globally in app.py."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


# ── request body ──────────────────────────────────────────────
def get_body(request):
    """Return a dict body, or 400. Guards null / "str" / [] payloads."""
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError("Request body must be valid JSON")
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object")
    return data


def require(data, *fields):
    """Reject missing/blank fields. Note: 0 and False are valid values."""
    for f in fields:
        v = data.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ApiError(f"{f} is required")


# ── scalars ───────────────────────────────────────────────────
def parse_date(value, field="date", required=False):
    """'YYYY-MM-DD' -> date. Blank/None -> None (unless required)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ApiError(f"{field} is required")
        return None
    if hasattr(value, "year") and not isinstance(value, str):
        return value
    try:
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ApiError(f"{field} must be a valid date (YYYY-MM-DD)")


def parse_datetime(value, field="datetime", required=False):
    """ISO datetime (or plain date) -> datetime. Blank/None -> None."""
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ApiError(f"{field} is required")
        return None
    if isinstance(value, datetime):
        return value
    raw = str(value).strip().replace("Z", "").replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ApiError(f"{field} must be a valid date/time")


def parse_decimal(value, field="amount", required=False, min_value=None):
    """Numeric string -> float, with a clean 400 instead of a flush-time crash."""
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ApiError(f"{field} is required")
        return None
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ApiError(f"{field} must be a number")
    if num != num or num in (float("inf"), float("-inf")):
        raise ApiError(f"{field} must be a number")
    if min_value is not None and num < min_value:
        raise ApiError(f"{field} must be at least {min_value}")
    return num


def parse_int(value, field="value", required=False, min_value=None, max_value=None):
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ApiError(f"{field} is required")
        return None
    try:
        num = int(value)
    except (ValueError, TypeError):
        raise ApiError(f"{field} must be a whole number")
    if min_value is not None and num < min_value:
        raise ApiError(f"{field} must be at least {min_value}")
    if max_value is not None and num > max_value:
        raise ApiError(f"{field} must be at most {max_value}")
    return num


# ── enums ─────────────────────────────────────────────────────
# Unvalidated enum values used to COMMIT and then break every later read of
# that row, so these are checked before the object is ever constructed.
ENUMS = {
    "role": ["ADMIN", "TENANT", "OWNER", "TREASURER", "WORKER",
             "COMMITTEE_MEMBER", "AUDITOR", "SYSTEM_ADMIN"],
    "complaint_category": ["PLUMBING", "ELECTRICAL", "CLEANING", "SECURITY", "OTHER"],
    "priority": ["LOW", "MEDIUM", "HIGH"],
    "complaint_status": ["OPEN", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "CLOSED"],
    "invoice_status": ["PAID", "UNPAID", "OVERDUE"],
    "expense_category": ["SALARY", "MAINTENANCE", "UTILITIES", "CONSUMABLES", "MISCELLANEOUS"],
    "task_category": ["GENERATOR", "WATER_TANK", "CLEANING", "ELECTRICAL", "PLUMBING", "OTHER"],
    "task_status": ["PENDING", "IN_PROGRESS", "COMPLETED"],
    "announcement_category": ["GENERAL", "FINANCIAL", "MAINTENANCE", "EMERGENCY"],
    "vote_status": ["DRAFT", "ACTIVE", "CLOSED"],
    "equipment_category": ["GENERATOR", "WATER_TANK", "LIFT", "PEST_CONTROL", "FIRE_SAFETY", "OTHER"],
    "conflict_category": ["NOISE", "PARKING", "GARBAGE", "COMMON_AREA_MISUSE", "PETS", "OTHER"],
    "conflict_status": ["OPEN", "UNDER_REVIEW", "RESOLVED"],
    "parking_status": ["AVAILABLE", "OCCUPIED", "RESERVED"],
}


def parse_enum(value, enum_name, field=None, required=False, default=None):
    field = field or enum_name
    allowed = ENUMS[enum_name]
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ApiError(f"{field} is required")
        return default
    val = str(value).strip().upper()
    if val not in allowed:
        raise ApiError(f"{field} must be one of: {', '.join(allowed)}")
    return val


def clean_phone(value):
    """Blank phone -> None. users.phone is UNIQUE, and many NULLs are allowed
    while many '' values are not (that collision broke registration)."""
    if value is None:
        return None
    v = str(value).strip()
    return v or None
