import os
import re

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, send_from_directory, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import desc

from app.extensions import db, limiter
from app.forms import ContactForm
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.free_resource import FreeResource
from app.models.lead import Lead
from app.models.result import Result
from app.models.testimonial import Testimonial
from app.services.email_service import send_lead_notification
from app.services.whatsapp import get_default_demo_link


main_bp = Blueprint("main", __name__)

FREE_RESOURCE_TOKEN_SALT = "free-resource-download-v1"
FREE_RESOURCE_TOKEN_MAX_AGE_SECONDS = 15 * 60
RESOURCE_ICON_MAP = {
    "pdf": "📘",
    "link": "🔗",
    "video": "🎥",
    "mock_test": "🧪",
}


def _resource_serializer():
    secret_key = current_app.config.get("SECRET_KEY") or current_app.secret_key
    if not secret_key:
        raise RuntimeError("SECRET_KEY is required for free resource download links.")
    return URLSafeTimedSerializer(secret_key=secret_key, salt=FREE_RESOURCE_TOKEN_SALT)


def _resource_download_name(resource, filename):
    ext = os.path.splitext(filename or "")[1] or ".pdf"
    base = re.sub(r"[^a-zA-Z0-9]+", "-", (resource.title or "resource").strip()).strip("-").lower()
    if not base:
        base = "resource"
    return f"{base}{ext}"


def _deliver_free_resource(resource):
    if resource.external_url:
        resource.download_count = int(resource.download_count or 0) + 1
        db.session.commit()
        return redirect(resource.external_url)

    local_path = resource.local_file_path
    if not local_path:
        abort(404)

    absolute_path = os.path.join(current_app.static_folder, *local_path.split("/"))
    if not os.path.isfile(absolute_path):
        abort(404)

    resource.download_count = int(resource.download_count or 0) + 1
    db.session.commit()

    directory = os.path.dirname(absolute_path)
    filename = os.path.basename(absolute_path)
    return send_from_directory(
        directory,
        filename,
        as_attachment=True,
        download_name=_resource_download_name(resource, filename),
    )


def _resource_cards_for_template(resources):
    cards = []
    for resource in resources:
        category_label = (resource.category or "general").upper()
        open_mode = resource.access_mode
        item = {
            "id": str(resource.id),
            "title": resource.title,
            "description": resource.description or "",
            "exam": category_label,
            "icon": RESOURCE_ICON_MAP.get(resource.resource_type, "📘"),
            "gated": bool(resource.is_gated),
            "open_mode": open_mode,
            "cta_label": "Visit Resource" if open_mode == "navigate" else "Download Free",
        }
        if not resource.is_gated:
            item["download_url"] = url_for("main.access_free_resource", resource_id=resource.id)
        cards.append(item)
    return cards


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
    testimonials = (
        Testimonial.query.filter(
            Testimonial.is_active.is_(True),
            Testimonial.display_location.in_(["homepage", "all"]),
        )
        .order_by(Testimonial.display_order.asc(), Testimonial.id.asc())
        .limit(6)
        .all()
    )
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
        testimonials=testimonials,
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
    resources = (
        FreeResource.query.filter(FreeResource.is_active.is_(True))
        .order_by(FreeResource.display_order.asc(), FreeResource.id.asc())
        .all()
    )
    return render_template("main/free_resources.html", resources=_resource_cards_for_template(resources))


@main_bp.post("/free-resources/capture-email")
@limiter.limit("20/minute")
def capture_resource_email():
    payload = request.get_json(silent=True) or {}
    if not payload and request.form:
        payload = request.form.to_dict(flat=True)

    email = (payload.get("email") or "").strip().lower()
    resource_id_raw = (payload.get("resource_id") or "").strip()

    if not email:
        return jsonify({"status": "error", "errors": {"email": "Email is required."}}), 400

    try:
        resource_id = int(resource_id_raw)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "errors": {"resource": "Invalid resource selected."}}), 400

    resource = FreeResource.query.filter_by(id=resource_id, is_active=True).first()
    if not resource or not resource.is_gated:
        return jsonify({"status": "error", "errors": {"resource": "Invalid resource selected."}}), 400

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"status": "error", "errors": {"email": "Enter a valid email address."}}), 400

    try:
        token = _resource_serializer().dumps({"resource_id": resource.id, "email": email})
        download_url = url_for("main.download_free_resource", token=token)

        lead = Lead(
            first_name="Resource",
            last_name="Download",
            phone="0000000000",
            email=email,
            exam_interest=(resource.category or "general").upper(),
            source_page="free-resources",
            status="new",
            notes=f"resource_id={resource.id}; resource_title={resource.title}",
        )
        db.session.add(lead)
        db.session.commit()

        return jsonify(
            {
                "status": "ok",
                "message": "Email captured",
                "download_url": download_url,
                "open_mode": resource.access_mode,
            }
        )
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error"}), 500


@main_bp.get("/free-resources/access/<int:resource_id>")
def access_free_resource(resource_id):
    resource = FreeResource.query.filter_by(id=resource_id, is_active=True).first()
    if not resource or resource.is_gated:
        abort(404)
    return _deliver_free_resource(resource)


@main_bp.get("/free-resources/download/<token>")
def download_free_resource(token):
    try:
        payload = _resource_serializer().loads(token, max_age=FREE_RESOURCE_TOKEN_MAX_AGE_SECONDS)
    except SignatureExpired:
        return render_template("errors/403.html"), 403
    except BadSignature:
        abort(404)

    try:
        resource_id = int(payload.get("resource_id"))
    except (TypeError, ValueError):
        abort(404)

    resource = FreeResource.query.filter_by(id=resource_id, is_active=True).first()
    if not resource:
        abort(404)

    return _deliver_free_resource(resource)
