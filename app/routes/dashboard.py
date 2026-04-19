import json
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import desc

from app.extensions import db
from app.forms import ProfileUpdateForm
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.free_resource import FreeResource
from app.models.test_series import TestAttempt
from app.services.enrollment_service import ensure_student_enrollments


dashboard_bp = Blueprint("dashboard", __name__)


EXAM_CATEGORY_MAP = {
    "CAT": "cat",
    "CLAT": "clat",
    "IPMAT": "ipmat",
    "GMAT": "gmat",
    "CUET": "cuet",
    "Boards": "general",
}

EXAM_TO_RESOURCE_CATEGORY = {
    "CAT": "cat",
    "CLAT": "clat",
    "IPMAT": "ipmat",
    "GMAT": "gmat",
    "CUET": "cuet",
    "Boards": "general",
}

RESOURCE_TYPE_TO_SECTION = {
    "pdf": "papers",
    "mock_test": "mock",
    "link": "online",
    "video": "online",
}

RESOURCE_TYPE_TO_LABEL = {
    "pdf": "PDF",
    "mock_test": "Mock Test",
    "link": "Link",
    "video": "Video",
}


def _normalize_exam(raw_exam):
    exam_text = " ".join(str(raw_exam or "").split()).strip()
    exam_text = exam_text.replace("–", "-").replace("—", "-")
    if not exam_text:
        return None

    alias_map = {
        "CAT": "CAT",
        "CAT/MBA ENTRANCE": "CAT",
        "MBA": "CAT",
        "CLAT": "CLAT",
        "CLAT/AILET/LAW": "CLAT",
        "AILET": "CLAT",
        "LAW": "CLAT",
        "IPMAT": "IPMAT",
        "IPMAT/BBA": "IPMAT",
        "BBA": "IPMAT",
        "GMAT": "GMAT",
        "GMAT/GRE": "GMAT",
        "GRE": "GMAT",
        "CUET": "CUET",
        "BOARDS": "Boards",
        "CLASS XI-XII MATHEMATICS": "Boards",
        "CLASS XI-XII MATHS": "Boards",
        "GENERAL": "Boards",
    }

    upper_exam = exam_text.upper()
    if upper_exam in alias_map:
        return alias_map[upper_exam]

    if "CLAT" in upper_exam or "AILET" in upper_exam:
        return "CLAT"
    if "IPMAT" in upper_exam or "BBA" in upper_exam:
        return "IPMAT"
    if "GMAT" in upper_exam or "GRE" in upper_exam:
        return "GMAT"
    if "CAT" in upper_exam:
        return "CAT"
    if "CUET" in upper_exam:
        return "CUET"
    if "BOARD" in upper_exam or "MATH" in upper_exam:
        return "Boards"

    return exam_text


def login_required_check():
    if not current_user.is_authenticated:
        next_url = request.full_path if request.query_string else request.path
        return redirect(url_for("auth.login", next=next_url))
    return None


dashboard_bp.before_request(login_required_check)


def _current_date_label():
    return datetime.now().strftime("%d %B %Y")


