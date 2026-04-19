import csv
import io
import json
import os
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

from flask import Blueprint, Response, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms.admin_forms import (
    AnnouncementForm,
    BatchScheduleForm,
    CourseCreateForm,
    CourseEditForm,
    FacultyForm,
    FreeResourceForm,
    ManualEnrollmentForm,
    ManualLeadForm,
    ManualPaymentForm,
    ManualStudentForm,
    ResultForm,
    ScholarshipQuestionForm,
    SiteSettingsForm,
    TestimonialForm,
    TestSeriesForm,
)
from app.forms.blog_form import BlogPostForm
from app.models import (
    Announcement,
    BatchSchedule,
    BlogPost,
    Course,
    Enrollment,
    Faculty,
    FreeResource,
    Lead,
    Payment,
    Result,
    ScholarshipQuestion,
    SiteSetting,
    TestAttempt,
    TestSeries,
    Testimonial,
    User,
)
from app.services.enrollment_service import ensure_student_enrollments
from app.services.scholarship_enrollment import (
    apply_scholarship_payment,
    calculate_scholarship_amounts,
    find_user_for_lead,
    resolve_exam_category,
)
from app.utils.image_handler import delete_image, save_uploaded_image


admin_bp = Blueprint("admin", __name__)

LEAD_STATUSES = {"new", "contacted", "enrolled", "dropped"}
PAYMENT_STATUSES = {"pending", "success", "failed"}
BLOG_CATEGORIES = {"cat", "clat", "ipmat", "gmat", "cuet", "general"}
FREE_RESOURCE_STORAGE_DIR = "downloads/free_resources"
MAX_FREE_RESOURCE_PDF_BYTES = 20 * 1024 * 1024


SITE_SETTINGS_FIELD_MAP = {
    "institute_name": ("text", "Institute Name", "contact"),
    "address": ("textarea", "Address", "contact"),
    "phone_primary": ("phone", "Primary Phone", "contact"),
    "phone_secondary": ("phone", "Secondary Phone", "contact"),
    "email": ("email", "Email", "contact"),
    "whatsapp_number": ("phone", "WhatsApp Number", "contact"),
    "hours_weekday": ("text", "Weekday Hours", "contact"),
    "hours_sunday": ("text", "Sunday Hours", "contact"),
    "instagram_url": ("url", "Instagram URL", "social"),
    "youtube_url": ("url", "YouTube URL", "social"),
    "facebook_url": ("url", "Facebook URL", "social"),
    "linkedin_url": ("url", "LinkedIn URL", "social"),
    "google_maps_embed_url": ("textarea", "Google Maps Embed URL", "social"),
    "homepage_meta_title": ("text", "Homepage Meta Title", "seo"),
    "homepage_meta_description": ("textarea", "Homepage Meta Description", "seo"),
    "og_image_url": ("url", "OG Image URL", "seo"),
    "hero_headline": ("text", "Hero Headline", "display"),
    "hero_subheadline": ("textarea", "Hero Subheadline", "display"),
    "show_scholarship_banner": ("boolean", "Show Scholarship Banner", "display"),
    "scholarship_banner_text": ("text", "Scholarship Banner Text", "display"),
}


@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.url))
    if current_user.role != "admin":
        abort(403)


def _format_datetime(dt_value):
    if not dt_value:
        return ""
    return dt_value.strftime("%d %b %Y, %I:%M %p")


def _is_ajax_request():
    return request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _json_list(raw_value):
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _split_csv(raw_value):
    return [item.strip() for item in (raw_value or "").split(",") if item and item.strip()]


def _split_lines(raw_value):
    return [item.strip() for item in (raw_value or "").splitlines() if item and item.strip()]


def _normalized_slug(raw_value, fallback=""):
    candidate = (raw_value or "").strip() or (fallback or "").strip()
    if not candidate:
        return ""

    normalized = unicodedata.normalize("NFKD", str(candidate))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    normalized = re.sub(r"-{2,}", "-", normalized)

    if not normalized:
        normalized = "item"

    return normalized


