import logging
import traceback

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from config import Config
from models import db
from utils import ApiError

# ── imports all route blueprints ──────────────────────────────
from auth.routes import auth_bp
from api.members import members_bp
from api.complaints import complaints_bp
from api.invoices import invoices_bp
from api.expenses import expenses_bp
from api.notices import notices_bp
from api.polls import polls_bp
from api.maintenance import maintenance_bp
from api.equipment import equipment_bp
from api.health import health_bp
from api.conflicts import conflicts_bp
from api.parking import parking_bp
from api.emergency import emergency_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    JWTManager(app)
    CORS(app)

    # ── register all blueprints ────────────────────────────────
    app.register_blueprint(auth_bp,        url_prefix="/api/auth")
    app.register_blueprint(members_bp,     url_prefix="/api/members")
    app.register_blueprint(complaints_bp,  url_prefix="/api/complaints")
    app.register_blueprint(invoices_bp,    url_prefix="/api/invoices")
    app.register_blueprint(expenses_bp,    url_prefix="/api/expenses")
    app.register_blueprint(notices_bp,     url_prefix="/api/notices")
    app.register_blueprint(polls_bp,       url_prefix="/api/polls")
    app.register_blueprint(maintenance_bp, url_prefix="/api/maintenance")
    app.register_blueprint(equipment_bp,   url_prefix="/api/equipment")
    app.register_blueprint(health_bp,      url_prefix="/api/health")
    app.register_blueprint(conflicts_bp,   url_prefix="/api/conflicts")
    app.register_blueprint(parking_bp,     url_prefix="/api/parking")
    app.register_blueprint(emergency_bp,   url_prefix="/api/emergency")

    _register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


def _register_error_handlers(app):
    """Always answer the SPA with JSON.

    Without these, any DB violation or bad input produced an HTML 500, which the
    frontend rendered as an undefined error message ("nothing happened").
    """

    @app.errorhandler(ApiError)
    def _api_error(err):
        return jsonify({"error": err.message}), err.status

    @app.errorhandler(IntegrityError)
    def _integrity_error(err):
        db.session.rollback()
        detail = str(getattr(err, "orig", err))
        if "UNIQUE" in detail.upper():
            field = detail.rsplit(".", 1)[-1].strip() if "." in detail else "value"
            message = f"That {field} is already in use"
        elif "NOT NULL" in detail.upper():
            field = detail.rsplit(".", 1)[-1].strip() if "." in detail else "field"
            message = f"{field} is required"
        else:
            message = "That change conflicts with existing data"
        app.logger.warning("IntegrityError: %s", detail)
        return jsonify({"error": message}), 409

    @app.errorhandler(SQLAlchemyError)
    def _db_error(err):
        db.session.rollback()
        app.logger.error("Database error: %s\n%s", err, traceback.format_exc())
        return jsonify({"error": "Database error"}), 500

    @app.errorhandler(HTTPException)
    def _http_error(err):
        # Keeps 404/405/415 etc. as JSON rather than Werkzeug's HTML pages.
        return jsonify({"error": err.description}), err.code

    @app.errorhandler(Exception)
    def _unhandled(err):
        db.session.rollback()
        app.logger.error("Unhandled error: %s\n%s", err, traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