def _resource_catalog():
    return [
        {
            "title": "CAT Previous Year Papers",
            "description": "Download solved and unsolved CAT papers for quantitative and verbal revision.",
            "type": "PDF",
            "exam_tag": "CAT",
            "url": "/free-resources",
            "year": "2024",
            "section": "papers",
        },
        {
            "title": "CLAT Previous Year Papers",
            "description": "Practice CLAT legal reasoning and reading comprehension from past papers.",
            "type": "PDF",
            "exam_tag": "CLAT",
            "url": "/free-resources",
            "year": "2025",
            "section": "papers",
        },
        {
            "title": "IPMAT Previous Year Papers",
            "description": "Build speed for IPMAT quant and verbal through previous year paper sets.",
            "type": "PDF",
            "exam_tag": "IPMAT",
            "url": "/free-resources",
            "year": "2024",
            "section": "papers",
        },
        {
            "title": "CUET Previous Year Papers",
            "description": "Access CUET previous year practice sets and section-wise question banks.",
            "type": "PDF",
            "exam_tag": "CUET",
            "url": "/free-resources",
            "year": "2024",
            "section": "papers",
        },
        {
            "title": "Official CAT Website",
            "description": "Official updates, notifications, and test details from the CAT authorities.",
            "type": "Link",
            "exam_tag": "CAT",
            "url": "https://iimcat.ac.in",
            "section": "online",
        },
        {
            "title": "Official CLAT Website",
            "description": "Consortium updates, counselling announcements, and CLAT notices.",
            "type": "Link",
            "exam_tag": "CLAT",
            "url": "https://consortiumofnlus.ac.in",
            "section": "online",
        },
        {
            "title": "Official IPMAT Website",
            "description": "Get official information about IIM Indore IPMAT admissions.",
            "type": "Link",
            "exam_tag": "IPMAT",
            "url": "https://www.iimidr.ac.in",
            "section": "online",
        },
        {
            "title": "Official CUET Portal",
            "description": "Visit the official CUET page for exam notices and updates.",
            "type": "Link",
            "exam_tag": "CUET",
            "url": "https://cuet.nta.nic.in",
            "section": "online",
        },
        {
            "title": "Official GMAT Website",
            "description": "Explore GMAT Focus Edition details and official test resources.",
            "type": "Link",
            "exam_tag": "GMAT",
            "url": "https://www.mba.com/exams/gmat-exam",
            "section": "online",
        },
        {
            "title": "CL National Study Material Hub",
            "description": "Curated preparation support from Career Launcher national learning resources.",
            "type": "Link",
            "exam_tag": "ALL",
            "url": "https://clahmedabad.onrender.com",
            "section": "online",
        },
        {
            "title": "CAT Free Mock Test",
            "description": "Attempt a free CAT mock and review your detailed score analysis.",
            "type": "Link",
            "exam_tag": "CAT",
            "url": "/test-series/cat",
            "section": "mock",
        },
        {
            "title": "CLAT Free Mock Test",
            "description": "Take a free CLAT mock and evaluate section-wise readiness.",
            "type": "Link",
            "exam_tag": "CLAT",
            "url": "/test-series/clat",
            "section": "mock",
        },
        {
            "title": "IPMAT Free Mock Test",
            "description": "Practice with a free IPMAT mock test under timed conditions.",
            "type": "Link",
            "exam_tag": "IPMAT",
            "url": "/test-series/ipmat",
            "section": "mock",
        },
        {
            "title": "CUET Free Mock Test",
            "description": "Evaluate your CUET readiness with topic-level mock diagnostics.",
            "type": "Link",
            "exam_tag": "CUET",
            "url": "/test-series/cuet",
            "section": "mock",
        },
        {
            "title": "GMAT Quant and Verbal Strategy Session",
            "description": "Recorded orientation on GMAT preparation strategy and sectional planning.",
            "type": "Video",
            "exam_tag": "GMAT",
            "url": "https://clahmedabad.onrender.com/video-gallery/",
            "section": "online",
        },
    ]


def _resources_for_exam(exam):
    all_resources = _resource_catalog()
    normalized_exam = _normalize_exam(exam)
    if not normalized_exam:
        return all_resources

    return [
        item
        for item in all_resources
        if item.get("exam_tag") in {"ALL", normalized_exam}
    ]


def _resource_from_model(resource):
    resource_type = (resource.resource_type or "").strip().lower()
    section = RESOURCE_TYPE_TO_SECTION.get(resource_type)
    if not section:
        return None

    category = (resource.category or "general").strip().lower()
    exam_tag = "ALL" if category == "general" else category.upper()

    if resource.is_gated:
        resource_url = url_for("main.free_resources")
    else:
        resource_url = url_for("main.access_free_resource", resource_id=resource.id)

    return {
        "title": resource.title,
        "description": resource.description or "",
        "type": RESOURCE_TYPE_TO_LABEL.get(resource_type, "Resource"),
        "exam_tag": exam_tag,
        "url": resource_url,
        "year": str(resource.year) if resource.year else "",
        "section": section,
    }


def _resources_from_database(exam):
    normalized_exam = _normalize_exam(exam)

    query = FreeResource.query.filter(FreeResource.is_active.is_(True))
    if normalized_exam:
        target_category = EXAM_TO_RESOURCE_CATEGORY.get(normalized_exam)
        allowed_categories = {"general"}
        if target_category:
            allowed_categories.add(target_category)
        query = query.filter(FreeResource.category.in_(sorted(allowed_categories)))

    records = query.order_by(FreeResource.display_order.asc(), FreeResource.id.asc()).all()

    items = []
    for record in records:
        mapped = _resource_from_model(record)
        if mapped:
            items.append(mapped)

    return items


def _merge_resources(primary_resources, fallback_resources):
    merged = list(primary_resources)
    seen_keys = {
        (item.get("section"), (item.get("title") or "").strip().lower())
        for item in merged
    }
    present_sections = {item.get("section") for item in merged}

    for section_name in ("papers", "mock", "online"):
        if section_name in present_sections:
            continue

        for item in fallback_resources:
            if item.get("section") != section_name:
                continue

            key = (section_name, (item.get("title") or "").strip().lower())
            if key in seen_keys:
                continue

            merged.append(item)
            seen_keys.add(key)

    return merged


@dashboard_bp.get("")
@dashboard_bp.get("/")
def overview():
    try:
        ensure_student_enrollments(current_user)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Dashboard enrollment sync failed for user %s: %s", current_user.id, exc)

    enrollments_query = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id, Enrollment.status == "active")
    )
    if current_user.enrolled_exam:
        enrollments_query = enrollments_query.filter(Course.exam_category == current_user.enrolled_exam)

    enrollments = enrollments_query.order_by(desc(Enrollment.enrolled_at)).all()

    recent_attempts = (
        TestAttempt.query.filter_by(user_id=current_user.id)
        .order_by(desc(TestAttempt.started_at))
        .limit(5)
        .all()
    )
    attempt_count = TestAttempt.query.filter_by(user_id=current_user.id).count()

    return render_template(
        "dashboard/overview.html",
        enrollments=enrollments,
        recent_attempts=recent_attempts,
        attempt_count=attempt_count,
        scholarship_pct=current_user.scholarship_pct,
        user=current_user,
        current_date=_current_date_label(),
    )


