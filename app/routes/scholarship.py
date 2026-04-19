import random
import re
import secrets
from datetime import datetime

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user
from sqlalchemy import func

from app.extensions import db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.exam_session import ExamSession
from app.models.lead import Lead
from app.models.scholarship_question import ScholarshipQuestion
from app.models.user import User
from app.services.email_service import send_scholarship_result
from app.services.scholarship_enrollment import calculate_scholarship_amounts
from app.services.scholarship import calculate_scholarship_band, generate_certificate_pdf
from app.services.whatsapp import generate_whatsapp_link


scholarship_bp = Blueprint("scholarship", __name__)

EXAM_INTEREST_MAP = {
    "CAT/MBA Entrance": "CAT",
    "CLAT/AILET/Law": "CLAT",
    "IPMAT/BBA": "IPMAT",
    "GMAT/GRE": "GMAT",
    "CUET": "CUET",
    "Class XI–XII Mathematics": "Boards",
}

SCHOLARSHIP_BANDS = [
    {"score_range": "90% and above", "scholarship_pct": 50, "band_name": "Gold Scholar"},
    {"score_range": "75% to 89.99%", "scholarship_pct": 35, "band_name": "Silver Scholar"},
    {"score_range": "60% to 74.99%", "scholarship_pct": 25, "band_name": "Merit Scholar"},
    {"score_range": "45% to 59.99%", "scholarship_pct": 15, "band_name": "Achiever Scholar"},
    {"score_range": "Below 45%", "scholarship_pct": 10, "band_name": "Participation Benefit"},
]


def _is_valid_indian_mobile(phone):
    cleaned_phone = re.sub(r"\D", "", phone or "")
    return bool(re.fullmatch(r"[6-9]\d{9}", cleaned_phone))


def _normalize_question_ids(raw_question_ids):
    if not raw_question_ids:
        return []

    candidate_ids = raw_question_ids
    if isinstance(raw_question_ids, str):
        candidate_ids = re.findall(r"\d+", raw_question_ids)

    normalized_ids = []
    seen_ids = set()

    for candidate in candidate_ids:
        try:
            question_id = int(candidate)
        except (TypeError, ValueError):
            continue

        if question_id <= 0 or question_id in seen_ids:
            continue

        seen_ids.add(question_id)
        normalized_ids.append(question_id)

    return normalized_ids


def _normalize_option_token(raw_value):
    token = str(raw_value or "").strip().lower()
    if not token:
        return ""

    compact_token = re.sub(r"[^a-z0-9]+", "", token)
    if compact_token in {"a", "b", "c", "d"}:
        return compact_token

    numeric_map = {"1": "a", "2": "b", "3": "c", "4": "d"}
    if compact_token in numeric_map:
        return numeric_map[compact_token]

    roman_map = {"i": "a", "ii": "b", "iii": "c", "iv": "d"}
    if compact_token in roman_map:
        return roman_map[compact_token]

    for prefix in ("option", "choice", "answer", "ans"):
        suffix = compact_token[len(prefix):]
        if compact_token.startswith(prefix) and suffix in {"a", "b", "c", "d"}:
            return suffix

    return ""


def _normalize_option_text(raw_value):
    return re.sub(r"\s+", " ", str(raw_value or "").strip().lower())


def _normalize_answer_choice(raw_value, question=None):
    normalized_token = _normalize_option_token(raw_value)
    if normalized_token:
        return normalized_token

    if question is None:
        return ""

    normalized_value = _normalize_option_text(raw_value)
    if not normalized_value:
        return ""

    option_lookup = {
        _normalize_option_text(question.option_a): "a",
        _normalize_option_text(question.option_b): "b",
        _normalize_option_text(question.option_c): "c",
        _normalize_option_text(question.option_d): "d",
    }
    return option_lookup.get(normalized_value, "")


def _has_active_scholarship_attempt():
    return bool(_normalize_question_ids(session.get("scholarship_question_ids") or []))


def _is_scholarship_retake_requested():
    return bool(session.get("scholarship_force_test"))


def _start_scholarship_attempt_session(force_retake=False):
    session["scholarship_force_test"] = bool(force_retake)
    session.pop("scholarship_result", None)
    session.pop("scholarship_question_ids", None)


