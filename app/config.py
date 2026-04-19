import os


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _database_url():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///dev.db").strip()
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Flask-SQLAlchemy resolves relative sqlite paths against app.instance_path.
    # Normalize legacy values to avoid ending up at instance/instance/<db>.db.
    if database_url.startswith("sqlite:///instance/"):
        database_url = database_url.replace("sqlite:///instance/", "sqlite:///", 1)

    return database_url


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = _to_bool(os.environ.get("MAIL_USE_TLS", "True"), default=True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

    WTF_CSRF_ENABLED = True
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = False
    TESTING = False

    @classmethod
    def validate(cls):
        return None


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise RuntimeError("SECRET_KEY environment variable is required in production.")

        database_url = os.environ.get("DATABASE_URL")
        if not database_url or not database_url.strip():
            raise RuntimeError(
                "DATABASE_URL environment variable is required in production. "
                "Set it to your Render PostgreSQL connection string."
            )


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    ENV = "testing"
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