@dashboard_bp.get("/courses")
def courses():
    try:
        ensure_student_enrollments(current_user)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Dashboard courses enrollment sync failed for user %s: %s", current_user.id, exc)

    enrollments_query = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id)
    )
    if current_user.enrolled_exam:
        enrollments_query = enrollments_query.filter(Course.exam_category == current_user.enrolled_exam)

    enrollments = enrollments_query.order_by(desc(Enrollment.enrolled_at)).all()

    return render_template(
        "dashboard/courses.html",
        enrollments=enrollments,
        current_date=_current_date_label(),
    )


@dashboard_bp.get("/tests")
def tests():
    attempts = (
        TestAttempt.query.filter_by(user_id=current_user.id)
        .order_by(desc(TestAttempt.started_at))
        .all()
    )

    for attempt in attempts:
        parsed_sections = {}
        if attempt.section_scores:
            try:
                section_data = json.loads(attempt.section_scores)
                if isinstance(section_data, dict):
                    parsed_sections = section_data
            except (TypeError, json.JSONDecodeError):
                parsed_sections = {}
        attempt.section_scores_dict = parsed_sections

    completed_attempts = [
        attempt
        for attempt in attempts
        if attempt.score is not None and attempt.max_score not in (None, 0)
    ]

    average_score_pct = 0.0
    if completed_attempts:
        average_score_pct = round(
            sum((attempt.score / attempt.max_score) * 100 for attempt in completed_attempts)
            / len(completed_attempts),
            1,
        )

    percentiles = [attempt.percentile for attempt in attempts if attempt.percentile is not None]
    best_percentile = round(max(percentiles), 2) if percentiles else None

    total_time_spent = sum((attempt.time_taken_mins or 0) for attempt in attempts)

    stats = {
        "total_attempts": len(attempts),
        "average_score_pct": average_score_pct,
        "best_percentile": best_percentile,
        "total_time_spent": total_time_spent,
    }

    return render_template(
        "dashboard/tests.html",
        attempts=attempts,
        stats=stats,
        current_date=_current_date_label(),
    )


@dashboard_bp.get("/resources")
def resources():
    enrolled_exam = _normalize_exam(current_user.enrolled_exam)
    db_resources = _resources_from_database(enrolled_exam)
    fallback_resources = _resources_for_exam(enrolled_exam)
    resources = _merge_resources(db_resources, fallback_resources) if db_resources else fallback_resources

    blog_posts = []
    category = EXAM_CATEGORY_MAP.get(enrolled_exam)
    if category:
        blog_posts = (
            BlogPost.query.filter_by(is_published=True, category=category)
            .order_by(desc(BlogPost.published_at), desc(BlogPost.updated_at))
            .limit(3)
            .all()
        )
    else:
        blog_posts = (
            BlogPost.query.filter_by(is_published=True)
            .order_by(desc(BlogPost.published_at), desc(BlogPost.updated_at))
            .limit(3)
            .all()
        )

    return render_template(
        "dashboard/resources.html",
        resources=resources,
        enrolled_exam=enrolled_exam,
        related_posts=blog_posts,
        current_date=_current_date_label(),
    )


@dashboard_bp.get("/profile")
def profile():
    form = ProfileUpdateForm()
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.phone.data = current_user.phone
    form.enrolled_exam.data = current_user.enrolled_exam or ""
    form.preferred_mode.data = current_user.preferred_mode or ""

    return render_template(
        "dashboard/profile.html",
        form=form,
        user=current_user,
        current_date=_current_date_label(),
    )


@dashboard_bp.post("/profile")
def profile_update():
    form = ProfileUpdateForm()

    if not form.validate_on_submit():
        return render_template(
            "dashboard/profile.html",
            form=form,
            user=current_user,
            current_date=_current_date_label(),
        )

    if form.new_password.data:
        if not current_user.check_password(form.current_password.data or ""):
            form.current_password.errors.append("Current password is incorrect.")
            return render_template(
                "dashboard/profile.html",
                form=form,
                user=current_user,
                current_date=_current_date_label(),
            )

    current_user.first_name = (form.first_name.data or "").strip()
    current_user.last_name = (form.last_name.data or "").strip()
    current_user.phone = (form.phone.data or "").strip()
    current_user.enrolled_exam = form.enrolled_exam.data or None
    current_user.preferred_mode = form.preferred_mode.data or None

    if form.new_password.data:
        current_user.set_password(form.new_password.data)

    db.session.commit()
    flash("Your profile has been updated successfully.", "success")

    return redirect(url_for("dashboard.profile"))
