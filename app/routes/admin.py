import csv
import io
from datetime import datetime

from flask import Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_

from app.extensions import db
from app.forms.admin_forms import CourseAdminForm
from app.forms.blog_form import BlogPostForm
from app.models import BlogPost, Course, Enrollment, Lead, Payment, Result, TestAttempt, TestSeries, User


admin_bp = Blueprint("admin", __name__)

LEAD_STATUSES = {"new", "contacted", "enrolled", "dropped"}
PAYMENT_STATUSES = {"pending", "success", "failed"}
BLOG_CATEGORIES = {"cat", "clat", "ipmat", "gmat", "cuet", "general"}


@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.url))
    if current_user.role != "admin":
        abort(403)


def _format_datetime(dt_value):
    if not dt_value:
        return ""
    return dt_value.strftime("%d %b %Y, %I:%M %p")


@admin_bp.get("")
@admin_bp.get("/")
def dashboard():
    total_leads = Lead.query.count()
    total_students = User.query.filter_by(role="student").count()
    total_enrollments = Enrollment.query.count()
    total_blog_posts = BlogPost.query.count()

    recent_leads = Lead.query.order_by(Lead.submitted_at.desc()).limit(10).all()
    recent_attempts = TestAttempt.query.order_by(TestAttempt.started_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()

    total_revenue = (
        db.session.query(func.coalesce(func.sum(Payment.amount_inr), 0))
        .filter(Payment.status == "success")
        .scalar()
        or 0
    )
    total_pending_amount = (
        db.session.query(func.coalesce(func.sum(Payment.amount_inr), 0))
        .filter(Payment.status == "pending")
        .scalar()
        or 0
    )

    lead_status_counts = {
        "new": Lead.query.filter_by(status="new").count(),
        "contacted": Lead.query.filter_by(status="contacted").count(),
        "enrolled": Lead.query.filter_by(status="enrolled").count(),
        "dropped": Lead.query.filter_by(status="dropped").count(),
    }

    lead_status_percentages = {
        key: round((value * 100.0 / total_leads), 1) if total_leads else 0
        for key, value in lead_status_counts.items()
    }

    return render_template(
        "admin/dashboard.html",
        total_leads=total_leads,
        total_students=total_students,
        total_enrollments=total_enrollments,
        total_blog_posts=total_blog_posts,
        recent_leads=recent_leads,
        recent_attempts=recent_attempts,
        recent_payments=recent_payments,
        total_revenue=total_revenue,
        total_pending_amount=total_pending_amount,
        lead_status_counts=lead_status_counts,
        lead_status_percentages=lead_status_percentages,
    )


@admin_bp.get("/leads")
def leads():
    status_filter = (request.args.get("status") or "").strip().lower()
    search_query = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = Lead.query

    if status_filter in LEAD_STATUSES:
        query = query.filter(Lead.status == status_filter)

    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Lead.first_name.ilike(pattern),
                Lead.last_name.ilike(pattern),
                Lead.phone.ilike(pattern),
                Lead.email.ilike(pattern),
            )
        )

    paginated_leads = query.order_by(Lead.submitted_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        "admin/leads.html",
        leads=paginated_leads,
        status_filter=status_filter,
        search_query=search_query,
    )


@admin_bp.post("/leads/<int:lead_id>/status")
def update_lead_status(lead_id):
    status_value = (request.form.get("status") or "").strip().lower()
    if not status_value and request.is_json:
        payload = request.get_json(silent=True) or {}
        status_value = (payload.get("status") or "").strip().lower()

    if status_value not in LEAD_STATUSES:
        return jsonify({"status": "error", "message": "Invalid status."}), 400

    lead = Lead.query.get_or_404(lead_id)
    lead.status = status_value
    if status_value == "contacted":
        lead.contacted_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"status": "ok", "new_status": lead.status})


@admin_bp.get("/leads/export")
def export_leads_csv():
    leads = Lead.query.order_by(Lead.submitted_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "First Name",
            "Last Name",
            "Phone",
            "Email",
            "Exam Interest",
            "Preferred Mode",
            "Source Page",
            "Status",
            "Submitted At",
            "Contacted At",
            "Notes",
        ]
    )

    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.first_name,
                lead.last_name,
                lead.phone,
                lead.email or "",
                lead.exam_interest or "",
                lead.preferred_mode or "",
                lead.source_page or "",
                lead.status,
                _format_datetime(lead.submitted_at),
                _format_datetime(lead.contacted_at),
                lead.notes or "",
            ]
        )

    filename = f"CL_Ahmedabad_Leads_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_bp.get("/students")
