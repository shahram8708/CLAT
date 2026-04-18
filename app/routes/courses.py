from flask import Blueprint, abort, render_template

from app.models.course import Course
from app.models.faculty import Faculty
from app.models.result import Result


courses_bp = Blueprint("courses", __name__)


def _common_faqs():
    return [
        {
            "question": "What is the batch size for this program?",
            "answer": "Each batch is intentionally kept small so faculty can provide individual attention and track performance closely.",
        },
        {
            "question": "Can I pay the fee in instalments?",
            "answer": "Yes. Most programs allow 2 to 3 instalments based on course duration and enrollment plan.",
        },
        {
            "question": "Do I get access to online study material and recordings?",
            "answer": "Yes. You get access to digital resources, assignments, and class support content for your enrolled program.",
        },
        {
            "question": "Can I attend a demo class before enrolling?",
            "answer": "Yes. You can book a free demo class to evaluate teaching quality and batch fit before enrollment.",
        },
        {
            "question": "Are scholarships available?",
            "answer": "Yes. Merit scholarship opportunities are available through CL Ahmedabad scholarship tests and counseling rounds.",
        },
        {
            "question": "Will I receive a certificate after course completion?",
            "answer": "Yes. Students who complete the program requirements receive a course completion certificate from the center.",
        },
    ]


def _specific_faqs(exam_category):
    category = (exam_category or "").upper()
    specific_map = {
        "CAT": [
            {
                "question": "Do you provide GD PI and WAT preparation for MBA admissions?",
                "answer": "Yes. The CAT pathway includes dedicated GD PI and WAT mentoring, mock interviews, and profile level feedback.",
            },
            {
                "question": "How do you guide students on percentile targets and B school cutoffs?",
                "answer": "Mentors provide institute wise percentile guidance using recent admission trends and your mock performance trajectory.",
            },
        ],
        "CLAT": [
            {
                "question": "How is legal reasoning taught for CLAT and AILET?",
                "answer": "Legal reasoning is taught through principle application, passage analysis, and timed sectional practice built for current paper patterns.",
            },
            {
                "question": "Do you help with NLU selection and counseling after results?",
                "answer": "Yes. Students receive NLU preference guidance and admission stage support based on rank, domicile, and category options.",
            },
        ],
        "IPMAT": [
            {
                "question": "Is interview preparation included for IPM admissions?",
                "answer": "Yes. Interview and communication prep modules are included for shortlisted students targeting IIM and top BBA pathways.",
            },
            {
                "question": "Can non commerce students handle the quant level in IPMAT?",
                "answer": "Yes. The course starts with fundamentals and gradually builds speed and accuracy through structured quant progression.",
            },
        ],
        "GMAT": [
            {
                "question": "Do you support both GMAT and GRE in the same mentoring cycle?",
                "answer": "Yes. Counselors map your profile and target schools, then recommend GMAT or GRE focused study plans.",
            },
            {
                "question": "Do you guide students on score goals for top global universities?",
                "answer": "Yes. Faculty and counselors help set realistic score targets based on your preferred countries and programs.",
            },
        ],
        "CUET": [
            {
                "question": "How do you handle domain subject combinations for CUET?",
                "answer": "Students receive planning support for domain selection, test priorities, and timetable balance for better score outcomes.",
            },
            {
                "question": "Is counseling support available for university applications after CUET?",
                "answer": "Yes. The team assists with university shortlisting and post result planning based on your CUET score profile.",
            },
        ],
        "BOARDS": [
            {
                "question": "Does this program help with both board exams and entrance prep?",
                "answer": "Yes. The schedule balances board syllabus completion and entrance level aptitude development in one learning track.",
            },
            {
                "question": "How frequently are doubt sessions conducted for school students?",
                "answer": "Weekly doubt clinics and regular revision classes are conducted to keep concepts clear throughout the academic year.",
            },
        ],
    }
    return specific_map.get(category, [])


def _build_batch_schedule(course):
    mode_value = (course.mode or "hybrid").title()
    course_title = course.title or "Program"
    return [
        {
            "name": f"June 2026 {course_title} Morning Batch",
            "timing": "Mon Wed Fri 8:00 AM to 10:00 AM",
            "start_date": "10 June 2026",
            "mode": mode_value,
            "seats": 8,
        },
        {
            "name": f"July 2026 {course_title} Evening Batch",
            "timing": "Tue Thu Sat 6:30 PM to 8:30 PM",
            "start_date": "8 July 2026",
            "mode": mode_value,
            "seats": 12,
        },
        {
            "name": f"Weekend Intensive {course_title} Batch",
            "timing": "Saturday Sunday 10:00 AM to 1:00 PM",
            "start_date": "20 July 2026",
            "mode": mode_value,
            "seats": 10,
        },
    ]


@courses_bp.get("")
@courses_bp.get("/")
def listing():
    courses = Course.query.filter_by(is_active=True).order_by(Course.display_order.asc()).all()

    grouped_courses = {}
    for course in courses:
        grouped_courses.setdefault(course.exam_category, []).append(course)

    return render_template("courses/listing.html", courses=courses, grouped_courses=grouped_courses)


@courses_bp.get("/<slug>")
def detail(slug):
    course = Course.query.filter_by(slug=slug).first()
    if not course or not course.is_active:
        abort(404)

    active_faculty = Faculty.query.filter_by(is_active=True).order_by(Faculty.display_order.asc()).all()
    assigned_faculty = [
        faculty
        for faculty in active_faculty
        if course.exam_category in (faculty.exam_tags_list or [])
    ]

    testimonials = (
        Result.query.filter(
            Result.is_active.is_(True),
            Result.exam == course.exam_category,
            Result.testimonial.isnot(None),
            Result.testimonial != "",
        )
        .order_by(Result.display_order.asc())
        .limit(3)
        .all()
    )

    faqs = _common_faqs() + _specific_faqs(course.exam_category)
    batches = _build_batch_schedule(course)

    fee_min = f"{course.fee_min:,}" if course.fee_min else ""
    fee_max = f"{course.fee_max:,}" if course.fee_max else ""
    fee_range = f"INR {fee_min} to INR {fee_max}" if fee_min and fee_max else "competitive fee options"

    meta_title = f"{course.title} Coaching in Ahmedabad | Career Launcher Ahmedabad"
    meta_description = (
        f"Join {course.title} coaching at Career Launcher Ahmedabad with expert faculty, "
        f"structured batches, and {fee_range}. Book a free demo class today."
    )

    return render_template(
        "courses/detail.html",
        course=course,
        assigned_faculty=assigned_faculty,
        testimonials=testimonials,
        faqs=faqs,
        batches=batches,
        meta_title=meta_title,
        meta_description=meta_description,
    )
