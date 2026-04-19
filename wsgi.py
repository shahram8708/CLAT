import json
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app
from app.extensions import db
from app.models import ExamSession, SiteSetting, User  # noqa: F401


flask_app = create_app()
# Keep `app` for WSGI servers (e.g., gunicorn wsgi:app).
app = flask_app

SEED_STATE_KEY = "system_seed_data_state"
SEED_STATE_LABEL = "System Seed State"
SEED_STATE_GROUP = "system"
DEFAULT_SEED_VERSION = "2026-04-19-v1"


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _utcnow():
    return datetime.now(timezone.utc)


def _build_seed_state(status, version, error_message=None):
    payload = {
        "status": status,
        "version": version,
        "timestamp": _utcnow().isoformat(),
    }
    if error_message:
        payload["error"] = str(error_message)[:240]
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def _parse_seed_state(raw_value):
    if not raw_value:
        return {}

    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _is_in_progress_state_stale(parsed_state, stale_minutes):
    raw_timestamp = parsed_state.get("timestamp")
    if not raw_timestamp:
        return True

    normalized = str(raw_timestamp).replace("Z", "+00:00")
    try:
        parsed_timestamp = datetime.fromisoformat(normalized)
    except ValueError:
        return True

    if parsed_timestamp.tzinfo is None:
        parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)

    return (_utcnow() - parsed_timestamp) > timedelta(minutes=max(stale_minutes, 1))


def _write_seed_state(status, seed_version, error_message=None):
    serialized_state = _build_seed_state(status, seed_version, error_message=error_message)

    try:
        updated_count = (
            SiteSetting.query.filter_by(key=SEED_STATE_KEY)
            .update(
                {
                    "value": serialized_state,
                    "setting_type": "json",
                    "label": SEED_STATE_LABEL,
                    "group": SEED_STATE_GROUP,
                },
                synchronize_session=False,
            )
        )

        if updated_count == 0:
            db.session.add(
                SiteSetting(
                    key=SEED_STATE_KEY,
                    value=serialized_state,
                    setting_type="json",
                    label=SEED_STATE_LABEL,
                    group=SEED_STATE_GROUP,
                )
            )

        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def _try_claim_seed_execution(seed_version, stale_minutes):
    in_progress_state = _build_seed_state("in_progress", seed_version)

    db.session.add(
        SiteSetting(
            key=SEED_STATE_KEY,
            value=in_progress_state,
            setting_type="json",
            label=SEED_STATE_LABEL,
            group=SEED_STATE_GROUP,
        )
    )

    try:
        db.session.commit()
        flask_app.logger.info("Acquired seed lock via first-time state insert.")
        return True
    except IntegrityError:
        db.session.rollback()

    existing_state_row = SiteSetting.query.filter_by(key=SEED_STATE_KEY).first()
    if existing_state_row is None:
        flask_app.logger.info("Seed state row disappeared during lock acquisition race.")
        return False

    parsed_state = _parse_seed_state(existing_state_row.value)
    current_status = str(parsed_state.get("status", "")).strip().lower()
    current_version = str(parsed_state.get("version", "")).strip()

    if current_status == "done" and current_version == seed_version:
        flask_app.logger.info("Seed already applied for version %s.", seed_version)
        return False

    if (
        current_status == "in_progress"
        and current_version == seed_version
        and not _is_in_progress_state_stale(parsed_state, stale_minutes)
    ):
        flask_app.logger.info("Seed currently running in another worker.")
        return False

    previous_value = existing_state_row.value
    updated_count = (
        SiteSetting.query.filter_by(key=SEED_STATE_KEY, value=previous_value)
        .update(
            {
                "value": in_progress_state,
                "setting_type": "json",
                "label": SEED_STATE_LABEL,
                "group": SEED_STATE_GROUP,
            },
            synchronize_session=False,
        )
    )

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flask_app.logger.info("Seed lock takeover failed due to concurrent commit.")
        return False

    if updated_count == 1:
        flask_app.logger.info("Acquired seed lock by takeover of prior state %s.", current_status or "unknown")
        return True

    flask_app.logger.info("Seed lock takeover lost to another worker.")
    return False


def ensure_database_tables():
    """Create missing tables on startup to avoid runtime OperationalError on fresh DBs."""
    with flask_app.app_context():
        try:
            db.create_all()
            flask_app.logger.info("Database tables are ready.")
        except SQLAlchemyError as exc:
            db.session.rollback()
            error_text = str(exc).lower()
            duplicate_table_markers = ("already exists", "duplicate table", "duplicate relation")

            if any(marker in error_text for marker in duplicate_table_markers):
                flask_app.logger.warning(
                    "Database table creation raced across workers; continuing startup."
                )
                return

            flask_app.logger.exception("Database table initialization failed.")
            raise


def run_seeds():
    from scripts.seed_data import seed_data

    seed_data()


def ensure_seed_data():
    if not _to_bool(os.environ.get("AUTO_RUN_SEEDS", "true"), default=True):
        flask_app.logger.info("Automatic seed execution is disabled via AUTO_RUN_SEEDS.")
        return

    seed_version = (os.environ.get("SEED_DATA_VERSION") or DEFAULT_SEED_VERSION).strip() or DEFAULT_SEED_VERSION
    stale_minutes = _to_int(os.environ.get("SEED_LOCK_STALE_MINUTES", "20"), default=20)

    with flask_app.app_context():
        if not _try_claim_seed_execution(seed_version=seed_version, stale_minutes=stale_minutes):
            return

        flask_app.logger.info("Running seed data for version %s.", seed_version)

        try:
            run_seeds()
        except Exception as exc:
            db.session.rollback()
            _write_seed_state("failed", seed_version, error_message=str(exc))
            flask_app.logger.exception("Seed data failed for version %s.", seed_version)
            raise

        _write_seed_state("done", seed_version)
        flask_app.logger.info("Seed data completed for version %s.", seed_version)


def bootstrap_startup():
    if _to_bool(os.environ.get("AUTO_CREATE_TABLES", "true"), default=True):
        ensure_database_tables()

    ensure_seed_data()


bootstrap_startup()


def ensure_admin_user():
    admin_user = User.query.filter_by(role="admin").first()
    if admin_user:
        flask_app.logger.info("Admin user already exists: %s", admin_user.email)
        return admin_user

    admin_user = User(
        email="admin@clahmedabad.com",
        first_name="Admin",
        last_name="CL Ahmedabad",
        phone="9978559986",
        role="admin",
        is_active=True,
    )
    admin_user.set_password("Admin@CL2026!")

    db.session.add(admin_user)
    db.session.commit()
    flask_app.logger.info("Created default admin user: %s", admin_user.email)
    return admin_user


def initialize_database():
    flask_app.logger.info("Initializing database tables.")
    db.create_all()
    flask_app.logger.info("Database tables are ready.")

    flask_app.logger.info("Running seed data.")
    try:
        run_seeds()
        flask_app.logger.info("Seed data complete.")
    except Exception as exc:
        db.session.rollback()
        flask_app.logger.exception("Seed data failed: %s", exc)
        raise

    flask_app.logger.info("Checking admin user.")
    ensure_admin_user()


if __name__ == "__main__":
    with flask_app.app_context():
        initialize_database()

    flask_app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
