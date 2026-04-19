import importlib
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from flask import Flask, render_template
from dotenv import load_dotenv
from whitenoise import WhiteNoise

# Load project .env early so config classes read populated environment values.
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

from app.config import config_map
from app.extensions import bcrypt, csrf, db, limiter, login_manager, mail, migrate, talisman


def _normalize_google_maps_embed_url(raw_url, fallback=""):
    candidate = (raw_url or "").strip()
    fallback_value = (fallback or "").strip()
    if not candidate:
        return fallback_value

    lower_candidate = candidate.lower()
    if "google.com/maps/embed" in lower_candidate:
        return candidate

    parsed = urlparse(candidate)
    host = (parsed.netloc or "").lower()
    path = parsed.path or ""

    if host in {"maps.google.com", "www.maps.google.com"}:
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        map_query = (query_params.get("q") or [""])[0].strip()
        if map_query:
            embed_query = urlencode({"q": map_query, "output": "embed"})
            return urlunparse(("https", "www.google.com", "/maps", "", embed_query, ""))
        return fallback_value or candidate

    if host in {"google.com", "www.google.com"} and path.startswith("/maps"):
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        output_mode = (query_params.get("output") or [""])[0].lower()
        if output_mode != "embed":
            query_params["output"] = ["embed"]
        embed_query = urlencode(query_params, doseq=True)
        return urlunparse(("https", "www.google.com", "/maps", "", embed_query, ""))

    return candidate


def create_app(config_name="development"):
    selected_config = config_name or os.environ.get("FLASK_ENV", "development")
    config_class = config_map.get(selected_config, config_map["development"])

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    config_class.validate()

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    bcrypt.init_app(app)

    csp = {
        "default-src": "'self'",
        "connect-src": [
            "'self'",
            "cdn.jsdelivr.net",
            "cdn.quilljs.com",
            "checkout.razorpay.com",
            "api.razorpay.com",
            "lumberjack.razorpay.com",
        ],
        "frame-src": [
            "'self'",
            "checkout.razorpay.com",
            "api.razorpay.com",
            "www.google.com",
            "www.youtube.com",
            "youtube.com",
            "www.youtube-nocookie.com",
        ],
        "script-src": [
            "'self'",
            "cdn.jsdelivr.net",
            "cdn.quilljs.com",
            "checkout.razorpay.com",
            "cdn.razorpay.com",
            "fonts.googleapis.com",
            "'unsafe-inline'",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "fonts.googleapis.com",
            "cdn.jsdelivr.net",
            "cdn.quilljs.com",
            "cdnjs.cloudflare.com",
        ],
        "font-src": ["fonts.gstatic.com", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        "img-src": [
            "'self'",
            "data:",
            "*.googleapis.com",
            "https://instamark.net",
            "https://*.instamark.net",
        ],
    }
    force_https = app.config.get("ENV") != "development"
    talisman.init_app(app, content_security_policy=csp, force_https=force_https)

    @app.template_filter("format_inr")
    def format_inr(value):
        if value is None:
            return "0"

        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            return "0"

        sign = "-" if numeric_value < 0 else ""
        digits = str(abs(numeric_value))

        if len(digits) <= 3:
            return f"{sign}{digits}"

        last_three = digits[-3:]
        prefix = digits[:-3]
        chunks = []

        while len(prefix) > 2:
            chunks.insert(0, prefix[-2:])
            prefix = prefix[:-2]

        if prefix:
            chunks.insert(0, prefix)

        return f"{sign}{','.join(chunks + [last_three])}"

    from app.routes.auth import auth_bp
    from app.routes.blog import blog_bp
    from app.routes.courses import courses_bp
    from app.routes.demo import demo_bp
    from app.routes.faculty import faculty_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.payment import payment_bp
    from app.routes.results import results_bp
    from app.routes.scholarship import scholarship_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.seo import seo_bp
    from app.routes.tests import tests_bp

    # from app.routes.admin import admin_bp
    # from app.routes.course import course_bp

    app.register_blueprint(auth_bp, url_prefix="")
    app.register_blueprint(main_bp, url_prefix="")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(faculty_bp, url_prefix="/faculty")
    app.register_blueprint(results_bp, url_prefix="/results")
    app.register_blueprint(demo_bp, url_prefix="/demo")
    app.register_blueprint(blog_bp, url_prefix="/blog")
    app.register_blueprint(tests_bp, url_prefix="/test-series")
    app.register_blueprint(scholarship_bp, url_prefix="/scholarship")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(seo_bp, url_prefix="")
    # app.register_blueprint(admin_bp, url_prefix="/admin")
    # app.register_blueprint(course_bp, url_prefix="/courses")

    @app.context_processor
    def inject_site_settings():
        try:
            from app.models.site_setting import SiteSetting

            def get_setting(key, default=""):
                try:
                    value = SiteSetting.get(key, default)
                    if key == "google_maps_embed_url":
                        return _normalize_google_maps_embed_url(value, fallback=default)
                    return value
                except Exception:
                    db.session.rollback()
                    return default

            return dict(get_setting=get_setting)
        except Exception:

            def get_setting(key, default=""):
                return default

            return dict(get_setting=get_setting)

    @app.context_processor
    def inject_announcements():
        try:
            from app.models.announcement import Announcement

            now = datetime.utcnow()
            active = (
                Announcement.query.filter(
                    Announcement.is_active.is_(True),
                    db.or_(Announcement.start_date.is_(None), Announcement.start_date <= now),
                    db.or_(Announcement.end_date.is_(None), Announcement.end_date >= now),
                )
                .order_by(Announcement.created_at.desc(), Announcement.id.desc())
                .all()
            )
            return dict(active_announcements=active)
        except Exception:
            db.session.rollback()
            return dict(active_announcements=[])

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    # Avoid wrapping Flask static serving in development, which can cause
    # range/content-length mismatches with browser cache behavior.
    if app.config.get("ENV") == "production":
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=app.static_folder, prefix="static/")

    importlib.import_module("app.models")
    from app.models import (  # noqa: F401
        Announcement,
        BatchSchedule,
        FreeResource,
        ScholarshipQuestion,
        SiteSetting,
        Testimonial,
    )

    return app
