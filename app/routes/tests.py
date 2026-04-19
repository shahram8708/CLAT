from collections import OrderedDict, defaultdict
import json
import random
import re
import secrets
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models.blog import BlogPost
from app.models.exam_session import ExamSession
from app.models.payment import Payment
from app.models.scholarship_question import ScholarshipQuestion
from app.models.test_series import TestAttempt
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

QUESTION_MIX_BY_EXAM = {
    "CAT": {"arithmetic": 7, "reasoning": 7, "verbal": 4, "general_awareness": 2},
    "CLAT": {"verbal": 8, "reasoning": 6, "general_awareness": 4, "arithmetic": 2},
    "IPMAT": {"arithmetic": 8, "reasoning": 5, "verbal": 5, "general_awareness": 2},
    "CUET": {"arithmetic": 6, "reasoning": 5, "verbal": 5, "general_awareness": 4},
    "GMAT": {"arithmetic": 8, "reasoning": 6, "verbal": 6, "general_awareness": 0},
    "DEFAULT": {"arithmetic": 6, "reasoning": 5, "verbal": 5, "general_awareness": 4},
}

SECTION_LABELS = {
    "arithmetic": "Quant",
    "reasoning": "Logical Reasoning",
    "verbal": "Verbal Ability",
    "general_awareness": "General Awareness",
}

MAX_TEST_VIOLATIONS = 3


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


def _clear_test_session_data():
    session.pop("test_series_question_ids", None)
    session.pop("test_series_exam_session_token", None)
    session.pop("test_series_id", None)
    session.pop("test_series_start_time", None)


def _user_has_series_access(test_series):
    if not test_series:
        return False

    if test_series.is_free:
        return True

    if not current_user.is_authenticated:
        return False

    purchased = Payment.query.filter_by(
        user_id=current_user.id,
        test_series_id=test_series.id,
        status="success",
    ).first()

    return purchased is not None


def _target_question_count(duration_mins):
    try:
        duration = int(duration_mins or 60)
    except (TypeError, ValueError):
        duration = 60

    if duration <= 45:
        return 12
    if duration <= 75:
        return 15
    return 20


def _select_questions_for_series(exam_name, target_count):
    question_pool = ScholarshipQuestion.query.order_by(
        ScholarshipQuestion.display_order.asc(),
        ScholarshipQuestion.id.asc(),
    ).all()
    if not question_pool:
        return []

    mix = QUESTION_MIX_BY_EXAM.get((exam_name or "").upper(), QUESTION_MIX_BY_EXAM["DEFAULT"])

    grouped_questions = defaultdict(list)
    for question in question_pool:
        subject = (question.subject or "general_awareness").strip().lower() or "general_awareness"
        grouped_questions[subject].append(question)

    selected = []
    selected_ids = set()
    rng = random.SystemRandom()

    for subject, desired_count in mix.items():
        subject_questions = [
            question
            for question in grouped_questions.get(subject, [])
            if question.id not in selected_ids
        ]
        if not subject_questions:
            continue

        take_count = min(desired_count, len(subject_questions))
        for question in rng.sample(subject_questions, take_count):
            selected.append(question)
            selected_ids.add(question.id)

    needed = max(0, target_count - len(selected))
    if needed:
        remaining = [question for question in question_pool if question.id not in selected_ids]
        if len(remaining) <= needed:
            selected.extend(remaining)
        else:
            selected.extend(rng.sample(remaining, needed))

    if not selected:
        return []

    rng.shuffle(selected)
    return selected


def _series_exam_page_url(test_series):
    exam_slug = (test_series.exam or "").strip().lower()
    if exam_slug in {"cat", "clat", "ipmat", "cuet", "gmat"}:
        return url_for("tests.exam_tests", exam=exam_slug)
    return url_for("tests.listing")


