from collections import OrderedDict

from flask import Blueprint, abort, render_template
from sqlalchemy import func

from app.models.blog import BlogPost
from app.models.test_series import TestSeries


tests_bp = Blueprint("tests", __name__)

VALID_EXAMS = {"CAT", "CLAT", "IPMAT", "CUET", "GMAT"}
EXAM_ORDER = ["CAT", "CLAT", "IPMAT", "CUET"]
BLOG_CATEGORY_MAP = {
    "CAT": "cat",
    "CLAT": "clat",
    "IPMAT": "ipmat",
    "CUET": "cuet",
    "GMAT": "gmat",
}

EXAM_TIPS = {
    "CAT": [
        {
            "icon": "⏱️",
            "title": "Track Section Timing",
            "text": "Fix target checkpoints for VARC, DILR, and QA so one difficult set does not derail your attempt plan.",
        },
        {
            "icon": "📈",
            "title": "Review Every Mock Deeply",
            "text": "Spend at least twice the test duration on analysis to identify question selection and pacing mistakes.",
        },
        {
            "icon": "🧠",
            "title": "Prioritize Accuracy",
            "text": "Consistent high accuracy on fewer questions outperforms random attempts in high percentile ranges.",
        },
    ],
    "CLAT": [
        {
            "icon": "📚",
            "title": "Read Daily Editorials",
            "text": "Build passage stamina and comprehension speed with daily legal and current affairs reading.",
        },
        {
            "icon": "⚖️",
            "title": "Practice Principle Application",
            "text": "In legal reasoning, focus on applying the given principle, not prior legal knowledge.",
        },
        {
            "icon": "📝",
            "title": "Use Section Sequencing",
            "text": "Start with your strongest section and keep quantitative techniques for a focused final push.",
        },
    ],
    "IPMAT": [
        {
            "icon": "➗",
            "title": "Strengthen Arithmetic First",
            "text": "Arithmetic and algebra fundamentals drive confidence and speed across IPMAT quant sections.",
        },
        {
            "icon": "📖",
            "title": "Build Verbal Consistency",
            "text": "Daily reading and vocabulary revision improve verbal accuracy under time pressure.",
        },
        {
            "icon": "🎯",
            "title": "Attempt Mixed Mocks",
            "text": "Alternate between easy and difficult mocks to train strategy for variable exam difficulty.",
        },
    ],
    "CUET": [
        {
            "icon": "🧩",
            "title": "Map Domain Priorities",
            "text": "Identify high weightage chapters in your domain subjects and allocate weekly revision blocks.",
        },
        {
            "icon": "📊",
            "title": "Use Short Timed Drills",
            "text": "Frequent 20 minute quizzes boost retention and reduce pressure in full length mocks.",
        },
        {
            "icon": "🔁",
            "title": "Revise Monthly Notes",
            "text": "Keep compact notes for formulas, facts, and concepts and revise them every week.",
        },
    ],
    "GMAT": [
        {
            "icon": "📐",
            "title": "Master Data Sufficiency Logic",
            "text": "Focus on sufficiency reasoning and avoid full calculations unless they are required.",
        },
        {
            "icon": "📘",
            "title": "Train Critical Reasoning",
            "text": "Practice assumption, strengthen, and weaken patterns to improve verbal score reliability.",
        },
        {
            "icon": "🎛️",
            "title": "Simulate Real Test Conditions",
            "text": "Use full adaptive practice tests and evaluate pacing by question difficulty segments.",
        },
    ],
}


@tests_bp.get("")
@tests_bp.get("/")
def listing():
    series_items = (
        TestSeries.query.filter_by(is_active=True)
        .order_by(TestSeries.exam.asc(), TestSeries.name.asc())
        .all()
    )

    grouped_series = OrderedDict()
    for exam in EXAM_ORDER:
        grouped_series[exam] = []
    grouped_series["Others"] = []

    for series in series_items:
        exam_name = (series.exam or "").upper()
        if exam_name in grouped_series:
            grouped_series[exam_name].append(series)
        else:
            grouped_series["Others"].append(series)

    all_series = []
    for exam_name, exam_series in grouped_series.items():
        if exam_name != "Others":
            all_series.extend(exam_series)
    all_series.extend(grouped_series["Others"])

    exams = [exam_name for exam_name in EXAM_ORDER if grouped_series.get(exam_name)]

    return render_template(
        "tests/listing.html",
        grouped_series=grouped_series,
        all_series=all_series,
        exams=exams,
    )


@tests_bp.get("/<exam>")
def exam_tests(exam):
    exam_name = (exam or "").upper()
    if exam_name not in VALID_EXAMS:
        abort(404)

    series_list = (
        TestSeries.query.filter(
            TestSeries.is_active.is_(True),
            func.upper(TestSeries.exam) == exam_name,
        )
        .order_by(TestSeries.is_free.desc(), TestSeries.name.asc())
        .all()
    )

    related_posts = []
    blog_category = BLOG_CATEGORY_MAP.get(exam_name)
    if blog_category:
        related_posts = (
            BlogPost.query.filter_by(category=blog_category, is_published=True)
            .order_by(BlogPost.published_at.desc(), BlogPost.updated_at.desc())
            .limit(2)
            .all()
        )

    return render_template(
        "tests/exam_tests.html",
        series_list=series_list,
        exam=exam_name,
        exam_tips=EXAM_TIPS.get(exam_name, EXAM_TIPS["CAT"]),
        related_posts=related_posts,
    )