def _is_external_url(value):
    parsed = urlparse((value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normalized_free_resource_local_path(value):
    cleaned = (value or "").strip().replace("\\", "/")
    if not cleaned or _is_external_url(cleaned):
        return None

    cleaned = cleaned.lstrip("/")
    if cleaned.startswith("static/"):
        cleaned = cleaned[len("static/"):]

    if cleaned.startswith("downloads/free_resources/"):
        return cleaned
    if cleaned.startswith("free_resources/"):
        return f"downloads/{cleaned}"
    if "/" not in cleaned and cleaned.lower().endswith(".pdf"):
        return f"downloads/free_resources/{cleaned}"
    return None


def _free_resource_absolute_path(local_path):
    if not local_path:
        return None
    segments = [segment for segment in local_path.split("/") if segment]
    return os.path.join(current_app.static_folder, *segments)


def _human_file_size(num_bytes):
    if not num_bytes:
        return None
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes} B"


def _uploaded_file_size(file_storage):
    stream = getattr(file_storage, "stream", None)
    if not stream:
        return 0

    try:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(0)
        return size
    except Exception:
        try:
            stream.seek(0)
        except Exception:
            pass
        return 0


def _save_uploaded_free_resource_pdf(file_storage, title):
    file_name = secure_filename((file_storage.filename or "").strip())
    if not file_name or not file_name.lower().endswith(".pdf"):
        raise ValueError("Please upload a valid PDF file.")

    file_size_bytes = _uploaded_file_size(file_storage)
    if file_size_bytes > MAX_FREE_RESOURCE_PDF_BYTES:
        raise ValueError("PDF must be 20 MB or smaller.")

    slug = _normalized_slug(title, fallback="resource")
    timestamp = int(time.time())
    output_name = f"{slug}-{timestamp}.pdf"

    storage_dir = _free_resource_absolute_path(FREE_RESOURCE_STORAGE_DIR)
    os.makedirs(storage_dir, exist_ok=True)

    output_path = os.path.join(storage_dir, output_name)
    file_storage.stream.seek(0)
    file_storage.save(output_path)

    return f"{FREE_RESOURCE_STORAGE_DIR}/{output_name}", file_size_bytes


def _delete_free_resource_file_if_exists(url_value):
    local_path = _normalized_free_resource_local_path(url_value)
    if not local_path:
        return

    absolute_path = _free_resource_absolute_path(local_path)
    if not absolute_path or not os.path.isfile(absolute_path):
        return

    try:
        os.remove(absolute_path)
    except OSError:
        current_app.logger.warning("Could not remove free resource file: %s", absolute_path)


def _student_choices():
    students = User.query.filter_by(role="student").order_by(User.first_name.asc(), User.last_name.asc()).all()
    return [(student.id, f"{student.get_full_name()} ({student.email})") for student in students]


def _course_choices(active_only=False):
    query = Course.query
    if active_only:
        query = query.filter(Course.is_active.is_(True))
    courses = query.order_by(Course.display_order.asc(), Course.title.asc()).all()
    return [(course.id, f"{(course.icon or '📘')} {course.title}") for course in courses]


def _faculty_choices(active_only=False):
    query = Faculty.query
    if active_only:
        query = query.filter(Faculty.is_active.is_(True))
    faculty_members = query.order_by(Faculty.display_order.asc(), Faculty.name.asc()).all()
    return [(faculty.id, faculty.name) for faculty in faculty_members]


def _test_series_choices(active_only=False):
    query = TestSeries.query
    if active_only:
        query = query.filter(TestSeries.is_active.is_(True))
    test_series = query.order_by(TestSeries.exam.asc(), TestSeries.name.asc()).all()
    return [(item.id, f"{item.name} ({item.exam})") for item in test_series]


def _populate_batch_form_choices(form):
    form.course_id.choices = _course_choices(active_only=True)
    form.faculty_id.choices = [(0, "Not Assigned")] + _faculty_choices(active_only=True)


def _populate_enrollment_form_choices(form):
    form.user_id.choices = _student_choices()
    form.course_id.choices = _course_choices(active_only=True)


def _populate_payment_form_choices(form):
    form.user_id.choices = _student_choices()
    form.test_series_id.choices = [(0, "Not Linked to Test Series")] + _test_series_choices(active_only=True)


def _sync_offline_enrollment_from_lead(lead):
    if not lead:
        return

    user = find_user_for_lead(lead)
    if not user:
        return

    exam_category = resolve_exam_category(lead.exam_interest, fallback=user.enrolled_exam)

    course_query = Course.query.filter(Course.is_active.is_(True))
    if exam_category:
        course_query = course_query.filter(Course.exam_category == exam_category)

    course = course_query.order_by(Course.display_order.asc(), Course.id.asc()).first()
    if not course:
        return

    fee_data = calculate_scholarship_amounts(course, user.scholarship_pct)
    payable_amount = int(fee_data["payable"] or fee_data["original_fee"] or 0)
    if payable_amount <= 0:
        return

    apply_scholarship_payment(
        user=user,
        course=course,
        amount_paid=payable_amount,
        payment_mode="offline",
        payment_reference=f"Lead #{lead.id}",
        lead=lead,
    )


def _apply_course_form_to_model(course, form, keep_slug=False):
    if not keep_slug:
        course.slug = _normalized_slug(form.slug.data, fallback=form.title.data)

    course.title = (form.title.data or "").strip()
    course.exam_category = form.exam_category.data
    course.exams_covered = json.dumps(_split_csv(form.exams_covered.data), ensure_ascii=False)
    course.description = (form.description.data or "").strip()
    course.long_description = (form.long_description.data or "").strip() or None
    course.duration = (form.duration.data or "").strip() or None
    course.mode = form.mode.data
    course.batch_size = form.batch_size.data
    course.fee_min = form.fee_min.data
    course.fee_max = form.fee_max.data
    course.icon = ((form.icon.data or "").strip() or None)
    course.is_active = bool(form.is_active.data)
    course.display_order = int(form.display_order.data or 0)
    course.meta_title = ((form.meta_title.data or "").strip() or None)
    course.meta_description = ((form.meta_description.data or "").strip() or None)
    course.certificate_offered = bool(form.certificate_offered.data)
    course.emi_available = bool(form.emi_available.data)
    course.prerequisite = ((form.prerequisite.data or "").strip() or None)


def _apply_faculty_form_to_model(faculty, form):
    faculty.slug = _normalized_slug(form.slug.data, fallback=form.name.data)
    faculty.name = (form.name.data or "").strip()
    faculty.title = (form.title.data or "").strip() or None
    faculty.qualification = (form.qualification.data or "").strip() or None
    faculty.exam_score = (form.exam_score.data or "").strip() or None
    faculty.experience_yrs = form.experience_yrs.data
    faculty.subjects = json.dumps(_split_csv(form.subjects_input.data), ensure_ascii=False)
    faculty.exam_tags = json.dumps(_split_csv(form.exam_tags_input.data), ensure_ascii=False)
    faculty.bio_short = (form.bio_short.data or "").strip() or None
    faculty.bio_long = (form.bio_long.data or "").strip() or None

    youtube_url = ((form.youtube_url.data or "").strip() or None)
    faculty.youtube_url = youtube_url
    faculty.video_intro_url = youtube_url

    faculty.instagram_url = ((form.instagram_url.data or "").strip() or None)
    faculty.linkedin_url = ((form.linkedin_url.data or "").strip() or None)
    faculty.total_students_trained = form.total_students_trained.data
    faculty.joining_year = form.joining_year.data
    faculty.achievements = json.dumps(_split_lines(form.achievements_input.data), ensure_ascii=False)
    faculty.is_active = bool(form.is_active.data)
    faculty.display_order = int(form.display_order.data or 0)


def _apply_result_form_to_model(result, form):
    result.student_name = (form.student_name.data or "").strip()
    result.exam = form.exam.data
    result.year = int(form.year.data)
    result.rank_percentile = (form.rank_percentile.data or "").strip() or None
    result.target_college = (form.target_college.data or "").strip() or None
    result.testimonial = (form.testimonial.data or "").strip() or None
    result.score_details = (form.score_details.data or "").strip() or None
    result.city = (form.city.data or "").strip() or None
    result.coaching_duration = (form.coaching_duration.data or "").strip() or None
    result.video_testimonial_url = (form.video_testimonial_url.data or "").strip() or None
    result.is_active = bool(form.is_active.data)
    result.display_order = int(form.display_order.data or 0)


def _apply_test_series_form_to_model(test_series, form):
    test_series.name = (form.name.data or "").strip()
    test_series.exam = form.exam.data
    test_series.description = (form.description.data or "").strip() or None
    test_series.total_tests = form.total_tests.data
    test_series.duration_mins = form.duration_mins.data
    test_series.is_free = bool(form.is_free.data)
    test_series.price = None if test_series.is_free else int(form.price.data or 0)
    test_series.razorpay_plan_id = (form.razorpay_plan_id.data or "").strip() or None
    test_series.is_active = bool(form.is_active.data)


def _apply_free_resource_form_to_model(resource, form, *, existing_url=None):
    previous_url = ((existing_url if existing_url is not None else resource.url) or "").strip()

    resource.title = (form.title.data or "").strip()
    resource.description = (form.description.data or "").strip() or None
    resource.category = form.category.data
    resource.resource_type = form.resource_type.data
    resource.file_size = (form.file_size.data or "").strip() or None
    resource.year = form.year.data
    resource.is_gated = bool(form.is_gated.data)
    resource.is_active = bool(form.is_active.data)
    resource.display_order = int(form.display_order.data or 0)

    delivery_mode = (form.delivery_mode.data or "").strip()
    if delivery_mode == "upload":
        uploaded_file = form.pdf_upload.data
        has_uploaded_file = bool(uploaded_file and getattr(uploaded_file, "filename", ""))

        if has_uploaded_file:
            new_local_path, upload_size = _save_uploaded_free_resource_pdf(uploaded_file, resource.title)
            old_local_path = _normalized_free_resource_local_path(previous_url)
            if old_local_path and old_local_path != new_local_path:
                _delete_free_resource_file_if_exists(old_local_path)

            resource.url = new_local_path
            resource.resource_type = "pdf"
            if not resource.file_size and upload_size:
                resource.file_size = _human_file_size(upload_size)
            return

        existing_local_path = _normalized_free_resource_local_path(previous_url)
        if not existing_local_path:
            raise ValueError("Please upload a PDF file.")

        resource.url = existing_local_path
        resource.resource_type = "pdf"
        return

    if delivery_mode == "link":
        external_url = (form.external_url.data or "").strip()
        if not _is_external_url(external_url):
            raise ValueError("Please enter a valid external URL.")

        old_local_path = _normalized_free_resource_local_path(previous_url)
        if old_local_path:
            _delete_free_resource_file_if_exists(old_local_path)

        resource.url = external_url
        return

    raise ValueError("Select a valid delivery source.")


def _apply_announcement_form_to_model(announcement, form):
    announcement.title = (form.title.data or "").strip()
    announcement.message = (form.message.data or "").strip()
    announcement.announcement_type = form.announcement_type.data
    announcement.display_location = form.display_location.data
    announcement.cta_text = (form.cta_text.data or "").strip() or None
    announcement.cta_url = (form.cta_url.data or "").strip() or None
    announcement.start_date = form.start_date.data
    announcement.end_date = form.end_date.data
    announcement.is_active = bool(form.is_active.data)


def _apply_testimonial_form_to_model(testimonial, form):
    testimonial.student_name = (form.student_name.data or "").strip()
    testimonial.designation = (form.designation.data or "").strip() or None
    testimonial.course = (form.course.data or "").strip() or None
    testimonial.exam = (form.exam.data or "").strip() or None

    rating_value = (form.rating.data or "").strip()
    testimonial.rating = int(rating_value) if rating_value.isdigit() else None

    testimonial.testimonial_text = (form.testimonial_text.data or "").strip()
    testimonial.video_url = (form.video_url.data or "").strip() or None
    testimonial.display_location = form.display_location.data
    testimonial.is_active = bool(form.is_active.data)
    testimonial.display_order = int(form.display_order.data or 0)


def _apply_batch_form_to_model(batch, form):
    batch.course_id = int(form.course_id.data)
    batch.batch_name = (form.batch_name.data or "").strip()
    batch.timing = (form.timing.data or "").strip()
    batch.start_date = form.start_date.data
    batch.end_date = form.end_date.data
    batch.mode = form.mode.data
    batch.total_seats = int(form.total_seats.data or 0)
    batch.seats_filled = int(form.seats_filled.data or 0)
    batch.fee = form.fee.data

    faculty_id = int(form.faculty_id.data or 0)
    batch.faculty_id = faculty_id or None

    batch.is_active = bool(form.is_active.data)
    batch.notes = (form.notes.data or "").strip() or None


def _load_site_settings_into_form(form):
    for field_name, (setting_type, _label, _group) in SITE_SETTINGS_FIELD_MAP.items():
        default = False if setting_type == "boolean" else ""
        value = SiteSetting.get(field_name, default)
        if setting_type == "boolean":
            value = bool(value)
        getattr(form, field_name).data = value


def _save_site_settings_from_form(form):
    for field_name, (setting_type, label, group) in SITE_SETTINGS_FIELD_MAP.items():
        field_value = getattr(form, field_name).data
        SiteSetting.set(
            key=field_name,
            value=field_value,
            setting_type=setting_type,
            label=label,
            group=group,
            updated_by=current_user.id,
        )


@admin_bp.get("")
@admin_bp.get("/")
def dashboard():
    total_leads = Lead.query.count()
    total_students = User.query.filter_by(role="student").count()
    total_enrollments = Enrollment.query.count()
    total_blog_posts = BlogPost.query.count()

    recent_leads = Lead.query.order_by(Lead.submitted_at.desc()).limit(10).all()
    recent_attempts = TestAttempt.query.order_by(TestAttempt.started_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()

    total_revenue = (
        db.session.query(func.coalesce(func.sum(Payment.amount_inr), 0))
        .filter(Payment.status == "success")
        .scalar()
        or 0
    )
    total_pending_amount = (
        db.session.query(func.coalesce(func.sum(Payment.amount_inr), 0))
        .filter(Payment.status == "pending")
        .scalar()
        or 0
    )

    lead_status_counts = {
        "new": Lead.query.filter_by(status="new").count(),
        "contacted": Lead.query.filter_by(status="contacted").count(),
        "enrolled": Lead.query.filter_by(status="enrolled").count(),
        "dropped": Lead.query.filter_by(status="dropped").count(),
    }

    lead_status_percentages = {
        key: round((value * 100.0 / total_leads), 1) if total_leads else 0
        for key, value in lead_status_counts.items()
    }

    return render_template(
        "admin/dashboard.html",
        total_leads=total_leads,
        total_students=total_students,
        total_enrollments=total_enrollments,
        total_blog_posts=total_blog_posts,
        recent_leads=recent_leads,
        recent_attempts=recent_attempts,
        recent_payments=recent_payments,
        total_revenue=total_revenue,
        total_pending_amount=total_pending_amount,
        lead_status_counts=lead_status_counts,
        lead_status_percentages=lead_status_percentages,
    )


@admin_bp.get("/leads")
def leads():
    status_filter = (request.args.get("status") or "").strip().lower()
    search_query = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = Lead.query

    if status_filter in LEAD_STATUSES:
        query = query.filter(Lead.status == status_filter)

    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Lead.first_name.ilike(pattern),
                Lead.last_name.ilike(pattern),
                Lead.phone.ilike(pattern),
                Lead.email.ilike(pattern),
            )
        )

    paginated_leads = query.order_by(Lead.submitted_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        "admin/leads.html",
        leads=paginated_leads,
        status_filter=status_filter,
        search_query=search_query,
    )


@admin_bp.get("/leads/new")
def new_lead():
    form = ManualLeadForm()
    return render_template("admin/lead_form.html", form=form, is_new=True, lead=None)


