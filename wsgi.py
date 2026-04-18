from app import create_app
from app.extensions import db
from app.models.user import User


app = create_app()


def run_seeds():
    from scripts.seed_data import seed_data

    seed_data()


def ensure_admin_user():
    admin_user = User.query.filter_by(role="admin").first()
    if admin_user:
        app.logger.info("Admin user already exists: %s", admin_user.email)
        return admin_user

    admin_user = User(
        email="admin@clahmedabad.com",
        first_name="Admin",
        last_name="CL Ahmedabad",
        phone="9978559986",
        role="admin",
        is_active=True,
    )
    admin_user.set_password("Admin@CL2025!")

    db.session.add(admin_user)
    db.session.commit()
    app.logger.info("Created default admin user: %s", admin_user.email)
    return admin_user


def initialize_database():
    app.logger.info("Initializing database tables.")
    db.create_all()
    app.logger.info("Database tables are ready.")

    app.logger.info("Running seed data.")
    try:
        run_seeds()
        app.logger.info("Seed data complete.")
    except Exception as exc:
        db.session.rollback()
        app.logger.exception("Seed data failed: %s", exc)
        raise

    app.logger.info("Checking admin user.")
    ensure_admin_user()


if __name__ == "__main__":
    with app.app_context():
        initialize_database()

    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