def _band_from_scholarship_pct(scholarship_pct):
    pct = int(scholarship_pct or 10)
    if pct >= 50:
        return "Gold Scholar"
    if pct >= 35:
        return "Silver Scholar"
    if pct >= 25:
        return "Merit Scholar"
    if pct >= 15:
        return "Achiever Scholar"
    return "Participation Benefit"


def _reconstruct_result_from_scholarship(scholarship_pct):
    pct = int(scholarship_pct or 10)
    if pct >= 50:
        score = 18
    elif pct >= 35:
        score = 15
    elif pct >= 25:
        score = 12
    elif pct >= 15:
        score = 9
    else:
        score = 8

    result = calculate_scholarship_band(score=score, max_score=20)
    result["score"] = score
    result["max_score"] = 20
    result["scholarship_pct"] = pct
    result["band_name"] = _band_from_scholarship_pct(pct)
    return result


def _build_course_offers_for_user(user):
    scholarship_pct = int(user.scholarship_pct or 0)

    courses = (
        Course.query.filter(Course.is_active.is_(True))
        .order_by(Course.display_order.asc(), Course.id.asc())
        .all()
    )

    enrollment_map = {}
    user_enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    for enrollment in user_enrollments:
        if enrollment.course_id is not None:
            enrollment_map[enrollment.course_id] = max(
                int(enrollment.fee_paid or 0),
                int(enrollment_map.get(enrollment.course_id, 0)),
            )

    offers = []
    for course in courses:
        fee_data = calculate_scholarship_amounts(course, scholarship_pct)
        if int(fee_data["original_fee"] or 0) <= 0:
            continue

        paid_amount = int(enrollment_map.get(course.id, 0))
        offers.append(
            {
                "id": course.id,
                "title": course.title,
                "slug": course.slug,
                "exam_category": course.exam_category,
                "fee_min": int(course.fee_min or 0),
                "fee_max": int(course.fee_max or 0),
                "original_fee": int(fee_data["original_fee"] or 0),
                "discount": int(fee_data["discount"] or 0),
                "payable": int(fee_data["payable"] or 0),
                "scholarship_pct": int(fee_data["scholarship_pct"] or 0),
                "fee_paid": paid_amount,
                "is_paid": paid_amount >= int(fee_data["payable"] or 0),
            }
        )

    return offers


@scholarship_bp.get("")
@scholarship_bp.get("/")
def info():
    whatsapp_link = generate_whatsapp_link(
        custom_message="Hi, I have a query about the CL Ahmedabad scholarship test."
    )
    return render_template(
        "scholarship/info.html",
        bands=SCHOLARSHIP_BANDS,
        whatsapp_link=whatsapp_link,
    )


@scholarship_bp.post("/register")
def register():
    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    phone = re.sub(r"\D", "", request.form.get("phone") or "")
    email = (request.form.get("email") or "").strip().lower()
    exam_interest = (request.form.get("exam_interest") or "").strip()

    if not all([first_name, last_name, phone, email, exam_interest]):
        flash("Please fill all required fields to continue.", "danger")
        return redirect(url_for("scholarship.info"))

    if not _is_valid_indian_mobile(phone):
        flash("Please enter a valid 10 digit Indian mobile number.", "danger")
        return redirect(url_for("scholarship.info"))

    user = User.query.filter(func.lower(User.email) == email).first()

    lead = Lead(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        exam_interest=exam_interest,
        preferred_mode=None,
        source_page="scholarship",
        status="new",
    )
    db.session.add(lead)

    if user:
        if not user.is_active:
            user.is_active = True
        db.session.commit()
        login_user(user)
        _start_scholarship_attempt_session(force_retake=False)
        return redirect(url_for("scholarship.test"))

    temp_password = secrets.token_urlsafe(9)
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        role="student",
        is_active=True,
        enrolled_exam=EXAM_INTEREST_MAP.get(exam_interest),
    )
    new_user.set_password(temp_password)

    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    _start_scholarship_attempt_session(force_retake=False)
    return redirect(url_for("scholarship.test"))


