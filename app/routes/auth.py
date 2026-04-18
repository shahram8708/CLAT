from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from app.extensions import db, limiter
from app.forms import LoginForm, RegistrationForm
from app.models.user import User
from app.services.email_service import send_registration_welcome

try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlsplit

    def url_parse(url):
        return urlsplit(url)


auth_bp = Blueprint("auth", __name__)

EXAM_INTEREST_MAP = {
    "CAT/MBA Entrance": "CAT",
    "CLAT/AILET/Law": "CLAT",
    "IPMAT/BBA": "IPMAT",
    "GMAT/GRE": "GMAT",
    "CUET": "CUET",
    "Class XI–XII Mathematics": "Boards",
}

PREFERRED_MODE_MAP = {
    "Classroom – Navrangpura Centre": "classroom",
    "Online – AFA (Attend From Anywhere)": "online",
    "Decide After Demo": "hybrid",
}


def _safe_next_url():
    next_url = request.args.get("next", "")
    if next_url and not url_parse(next_url).netloc:
        return next_url
    return None


@auth_bp.get("/login", endpoint="login")
def login():
    if current_user.is_authenticated:
        return redirect("/dashboard")

    form = LoginForm()
    return render_template("auth/login.html", form=form)


@auth_bp.post("/login")
@limiter.limit("10/hour")
def login_submit():
    if current_user.is_authenticated:
        return redirect("/dashboard")

    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("auth/login.html", form=form)

    normalized_email = (form.email.data or "").strip().lower()
    user = User.query.filter(func.lower(User.email) == normalized_email).first()

    if not user or not user.check_password(form.password.data):
        flash("Invalid email or password.", "danger")
        return render_template("auth/login.html", form=form)

    if not user.is_active:
        flash("Your account has been deactivated. Please contact us.", "warning")
        return render_template("auth/login.html", form=form)

    login_user(user, remember=form.remember_me.data)
    user.last_login = datetime.utcnow()
    db.session.commit()

    return redirect(_safe_next_url() or "/dashboard")


@auth_bp.get("/register", endpoint="register")
def register():
    if current_user.is_authenticated:
        return redirect("/dashboard")

    form = RegistrationForm()
    return render_template("auth/register.html", form=form)


@auth_bp.post("/register")
def register_submit():
    if current_user.is_authenticated:
        return redirect("/dashboard")

    form = RegistrationForm()
    if not form.validate_on_submit():
        return render_template("auth/register.html", form=form)

    normalized_email = (form.email.data or "").strip().lower()
    existing_user = User.query.filter(func.lower(User.email) == normalized_email).first()
    if existing_user:
        flash("An account with this email already exists. Please login.", "warning")
        return render_template("auth/register.html", form=form)

    user = User(
        first_name=(form.first_name.data or "").strip(),
        last_name=(form.last_name.data or "").strip(),
        email=normalized_email,
        phone=(form.phone.data or "").strip(),
        role="student",
        is_active=True,
        enrolled_exam=EXAM_INTEREST_MAP.get(form.exam_interest.data),
        preferred_mode=PREFERRED_MODE_MAP.get(form.preferred_mode.data),
    )
    user.set_password(form.password.data)

    db.session.add(user)
    db.session.commit()

    login_user(user)

    try:
        send_registration_welcome(user)
    except Exception as exc:
        current_app.logger.error("Registration welcome email failed: %s", exc)

    flash("Welcome to CL Ahmedabad! Your account has been created.", "success")
    return redirect("/dashboard")


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect("/")
