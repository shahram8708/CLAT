from app.models import Lead, User
from tests.conftest import login_as


def test_homepage_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_about_page_returns_200(client):
    response = client.get("/about")
    assert response.status_code == 200


def test_contact_page_returns_200(client):
    response = client.get("/contact")
    assert response.status_code == 200


def test_courses_listing_returns_200(client):
    response = client.get("/courses")
    assert response.status_code == 200


def test_course_detail_returns_200(client, sample_course):
    response = client.get("/courses/test-cat-mba")
    assert response.status_code == 200


def test_course_detail_404_for_invalid_slug(client):
    response = client.get("/courses/nonexistent-slug")
    assert response.status_code == 404


def test_faculty_listing_returns_200(client):
    response = client.get("/faculty")
    assert response.status_code == 200


def test_results_page_returns_200(client):
    response = client.get("/results")
    assert response.status_code == 200


def test_blog_listing_returns_200(client):
    response = client.get("/blog")
    assert response.status_code == 200


def test_blog_article_returns_200(client, sample_blog_post):
    response = client.get("/blog/cat/test-post")
    assert response.status_code == 200


def test_test_series_returns_200(client):
    response = client.get("/test-series")
    assert response.status_code == 200


def test_scholarship_info_returns_200(client):
    response = client.get("/scholarship")
    assert response.status_code == 200


def test_sitemap_returns_xml(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.content_type.lower()


def test_robots_txt_returns_200(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert b"User-agent" in response.data


def test_privacy_policy_returns_200(client):
    response = client.get("/privacy-policy")
    assert response.status_code == 200


def test_terms_returns_200(client):
    response = client.get("/terms")
    assert response.status_code == 200


def test_login_page_returns_200(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_register_page_returns_200(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_login_with_valid_credentials(client, admin_user):
    response = login_as(client, "testadmin@test.com", "TestAdmin@123")
    assert response.status_code == 302

    with client.session_transaction() as session_data:
        assert session_data.get("_user_id") is not None


def test_login_with_invalid_password(client, admin_user):
    response = login_as(client, "testadmin@test.com", "WrongPassword@123")
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_login_with_nonexistent_email(client):
    response = login_as(client, "missing@test.com", "AnyPassword@123")
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_logout_redirects(client, admin_user):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_register_creates_user(client):
    response = client.post(
        "/register",
        data={
            "first_name": "Ravi",
            "last_name": "Shah",
            "email": "ravi@example.com",
            "phone": "9876543210",
            "password": "StrongPass@123",
            "confirm_password": "StrongPass@123",
            "exam_interest": "CAT/MBA Entrance",
            "preferred_mode": "Classroom – Navrangpura Centre",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert User.query.filter_by(email="ravi@example.com").first() is not None


def test_register_duplicate_email_rejected(client, student_user):
    response = client.post(
        "/register",
        data={
            "first_name": "Another",
            "last_name": "User",
            "email": "teststudent@test.com",
            "phone": "9876501234",
            "password": "StrongPass@123",
            "confirm_password": "StrongPass@123",
            "exam_interest": "CAT/MBA Entrance",
            "preferred_mode": "Classroom – Navrangpura Centre",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"already exists" in response.data


def test_demo_page_returns_200(client):
    response = client.get("/demo")
    assert response.status_code == 200


def test_demo_post_creates_lead(client):
    response = client.post(
        "/demo",
        data={
            "first_name": "Amit",
            "last_name": "Patel",
            "phone": "9876543210",
            "email": "amit@example.com",
            "exam_interest": "CAT/MBA Entrance",
            "preferred_mode": "Classroom – Navrangpura Centre",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 200)
    assert Lead.query.filter_by(source_page="demo").count() == 1


def test_demo_post_rejects_invalid_phone(client):
    response = client.post(
        "/demo",
        data={
            "first_name": "Amit",
            "last_name": "Patel",
            "phone": "abc",
            "email": "amit@example.com",
            "exam_interest": "CAT/MBA Entrance",
            "preferred_mode": "Classroom – Navrangpura Centre",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert Lead.query.filter_by(source_page="demo").count() == 0


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_dashboard_accessible_when_logged_in(client, student_user):
    login_as(client, "teststudent@test.com", "TestStudent@123")
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_dashboard_courses_returns_200(client, student_user):
    login_as(client, "teststudent@test.com", "TestStudent@123")
    response = client.get("/dashboard/courses")
    assert response.status_code == 200


def test_dashboard_tests_returns_200(client, student_user):
    login_as(client, "teststudent@test.com", "TestStudent@123")
    response = client.get("/dashboard/tests")
    assert response.status_code == 200


def test_dashboard_profile_returns_200(client, student_user):
    login_as(client, "teststudent@test.com", "TestStudent@123")
    response = client.get("/dashboard/profile")
    assert response.status_code == 200


def test_admin_dashboard_requires_admin(client, student_user):
    login_as(client, "teststudent@test.com", "TestStudent@123")
    response = client.get("/admin")
    assert response.status_code == 403


def test_admin_dashboard_accessible_to_admin(client, admin_user):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin")
    assert response.status_code == 200


def test_admin_leads_returns_200(client, admin_user, sample_lead):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin/leads")
    assert response.status_code == 200


def test_admin_leads_export_returns_csv(client, admin_user, sample_lead):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin/leads/export")
    assert response.status_code == 200
    assert response.content_type.startswith("text/csv")


def test_admin_students_returns_200(client, admin_user, student_user):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin/students")
    assert response.status_code == 200


def test_admin_blog_returns_200(client, admin_user, sample_blog_post):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin/blog")
    assert response.status_code == 200


def test_admin_results_returns_200(client, admin_user):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin/results")
    assert response.status_code == 200


def test_admin_courses_returns_200(client, admin_user, sample_course):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin/courses")
    assert response.status_code == 200


def test_admin_payments_returns_200(client, admin_user):
    login_as(client, "testadmin@test.com", "TestAdmin@123")
    response = client.get("/admin/payments")
    assert response.status_code == 200


def test_404_handler(client):
    response = client.get("/this-page-definitely-does-not-exist-xyz")
    assert response.status_code == 404