@scholarship_bp.get("/test")
@login_required
def test():
    if current_user.scholarship_pct is not None:
        session.pop("scholarship_force_test", None)
        return redirect(url_for("scholarship.result"))

    old_sessions = ExamSession.query.filter_by(
        user_id=current_user.id,
        is_submitted=False,
        exam_type="scholarship",
    ).all()
    for old_session in old_sessions:
        old_session.is_submitted = True
        if old_session.submitted_at is None:
            old_session.submitted_at = datetime.utcnow()
    db.session.flush()

    user_agent = (request.user_agent.string or "")[:500]
    exam_session = ExamSession(
        user_id=current_user.id,
        session_token=secrets.token_hex(32),
        exam_type="scholarship",
        ip_address=request.remote_addr,
        user_agent=user_agent,
    )
    db.session.add(exam_session)
    db.session.commit()

    session["exam_session_token"] = exam_session.session_token
    session["exam_start_time"] = datetime.utcnow().isoformat()

    question_pool = ScholarshipQuestion.query.order_by(
        ScholarshipQuestion.display_order.asc(),
        ScholarshipQuestion.id.asc(),
    ).all()

    if not question_pool:
        flash("Scholarship test is currently unavailable. Please try again shortly.", "warning")
        return redirect(url_for("scholarship.info"))

    selected_questions = random.sample(question_pool, min(20, len(question_pool)))
    session["scholarship_question_ids"] = [question.id for question in selected_questions]
    session.pop("scholarship_force_test", None)

    server_time_remaining = exam_session.seconds_remaining()

    return render_template(
        "scholarship/test.html",
        questions=selected_questions,
        server_time_remaining=server_time_remaining,
        exam_session_token=exam_session.session_token,
    )


@scholarship_bp.post("/submit")
@login_required
def submit():
    submitted_token = request.form.get("exam_session_token")
    stored_token = session.get("exam_session_token")

    if not submitted_token or not stored_token or submitted_token != stored_token:
        flash("Invalid exam session. Please contact support.", "danger")
        return redirect(url_for("scholarship.info"))

    exam_session = ExamSession.query.filter_by(
        session_token=stored_token,
        user_id=current_user.id,
        is_submitted=False,
        exam_type="scholarship",
    ).first()

    if not exam_session:
        flash("Exam session not found or already submitted.", "danger")
        return redirect(url_for("scholarship.info"))

    if exam_session.is_expired():
        current_app.logger.warning(
            "Late submission by user %s. Session started: %s. Submitted at: %s",
            current_user.id,
            exam_session.started_at,
            datetime.utcnow(),
        )

    exam_session.is_submitted = True
    exam_session.submitted_at = datetime.utcnow()

    raw_question_ids = session.get("scholarship_question_ids") or []
    question_ids = _normalize_question_ids(raw_question_ids)

    if not question_ids:
        db.session.commit()
        session.pop("scholarship_question_ids", None)
        session.pop("exam_session_token", None)
        session.pop("exam_start_time", None)
        session.pop("scholarship_force_test", None)
        flash("Session expired. Please try again.", "danger")
        return redirect(url_for("scholarship.info"))

    questions = ScholarshipQuestion.query.filter(ScholarshipQuestion.id.in_(question_ids)).all()
    if not questions:
        db.session.commit()
        session.pop("scholarship_question_ids", None)
        session.pop("exam_session_token", None)
        session.pop("exam_start_time", None)
        session.pop("scholarship_force_test", None)
        flash("We could not evaluate your test right now. Please attempt it again.", "danger")
        return redirect(url_for("scholarship.info"))

    question_map = {question.id: question for question in questions}
    available_question_ids = [question_id for question_id in question_ids if question_id in question_map]

    if not available_question_ids:
        db.session.commit()
        session.pop("scholarship_question_ids", None)
        session.pop("exam_session_token", None)
        session.pop("exam_start_time", None)
        session.pop("scholarship_force_test", None)
        flash("We could not evaluate your test right now. Please attempt it again.", "danger")
        return redirect(url_for("scholarship.info"))

    correct_count = 0
    for question_id in available_question_ids:
        question = question_map[question_id]
        submitted_answer = _normalize_answer_choice(request.form.get(f"answer_{question_id}"), question)
        expected_answer = _normalize_answer_choice(question.correct_answer, question)

        if submitted_answer and expected_answer and submitted_answer == expected_answer:
            correct_count += 1

    total_questions = len(available_question_ids)
    result_data = calculate_scholarship_band(score=correct_count, max_score=total_questions)
    current_user.scholarship_pct = result_data["scholarship_pct"]

    auto_submitted = (request.form.get("auto_submitted") or "").strip().lower() == "true"
    db.session.commit()

    session["scholarship_result"] = {
        "score": correct_count,
        "max_score": total_questions,
        "percentage": result_data["percentage"],
        "scholarship_pct": result_data["scholarship_pct"],
        "band_name": result_data["band_name"],
        "message": result_data["message"],
        "auto_submitted": auto_submitted,
    }
    session.pop("scholarship_force_test", None)
    session.pop("scholarship_question_ids", None)
    session.pop("exam_session_token", None)
    session.pop("exam_start_time", None)

    try:
        send_scholarship_result(current_user, result_data["scholarship_pct"])
    except Exception as exc:
        current_app.logger.error("Failed to send scholarship result email: %s", exc)

    return redirect(url_for("scholarship.result"))


