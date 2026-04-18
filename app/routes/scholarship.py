import random
import re
import secrets

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user
from sqlalchemy import func

from app.extensions import db
from app.models.lead import Lead
from app.models.scholarship_question import ScholarshipQuestion
from app.models.user import User
from app.services.email_service import send_scholarship_result
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
    return redirect(url_for("scholarship.test"))


@scholarship_bp.get("/test")
@login_required
def test():
    if current_user.scholarship_pct is not None:
        return redirect(url_for("scholarship.result"))

    question_pool = ScholarshipQuestion.query.order_by(
        ScholarshipQuestion.display_order.asc(),
        ScholarshipQuestion.id.asc(),
    ).all()

    if len(question_pool) < 20:
        flash("Scholarship test is currently unavailable. Please try again shortly.", "warning")
        return redirect(url_for("scholarship.info"))

    selected_questions = random.sample(question_pool, 20)
    session["scholarship_question_ids"] = [question.id for question in selected_questions]

    return render_template("scholarship/test.html", questions=selected_questions)


@scholarship_bp.post("/submit")
@login_required
def submit():
    question_ids = session.get("scholarship_question_ids") or []
    if not question_ids:
        return redirect(url_for("scholarship.test"))

    questions = ScholarshipQuestion.query.filter(ScholarshipQuestion.id.in_(question_ids)).all()
    question_map = {question.id: question for question in questions}

    correct_count = 0
    for question_id in question_ids:
        submitted_answer = (request.form.get(f"answer_{question_id}") or "").strip().lower()
        question = question_map.get(question_id)
        if question and submitted_answer == (question.correct_answer or "").strip().lower():
            correct_count += 1

    result_data = calculate_scholarship_band(score=correct_count, max_score=20)
    current_user.scholarship_pct = result_data["scholarship_pct"]
    db.session.commit()

    session["scholarship_result"] = {
        "score": correct_count,
        "max_score": 20,
        "percentage": result_data["percentage"],
        "scholarship_pct": result_data["scholarship_pct"],
        "band_name": result_data["band_name"],
        "message": result_data["message"],
    }
    session.pop("scholarship_question_ids", None)

    try:
        send_scholarship_result(current_user, result_data["scholarship_pct"])
    except Exception as exc:
        current_app.logger.error("Failed to send scholarship result email: %s", exc)

    return redirect(url_for("scholarship.result"))


@scholarship_bp.get("/result")
@login_required
def result():
    result_data = session.get("scholarship_result")

    if not result_data and current_user.scholarship_pct is None:
        return redirect(url_for("scholarship.test"))

    if not result_data and current_user.scholarship_pct is not None:
        result_data = _reconstruct_result_from_scholarship(current_user.scholarship_pct)

    return render_template("scholarship/result.html", result=result_data, user=current_user)


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
