from app import create_app
from app.extensions import db
from app.models import ExamSession, User  # noqa: F401


flask_app = create_app()
# Keep `app` for WSGI servers (e.g., gunicorn wsgi:app).
app = flask_app


def run_seeds():
    from scripts.seed_data import seed_data

    seed_data()


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
