from datetime import datetime

import pytest

from app import create_app
from app.extensions import db
from app.models import BlogPost, Course, Lead, TestSeries, User


@pytest.fixture
def app():
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SERVER_NAME="localhost",
    )
    yield app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        ctx = app.app_context()
        ctx.push()
        db.create_all()

        yield client

        db.session.remove()
        db.drop_all()
        ctx.pop()


@pytest.fixture
def admin_user(client):
    user = User(
        role="admin",
        email="testadmin@test.com",
        first_name="Test",
        last_name="Admin",
        phone="9999999999",
        is_active=True,
    )
    user.set_password("TestAdmin@123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_user(client):
    user = User(
        role="student",
        email="teststudent@test.com",
        first_name="Test",
        last_name="Student",
        phone="8888888888",
        is_active=True,
        enrolled_exam="CAT",
    )
    user.set_password("TestStudent@123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_course(client):
    course = Course(
        slug="test-cat-mba",
        title="Test CAT Course",
        exam_category="CAT",
        is_active=True,
        fee_min=50000,
        fee_max=100000,
        display_order=1,
    )
    db.session.add(course)
    db.session.commit()
    return course


@pytest.fixture
def sample_lead(client):
    lead = Lead(
        first_name="John",
        last_name="Doe",
        phone="9876543210",
        email="john@test.com",
        source_page="demo",
        status="new",
    )
    db.session.add(lead)
    db.session.commit()
    return lead


@pytest.fixture
def sample_blog_post(client):
    post = BlogPost(
        title="Test Post",
        slug="test-post",
        category="cat",
        content="<p>Test content for article.</p>",
        is_published=True,
        published_at=datetime.utcnow(),
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture
def sample_test_series(client):
    series = TestSeries(
        name="Test Paid Series",
        exam="CAT",
        description="Sample paid series.",
        total_tests=3,
        duration_mins=60,
        is_free=False,
        price=999,
        is_active=True,
    )
    db.session.add(series)
    db.session.commit()
    return series


def login_as(client, email, password):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": password,
            "remember_me": "y",
        },
        follow_redirects=False,
    )
