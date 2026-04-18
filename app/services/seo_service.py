from datetime import datetime

from app.models.blog import BlogPost
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.test_series import TestSeries


def generate_sitemap(app):
    base_url = (app.config.get("SITE_URL") or "https://careerlauncherahmedabad.com").rstrip("/")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    static_pages = [
        ("/", 1.0, "daily"),
        ("/about", 0.7, "monthly"),
        ("/contact", 0.7, "monthly"),
        ("/courses", 0.9, "weekly"),
        ("/faculty", 0.8, "monthly"),
        ("/results", 0.8, "monthly"),
        ("/test-series", 0.8, "weekly"),
        ("/scholarship", 0.8, "monthly"),
        ("/blog", 0.8, "daily"),
        ("/free-resources", 0.7, "weekly"),
        ("/demo", 0.9, "monthly"),
    ]

    entries = [
        {
            "loc": f"{base_url}{path}",
            "lastmod": today,
            "changefreq": changefreq,
            "priority": priority,
        }
        for path, priority, changefreq in static_pages
    ]

    active_courses = Course.query.filter_by(is_active=True).all()
    for course in active_courses:
        entries.append(
            {
                "loc": f"{base_url}/courses/{course.slug}",
                "lastmod": today,
                "changefreq": "weekly",
                "priority": 0.9,
            }
        )

    active_faculty = Faculty.query.filter_by(is_active=True).all()
    for faculty in active_faculty:
        entries.append(
            {
                "loc": f"{base_url}/faculty/{faculty.slug}",
                "lastmod": today,
                "changefreq": "monthly",
                "priority": 0.7,
            }
        )

    published_posts = BlogPost.query.filter_by(is_published=True).all()
    for post in published_posts:
        lastmod = (post.published_at or datetime.utcnow()).strftime("%Y-%m-%d")
        entries.append(
            {
                "loc": f"{base_url}/blog/{post.category}/{post.slug}",
                "lastmod": lastmod,
                "changefreq": "weekly",
                "priority": 0.8,
            }
        )

    active_test_series = TestSeries.query.filter_by(is_active=True).all()
    seen_exams = set()
    for series in active_test_series:
        exam = (series.exam or "").strip().lower()
        if not exam or exam in seen_exams:
            continue
        seen_exams.add(exam)
        entries.append(
            {
                "loc": f"{base_url}/test-series/{exam}",
                "lastmod": today,
                "changefreq": "weekly",
                "priority": 0.7,
            }
        )

    return entries
