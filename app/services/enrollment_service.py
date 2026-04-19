from datetime import datetime

from app.extensions import db
from app.models.course import Course
from app.models.enrollment import Enrollment


def ensure_student_enrollments(user):
    if not user or getattr(user, "role", None) != "student":
        return []

    preferred_exam_value = (user.enrolled_exam or "").strip()
    preferred_exam = preferred_exam_value.upper()

    existing_enrollments = (
        Enrollment.query.filter_by(user_id=user.id)
        .order_by(Enrollment.enrolled_at.desc(), Enrollment.id.desc())
        .all()
    )
    if not preferred_exam:
        return existing_enrollments

    preferred_courses = (
        Course.query.filter(
            Course.is_active.is_(True),
            Course.exam_category == preferred_exam_value,
        )
        .order_by(Course.display_order.asc(), Course.id.asc())
        .all()
    )
    if not preferred_courses:
        return existing_enrollments

    existing_preferred_course_ids = set()
    for enrollment in existing_enrollments:
        if enrollment.course and (enrollment.course.exam_category or "").strip().upper() == preferred_exam:
            existing_preferred_course_ids.add(enrollment.course_id)

    missing_preferred_courses = [
        course for course in preferred_courses if course.id not in existing_preferred_course_ids
    ]

    if not missing_preferred_courses:
        return existing_enrollments

    for course in missing_preferred_courses:
        db.session.add(
            Enrollment(
                user_id=user.id,
                course_id=course.id,
                enrolled_at=datetime.utcnow(),
                batch_name="Counselling Batch",
                fee_paid=None,
                scholarship_pct=user.scholarship_pct,
                status="active",
            )
        )

    db.session.commit()

    return (
        Enrollment.query.filter_by(user_id=user.id)
        .order_by(Enrollment.enrolled_at.desc(), Enrollment.id.desc())
        .all()
    )
