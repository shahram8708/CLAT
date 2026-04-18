from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from sqlalchemy import desc

from app.extensions import db, limiter
from app.forms import ContactForm
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.lead import Lead
from app.models.result import Result
from app.services.email_service import send_lead_notification
from app.services.whatsapp import get_default_demo_link


main_bp = Blueprint("main", __name__)


def _split_name(full_name):
    clean_name = " ".join((full_name or "").strip().split())
    if not clean_name:
        return "", ""
    parts = clean_name.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


def _format_inr_value(value):
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


@main_bp.app_template_filter("format_inr")
def format_inr(value):
    return _format_inr_value(value)


@main_bp.get("/")
def index():
    courses = Course.query.filter_by(is_active=True).order_by(Course.display_order.asc()).all()
    faculty = Faculty.query.filter_by(is_active=True).order_by(Faculty.display_order.asc()).limit(4).all()
    results = Result.query.filter_by(is_active=True).order_by(Result.display_order.asc()).limit(6).all()
    blog_posts = (
        BlogPost.query.filter_by(is_published=True)
        .order_by(desc(BlogPost.published_at))
        .limit(3)
        .all()
    )

    return render_template(
        "main/index.html",
        courses=courses,
        faculty=faculty,
        results=results,
        blog_posts=blog_posts,
        demo_whatsapp_link=get_default_demo_link(),
    )


@main_bp.get("/about")
def about():
    return render_template("main/about.html")


@main_bp.get("/contact")
def contact():
    form = ContactForm()
    sent = request.args.get("sent") == "1"
    return render_template("main/contact.html", form=form, sent=sent)


@main_bp.post("/contact")
@limiter.limit("10/minute")
def contact_submit():
    form = ContactForm()
    if not form.validate_on_submit():
        return render_template("main/contact.html", form=form, sent=False), 400

    first_name, last_name = _split_name(form.name.data)
    lead = Lead(
        first_name=first_name or "Student",
        last_name=last_name or "Inquiry",
        phone=form.phone.data.strip(),
        email=form.email.data.strip(),
        exam_interest=form.subject.data,
        preferred_mode=None,
        source_page="contact",
        notes=form.message.data.strip(),
    )

    db.session.add(lead)
    db.session.commit()
    send_lead_notification(lead)

    return redirect(url_for("main.contact", sent=1))


@main_bp.get("/free-resources")
def free_resources():
    return render_template("main/free_resources.html")


@main_bp.post("/free-resources/capture-email")
@limiter.limit("20/minute")
def capture_resource_email():
    payload = request.get_json(silent=True) or {}
    if not payload and request.form:
        payload = request.form.to_dict(flat=True)

    email = (payload.get("email") or "").strip().lower()

    if not email:
        return jsonify({"status": "error", "errors": {"email": "Email is required."}}), 400

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"status": "error", "errors": {"email": "Enter a valid email address."}}), 400

    try:
        lead = Lead(
            first_name="Resource",
            last_name="Download",
            phone="0000000000",
            email=email,
            source_page="free-resources",
            status="new",
        )
        db.session.add(lead)
        db.session.commit()

        return jsonify({"status": "ok", "message": "Email captured"})
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error"}), 500
