from flask import Blueprint, render_template

from app.models.result import Result


results_bp = Blueprint("results", __name__)


@results_bp.get("")
@results_bp.get("/")
def index():
    all_results = Result.query.filter_by(is_active=True).order_by(Result.display_order.asc()).all()

    ordered_exams = ["CAT", "CLAT", "IPMAT", "GMAT", "CUET", "Other"]
    grouped_results = {exam: [] for exam in ordered_exams}

    for result in all_results:
        exam_key = result.exam if result.exam in ordered_exams[:-1] else "Other"
        grouped_results.setdefault(exam_key, []).append(result)

    exams = [exam for exam in ordered_exams if grouped_results.get(exam)]

    return render_template(
        "results/index.html",
        grouped_results=grouped_results,
        all_results=all_results,
        exams=exams,
    )
