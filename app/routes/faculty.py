from flask import Blueprint, abort, render_template

from app.models.faculty import Faculty
from app.models.result import Result


faculty_bp = Blueprint("faculty", __name__)


@faculty_bp.get("")
@faculty_bp.get("/")
def listing():
    faculty_list = Faculty.query.filter_by(is_active=True).order_by(Faculty.display_order.asc()).all()

    unique_tags = set()
    for faculty in faculty_list:
        for tag in faculty.exam_tags_list or []:
            if tag:
                unique_tags.add(tag)

    all_exam_tags = sorted(unique_tags)

    return render_template(
        "faculty/listing.html",
        faculty_list=faculty_list,
        all_exam_tags=all_exam_tags,
    )


@faculty_bp.get("/<slug>")
def profile(slug):
    faculty = Faculty.query.filter_by(slug=slug).first()
    if not faculty or not faculty.is_active:
        abort(404)

    exam_tags = faculty.exam_tags_list or []
    subjects = faculty.subjects_list or []

    all_results = Result.query.filter_by(is_active=True).order_by(Result.display_order.asc()).all()
    related_results = [result for result in all_results if result.exam in exam_tags][:3]

    meta_title = f"{faculty.name} — {faculty.title} | Career Launcher Ahmedabad"

    return render_template(
        "faculty/profile.html",
        faculty=faculty,
        related_results=related_results,
        exam_tags=exam_tags,
        subjects=subjects,
        meta_title=meta_title,
    )
