"""
Shared request-validation helpers.

The API previously assigned raw client strings straight into typed SQLAlchemy
columns, which raised at flush time and surfaced as HTML 500s. Everything here
raises ApiError, which app.py turns into a clean JSON 4xx response.
"""
from datetime import datetime, timedelta


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
    # EmergencyContact.service_type is a free-text String(50); validating here
    # keeps the stored values consistent without needing a schema migration.
    "service_type": ["PLUMBER", "ELECTRICIAN", "SECURITY", "FIRE",
                     "AMBULANCE", "POLICE", "LIFT", "WATER", "OTHER"],
    "event_type": ["MEETING", "EVENT", "HOLIDAY", "DEADLINE", "OTHER"],
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


# ── query-param filters ──────────────────────────────────────
def parse_bool(value, field="value"):
    """'true'/'1'/'yes' -> True, 'false'/'0'/'no' -> False. Blank/None -> None."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    raise ApiError(f"{field} must be true or false")


def search_term(value):
    """Trim a free-text search param; blank -> None. Escapes SQL LIKE wildcards
    so a literal % or _ in a search box does not act as a wildcard."""
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    return v.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def ilike(column, term):
    """column ILIKE %term% with wildcards escaped, using '\\' as the escape char."""
    from sqlalchemy import func
    return func.lower(column).like(f"%{term.lower()}%", escape="\\")


def apply_date_range(query, column, args, from_field="from", to_field="to"):
    """Filter `column` to [from, to] (inclusive) from request.args. Either bound
    may be omitted. Raises if from > to.

    The upper bound uses `column < end + 1 day` rather than `column <= end`:
    `column` may be a DateTime (e.g. Complaint.created_at), and a `<=` compare
    against a bare date would exclude anything created later that same day.
    The `< next day` form is correct for both Date and DateTime columns.
    """
    start = parse_date(args.get(from_field), from_field)
    end = parse_date(args.get(to_field), to_field)
    if start and end and start > end:
        raise ApiError(f"{from_field} must not be after {to_field}")
    if start:
        query = query.filter(column >= start)
    if end:
        query = query.filter(column < end + timedelta(days=1))
    return query


def parse_amount_range(args, min_field="min_amount", max_field="max_amount"):
    """Return (min, max) decimals from request.args, or (None, None). Raises if
    min > max."""
    lo = parse_decimal(args.get(min_field), min_field, min_value=0)
    hi = parse_decimal(args.get(max_field), max_field, min_value=0)
    if lo is not None and hi is not None and lo > hi:
        raise ApiError(f"{min_field} must not be greater than {max_field}")
    return lo, hi


def csv_response(rows, columns, filename):
    """Build a Flask Response streaming `rows` (list of dicts) as CSV.

    `columns` is an ordered list of (header, key) pairs so column order and
    header text are explicit rather than dict-iteration order.
    """
    import csv
    import io
    from flask import Response

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([header for header, _ in columns])
    for row in rows:
        writer.writerow([row.get(key, "") for _, key in columns])

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