@admin_bp.post("/leads/new")
def create_lead():
    form = ManualLeadForm()
    if not form.validate_on_submit():
        return render_template("admin/lead_form.html", form=form, is_new=True, lead=None)

    lead = Lead(
        first_name=(form.first_name.data or "").strip(),
        last_name=(form.last_name.data or "").strip(),
        phone=(form.phone.data or "").strip(),
        email=((form.email.data or "").strip() or None),
        exam_interest=((form.exam_interest.data or "").strip() or None),
        preferred_mode=((form.preferred_mode.data or "").strip() or None),
        source_page=form.source_page.data,
        notes=(form.notes.data or "").strip() or None,
        status=form.status.data,
    )
    if lead.status == "contacted":
        lead.contacted_at = datetime.utcnow()

    db.session.add(lead)
    db.session.commit()

    flash("Lead created successfully.", "success")
    return redirect(url_for("admin.leads"))


@admin_bp.get("/leads/<int:lead_id>/edit")
def edit_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = ManualLeadForm(obj=lead)
    return render_template("admin/lead_form.html", form=form, is_new=False, lead=lead)


@admin_bp.post("/leads/<int:lead_id>/edit")
def update_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = ManualLeadForm()

    if not form.validate_on_submit():
        return render_template("admin/lead_form.html", form=form, is_new=False, lead=lead)

    previous_status = lead.status

    lead.first_name = (form.first_name.data or "").strip()
    lead.last_name = (form.last_name.data or "").strip()
    lead.phone = (form.phone.data or "").strip()
    lead.email = ((form.email.data or "").strip() or None)
    lead.exam_interest = ((form.exam_interest.data or "").strip() or None)
    lead.preferred_mode = ((form.preferred_mode.data or "").strip() or None)
    lead.source_page = form.source_page.data
    lead.notes = (form.notes.data or "").strip() or None
    lead.status = form.status.data

    if lead.status == "contacted" and lead.contacted_at is None:
        lead.contacted_at = datetime.utcnow()
    if previous_status != "enrolled" and lead.status == "enrolled":
        if lead.contacted_at is None:
            lead.contacted_at = datetime.utcnow()
        _sync_offline_enrollment_from_lead(lead)

    db.session.commit()
    flash("Lead updated successfully.", "success")
    return redirect(url_for("admin.leads"))


@admin_bp.post("/leads/<int:lead_id>/delete")
def delete_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()

    flash("Lead deleted.", "success")
    return redirect(url_for("admin.leads"))


@admin_bp.post("/leads/bulk-status")
def bulk_update_lead_status():
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        lead_ids = payload.get("lead_ids") or []
        new_status = (payload.get("new_status") or "").strip().lower()
    else:
        lead_ids = request.form.getlist("lead_ids")
        new_status = (request.form.get("new_status") or "").strip().lower()

    if new_status not in LEAD_STATUSES:
        return jsonify({"status": "error", "message": "Invalid status."}), 400

    normalized_ids = []
    for candidate in lead_ids:
        try:
            normalized_ids.append(int(candidate))
        except (TypeError, ValueError):
            continue

    if not normalized_ids:
        return jsonify({"status": "error", "message": "No leads selected."}), 400

    leads_to_update = Lead.query.filter(Lead.id.in_(normalized_ids)).all()
    updated_count = 0

    for lead in leads_to_update:
        if lead.status == "enrolled" and new_status != "enrolled":
            continue
        if lead.status != new_status:
            lead.status = new_status
            if new_status == "contacted" and lead.contacted_at is None:
                lead.contacted_at = datetime.utcnow()
            if new_status == "enrolled":
                if lead.contacted_at is None:
                    lead.contacted_at = datetime.utcnow()
                _sync_offline_enrollment_from_lead(lead)
            updated_count += 1

    db.session.commit()
    return jsonify({"status": "ok", "updated_count": updated_count})


@admin_bp.post("/leads/<int:lead_id>/status")
def update_lead_status(lead_id):
    status_value = (request.form.get("status") or "").strip().lower()
    if not status_value and request.is_json:
        payload = request.get_json(silent=True) or {}
        status_value = (payload.get("status") or "").strip().lower()

    if status_value not in LEAD_STATUSES:
        return jsonify({"status": "error", "message": "Invalid status."}), 400

    lead = Lead.query.get_or_404(lead_id)

    if lead.status == "enrolled" and status_value != "enrolled":
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Status is locked for enrolled lead.",
                    "new_status": lead.status,
                    "locked": True,
                }
            ),
            409,
        )

    if lead.status == status_value:
        return jsonify(
            {
                "status": "ok",
                "new_status": lead.status,
                "locked": lead.status == "enrolled",
            }
        )

    lead.status = status_value
    if status_value == "contacted":
        lead.contacted_at = datetime.utcnow()
    elif status_value == "enrolled":
        if lead.contacted_at is None:
            lead.contacted_at = datetime.utcnow()
        _sync_offline_enrollment_from_lead(lead)

    db.session.commit()
    return jsonify(
        {
            "status": "ok",
            "new_status": lead.status,
            "locked": lead.status == "enrolled",
        }
    )


@admin_bp.get("/leads/export")
def export_leads_csv():
    leads = Lead.query.order_by(Lead.submitted_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "First Name",
            "Last Name",
            "Phone",
            "Email",
            "Exam Interest",
            "Preferred Mode",
            "Source Page",
            "Status",
            "Submitted At",
            "Contacted At",
            "Notes",
        ]
    )

    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.first_name,
                lead.last_name,
                lead.phone,
                lead.email or "",
                lead.exam_interest or "",
                lead.preferred_mode or "",
                lead.source_page or "",
                lead.status,
                _format_datetime(lead.submitted_at),
                _format_datetime(lead.contacted_at),
                lead.notes or "",
            ]
        )

    filename = f"CL_Ahmedabad_Leads_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_bp.get("/students")
def students():
    search_query = (request.args.get("q") or "").strip()
    exam_filter = (request.args.get("exam") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = User.query.filter(User.role == "student")

    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.email.ilike(pattern),
                User.phone.ilike(pattern),
            )
        )

    if exam_filter:
        query = query.filter(User.enrolled_exam == exam_filter)

    paginated_students = query.order_by(User.created_at.desc()).paginate(page=page, per_page=25, error_out=False)

    return render_template(
        "admin/students.html",
        students=paginated_students,
        search_query=search_query,
        exam_filter=exam_filter,
    )


@admin_bp.get("/students/new")
def new_student():
    form = ManualStudentForm()
    return render_template("admin/student_form.html", form=form, is_new=True, user=None)


@admin_bp.post("/students/new")
def create_student():
    form = ManualStudentForm()

    if not form.validate_on_submit():
        return render_template("admin/student_form.html", form=form, is_new=True, user=None)

    if not (form.password.data or ""):
        form.password.errors.append("Password is required for new students.")
        return render_template("admin/student_form.html", form=form, is_new=True, user=None)

    email_value = (form.email.data or "").strip().lower()
    existing_user = User.query.filter(func.lower(User.email) == email_value).first()
    if existing_user:
        form.email.errors.append("Email already exists.")
        return render_template("admin/student_form.html", form=form, is_new=True, user=None)

    student = User(
        first_name=(form.first_name.data or "").strip(),
        last_name=(form.last_name.data or "").strip(),
        email=email_value,
        phone=(form.phone.data or "").strip(),
        role="student",
        is_active=bool(form.is_active.data),
        enrolled_exam=(form.enrolled_exam.data or None),
        preferred_mode=(form.preferred_mode.data or None),
        scholarship_pct=form.scholarship_pct.data,
    )
    student.set_password(form.password.data)

    db.session.add(student)
    db.session.commit()

    flash("Student account created successfully.", "success")
    return redirect(url_for("admin.students"))