def _calculate_percentile_rank_for_attempt(
    test_series_id,
    attempt_user_id,
    score_percentage,
    completed_at=None,
):
    peer_attempts = (
        TestAttempt.query.filter(
            TestAttempt.test_id == test_series_id,
            TestAttempt.score.isnot(None),
            TestAttempt.max_score.isnot(None),
            TestAttempt.max_score > 0,
            TestAttempt.completed_at.isnot(None),
        )
        .order_by(TestAttempt.completed_at.asc())
        .all()
    )

    user_snapshot = {}
    for peer_attempt in peer_attempts:
        if peer_attempt.max_score in (None, 0):
            continue
        peer_pct = (peer_attempt.score / peer_attempt.max_score) * 100
        existing = user_snapshot.get(peer_attempt.user_id)
        if existing is None:
            user_snapshot[peer_attempt.user_id] = {
                "percentage": peer_pct,
                "completed_at": peer_attempt.completed_at,
            }
            continue

        existing_pct = existing["percentage"]
        existing_completed_at = existing["completed_at"]
        should_replace = peer_pct > (existing_pct + 1e-9)
        if not should_replace and abs(peer_pct - existing_pct) <= 1e-9:
            if existing_completed_at is None:
                should_replace = peer_attempt.completed_at is not None
            elif peer_attempt.completed_at is not None:
                should_replace = peer_attempt.completed_at < existing_completed_at

        if should_replace:
            user_snapshot[peer_attempt.user_id] = {
                "percentage": peer_pct,
                "completed_at": peer_attempt.completed_at,
            }

    if attempt_user_id is not None and score_percentage is not None:
        user_snapshot[attempt_user_id] = {
            "percentage": score_percentage,
            "completed_at": completed_at,
        }

    participant_count = len(user_snapshot)
    if participant_count <= 1:
        return {
            "percentile": None,
            "rank": None,
            "participant_count": participant_count,
        }

    current_entry = user_snapshot.get(attempt_user_id)
    if not current_entry:
        return {
            "percentile": None,
            "rank": None,
            "participant_count": participant_count,
        }

    current_pct = current_entry["percentage"]
    peer_percentages = [entry["percentage"] for entry in user_snapshot.values()]
    if not peer_percentages:
        return {
            "percentile": None,
            "rank": None,
            "participant_count": participant_count,
        }

    below_or_equal = sum(1 for pct in peer_percentages if pct <= (current_pct + 1e-9))
    higher_count = sum(1 for pct in peer_percentages if pct > (current_pct + 1e-9))
    return {
        "percentile": round((below_or_equal / participant_count) * 100, 2),
        "rank": higher_count + 1,
        "participant_count": participant_count,
    }


def _calculate_percentile_for_attempt(
    test_series_id,
    score_percentage,
    attempt_user_id=None,
    completed_at=None,
):
    stats = _calculate_percentile_rank_for_attempt(
        test_series_id=test_series_id,
        attempt_user_id=attempt_user_id,
        score_percentage=score_percentage,
        completed_at=completed_at,
    )
    return stats.get("percentile")


def _get_purchased_test_series_ids():
    if not current_user.is_authenticated:
        return set()

    purchased_rows = (
        Payment.query.with_entities(Payment.test_series_id)
        .filter(
            Payment.user_id == current_user.id,
            Payment.status == "success",
            Payment.test_series_id.isnot(None),
        )
        .distinct()
        .all()
    )

    return {row[0] for row in purchased_rows if row[0] is not None}


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
    purchased_series_ids = _get_purchased_test_series_ids()

    return render_template(
        "tests/listing.html",
        grouped_series=grouped_series,
        all_series=all_series,
        exams=exams,
        purchased_series_ids=purchased_series_ids,
    )


@tests_bp.get("/attempt/<int:test_series_id>")
@login_required
def attempt_test(test_series_id):
    return redirect(url_for("tests.start_test", test_series_id=test_series_id))


@tests_bp.get("/start/<int:test_series_id>")
@login_required
def start_test(test_series_id):
    test_series = TestSeries.query.filter_by(id=test_series_id, is_active=True).first_or_404()

    if not _user_has_series_access(test_series):
        flash("Please purchase this test series to start attempting tests.", "warning")
        return redirect(_series_exam_page_url(test_series))

    selected_questions = _select_questions_for_series(
        exam_name=test_series.exam,
        target_count=_target_question_count(test_series.duration_mins),
    )
    if not selected_questions:
        flash("Mock questions are being updated. Please try again shortly.", "warning")
        return redirect(_series_exam_page_url(test_series))

    active_sessions = ExamSession.query.filter(
        ExamSession.user_id == current_user.id,
        ExamSession.is_submitted.is_(False),
        ExamSession.exam_type.like("test_series:%"),
    ).all()
    for active_session in active_sessions:
        active_session.is_submitted = True
        if active_session.submitted_at is None:
            active_session.submitted_at = datetime.utcnow()

    duration_seconds = max(600, int((test_series.duration_mins or 60) * 60))
    exam_session = ExamSession(
        user_id=current_user.id,
        session_token=secrets.token_hex(32),
        exam_type=f"test_series:{test_series.id}",
        ip_address=request.remote_addr,
        user_agent=(request.user_agent.string or "")[:500],
        max_duration_seconds=duration_seconds,
    )
    db.session.add(exam_session)
    db.session.commit()

    session["test_series_question_ids"] = [question.id for question in selected_questions]
    session["test_series_exam_session_token"] = exam_session.session_token
    session["test_series_id"] = test_series.id
    session["test_series_start_time"] = datetime.utcnow().isoformat()

    return render_template(
        "tests/take_test.html",
        test_series=test_series,
        questions=selected_questions,
        total_questions=len(selected_questions),
        server_time_remaining=exam_session.seconds_remaining(),
        exam_session_token=exam_session.session_token,
    )


