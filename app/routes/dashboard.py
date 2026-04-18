import json
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import desc

from app.extensions import db
from app.forms import ProfileUpdateForm
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.test_series import TestAttempt


dashboard_bp = Blueprint("dashboard", __name__)


EXAM_CATEGORY_MAP = {
    "CAT": "cat",
    "CLAT": "clat",
    "IPMAT": "ipmat",
    "GMAT": "gmat",
    "CUET": "cuet",
    "Boards": "general",
}


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
            "url": "https://www.careerlauncher.com",
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
            "url": "https://www.careerlauncher.com/video-gallery/",
            "section": "online",
        },
    ]


def _resources_for_exam(exam):
    all_resources = _resource_catalog()
    if not exam:
        return all_resources
    return [
        item
        for item in all_resources
        if item.get("exam_tag") in {"ALL", exam}
    ]


@dashboard_bp.get("")
@dashboard_bp.get("/")
def overview():
    enrollments = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id, Enrollment.status == "active")
        .order_by(desc(Enrollment.enrolled_at))
        .all()
    )

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
    enrollments = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id)
        .order_by(desc(Enrollment.enrolled_at))
        .all()
    )

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
    enrolled_exam = current_user.enrolled_exam
    resources = _resources_for_exam(enrolled_exam)

    blog_posts = []
    category = EXAM_CATEGORY_MAP.get(enrolled_exam)
    if category:
        blog_posts = (
            BlogPost.query.filter_by(is_published=True, category=category)
            .order_by(desc(BlogPost.published_at), desc(BlogPost.updated_at))
            .limit(3)
            .all()
        )
    elif not enrolled_exam:
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