@admin_bp.get("/students/<int:user_id>")
def student_detail(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()

    try:
        ensure_student_enrollments(student)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Admin enrollment sync failed for user %s: %s", student.id, exc)

    enrollments_query = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == student.id)
    )
    if student.enrolled_exam:
        enrollments_query = enrollments_query.filter(Course.exam_category == student.enrolled_exam)

    enrollments = enrollments_query.order_by(Enrollment.enrolled_at.desc()).all()
    attempts = (
        TestAttempt.query.filter_by(user_id=student.id)
        .order_by(TestAttempt.started_at.desc())
        .limit(10)
        .all()
    )
    payments = (
        db.session.query(Payment, TestSeries.name.label("test_series_name"))
        .outerjoin(TestSeries, TestSeries.id == Payment.test_series_id)
        .filter(Payment.user_id == student.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return render_template(
        "admin/student_detail.html",
        user=student,
        enrollments=enrollments,
        attempts=attempts,
        payments=payments,
    )


@admin_bp.get("/students/<int:user_id>/edit")
def edit_student(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()
    form = ManualStudentForm(obj=student)
    form.password.data = ""
    return render_template("admin/student_form.html", form=form, is_new=False, user=student)


@admin_bp.post("/students/<int:user_id>/edit")
def update_student(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()
    form = ManualStudentForm()

    if not form.validate_on_submit():
        return render_template("admin/student_form.html", form=form, is_new=False, user=student)

    email_value = (form.email.data or "").strip().lower()
    duplicate = User.query.filter(func.lower(User.email) == email_value, User.id != student.id).first()
    if duplicate:
        form.email.errors.append("Email already exists.")
        return render_template("admin/student_form.html", form=form, is_new=False, user=student)

    student.first_name = (form.first_name.data or "").strip()
    student.last_name = (form.last_name.data or "").strip()
    student.email = email_value
    student.phone = (form.phone.data or "").strip()
    student.enrolled_exam = form.enrolled_exam.data or None
    student.preferred_mode = form.preferred_mode.data or None
    student.scholarship_pct = form.scholarship_pct.data
    student.is_active = bool(form.is_active.data)

    if (form.password.data or "").strip():
        student.set_password(form.password.data)

    db.session.commit()
    flash("Student updated successfully.", "success")
    return redirect(url_for("admin.students"))


@admin_bp.post("/students/<int:user_id>/toggle-active")
def toggle_student_active(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()
    student.is_active = not bool(student.is_active)
    db.session.commit()

    if _is_ajax_request():
        return jsonify({"status": "ok", "is_active": student.is_active})

    flash("Student status updated successfully.", "success")
    return redirect(url_for("admin.student_detail", user_id=student.id))


@admin_bp.post("/students/<int:user_id>/assign-scholarship")
def assign_student_scholarship(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()
    payload = request.get_json(silent=True) or {}

    try:
        scholarship_pct = int(payload.get("scholarship_pct"))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid scholarship value."}), 400

    if scholarship_pct < 0 or scholarship_pct > 50:
        return jsonify({"status": "error", "message": "Scholarship must be between 0 and 50."}), 400

    student.scholarship_pct = scholarship_pct
    db.session.commit()
    return jsonify({"status": "ok"})


@admin_bp.get("/students/<int:user_id>/summary")
def student_summary(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()

    active_enrollments = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == student.id, Enrollment.status == "active")
        .order_by(Enrollment.enrolled_at.desc())
        .all()
    )

    enrollment_data = [
        {
            "id": enrollment.id,
            "course": enrollment.course.title if enrollment.course else "",
            "batch_name": enrollment.batch_name or "",
            "status": enrollment.status,
        }
        for enrollment in active_enrollments
    ]

    return jsonify(
        {
            "status": "ok",
            "student": {
                "id": student.id,
                "name": student.get_full_name(),
                "email": student.email,
                "enrolled_exam": student.enrolled_exam,
                "scholarship_pct": student.scholarship_pct,
            },
            "active_enrollments": enrollment_data,
        }
    )


@admin_bp.get("/students/export")
def export_students_csv():
    students = User.query.filter_by(role="student").order_by(User.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "First Name",
            "Last Name",
            "Email",
            "Phone",
            "Enrolled Exam",
            "Preferred Mode",
            "Scholarship %",
            "Is Active",
            "Created At",
        ]
    )

    for student in students:
        writer.writerow(
            [
                student.id,
                student.first_name,
                student.last_name,
                student.email,
                student.phone,
                student.enrolled_exam or "",
                student.preferred_mode or "",
                student.scholarship_pct if student.scholarship_pct is not None else "",
                "Yes" if student.is_active else "No",
                _format_datetime(student.created_at),
            ]
        )

    filename = f"CL_Ahmedabad_Students_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_bp.get("/enrollments")
def enrollments():
    page = request.args.get("page", 1, type=int)
    course_id = request.args.get("course_id", type=int)
    status_filter = (request.args.get("status") or "").strip().lower()
    user_id = request.args.get("user_id", type=int)

    query = (
        Enrollment.query.join(User, Enrollment.user_id == User.id)
        .join(Course, Enrollment.course_id == Course.id)
    )

    if course_id:
        query = query.filter(Enrollment.course_id == course_id)
    if user_id:
        query = query.filter(Enrollment.user_id == user_id)
    if status_filter in {"active", "completed", "paused"}:
        query = query.filter(Enrollment.status == status_filter)

    paginated_enrollments = query.order_by(Enrollment.enrolled_at.desc()).paginate(page=page, per_page=25, error_out=False)

    total_fee_collected = (
        db.session.query(func.coalesce(func.sum(Enrollment.fee_paid), 0))
        .filter(Enrollment.status == "active")
        .scalar()
        or 0
    )
    total_active_enrollments = Enrollment.query.filter_by(status="active").count()

    return render_template(
        "admin/enrollments.html",
        enrollments=paginated_enrollments,
        total_fee_collected=total_fee_collected,
        total_active_enrollments=total_active_enrollments,
        course_choices=_course_choices(active_only=False),
        status_filter=status_filter,
        course_filter=course_id,
        user_filter=user_id,
    )


@admin_bp.get("/enrollments/new")
def new_enrollment():
    form = ManualEnrollmentForm()
    _populate_enrollment_form_choices(form)
    return render_template("admin/enrollment_form.html", form=form, is_new=True, enrollment=None)


@admin_bp.post("/enrollments/new")
def create_enrollment():
    form = ManualEnrollmentForm()
    _populate_enrollment_form_choices(form)

    if not form.validate_on_submit():
        return render_template("admin/enrollment_form.html", form=form, is_new=True, enrollment=None)

    duplicate_active = Enrollment.query.filter_by(
        user_id=form.user_id.data,
        course_id=form.course_id.data,
        status="active",
    ).first()

    if duplicate_active:
        flash("Student already has an active enrollment in this course. Admin override applied.", "warning")

    enrollment = Enrollment(
        user_id=form.user_id.data,
        course_id=form.course_id.data,
        batch_name=(form.batch_name.data or "").strip() or None,
        fee_paid=form.fee_paid.data,
        scholarship_pct=form.scholarship_pct.data,
        status=form.status.data,
    )

    db.session.add(enrollment)
    db.session.commit()

    flash("Enrollment created successfully.", "success")
    return redirect(url_for("admin.enrollments"))


@admin_bp.get("/enrollments/<int:enrollment_id>/edit")
def edit_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    form = ManualEnrollmentForm(obj=enrollment)
    _populate_enrollment_form_choices(form)
    return render_template("admin/enrollment_form.html", form=form, is_new=False, enrollment=enrollment)


@admin_bp.post("/enrollments/<int:enrollment_id>/edit")
def update_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    form = ManualEnrollmentForm()
    _populate_enrollment_form_choices(form)

    if not form.validate_on_submit():
        return render_template("admin/enrollment_form.html", form=form, is_new=False, enrollment=enrollment)

    enrollment.user_id = form.user_id.data
    enrollment.course_id = form.course_id.data
    enrollment.batch_name = (form.batch_name.data or "").strip() or None
    enrollment.fee_paid = form.fee_paid.data
    enrollment.scholarship_pct = form.scholarship_pct.data
    enrollment.status = form.status.data

    db.session.commit()
    flash("Enrollment updated successfully.", "success")
    return redirect(url_for("admin.enrollments"))


@admin_bp.post("/enrollments/<int:enrollment_id>/delete")
def delete_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()

    flash("Enrollment deleted.", "success")
    return redirect(url_for("admin.enrollments"))


@admin_bp.get("/courses")
def courses():
    all_courses = Course.query.order_by(Course.display_order.asc(), Course.id.asc()).all()
    batch_counts = {
        course.id: BatchSchedule.query.filter_by(course_id=course.id).count()
        for course in all_courses
    }
    return render_template("admin/courses.html", courses=all_courses, batch_counts=batch_counts)


@admin_bp.get("/courses/new")
def new_course():
    form = CourseCreateForm()
    form.display_order.data = Course.query.count() + 1
    return render_template("admin/course_edit.html", form=form, course=None, is_new=True)


@admin_bp.post("/courses/new")
def create_course():
    form = CourseCreateForm()

    if not form.validate_on_submit():
        return render_template("admin/course_edit.html", form=form, course=None, is_new=True)

    slug_value = _normalized_slug(form.slug.data, fallback=form.title.data)
    duplicate = db.session.query(Course.id).filter(func.lower(Course.slug) == slug_value.lower()).first()
    if duplicate:
        form.slug.errors.append("A course with this slug already exists.")
        return render_template("admin/course_edit.html", form=form, course=None, is_new=True)

    course = Course()
    _apply_course_form_to_model(course, form, keep_slug=False)

    db.session.add(course)
    db.session.commit()

    flash(f"Course '{course.title}' created successfully.", "success")
    return redirect(url_for("admin.courses"))


@admin_bp.get("/courses/<int:course_id>/edit")
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseEditForm(obj=course)
    form.slug.data = course.slug
    form.exams_covered.data = ", ".join(course.exams_list)
    return render_template("admin/course_edit.html", form=form, course=course, is_new=False)


@admin_bp.post("/courses/<int:course_id>/edit")
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseEditForm()

    if not form.validate_on_submit():
        return render_template("admin/course_edit.html", form=form, course=course, is_new=False)

    _apply_course_form_to_model(course, form, keep_slug=True)
    db.session.commit()

    flash("Course updated successfully.", "success")
    return redirect(url_for("admin.courses"))


@admin_bp.post("/courses/<int:course_id>/delete")
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    active_enrollments_count = Enrollment.query.filter_by(course_id=course.id, status="active").count()
    if active_enrollments_count > 0:
        flash("Cannot delete a course with active enrollments. Deactivate it instead.", "warning")
        return redirect(url_for("admin.courses"))

    course.is_active = False
    db.session.commit()

    flash("Course deactivated.", "success")
    return redirect(url_for("admin.courses"))


@admin_bp.get("/courses/<int:course_id>/syllabus")
def course_syllabus_editor(course_id):
    course = Course.query.get_or_404(course_id)
    syllabus_data = course.syllabus_list
    return render_template("admin/course_syllabus.html", course=course, syllabus_data=syllabus_data)


@admin_bp.post("/courses/<int:course_id>/syllabus")
def save_course_syllabus(course_id):
    course = Course.query.get_or_404(course_id)
    payload = request.get_json(silent=True)

    if not isinstance(payload, list):
        return jsonify({"status": "error", "message": "Invalid syllabus data."}), 400

    cleaned = []
    for item in payload:
        if not isinstance(item, dict):
            return jsonify({"status": "error", "message": "Invalid syllabus structure."}), 400

        subject = (item.get("subject") or "").strip()
        topics = item.get("topics") or []

        if not subject or not isinstance(topics, list):
            return jsonify({"status": "error", "message": "Each subject requires a title and topics list."}), 400

        cleaned_topics = [str(topic).strip() for topic in topics if str(topic).strip()]
        cleaned.append({"subject": subject, "topics": cleaned_topics})

    course.syllabus_json = json.dumps(cleaned, ensure_ascii=False)
    db.session.commit()

    return jsonify({"status": "ok", "message": "Syllabus saved."})


@admin_bp.get("/courses/<int:course_id>/faqs")
def course_faq_editor(course_id):
    course = Course.query.get_or_404(course_id)
    faqs_data = course.faqs_list
    return render_template("admin/course_faqs.html", course=course, faqs_data=faqs_data)


@admin_bp.post("/courses/<int:course_id>/faqs")
def save_course_faqs(course_id):
    course = Course.query.get_or_404(course_id)
    payload = request.get_json(silent=True)

    if not isinstance(payload, list):
        return jsonify({"status": "error", "message": "Invalid FAQ data."}), 400

    cleaned = []
    for item in payload:
        if not isinstance(item, dict):
            return jsonify({"status": "error", "message": "Invalid FAQ structure."}), 400

        question = (item.get("question") or "").strip()
        answer = (item.get("answer") or "").strip()
        if not question or not answer:
            return jsonify({"status": "error", "message": "Each FAQ requires question and answer."}), 400

        cleaned.append({"question": question, "answer": answer})

    course.faqs_json = json.dumps(cleaned, ensure_ascii=False)
    db.session.commit()
    return jsonify({"status": "ok"})


@admin_bp.get("/faculty")
def faculty():
    faculty_list = Faculty.query.order_by(Faculty.display_order.asc(), Faculty.id.asc()).all()
    return render_template("admin/faculty.html", faculty_list=faculty_list)


@admin_bp.get("/faculty/new")
def new_faculty():
    form = FacultyForm()
    form.display_order.data = Faculty.query.count() + 1
    return render_template("admin/faculty_form.html", form=form, is_new=True, faculty=None)


@admin_bp.post("/faculty/new")
def create_faculty():
    form = FacultyForm()
    if not form.validate_on_submit():
        return render_template("admin/faculty_form.html", form=form, is_new=True, faculty=None)

    slug_value = _normalized_slug(form.slug.data, fallback=form.name.data)
    duplicate = db.session.query(Faculty.id).filter(func.lower(Faculty.slug) == slug_value.lower()).first()
    if duplicate:
        form.slug.errors.append("A faculty profile with this slug already exists.")
        return render_template("admin/faculty_form.html", form=form, is_new=True, faculty=None)

    faculty_obj = Faculty()
    _apply_faculty_form_to_model(faculty_obj, form)

    if form.photo_upload.data:
        try:
            faculty_obj.photo_url = save_uploaded_image(
                file_storage=form.photo_upload.data,
                folder="faculty",
                filename_prefix=faculty_obj.slug,
                size=(400, 400),
            )
        except ValueError as exc:
            form.photo_upload.errors.append(str(exc))
            return render_template("admin/faculty_form.html", form=form, is_new=True, faculty=None)

    db.session.add(faculty_obj)
    db.session.commit()

    flash("Faculty member created successfully.", "success")
    return redirect(url_for("admin.faculty"))


@admin_bp.get("/faculty/<int:faculty_id>/edit")
def edit_faculty(faculty_id):
    faculty_obj = Faculty.query.get_or_404(faculty_id)
    form = FacultyForm(obj=faculty_obj)
    form.subjects_input.data = ", ".join(faculty_obj.subjects_list)
    form.exam_tags_input.data = ", ".join(faculty_obj.exam_tags_list)
    form.achievements_input.data = "\n".join(faculty_obj.achievements_list)
    form.youtube_url.data = faculty_obj.video_intro_url or faculty_obj.youtube_url

    return render_template("admin/faculty_form.html", form=form, is_new=False, faculty=faculty_obj)


@admin_bp.post("/faculty/<int:faculty_id>/edit")
def update_faculty(faculty_id):
    faculty_obj = Faculty.query.get_or_404(faculty_id)
    form = FacultyForm()

    if not form.validate_on_submit():
        return render_template("admin/faculty_form.html", form=form, is_new=False, faculty=faculty_obj)

    slug_value = _normalized_slug(form.slug.data, fallback=form.name.data)
    duplicate = (
        db.session.query(Faculty.id)
        .filter(func.lower(Faculty.slug) == slug_value.lower(), Faculty.id != faculty_obj.id)
        .first()
    )
    if duplicate:
        form.slug.errors.append("A faculty profile with this slug already exists.")
        return render_template("admin/faculty_form.html", form=form, is_new=False, faculty=faculty_obj)

    previous_photo = faculty_obj.photo_url

    _apply_faculty_form_to_model(faculty_obj, form)

    if form.photo_upload.data:
        try:
            faculty_obj.photo_url = save_uploaded_image(
                file_storage=form.photo_upload.data,
                folder="faculty",
                filename_prefix=faculty_obj.slug,
                size=(400, 400),
            )
            if previous_photo and previous_photo != faculty_obj.photo_url:
                delete_image(previous_photo)
        except ValueError as exc:
            form.photo_upload.errors.append(str(exc))
            return render_template("admin/faculty_form.html", form=form, is_new=False, faculty=faculty_obj)

    db.session.commit()

    flash("Faculty updated successfully.", "success")
    return redirect(url_for("admin.faculty"))


@admin_bp.post("/faculty/<int:faculty_id>/delete")
def delete_faculty(faculty_id):
    faculty_obj = Faculty.query.get_or_404(faculty_id)

    assigned_batches = BatchSchedule.query.filter_by(faculty_id=faculty_obj.id, is_active=True).count()
    if assigned_batches > 0:
        flash("Cannot delete faculty assigned to active batches.", "warning")
        return redirect(url_for("admin.faculty"))

    if faculty_obj.photo_url:
        delete_image(faculty_obj.photo_url)

    faculty_obj.is_active = False
    db.session.commit()

    flash("Faculty profile deactivated.", "success")
    return redirect(url_for("admin.faculty"))


@admin_bp.post("/faculty/<int:faculty_id>/toggle-active")
def toggle_faculty_active(faculty_id):
    faculty_obj = Faculty.query.get_or_404(faculty_id)
    faculty_obj.is_active = not bool(faculty_obj.is_active)
    db.session.commit()
    return jsonify({"status": "ok", "is_active": faculty_obj.is_active})


@admin_bp.post("/faculty/reorder")
def reorder_faculty():
    payload = request.get_json(silent=True)
    if not isinstance(payload, list):
        return jsonify({"status": "error", "message": "Invalid payload."}), 400

    for item in payload:
        if not isinstance(item, dict):
            continue
        faculty_id = item.get("id")
        order = item.get("order")
        try:
            faculty_id = int(faculty_id)
            order = int(order)
        except (TypeError, ValueError):
            continue

        faculty_obj = Faculty.query.get(faculty_id)
        if faculty_obj:
            faculty_obj.display_order = order

    db.session.commit()
    return jsonify({"status": "ok"})


@admin_bp.get("/blog")
def blog_posts():
    category_filter = (request.args.get("category") or "").strip().lower()
    status_filter = (request.args.get("status") or "").strip().lower()
    page = request.args.get("page", 1, type=int)

    query = BlogPost.query

    if category_filter in BLOG_CATEGORIES:
        query = query.filter(BlogPost.category == category_filter)

    if status_filter == "published":
        query = query.filter(BlogPost.is_published.is_(True))
    elif status_filter == "draft":
        query = query.filter(BlogPost.is_published.is_(False))

    posts = query.order_by(BlogPost.published_at.desc(), BlogPost.updated_at.desc()).paginate(
        page=page,
        per_page=15,
        error_out=False,
    )

    return render_template(
        "admin/blog.html",
        posts=posts,
        category_filter=category_filter,
        status_filter=status_filter,
    )


@admin_bp.get("/blog/new")
def new_blog_post():
    form = BlogPostForm()
    return render_template("admin/blog_edit.html", form=form, is_new=True)


@admin_bp.post("/blog/new")
def create_blog_post():
    form = BlogPostForm()

    if not form.validate_on_submit():
        return render_template("admin/blog_edit.html", form=form, is_new=True)

    slug_value = (form.slug.data or "").strip()
    duplicate = db.session.query(BlogPost.id).filter(func.lower(BlogPost.slug) == slug_value.lower()).first()
    if duplicate:
        form.slug.errors.append("A post with this slug already exists.")
        return render_template("admin/blog_edit.html", form=form, is_new=True)

    post = BlogPost(
        title=(form.title.data or "").strip(),
        slug=slug_value,
        category=form.category.data,
        content=form.content.data or "",
        excerpt=form.excerpt.data,
        featured_image=form.featured_image.data,
        author_id=current_user.id,
        meta_title=form.meta_title.data,
        meta_description=form.meta_description.data,
        is_published=bool(form.is_published.data),
        published_at=datetime.utcnow() if form.is_published.data else None,
    )

    db.session.add(post)
    db.session.commit()

    flash("Blog post created.", "success")
    return redirect(url_for("admin.blog_posts"))


@admin_bp.get("/blog/<int:post_id>/edit")
def edit_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)
    return render_template("admin/blog_edit.html", form=form, post=post, is_new=False)


@admin_bp.post("/blog/<int:post_id>/edit")
def update_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm()

    if not form.validate_on_submit():
        return render_template("admin/blog_edit.html", form=form, post=post, is_new=False)

    slug_value = (form.slug.data or "").strip()
    duplicate = (
        db.session.query(BlogPost.id)
        .filter(func.lower(BlogPost.slug) == slug_value.lower(), BlogPost.id != post.id)
        .first()
    )
    if duplicate:
        form.slug.errors.append("A post with this slug already exists.")
        return render_template("admin/blog_edit.html", form=form, post=post, is_new=False)

    post.title = (form.title.data or "").strip()
    post.slug = slug_value
    post.category = form.category.data
    post.content = form.content.data or ""
    post.excerpt = form.excerpt.data
    post.featured_image = form.featured_image.data
    post.meta_title = form.meta_title.data
    post.meta_description = form.meta_description.data
    post.is_published = bool(form.is_published.data)

    if post.is_published and not post.published_at:
        post.published_at = datetime.utcnow()

    post.updated_at = datetime.utcnow()
    db.session.commit()

    flash("Blog post updated.", "success")
    return redirect(url_for("admin.blog_posts"))


@admin_bp.post("/blog/<int:post_id>/delete")
def delete_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash("Blog post deleted.", "success")
    return redirect(url_for("admin.blog_posts"))


@admin_bp.get("/results")
def results():
    results_list = Result.query.order_by(Result.display_order.asc(), Result.id.asc()).all()
    return render_template("admin/results.html", results=results_list)


@admin_bp.get("/results/new")
def new_result():
    form = ResultForm()
    form.display_order.data = Result.query.count() + 1
    return render_template("admin/result_form.html", form=form, is_new=True, result=None)


@admin_bp.post("/results/new")
def create_result():
    form = ResultForm()

    if not form.validate_on_submit():
        return render_template("admin/result_form.html", form=form, is_new=True, result=None)

    result = Result()
    _apply_result_form_to_model(result, form)

    if form.photo_upload.data:
        try:
            filename_prefix = _normalized_slug(result.student_name, fallback=f"result-{int(time.time())}")
            result.photo_url = save_uploaded_image(
                file_storage=form.photo_upload.data,
                folder="results",
                filename_prefix=filename_prefix,
                size=(400, 400),
            )
        except ValueError as exc:
            form.photo_upload.errors.append(str(exc))
            return render_template("admin/result_form.html", form=form, is_new=True, result=None)

    db.session.add(result)
    db.session.commit()

    flash("Result created successfully.", "success")
    return redirect(url_for("admin.results"))


@admin_bp.get("/results/<int:result_id>/edit")
def edit_result(result_id):
    result = Result.query.get_or_404(result_id)
    form = ResultForm(obj=result)
    return render_template("admin/result_form.html", form=form, is_new=False, result=result)


@admin_bp.post("/results/<int:result_id>/edit")
def update_result(result_id):
    result = Result.query.get_or_404(result_id)
    form = ResultForm()

    if not form.validate_on_submit():
        return render_template("admin/result_form.html", form=form, is_new=False, result=result)

    previous_photo = result.photo_url
    _apply_result_form_to_model(result, form)

    if form.photo_upload.data:
        try:
            filename_prefix = _normalized_slug(result.student_name, fallback=f"result-{result.id}")
            result.photo_url = save_uploaded_image(
                file_storage=form.photo_upload.data,
                folder="results",
                filename_prefix=filename_prefix,
                size=(400, 400),
            )
            if previous_photo and previous_photo != result.photo_url:
                delete_image(previous_photo)
        except ValueError as exc:
            form.photo_upload.errors.append(str(exc))
            return render_template("admin/result_form.html", form=form, is_new=False, result=result)

    db.session.commit()

    flash("Result updated successfully.", "success")
    return redirect(url_for("admin.results"))


@admin_bp.post("/results/<int:result_id>/delete")
def delete_result(result_id):
    result = Result.query.get_or_404(result_id)

    if result.photo_url:
        delete_image(result.photo_url)

    db.session.delete(result)
    db.session.commit()

    if _is_ajax_request():
        return jsonify({"status": "ok"})

    flash("Result deleted.", "success")
    return redirect(url_for("admin.results"))


@admin_bp.post("/results/<int:result_id>/toggle-active")
def toggle_result_active(result_id):
    result = Result.query.get_or_404(result_id)
    result.is_active = not bool(result.is_active)
    db.session.commit()
    return jsonify({"status": "ok", "is_active": result.is_active})


@admin_bp.get("/test-series")
def test_series():
    series_list = TestSeries.query.order_by(TestSeries.exam.asc(), TestSeries.name.asc()).all()
    return render_template("admin/test_series.html", series_list=series_list)


@admin_bp.get("/test-series/new")
def new_test_series():
    form = TestSeriesForm()
    return render_template("admin/test_series_form.html", form=form, is_new=True, series=None)


@admin_bp.post("/test-series/new")
def create_test_series():
    form = TestSeriesForm()
    if not form.validate_on_submit():
        return render_template("admin/test_series_form.html", form=form, is_new=True, series=None)

    series = TestSeries()
    _apply_test_series_form_to_model(series, form)

    db.session.add(series)
    db.session.commit()

    flash("Test series created successfully.", "success")
    return redirect(url_for("admin.test_series"))


@admin_bp.get("/test-series/<int:series_id>/edit")
def edit_test_series(series_id):
    series = TestSeries.query.get_or_404(series_id)
    form = TestSeriesForm(obj=series)
    return render_template("admin/test_series_form.html", form=form, is_new=False, series=series)


@admin_bp.post("/test-series/<int:series_id>/edit")
def update_test_series(series_id):
    series = TestSeries.query.get_or_404(series_id)
    form = TestSeriesForm()

    if not form.validate_on_submit():
        return render_template("admin/test_series_form.html", form=form, is_new=False, series=series)

    _apply_test_series_form_to_model(series, form)
    db.session.commit()

    flash("Test series updated successfully.", "success")
    return redirect(url_for("admin.test_series"))


@admin_bp.post("/test-series/<int:series_id>/delete")
def delete_test_series(series_id):
    series = TestSeries.query.get_or_404(series_id)
    attempts_count = TestAttempt.query.filter_by(test_id=series.id).count()

    if attempts_count > 0:
        series.is_active = False
        db.session.commit()
        flash("Cannot delete series with existing attempts. Deactivate it instead.", "warning")
        return redirect(url_for("admin.test_series"))

    db.session.delete(series)
    db.session.commit()
    flash("Test series deleted.", "success")
    return redirect(url_for("admin.test_series"))


@admin_bp.post("/test-series/<int:series_id>/toggle-active")
def toggle_test_series_active(series_id):
    series = TestSeries.query.get_or_404(series_id)
    series.is_active = not bool(series.is_active)
    db.session.commit()
    return jsonify({"status": "ok", "is_active": series.is_active})


@admin_bp.get("/scholarship-questions")
def scholarship_questions():
    questions = ScholarshipQuestion.query.order_by(
        ScholarshipQuestion.display_order.asc(),
        ScholarshipQuestion.id.asc(),
    ).all()
    return render_template(
        "admin/scholarship_questions.html",
        questions=questions,
        count=len(questions),
    )


@admin_bp.get("/scholarship-questions/new")
def new_scholarship_question():
    form = ScholarshipQuestionForm()
    form.display_order.data = ScholarshipQuestion.query.count() + 1
    return render_template("admin/scholarship_question_form.html", form=form, is_new=True, question=None)


@admin_bp.post("/scholarship-questions/new")
def create_scholarship_question():
    form = ScholarshipQuestionForm()
    if not form.validate_on_submit():
        return render_template("admin/scholarship_question_form.html", form=form, is_new=True, question=None)

    question = ScholarshipQuestion(
        question_text=(form.question_text.data or "").strip(),
        option_a=(form.option_a.data or "").strip(),
        option_b=(form.option_b.data or "").strip(),
        option_c=(form.option_c.data or "").strip(),
        option_d=(form.option_d.data or "").strip(),
        correct_answer=form.correct_answer.data,
        subject=form.subject.data,
        display_order=int(form.display_order.data or 0),
    )

    db.session.add(question)
    db.session.commit()

    total = ScholarshipQuestion.query.count()
    flash(f"Question added. Total questions: {total}.", "success")
    return redirect(url_for("admin.scholarship_questions"))


@admin_bp.get("/scholarship-questions/<int:question_id>/edit")
def edit_scholarship_question(question_id):
    question = ScholarshipQuestion.query.get_or_404(question_id)
    form = ScholarshipQuestionForm(obj=question)
    return render_template("admin/scholarship_question_form.html", form=form, is_new=False, question=question)


@admin_bp.post("/scholarship-questions/<int:question_id>/edit")
def update_scholarship_question(question_id):
    question = ScholarshipQuestion.query.get_or_404(question_id)
    form = ScholarshipQuestionForm()

    if not form.validate_on_submit():
        return render_template("admin/scholarship_question_form.html", form=form, is_new=False, question=question)

    question.question_text = (form.question_text.data or "").strip()
    question.option_a = (form.option_a.data or "").strip()
    question.option_b = (form.option_b.data or "").strip()
    question.option_c = (form.option_c.data or "").strip()
    question.option_d = (form.option_d.data or "").strip()
    question.correct_answer = form.correct_answer.data
    question.subject = form.subject.data
    question.display_order = int(form.display_order.data or 0)

    db.session.commit()
    flash("Question updated successfully.", "success")
    return redirect(url_for("admin.scholarship_questions"))


@admin_bp.post("/scholarship-questions/<int:question_id>/delete")
def delete_scholarship_question(question_id):
    question = ScholarshipQuestion.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()

    total = ScholarshipQuestion.query.count()
    flash(f"Question deleted. Total questions: {total}.", "success")
    return redirect(url_for("admin.scholarship_questions"))


@admin_bp.get("/free-resources")
def free_resources():
    resources = FreeResource.query.order_by(FreeResource.category.asc(), FreeResource.display_order.asc(), FreeResource.id.asc()).all()
    category_counts = Counter(resource.category for resource in resources)
    return render_template("admin/free_resources.html", resources=resources, category_counts=category_counts)


@admin_bp.get("/free-resources/new")
def new_free_resource():
    form = FreeResourceForm()
    form.display_order.data = FreeResource.query.count() + 1
    return render_template("admin/free_resource_form.html", form=form, is_new=True, resource=None)


@admin_bp.post("/free-resources/new")
def create_free_resource():
    form = FreeResourceForm()
    if not form.validate_on_submit():
        return render_template("admin/free_resource_form.html", form=form, is_new=True, resource=None)

    resource = FreeResource()
    try:
        _apply_free_resource_form_to_model(resource, form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return render_template("admin/free_resource_form.html", form=form, is_new=True, resource=None)

    db.session.add(resource)
    db.session.commit()

    flash("Resource created successfully.", "success")
    return redirect(url_for("admin.free_resources"))


@admin_bp.get("/free-resources/<int:resource_id>/edit")
def edit_free_resource(resource_id):
    resource = FreeResource.query.get_or_404(resource_id)
    form = FreeResourceForm(obj=resource)
    form.url.data = resource.url
    if resource.local_file_path:
        form.delivery_mode.data = "upload"
        form.external_url.data = ""
    else:
        form.delivery_mode.data = "link"
        form.external_url.data = (resource.external_url or resource.url or "").strip()
    return render_template("admin/free_resource_form.html", form=form, is_new=False, resource=resource)


@admin_bp.post("/free-resources/<int:resource_id>/edit")
def update_free_resource(resource_id):
    resource = FreeResource.query.get_or_404(resource_id)
    form = FreeResourceForm()

    if not form.validate_on_submit():
        return render_template("admin/free_resource_form.html", form=form, is_new=False, resource=resource)

    try:
        _apply_free_resource_form_to_model(resource, form, existing_url=resource.url)
    except ValueError as exc:
        flash(str(exc), "danger")
        return render_template("admin/free_resource_form.html", form=form, is_new=False, resource=resource)

    db.session.commit()

    flash("Resource updated successfully.", "success")
    return redirect(url_for("admin.free_resources"))


@admin_bp.post("/free-resources/<int:resource_id>/delete")
def delete_free_resource(resource_id):
    resource = FreeResource.query.get_or_404(resource_id)
    _delete_free_resource_file_if_exists(resource.url)
    db.session.delete(resource)
    db.session.commit()

    flash("Resource deleted.", "success")
    return redirect(url_for("admin.free_resources"))


@admin_bp.post("/free-resources/<int:resource_id>/toggle-active")
def toggle_free_resource_active(resource_id):
    resource = FreeResource.query.get_or_404(resource_id)
    resource.is_active = not bool(resource.is_active)
    db.session.commit()
    return jsonify({"status": "ok", "is_active": resource.is_active})


@admin_bp.get("/announcements")
def announcements():
    now = datetime.utcnow()
    announcement_list = Announcement.query.order_by(Announcement.created_at.desc(), Announcement.id.desc()).all()
    return render_template("admin/announcements.html", announcements=announcement_list, now=now)


@admin_bp.get("/announcements/new")
def new_announcement():
    form = AnnouncementForm()
    return render_template("admin/announcement_form.html", form=form, is_new=True, announcement=None)


@admin_bp.post("/announcements/new")
def create_announcement():
    form = AnnouncementForm()
    if not form.validate_on_submit():
        return render_template("admin/announcement_form.html", form=form, is_new=True, announcement=None)

    announcement = Announcement(created_by=current_user.id)
    _apply_announcement_form_to_model(announcement, form)

    db.session.add(announcement)
    db.session.commit()

    flash("Announcement created successfully.", "success")
    return redirect(url_for("admin.announcements"))


@admin_bp.get("/announcements/<int:announcement_id>/edit")
def edit_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm(obj=announcement)
    return render_template("admin/announcement_form.html", form=form, is_new=False, announcement=announcement)


@admin_bp.post("/announcements/<int:announcement_id>/edit")
def update_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm()

    if not form.validate_on_submit():
        return render_template("admin/announcement_form.html", form=form, is_new=False, announcement=announcement)

    _apply_announcement_form_to_model(announcement, form)
    db.session.commit()

    flash("Announcement updated successfully.", "success")
    return redirect(url_for("admin.announcements"))


@admin_bp.post("/announcements/<int:announcement_id>/delete")
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()

    flash("Announcement deleted.", "success")
    return redirect(url_for("admin.announcements"))


@admin_bp.post("/announcements/<int:announcement_id>/toggle-active")
def toggle_announcement_active(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not bool(announcement.is_active)
    db.session.commit()

    return jsonify({"status": "ok", "is_active": announcement.is_active})


@admin_bp.get("/testimonials")
def testimonials():
    testimonial_list = Testimonial.query.order_by(Testimonial.display_order.asc(), Testimonial.id.asc()).all()
    grouped_counts = Counter(item.display_location for item in testimonial_list)
    return render_template("admin/testimonials.html", testimonials=testimonial_list, grouped_counts=grouped_counts)


@admin_bp.get("/testimonials/new")
def new_testimonial():
    form = TestimonialForm()
    form.display_order.data = Testimonial.query.count() + 1
    return render_template("admin/testimonial_form.html", form=form, is_new=True, testimonial=None)


@admin_bp.post("/testimonials/new")
def create_testimonial():
    form = TestimonialForm()
    if not form.validate_on_submit():
        return render_template("admin/testimonial_form.html", form=form, is_new=True, testimonial=None)

    testimonial_obj = Testimonial()
    _apply_testimonial_form_to_model(testimonial_obj, form)

    if form.photo_upload.data:
        try:
            photo_prefix = _normalized_slug(testimonial_obj.student_name, fallback=f"testimonial-{int(time.time())}")
            testimonial_obj.student_photo_url = save_uploaded_image(
                file_storage=form.photo_upload.data,
                folder="testimonials",
                filename_prefix=photo_prefix,
                size=(400, 400),
            )
        except ValueError as exc:
            form.photo_upload.errors.append(str(exc))
            return render_template("admin/testimonial_form.html", form=form, is_new=True, testimonial=None)

    db.session.add(testimonial_obj)
    db.session.commit()

    flash("Testimonial created successfully.", "success")
    return redirect(url_for("admin.testimonials"))


@admin_bp.get("/testimonials/<int:testimonial_id>/edit")
def edit_testimonial(testimonial_id):
    testimonial_obj = Testimonial.query.get_or_404(testimonial_id)
    form = TestimonialForm(obj=testimonial_obj)
    if testimonial_obj.rating:
        form.rating.data = str(testimonial_obj.rating)
    return render_template("admin/testimonial_form.html", form=form, is_new=False, testimonial=testimonial_obj)


@admin_bp.post("/testimonials/<int:testimonial_id>/edit")
def update_testimonial(testimonial_id):
    testimonial_obj = Testimonial.query.get_or_404(testimonial_id)
    form = TestimonialForm()

    if not form.validate_on_submit():
        return render_template("admin/testimonial_form.html", form=form, is_new=False, testimonial=testimonial_obj)

    previous_photo = testimonial_obj.student_photo_url
    _apply_testimonial_form_to_model(testimonial_obj, form)

    if form.photo_upload.data:
        try:
            photo_prefix = _normalized_slug(testimonial_obj.student_name, fallback=f"testimonial-{testimonial_obj.id}")
            testimonial_obj.student_photo_url = save_uploaded_image(
                file_storage=form.photo_upload.data,
                folder="testimonials",
                filename_prefix=photo_prefix,
                size=(400, 400),
            )
            if previous_photo and previous_photo != testimonial_obj.student_photo_url:
                delete_image(previous_photo)
        except ValueError as exc:
            form.photo_upload.errors.append(str(exc))
            return render_template("admin/testimonial_form.html", form=form, is_new=False, testimonial=testimonial_obj)

    db.session.commit()

    flash("Testimonial updated successfully.", "success")
    return redirect(url_for("admin.testimonials"))


@admin_bp.post("/testimonials/<int:testimonial_id>/delete")
def delete_testimonial(testimonial_id):
    testimonial_obj = Testimonial.query.get_or_404(testimonial_id)

    if testimonial_obj.student_photo_url:
        delete_image(testimonial_obj.student_photo_url)

    db.session.delete(testimonial_obj)
    db.session.commit()

    flash("Testimonial deleted.", "success")
    return redirect(url_for("admin.testimonials"))


@admin_bp.post("/testimonials/<int:testimonial_id>/toggle-active")
def toggle_testimonial_active(testimonial_id):
    testimonial_obj = Testimonial.query.get_or_404(testimonial_id)
    testimonial_obj.is_active = not bool(testimonial_obj.is_active)
    db.session.commit()
    return jsonify({"status": "ok", "is_active": testimonial_obj.is_active})


@admin_bp.post("/testimonials/reorder")
def reorder_testimonials():
    payload = request.get_json(silent=True)
    if not isinstance(payload, list):
        return jsonify({"status": "error", "message": "Invalid payload."}), 400

    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            testimonial_id = int(item.get("id"))
            order = int(item.get("order"))
        except (TypeError, ValueError):
            continue

        testimonial_obj = Testimonial.query.get(testimonial_id)
        if testimonial_obj:
            testimonial_obj.display_order = order

    db.session.commit()
    return jsonify({"status": "ok"})


@admin_bp.get("/batches")
def batches():
    course_filter = request.args.get("course_id", type=int)

    query = BatchSchedule.query.join(Course, BatchSchedule.course_id == Course.id)
    if course_filter:
        query = query.filter(BatchSchedule.course_id == course_filter)

    batch_list = query.order_by(BatchSchedule.start_date.desc(), BatchSchedule.id.desc()).all()
    courses_filter = Course.query.order_by(Course.title.asc()).all()

    return render_template(
        "admin/batches.html",
        batch_list=batch_list,
        courses_filter=courses_filter,
        course_filter=course_filter,
    )


@admin_bp.get("/batches/new")
def new_batch():
    form = BatchScheduleForm()
    _populate_batch_form_choices(form)
    return render_template("admin/batch_form.html", form=form, is_new=True, batch=None)


@admin_bp.post("/batches/new")
def create_batch():
    form = BatchScheduleForm()
    _populate_batch_form_choices(form)

    if not form.validate_on_submit():
        return render_template("admin/batch_form.html", form=form, is_new=True, batch=None)

    batch = BatchSchedule()
    _apply_batch_form_to_model(batch, form)

    db.session.add(batch)
    db.session.commit()

    flash("Batch created successfully.", "success")
    return redirect(url_for("admin.batches"))


@admin_bp.get("/batches/<int:batch_id>/edit")
def edit_batch(batch_id):
    batch = BatchSchedule.query.get_or_404(batch_id)
    form = BatchScheduleForm(obj=batch)
    _populate_batch_form_choices(form)
    if batch.faculty_id is None:
        form.faculty_id.data = 0
    return render_template("admin/batch_form.html", form=form, is_new=False, batch=batch)


@admin_bp.post("/batches/<int:batch_id>/edit")
def update_batch(batch_id):
    batch = BatchSchedule.query.get_or_404(batch_id)
    form = BatchScheduleForm()
    _populate_batch_form_choices(form)

    if not form.validate_on_submit():
        return render_template("admin/batch_form.html", form=form, is_new=False, batch=batch)

    _apply_batch_form_to_model(batch, form)
    db.session.commit()

    flash("Batch updated successfully.", "success")
    return redirect(url_for("admin.batches"))


@admin_bp.post("/batches/<int:batch_id>/delete")
def delete_batch(batch_id):
    batch = BatchSchedule.query.get_or_404(batch_id)

    referenced_enrollments = Enrollment.query.filter_by(
        course_id=batch.course_id,
        batch_name=batch.batch_name,
        status="active",
    ).count()

    if referenced_enrollments > 0:
        batch.is_active = False
        db.session.commit()
        flash("Batch has active enrollments, so it was deactivated instead of deleted.", "warning")
        return redirect(url_for("admin.batches"))

    db.session.delete(batch)
    db.session.commit()

    flash("Batch deleted successfully.", "success")
    return redirect(url_for("admin.batches"))


@admin_bp.post("/batches/<int:batch_id>/update-seats")
def update_batch_seats(batch_id):
    batch = BatchSchedule.query.get_or_404(batch_id)
    payload = request.get_json(silent=True) or {}

    try:
        seats_filled = int(payload.get("seats_filled"))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid seat count."}), 400

    if seats_filled < 0:
        return jsonify({"status": "error", "message": "Seats filled cannot be negative."}), 400

    batch.seats_filled = seats_filled
    db.session.commit()

    return jsonify({"status": "ok", "seats_available": batch.seats_available})


@admin_bp.get("/payments")
def payments():
    status_filter = (request.args.get("status") or "").strip().lower()
    page = request.args.get("page", 1, type=int)

    query = (
        db.session.query(
            Payment,
            User.email.label("user_email"),
            TestSeries.name.label("test_series_name"),
        )
        .outerjoin(User, User.id == Payment.user_id)
        .outerjoin(TestSeries, TestSeries.id == Payment.test_series_id)
    )

    if status_filter in PAYMENT_STATUSES:
        query = query.filter(Payment.status == status_filter)

    paginated_payments = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    total_revenue = (
        db.session.query(func.coalesce(func.sum(Payment.amount_inr), 0))
        .filter(Payment.status == "success")
        .scalar()
        or 0
    )
    successful_count = Payment.query.filter_by(status="success").count()
    pending_failed_count = Payment.query.filter(Payment.status.in_(["pending", "failed"])).count()

    return render_template(
        "admin/payments.html",
        payments=paginated_payments,
        total_revenue=total_revenue,
        successful_count=successful_count,
        pending_failed_count=pending_failed_count,
        status_filter=status_filter,
    )


@admin_bp.get("/payments/new")
def new_payment():
    form = ManualPaymentForm()
    _populate_payment_form_choices(form)
    return render_template("admin/payment_form.html", form=form)


@admin_bp.post("/payments/new")
def create_payment():
    form = ManualPaymentForm()
    _populate_payment_form_choices(form)

    if not form.validate_on_submit():
        return render_template("admin/payment_form.html", form=form)

    test_series_id = int(form.test_series_id.data or 0) or None
    payment_method = form.payment_method.data
    reference_number = (form.reference_number.data or "").strip() or None
    notes = (form.notes.data or "").strip()

    metadata_lines = [f"method={payment_method}"]
    if reference_number:
        metadata_lines.append(f"reference={reference_number}")
    if notes:
        metadata_lines.append(notes)

    payment = Payment(
        user_id=form.user_id.data,
        test_series_id=test_series_id,
        amount_inr=int(form.amount_inr.data),
        status="success",
        payment_method=payment_method,
        reference_number=reference_number,
        notes=" | ".join(metadata_lines),
        razorpay_order_id=f"MANUAL_{int(time.time())}",
        razorpay_payment_id=reference_number,
    )

    db.session.add(payment)
    db.session.commit()

    flash("Manual payment recorded successfully.", "success")
    return redirect(url_for("admin.payments"))


@admin_bp.get("/settings")
def settings():
    form = SiteSettingsForm()
    _load_site_settings_into_form(form)
    courses = Course.query.order_by(Course.display_order.asc(), Course.id.asc()).all()
    saved = request.args.get("saved") == "1"

    return render_template("admin/settings.html", form=form, courses=courses, saved=saved)


@admin_bp.post("/settings")
def update_settings():
    form = SiteSettingsForm()

    if not form.validate_on_submit():
        courses = Course.query.order_by(Course.display_order.asc(), Course.id.asc()).all()
        return render_template("admin/settings.html", form=form, courses=courses, saved=False)

    _save_site_settings_from_form(form)

    courses = Course.query.order_by(Course.display_order.asc(), Course.id.asc()).all()
    for course in courses:
        meta_title_key = f"course_meta_title_{course.id}"
        meta_desc_key = f"course_meta_description_{course.id}"

        course.meta_title = (request.form.get(meta_title_key) or "").strip() or None
        course.meta_description = (request.form.get(meta_desc_key) or "").strip() or None

    db.session.commit()

    flash("Settings saved. Changes are live on the website.", "success")
    return redirect(url_for("admin.settings", saved=1))


def _shift_month(year_value, month_value, delta):
    month_index = month_value + delta
    year = year_value

    while month_index <= 0:
        month_index += 12
        year -= 1

    while month_index > 12:
        month_index -= 12
        year += 1

    return year, month_index


@admin_bp.get("/analytics")
def analytics():
    now = datetime.utcnow()

    thirty_day_start = (now - timedelta(days=29)).date()
    lead_rows = (
        db.session.query(func.date(Lead.submitted_at), func.count(Lead.id))
        .filter(Lead.submitted_at >= datetime.combine(thirty_day_start, datetime.min.time()))
        .group_by(func.date(Lead.submitted_at))
        .all()
    )
    lead_map = {str(row[0]): int(row[1]) for row in lead_rows}

    leads_per_day = []
    for offset in range(30):
        current_date = thirty_day_start + timedelta(days=offset)
        key = current_date.isoformat()
        leads_per_day.append({"date": key, "count": lead_map.get(key, 0)})

    conversion_counts = {status: 0 for status in ["new", "contacted", "enrolled", "dropped"]}
    for status, count in db.session.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all():
        if status in conversion_counts:
            conversion_counts[status] = int(count)

    source_breakdown = [
        {"source": source or "unknown", "count": int(count)}
        for source, count in db.session.query(Lead.source_page, func.count(Lead.id)).group_by(Lead.source_page).all()
    ]
    source_breakdown.sort(key=lambda item: item["count"], reverse=True)

    exam_breakdown = [
        {"exam": exam or "unknown", "count": int(count)}
        for exam, count in db.session.query(Lead.exam_interest, func.count(Lead.id)).group_by(Lead.exam_interest).all()
    ]
    exam_breakdown.sort(key=lambda item: item["count"], reverse=True)

    current_year, current_month = now.year, now.month
    month_keys = []
    for idx in range(5, -1, -1):
        year_value, month_value = _shift_month(current_year, current_month, -idx)
        month_keys.append((year_value, month_value))

    start_year, start_month = month_keys[0]
    revenue_start = datetime(start_year, start_month, 1)

    payments = Payment.query.filter(Payment.status == "success", Payment.created_at >= revenue_start).all()
    revenue_map = defaultdict(int)
    for payment in payments:
        if not payment.created_at:
            continue
        key = payment.created_at.strftime("%Y-%m")
        revenue_map[key] += int(payment.amount_inr or 0)

    revenue_data = []
    for year_value, month_value in month_keys:
        month_key = f"{year_value:04d}-{month_value:02d}"
        label = datetime(year_value, month_value, 1).strftime("%b %Y")
        revenue_data.append({"month": label, "amount": revenue_map.get(month_key, 0)})

    series_revenue_rows = (
        db.session.query(Payment.test_series_id, func.coalesce(func.sum(Payment.amount_inr), 0))
        .filter(Payment.status == "success", Payment.test_series_id.isnot(None))
        .group_by(Payment.test_series_id)
        .all()
    )
    series_revenue_map = {int(test_series_id): int(amount) for test_series_id, amount in series_revenue_rows if test_series_id}

    top_series_rows = (
        db.session.query(
            TestSeries.id,
            TestSeries.name,
            TestSeries.exam,
            TestSeries.is_free,
            func.count(TestAttempt.id).label("attempt_count"),
        )
        .outerjoin(TestAttempt, TestAttempt.test_id == TestSeries.id)
        .group_by(TestSeries.id, TestSeries.name, TestSeries.exam, TestSeries.is_free)
        .order_by(func.count(TestAttempt.id).desc(), TestSeries.name.asc())
        .limit(10)
        .all()
    )

    top_series_data = [
        {
            "id": row.id,
            "name": row.name,
            "exam": row.exam,
            "attempts": int(row.attempt_count or 0),
            "is_free": bool(row.is_free),
            "revenue": 0 if row.is_free else int(series_revenue_map.get(int(row.id), 0)),
        }
        for row in top_series_rows
    ]

    week_start_date = (now - timedelta(days=now.weekday())).date()
    first_week_date = week_start_date - timedelta(weeks=7)

    student_rows = User.query.filter(
        User.role == "student",
        User.created_at >= datetime.combine(first_week_date, datetime.min.time()),
    ).all()

    student_week_map = defaultdict(int)
    for student in student_rows:
        if not student.created_at:
            continue
        student_date = student.created_at.date()
        student_week_start = student_date - timedelta(days=student_date.weekday())
        student_week_map[student_week_start.isoformat()] += 1

    students_per_week = []
    for idx in range(8):
        current_week = first_week_date + timedelta(weeks=idx)
        key = current_week.isoformat()
        label = current_week.strftime("%d %b")
        students_per_week.append({"week": label, "count": student_week_map.get(key, 0)})

    month_start = datetime(now.year, now.month, 1)
    this_week_start = datetime.combine(week_start_date, datetime.min.time())

    summary_stats = {
        "leads_this_month": Lead.query.filter(Lead.submitted_at >= month_start).count(),
        "revenue_this_month": (
            db.session.query(func.coalesce(func.sum(Payment.amount_inr), 0))
            .filter(Payment.status == "success", Payment.created_at >= month_start)
            .scalar()
            or 0
        ),
        "new_students_this_week": User.query.filter(User.role == "student", User.created_at >= this_week_start).count(),
        "test_attempts_this_week": TestAttempt.query.filter(TestAttempt.started_at >= this_week_start).count(),
    }

    return render_template(
        "admin/analytics.html",
        summary_stats=summary_stats,
        leads_per_day=leads_per_day,
        conversion_counts=conversion_counts,
        source_breakdown=source_breakdown,
        exam_breakdown=exam_breakdown,
        revenue_data=revenue_data,
        top_series_data=top_series_data,
        students_per_week=students_per_week,
    )