@tests_bp.post("/submit/<int:test_series_id>")
@login_required
def submit_test(test_series_id):
    test_series = TestSeries.query.filter_by(id=test_series_id, is_active=True).first_or_404()

    submitted_token = (request.form.get("exam_session_token") or "").strip()
    stored_token = (session.get("test_series_exam_session_token") or "").strip()
    stored_series_id = session.get("test_series_id")

    if (
        not submitted_token
        or not stored_token
        or submitted_token != stored_token
        or stored_series_id != test_series_id
    ):
        flash("Invalid or expired test session. Please start the test again.", "danger")
        _clear_test_session_data()
        return redirect(url_for("tests.start_test", test_series_id=test_series_id))

    exam_session = ExamSession.query.filter_by(
        session_token=stored_token,
        user_id=current_user.id,
        is_submitted=False,
        exam_type=f"test_series:{test_series_id}",
    ).first()

    if not exam_session:
        flash("Test session not found or already submitted.", "danger")
        _clear_test_session_data()
        return redirect(url_for("tests.start_test", test_series_id=test_series_id))

    if not _user_has_series_access(test_series):
        exam_session.is_submitted = True
        exam_session.submitted_at = datetime.utcnow()
        db.session.commit()
        _clear_test_session_data()
        flash("Access to this test series is not available on your account.", "danger")
        return redirect(_series_exam_page_url(test_series))

    exam_session.is_submitted = True
    exam_session.submitted_at = datetime.utcnow()

    question_ids = _normalize_question_ids(session.get("test_series_question_ids") or [])
    if not question_ids:
        db.session.commit()
        _clear_test_session_data()
        flash("Session expired. Please start the test again.", "danger")
        return redirect(url_for("tests.start_test", test_series_id=test_series_id))

    questions = ScholarshipQuestion.query.filter(ScholarshipQuestion.id.in_(question_ids)).all()
    question_map = {question.id: question for question in questions}
    ordered_question_ids = [question_id for question_id in question_ids if question_id in question_map]

    if not ordered_question_ids:
        db.session.commit()
        _clear_test_session_data()
        flash("We could not evaluate this attempt. Please try again.", "danger")
        return redirect(url_for("tests.start_test", test_series_id=test_series_id))

    section_totals = defaultdict(int)
    section_correct = defaultdict(int)
    correct_count = 0

    for question_id in ordered_question_ids:
        question = question_map[question_id]
        subject_key = (question.subject or "general_awareness").strip().lower() or "general_awareness"
        section_totals[subject_key] += 1

        submitted_answer = _normalize_answer_choice(request.form.get(f"answer_{question_id}"), question)
        expected_answer = _normalize_answer_choice(question.correct_answer, question)

        if submitted_answer and expected_answer and submitted_answer == expected_answer:
            correct_count += 1
            section_correct[subject_key] += 1

    total_questions = len(ordered_question_ids)
    elapsed_seconds = max(0, int((exam_session.submitted_at - exam_session.started_at).total_seconds()))
    time_taken_mins = max(1, round(elapsed_seconds / 60))

    section_scores_payload = {}
    for subject_key, total in section_totals.items():
        label = SECTION_LABELS.get(subject_key, subject_key.replace("_", " ").title())
        section_scores_payload[label] = f"{section_correct.get(subject_key, 0)}/{total}"

    attempt = TestAttempt(
        user_id=current_user.id,
        test_id=test_series.id,
        score=correct_count,
        max_score=total_questions,
        section_scores=json.dumps(section_scores_payload),
        started_at=exam_session.started_at,
        completed_at=exam_session.submitted_at,
        time_taken_mins=time_taken_mins,
    )
    db.session.add(attempt)
    db.session.flush()

    score_percentage = (correct_count / total_questions) * 100 if total_questions else 0.0
    attempt.percentile = _calculate_percentile_for_attempt(
        test_series.id,
        score_percentage,
        attempt_user_id=current_user.id,
        completed_at=attempt.completed_at,
    )

    db.session.commit()
    _clear_test_session_data()

    auto_submitted = (request.form.get("auto_submitted") or "").strip().lower() == "true"
    if auto_submitted:
        flash("Your test was auto submitted and result has been generated.", "warning")
    else:
        flash("Test submitted successfully. Your score report is ready.", "success")

    return redirect(url_for("tests.test_result", attempt_id=attempt.id))