def students():
    search_query = (request.args.get("q") or "").strip()
    exam_filter = (request.args.get("exam") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = User.query.filter(User.role == "student")

    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.email.ilike(pattern),
                User.phone.ilike(pattern),
            )
        )

    if exam_filter:
        query = query.filter(User.enrolled_exam == exam_filter)

    paginated_students = query.order_by(User.created_at.desc()).paginate(page=page, per_page=25, error_out=False)

    return render_template(
        "admin/students.html",
        students=paginated_students,
        search_query=search_query,
        exam_filter=exam_filter,
    )


@admin_bp.get("/students/<int:user_id>")
def student_detail(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()

    enrollments = (
        Enrollment.query.join(Course, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == student.id)
        .order_by(Enrollment.enrolled_at.desc())
        .all()
    )
    attempts = (
        TestAttempt.query.filter_by(user_id=student.id)
        .order_by(TestAttempt.started_at.desc())
        .limit(10)
        .all()
    )
    payments = (
        db.session.query(Payment, TestSeries.name.label("test_series_name"))
        .outerjoin(TestSeries, TestSeries.id == Payment.test_series_id)
        .filter(Payment.user_id == student.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return render_template(
        "admin/student_detail.html",
        user=student,
        enrollments=enrollments,
        attempts=attempts,
        payments=payments,
    )


@admin_bp.post("/students/<int:user_id>/toggle-active")
def toggle_student_active(user_id):
    student = User.query.filter_by(id=user_id, role="student").first_or_404()
    student.is_active = not bool(student.is_active)
    db.session.commit()

    flash("Student status updated successfully.", "success")
    return redirect(url_for("admin.student_detail", user_id=student.id))


@admin_bp.get("/courses")
def courses():
    all_courses = Course.query.order_by(Course.display_order.asc(), Course.id.asc()).all()
    return render_template("admin/courses.html", courses=all_courses)


@admin_bp.get("/courses/<int:course_id>/edit")
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseAdminForm(obj=course)
    return render_template("admin/course_edit.html", form=form, course=course)


@admin_bp.post("/courses/<int:course_id>/edit")
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseAdminForm()

    if not form.validate_on_submit():
        return render_template("admin/course_edit.html", form=form, course=course)

    course.title = (form.title.data or "").strip()
    course.exam_category = form.exam_category.data
    course.description = (form.description.data or "").strip()
    course.duration = (form.duration.data or "").strip()
    course.mode = form.mode.data
    course.batch_size = form.batch_size.data
    course.fee_min = form.fee_min.data
    course.fee_max = form.fee_max.data
    course.icon = ((form.icon.data or "").strip() or None)
    course.is_active = bool(form.is_active.data)
    course.display_order = form.display_order.data or 0

    db.session.commit()
    flash("Course updated successfully.", "success")
    return redirect(url_for("admin.courses"))


@admin_bp.get("/blog")
def blog_posts():
    category_filter = (request.args.get("category") or "").strip().lower()
    status_filter = (request.args.get("status") or "").strip().lower()
    page = request.args.get("page", 1, type=int)

    query = BlogPost.query

    if category_filter in BLOG_CATEGORIES:
        query = query.filter(BlogPost.category == category_filter)

    if status_filter == "published":
        query = query.filter(BlogPost.is_published.is_(True))
    elif status_filter == "draft":
        query = query.filter(BlogPost.is_published.is_(False))

    posts = query.order_by(BlogPost.published_at.desc(), BlogPost.updated_at.desc()).paginate(
        page=page,
        per_page=15,
        error_out=False,
    )

    return render_template(
        "admin/blog.html",
        posts=posts,
        category_filter=category_filter,
        status_filter=status_filter,
    )


@admin_bp.get("/blog/new")
def new_blog_post():
    form = BlogPostForm()
    return render_template("admin/blog_edit.html", form=form, is_new=True)


@admin_bp.post("/blog/new")
def create_blog_post():
    form = BlogPostForm()

    if not form.validate_on_submit():
        return render_template("admin/blog_edit.html", form=form, is_new=True)

    slug_value = (form.slug.data or "").strip()
    duplicate = db.session.query(BlogPost.id).filter(func.lower(BlogPost.slug) == slug_value.lower()).first()
    if duplicate:
        form.slug.errors.append("A post with this slug already exists.")
        return render_template("admin/blog_edit.html", form=form, is_new=True)

    post = BlogPost(
        title=(form.title.data or "").strip(),
        slug=slug_value,
        category=form.category.data,
        content=form.content.data or "",
        excerpt=form.excerpt.data,
        featured_image=form.featured_image.data,
        author_id=current_user.id,
        meta_title=form.meta_title.data,
        meta_description=form.meta_description.data,
        is_published=bool(form.is_published.data),
        published_at=datetime.utcnow() if form.is_published.data else None,
    )

    db.session.add(post)
    db.session.commit()

    flash("Blog post created.", "success")
    return redirect(url_for("admin.blog_posts"))


@admin_bp.get("/blog/<int:post_id>/edit")
def edit_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)
    return render_template("admin/blog_edit.html", form=form, post=post, is_new=False)


@admin_bp.post("/blog/<int:post_id>/edit")
def update_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm()

    if not form.validate_on_submit():
        return render_template("admin/blog_edit.html", form=form, post=post, is_new=False)

    slug_value = (form.slug.data or "").strip()
    duplicate = (
        db.session.query(BlogPost.id)
        .filter(func.lower(BlogPost.slug) == slug_value.lower(), BlogPost.id != post.id)
        .first()
    )
    if duplicate:
        form.slug.errors.append("A post with this slug already exists.")
        return render_template("admin/blog_edit.html", form=form, post=post, is_new=False)

    post.title = (form.title.data or "").strip()
    post.slug = slug_value
    post.category = form.category.data
    post.content = form.content.data or ""
    post.excerpt = form.excerpt.data
    post.featured_image = form.featured_image.data
    post.meta_title = form.meta_title.data
    post.meta_description = form.meta_description.data
    post.is_published = bool(form.is_published.data)

    if post.is_published and not post.published_at:
        post.published_at = datetime.utcnow()

    post.updated_at = datetime.utcnow()
    db.session.commit()

    flash("Blog post updated.", "success")
    return redirect(url_for("admin.blog_posts"))


@admin_bp.post("/blog/<int:post_id>/delete")
def delete_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash("Blog post deleted.", "success")
    return redirect(url_for("admin.blog_posts"))


@admin_bp.get("/results")
def results():
    results_list = Result.query.order_by(Result.display_order.asc(), Result.id.asc()).all()
    return render_template("admin/results.html", results=results_list)


@admin_bp.post("/results/<int:result_id>/toggle-active")
def toggle_result_active(result_id):
    result = Result.query.get_or_404(result_id)
    result.is_active = not bool(result.is_active)
    db.session.commit()
    return jsonify({"status": "ok", "is_active": result.is_active})


@admin_bp.get("/payments")
def payments():
    status_filter = (request.args.get("status") or "").strip().lower()
    page = request.args.get("page", 1, type=int)

    query = (
        db.session.query(
            Payment,
            User.email.label("user_email"),
            TestSeries.name.label("test_series_name"),
        )
        .outerjoin(User, User.id == Payment.user_id)
        .outerjoin(TestSeries, TestSeries.id == Payment.test_series_id)
    )

    if status_filter in PAYMENT_STATUSES:
        query = query.filter(Payment.status == status_filter)

    paginated_payments = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    total_revenue = (
        db.session.query(func.coalesce(func.sum(Payment.amount_inr), 0))
        .filter(Payment.status == "success")
        .scalar()
        or 0
    )
    successful_count = Payment.query.filter_by(status="success").count()
    pending_failed_count = Payment.query.filter(Payment.status.in_(["pending", "failed"])).count()

    return render_template(
        "admin/payments.html",
        payments=paginated_payments,
        total_revenue=total_revenue,
        successful_count=successful_count,
        pending_failed_count=pending_failed_count,
        status_filter=status_filter,
    )
