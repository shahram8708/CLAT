from datetime import datetime
import re

from sqlalchemy import func

from app.extensions import db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lead import Lead
from app.models.user import User
from app.services.enrollment_service import ensure_student_enrollments


EXAM_INTEREST_TO_CATEGORY = {
    "CAT/MBA Entrance": "CAT",
    "CLAT/AILET/Law": "CLAT",
    "IPMAT/BBA": "IPMAT",
    "GMAT/GRE": "GMAT",
    "CUET": "CUET",
    "Class XI–XII Mathematics": "Boards",
}


def normalize_phone(value):
    return re.sub(r"\D", "", value or "")


def resolve_exam_category(exam_interest=None, fallback=None):
    if exam_interest:
        exam_value = EXAM_INTEREST_TO_CATEGORY.get((exam_interest or "").strip())
        if exam_value:
            return exam_value

    fallback_value = (fallback or "").strip()
    if fallback_value:
        return fallback_value

    return None


def calculate_course_base_fee(course):
    if not course:
        return 0

    fee_min = int(course.fee_min or 0)
    fee_max = int(course.fee_max or 0)

    if fee_min > 0 and fee_max > 0:
        return int(round((fee_min + fee_max) / 2))
    if fee_max > 0:
        return fee_max
    if fee_min > 0:
        return fee_min

    return 0


def calculate_scholarship_amounts(course, scholarship_pct):
    original_fee = calculate_course_base_fee(course)
    pct = int(scholarship_pct or 0)
    pct = max(0, min(pct, 50))

    discount = int((original_fee * pct) / 100)
    payable = max(0, original_fee - discount)

    return {
        "original_fee": original_fee,
        "scholarship_pct": pct,
        "discount": discount,
        "payable": payable,
    }


def find_user_for_lead(lead):
    if not lead:
        return None

    email = (lead.email or "").strip().lower()
    if email:
        user = User.query.filter(func.lower(User.email) == email).first()
        if user:
            return user

    lead_phone = normalize_phone(lead.phone)
    if not lead_phone:
        return None

    candidate_users = User.query.filter(User.phone.isnot(None)).all()
    for user in candidate_users:
        if normalize_phone(user.phone) == lead_phone:
            return user

    return None


def find_latest_lead_for_user(user):
    if not user:
        return None

    email = (user.email or "").strip().lower()
    if email:
        lead = (
            Lead.query.filter(func.lower(Lead.email) == email)
            .order_by(Lead.submitted_at.desc(), Lead.id.desc())
            .first()
        )
        if lead:
            return lead

    user_phone = normalize_phone(user.phone)
    if not user_phone:
        return None

    candidate_leads = Lead.query.order_by(Lead.submitted_at.desc(), Lead.id.desc()).limit(400).all()
    for lead in candidate_leads:
        if normalize_phone(lead.phone) == user_phone:
            return lead

    return None


def append_lead_note(lead, message):
    if not lead or not message:
        return

    timestamp = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")
    entry = f"[{timestamp}] {message}"

    if lead.notes:
        lead.notes = f"{lead.notes}\n{entry}"
    else:
        lead.notes = entry


def upsert_enrollment_for_course(user, course, scholarship_pct=None, fee_paid=None):
    if not user or not course:
        return None

    if (user.enrolled_exam or "").strip() != (course.exam_category or "").strip():
        user.enrolled_exam = course.exam_category

    ensure_student_enrollments(user)

    enrollment = (
        Enrollment.query.filter_by(user_id=user.id, course_id=course.id)
        .order_by(Enrollment.enrolled_at.desc(), Enrollment.id.desc())
        .first()
    )

    if not enrollment:
        enrollment = Enrollment(
            user_id=user.id,
            course_id=course.id,
            batch_name="Counselling Batch",
            enrolled_at=datetime.utcnow(),
            status="active",
        )
        db.session.add(enrollment)

    if scholarship_pct is not None:
        enrollment.scholarship_pct = int(scholarship_pct)

    if fee_paid is not None:
        paid_amount = max(0, int(fee_paid))
        existing_amount = int(enrollment.fee_paid or 0)
        enrollment.fee_paid = max(existing_amount, paid_amount)

    if not enrollment.batch_name:
        enrollment.batch_name = "Counselling Batch"

    enrollment.status = "active"
    return enrollment


def apply_scholarship_payment(user, course, amount_paid, payment_mode, payment_reference=None, lead=None):
    if not user or not course:
        return None, None

    enrollment = upsert_enrollment_for_course(
        user=user,
        course=course,
        scholarship_pct=int(user.scholarship_pct or 0),
        fee_paid=int(amount_paid or 0),
    )

    linked_lead = lead or find_latest_lead_for_user(user)
    if linked_lead:
        linked_lead.status = "enrolled"
        if linked_lead.contacted_at is None:
            linked_lead.contacted_at = datetime.utcnow()

        mode_text = (payment_mode or "payment").strip().title()
        ref_text = f" Reference: {payment_reference}." if payment_reference else ""
        append_lead_note(
            linked_lead,
            (
                f"Enrollment marked via {mode_text} payment for {course.title} "
                f"(Amount: INR {int(amount_paid or 0)}).{ref_text}"
            ),
        )

    return enrollment, linked_lead


def get_active_course_by_id(course_id):
    return Course.query.filter_by(id=course_id, is_active=True).first()