@tests_bp.post("/report-violation")
@login_required
def report_violation():
    payload = request.get_json(silent=True) or {}
    violation_type = payload.get("violation_type", "unknown")

    stored_token = session.get("test_series_exam_session_token")
    if not stored_token:
        return jsonify({"status": "error", "message": "No active session."}), 400

    exam_session = ExamSession.query.filter(
        ExamSession.session_token == stored_token,
        ExamSession.user_id == current_user.id,
        ExamSession.is_submitted.is_(False),
        ExamSession.exam_type.like("test_series:%"),
    ).first()
    if not exam_session:
        return jsonify({"status": "error", "message": "Session not found."}), 400

    exam_session.violation_count += 1
    db.session.commit()

    remaining = MAX_TEST_VIOLATIONS - exam_session.violation_count

    current_app.logger.warning(
        "Test series violation by user %s (%s): %s. Total violations: %s",
        current_user.id,
        current_user.email,
        violation_type,
        exam_session.violation_count,
    )

    return jsonify(
        {
            "status": "ok",
            "violation_count": exam_session.violation_count,
            "remaining_warnings": max(0, remaining),
            "auto_submit": exam_session.violation_count >= MAX_TEST_VIOLATIONS,
        }
    )


@tests_bp.get("/result/<int:attempt_id>")
@login_required
def test_result(attempt_id):
    attempt = TestAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()

    section_breakdown = {}
    if attempt.section_scores:
        try:
            parsed_data = json.loads(attempt.section_scores)
            if isinstance(parsed_data, dict):
                section_breakdown = parsed_data
        except (TypeError, json.JSONDecodeError):
            section_breakdown = {}

    score_pct = 0.0
    if attempt.score is not None and attempt.max_score not in (None, 0):
        score_pct = round((attempt.score / attempt.max_score) * 100, 1)

    competitive_stats = _calculate_percentile_rank_for_attempt(
        test_series_id=attempt.test_id,
        attempt_user_id=attempt.user_id,
        score_percentage=score_pct,
        completed_at=attempt.completed_at,
    )
    percentile_value = competitive_stats.get("percentile")
    attempt_rank = competitive_stats.get("rank")
    participant_count = competitive_stats.get("participant_count", 0)

    return render_template(
        "tests/result.html",
        attempt=attempt,
        score_pct=score_pct,
        section_breakdown=section_breakdown,
        percentile_value=percentile_value,
        attempt_rank=attempt_rank,
        participant_count=participant_count,
    )


@tests_bp.get("/series/<int:test_series_id>")
def series_detail(test_series_id):
    test_series = TestSeries.query.filter_by(id=test_series_id, is_active=True).first_or_404()

    purchased_series_ids = _get_purchased_test_series_ids()
    is_purchased = test_series.id in purchased_series_ids
    has_access = test_series.is_free or is_purchased

    latest_attempt = None
    if current_user.is_authenticated:
        latest_attempt = (
            TestAttempt.query.filter_by(user_id=current_user.id, test_id=test_series.id)
            .order_by(
                TestAttempt.completed_at.desc(),
                TestAttempt.started_at.desc(),
                TestAttempt.id.desc(),
            )
            .first()
        )

    exam_name = (test_series.exam or "").upper()
    related_series = []
    if exam_name:
        related_series = (
            TestSeries.query.filter(
                TestSeries.is_active.is_(True),
                func.upper(TestSeries.exam) == exam_name,
                TestSeries.id != test_series.id,
            )
            .order_by(TestSeries.is_free.desc(), TestSeries.name.asc())
            .limit(3)
            .all()
        )

    return render_template(
        "tests/series_detail.html",
        test_series=test_series,
        exam_name=exam_name,
        exam_page_url=_series_exam_page_url(test_series),
        has_access=has_access,
        is_purchased=is_purchased,
        latest_attempt=latest_attempt,
        related_series=related_series,
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

    purchased_series_ids = _get_purchased_test_series_ids()

    return render_template(
        "tests/exam_tests.html",
        series_list=series_list,
        exam=exam_name,
        exam_tips=EXAM_TIPS.get(exam_name, EXAM_TIPS["CAT"]),
        related_posts=related_posts,
        purchased_series_ids=purchased_series_ids,
    )