@scholarship_bp.post("/report-violation")
@login_required
def report_violation():
    data = request.get_json(silent=True) or {}
    violation_type = data.get("violation_type", "unknown")

    stored_token = session.get("exam_session_token")
    if not stored_token:
        return jsonify({"status": "error", "message": "No active session"}), 400

    exam_session = ExamSession.query.filter_by(
        session_token=stored_token,
        user_id=current_user.id,
        is_submitted=False,
        exam_type="scholarship",
    ).first()

    if not exam_session:
        return jsonify({"status": "error"}), 400

    exam_session.violation_count += 1
    db.session.commit()

    current_app.logger.warning(
        "Exam violation by user %s (%s): %s. Total violations: %s",
        current_user.id,
        current_user.email,
        violation_type,
        exam_session.violation_count,
    )

    max_violations = 3
    remaining = max_violations - exam_session.violation_count

    return jsonify(
        {
            "status": "ok",
            "violation_count": exam_session.violation_count,
            "remaining_warnings": max(0, remaining),
            "auto_submit": exam_session.violation_count >= max_violations,
        }
    )


@scholarship_bp.get("/result")
@login_required
def result():
    result_data = session.get("scholarship_result")

    if not result_data and current_user.scholarship_pct is None:
        return redirect(url_for("scholarship.test"))

    if not result_data and current_user.scholarship_pct is not None:
        result_data = _reconstruct_result_from_scholarship(current_user.scholarship_pct)

    course_offers = _build_course_offers_for_user(current_user)
    selected_course_id = None

    latest_paid_enrollment = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id.isnot(None),
            Enrollment.fee_paid.isnot(None),
            Enrollment.fee_paid > 0,
            Course.is_active.is_(True),
        )
        .order_by(Enrollment.enrolled_at.desc(), Enrollment.id.desc())
        .first()
    )
    if latest_paid_enrollment and latest_paid_enrollment.course_id is not None:
        selected_course_id = int(latest_paid_enrollment.course_id)

    requested_course_id = request.args.get("course_id", type=int)
    valid_offer_ids = {int(offer["id"]) for offer in course_offers}
    if requested_course_id in valid_offer_ids:
        selected_course_id = requested_course_id
    elif selected_course_id not in valid_offer_ids:
        selected_course_id = None

    if selected_course_id is None:
        paid_offer = next((offer for offer in course_offers if int(offer.get("fee_paid") or 0) > 0), None)
        if paid_offer:
            selected_course_id = int(paid_offer["id"])

    offline_support_link = generate_whatsapp_link(
        custom_message=(
            "Hi, I want to complete admission using my scholarship. "
            "Please share offline payment and enrollment steps."
        )
    )

    return render_template(
        "scholarship/result.html",
        result=result_data,
        user=current_user,
        course_offers=course_offers,
        selected_course_id=selected_course_id,
        offline_support_link=offline_support_link,
    )


@scholarship_bp.get("/certificate")
@login_required
def certificate():
    if current_user.scholarship_pct is None:
        return redirect(url_for("scholarship.test"))

    band_name = _band_from_scholarship_pct(current_user.scholarship_pct)
    pdf_bytes = generate_certificate_pdf(current_user, current_user.scholarship_pct, band_name)

    if not pdf_bytes:
        flash("Certificate could not be generated right now. Please try again in a few minutes.", "danger")
        return redirect(url_for("scholarship.result"))

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="CL_Scholarship_Certificate_{current_user.first_name}.pdf"'
            )
        },
    )
