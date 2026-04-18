import hashlib
import hmac
import json

from app.extensions import db
from app.models import BlogPost, Course, Enrollment, Faculty, Lead, User
from app.services.payment import verify_payment_signature
from app.services.scholarship import calculate_scholarship_band


def test_user_set_and_check_password(app):
    with app.app_context():
        user = User(
            first_name="Test",
            last_name="User",
            email="password@test.com",
            phone="9999999999",
            role="student",
            is_active=True,
        )
        user.set_password("MyPass@123")

        assert user.check_password("MyPass@123") is True
        assert user.check_password("wrongpass") is False


def test_user_get_full_name():
    user = User(first_name="Riya", last_name="Patel")
    assert user.get_full_name() == "Riya Patel"


def test_user_is_admin_true():
    user = User(role="admin")
    assert user.is_admin() is True


def test_user_is_admin_false():
    user = User(role="student")
    assert user.is_admin() is False


def test_course_exams_list_parsed_correctly():
    course = Course(exams_covered='["CAT","XAT","SNAP"]')
    assert course.exams_list == ["CAT", "XAT", "SNAP"]


def test_course_exams_list_returns_empty_list_on_null():
    course = Course(exams_covered=None)
    assert course.exams_list == []


def test_course_syllabus_list_parsed_correctly():
    syllabus = [
        {"subject": "Quant", "topics": ["Arithmetic", "Algebra"]},
        {"subject": "VARC", "topics": ["RC", "VA"]},
    ]
    course = Course(syllabus_json=json.dumps(syllabus))

    assert isinstance(course.syllabus_list, list)
    assert course.syllabus_list[0]["subject"] == "Quant"
    assert "topics" in course.syllabus_list[0]


def test_faculty_exam_tags_list_parsed_correctly():
    faculty = Faculty(exam_tags='["CAT","CLAT"]')
    assert faculty.exam_tags_list == ["CAT", "CLAT"]


def test_faculty_subjects_list_parsed_correctly():
    faculty = Faculty(subjects='["Quant","VARC"]')
    assert faculty.subjects_list == ["Quant", "VARC"]


def test_blog_post_read_time_minimum_one_minute():
    post = BlogPost(content="Short.")
    assert post.read_time >= 1


def test_blog_post_read_time_calculates_correctly():
    content = " ".join(["word"] * 400)
    post = BlogPost(content=content)
    assert post.read_time == 2


def test_scholarship_band_gold():
    result = calculate_scholarship_band(score=18, max_score=20)
    assert result["scholarship_pct"] == 50
    assert result["band_name"] == "Gold Scholar"


def test_scholarship_band_silver():
    result = calculate_scholarship_band(score=15, max_score=20)
    assert result["scholarship_pct"] == 35
    assert result["band_name"] == "Silver Scholar"


def test_scholarship_band_merit():
    result = calculate_scholarship_band(score=12, max_score=20)
    assert result["scholarship_pct"] == 25


def test_scholarship_band_achiever():
    result = calculate_scholarship_band(score=9, max_score=20)
    assert result["scholarship_pct"] == 15


def test_scholarship_band_participation():
    result = calculate_scholarship_band(score=5, max_score=20)
    assert result["scholarship_pct"] == 10


def test_scholarship_band_always_returns_complete_dict():
    result = calculate_scholarship_band(score=0, max_score=20)

    expected_keys = {"percentage", "scholarship_pct", "band_name", "message"}
    assert expected_keys.issubset(set(result.keys()))
    assert result["percentage"] is not None
    assert result["scholarship_pct"] is not None
    assert result["band_name"] is not None
    assert result["message"] is not None


def test_payment_verify_signature_valid(app):
    with app.app_context():
        app.config["RAZORPAY_KEY_SECRET"] = "test_secret_123"

        razorpay_order_id = "order_test_123"
        razorpay_payment_id = "pay_test_456"
        payload = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        key = app.config["RAZORPAY_KEY_SECRET"].encode("utf-8")
        valid_signature = hmac.new(key, payload, hashlib.sha256).hexdigest()

        assert (
            verify_payment_signature(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=valid_signature,
            )
            is True
        )


def test_payment_verify_signature_invalid(app):
    with app.app_context():
        app.config["RAZORPAY_KEY_SECRET"] = "test_secret_123"

        assert (
            verify_payment_signature(
                razorpay_order_id="order_test_123",
                razorpay_payment_id="pay_test_456",
                razorpay_signature="tampered_signature",
            )
            is False
        )


def test_lead_model_fields(client):
    lead = Lead(
        first_name="John",
        last_name="Doe",
        phone="9876543210",
        email="john@example.com",
        source_page="demo",
        status="new",
        exam_interest="CAT/MBA Entrance",
    )
    db.session.add(lead)
    db.session.commit()

    stored = Lead.query.filter_by(email="john@example.com").first()
    assert stored is not None
    assert stored.first_name == "John"
    assert stored.last_name == "Doe"
    assert stored.phone == "9876543210"
    assert stored.status == "new"


def test_enrollment_relationships(client):
    user = User(
        first_name="Rohan",
        last_name="Shah",
        email="rohan@example.com",
        phone="9000000000",
        role="student",
        is_active=True,
    )
    user.set_password("RohanPass@123")

    course = Course(
        slug="sample-course",
        title="Sample Course",
        exam_category="CAT",
        is_active=True,
    )

    db.session.add(user)
    db.session.add(course)
    db.session.commit()

    enrollment = Enrollment(user_id=user.id, course_id=course.id, status="active")
    db.session.add(enrollment)
    db.session.commit()

    stored = Enrollment.query.first()
    assert stored.user.get_full_name() == "Rohan Shah"
    assert stored.course.title == "Sample Course"
