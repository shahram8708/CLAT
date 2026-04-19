from flask import Blueprint, render_template

from app.models.result import Result
from app.models.testimonial import Testimonial


results_bp = Blueprint("results", __name__)


@results_bp.get("")
@results_bp.get("/")
def index():
    result_records = Result.query.filter_by(is_active=True).order_by(Result.display_order.asc(), Result.id.asc()).all()
    testimonial_records = (
        Testimonial.query.filter(
            Testimonial.is_active.is_(True),
            Testimonial.display_location.in_(["results", "all"]),
        )
        .order_by(Testimonial.display_order.asc(), Testimonial.id.asc())
        .all()
    )

    all_results = sorted(
        result_records + testimonial_records,
        key=lambda item: (int(getattr(item, "display_order", 0) or 0), int(getattr(item, "id", 0) or 0)),
    )

    ordered_exams = ["CAT", "CLAT", "IPMAT", "GMAT", "CUET", "Other"]
    grouped_results = {exam: [] for exam in ordered_exams}

    for result in all_results:
        exam_value = (getattr(result, "exam", "") or "").upper()
        exam_key = exam_value if exam_value in ordered_exams[:-1] else "Other"
        grouped_results.setdefault(exam_key, []).append(result)

    exams = [exam for exam in ordered_exams if grouped_results.get(exam)]

    return render_template(
        "results/index.html",
        grouped_results=grouped_results,
        all_results=all_results,
        exams=exams,
    )
