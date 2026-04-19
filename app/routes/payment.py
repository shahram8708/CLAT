from flask import Blueprint, jsonify, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Course, Enrollment, Payment, TestSeries
from app.services.payment import (
    create_razorpay_order,
    fetch_razorpay_order,
    get_razorpay_key_id,
    verify_payment_signature,
)
from app.services.scholarship_enrollment import apply_scholarship_payment, calculate_scholarship_amounts


payment_bp = Blueprint("payment", __name__)


def _series_redirect_url(test_series):
    if not test_series:
        return url_for("tests.listing")

    return url_for("tests.start_test", test_series_id=test_series.id)


def _scholarship_redirect_url():
    return url_for("scholarship.result", payment="success")


@payment_bp.post("/create-order")
@login_required
def create_order():
    payload = request.get_json(silent=True) or {}

    try:
        test_series_id = int(payload.get("test_series_id"))
        amount_inr = int(payload.get("amount_inr"))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid request payload."}), 400

    test_series = TestSeries.query.filter_by(id=test_series_id, is_active=True).first_or_404()

    if test_series.is_free or test_series.price is None:
        return jsonify({"status": "error", "message": "Selected series is not payable."}), 400

    if amount_inr != int(test_series.price):
        return jsonify({"status": "error", "message": "Invalid amount submitted."}), 400

    existing_success_payment = Payment.query.filter_by(
        user_id=current_user.id,
        test_series_id=test_series.id,
        status="success",
    ).first()
    if existing_success_payment:
        return jsonify(
            {
                "status": "already_purchased",
                "message": "You already have access to this test series.",
                "redirect": _series_redirect_url(test_series),
            }
        )

    order = create_razorpay_order(
        amount_inr=int(test_series.price),
        notes={"user_id": str(current_user.id), "test_series_id": str(test_series.id)},
    )
    if not order:
        return jsonify({"status": "error", "message": "Payment gateway error. Please try again."}), 502

    payment = Payment(
        user_id=current_user.id,
        test_series_id=test_series.id,
        razorpay_order_id=order.get("id"),
        amount_inr=int(test_series.price),
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "order_id": order.get("id"),
            "amount": int(test_series.price) * 100,
            "currency": "INR",
            "key_id": get_razorpay_key_id(),
            "user_name": current_user.get_full_name(),
            "user_email": current_user.email,
            "user_phone": current_user.phone,
        }
    )


@payment_bp.post("/create-scholarship-order")
@login_required
def create_scholarship_order():
    if current_user.scholarship_pct is None:
        return jsonify({"status": "error", "message": "Scholarship not available for this account."}), 403

    payload = request.get_json(silent=True) or {}

    try:
        course_id = int(payload.get("course_id"))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid course selection."}), 400

    course = Course.query.filter_by(id=course_id, is_active=True).first_or_404()
    fee_data = calculate_scholarship_amounts(course, current_user.scholarship_pct)

    payable_amount = int(fee_data["payable"] or 0)
    original_fee = int(fee_data["original_fee"] or 0)
    discount = int(fee_data["discount"] or 0)

    if original_fee <= 0 or payable_amount <= 0:
        return jsonify({"status": "error", "message": "Course fee is not configured for payment."}), 400

    existing_enrollment = (
        Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id)
        .order_by(Enrollment.enrolled_at.desc(), Enrollment.id.desc())
        .first()
    )
    if existing_enrollment and int(existing_enrollment.fee_paid or 0) >= payable_amount:
        return jsonify(
            {
                "status": "already_purchased",
                "message": "Payment already received for this course.",
                "redirect": _scholarship_redirect_url(),
            }
        )

    order = create_razorpay_order(
        amount_inr=payable_amount,
        notes={
            "payment_for": "scholarship_enrollment",
            "user_id": str(current_user.id),
            "course_id": str(course.id),
            "course_exam": (course.exam_category or ""),
            "scholarship_pct": str(int(current_user.scholarship_pct or 0)),
        },
    )
    if not order:
        return jsonify({"status": "error", "message": "Payment gateway error. Please try again."}), 502

    payment = Payment(
        user_id=current_user.id,
        test_series_id=None,
        razorpay_order_id=order.get("id"),
        amount_inr=payable_amount,
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "order_id": order.get("id"),
            "amount": payable_amount * 100,
            "currency": "INR",
            "key_id": get_razorpay_key_id(),
            "user_name": current_user.get_full_name(),
            "user_email": current_user.email,
            "user_phone": current_user.phone,
            "course_title": course.title,
            "original_fee": original_fee,
            "discount": discount,
            "payable": payable_amount,
        }
    )


@payment_bp.post("/verify")
@login_required
def verify_payment():
    payload = request.get_json(silent=True) or {}

    razorpay_order_id = (payload.get("razorpay_order_id") or "").strip()
    razorpay_payment_id = (payload.get("razorpay_payment_id") or "").strip()
    razorpay_signature = (payload.get("razorpay_signature") or "").strip()

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({"status": "error", "message": "Missing payment verification fields."}), 400

    signature_ok = verify_payment_signature(
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )

    if not signature_ok:
        payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()
        if payment:
            payment.status = "failed"
            db.session.commit()

        return jsonify({"status": "error", "message": "Payment verification failed. Please contact us."}), 400

    payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if not payment:
        return jsonify({"status": "error", "message": "Order not found."}), 404

    if payment.user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized payment verification request."}), 403

    test_series = TestSeries.query.get(payment.test_series_id) if payment.test_series_id else None
    redirect_url = _series_redirect_url(test_series)

    if payment.status == "success":
        return jsonify(
            {
                "status": "success",
                "message": "Payment already verified. You can continue your test series.",
                "redirect": redirect_url,
            }
        )

    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = "success"
    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "message": "Payment successful! You can now access the test series.",
            "redirect": redirect_url,
        }
    )


@payment_bp.post("/verify-scholarship")
@login_required
def verify_scholarship_payment():
    payload = request.get_json(silent=True) or {}

    razorpay_order_id = (payload.get("razorpay_order_id") or "").strip()
    razorpay_payment_id = (payload.get("razorpay_payment_id") or "").strip()
    razorpay_signature = (payload.get("razorpay_signature") or "").strip()

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({"status": "error", "message": "Missing payment verification fields."}), 400

    signature_ok = verify_payment_signature(
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )

    payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if not payment:
        return jsonify({"status": "error", "message": "Order not found."}), 404

    if payment.user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized payment verification request."}), 403

    if not signature_ok:
        payment.status = "failed"
        db.session.commit()
        return jsonify({"status": "error", "message": "Payment verification failed. Please contact support."}), 400

    if payment.status == "success":
        return jsonify(
            {
                "status": "success",
                "message": "Payment already verified.",
                "redirect": _scholarship_redirect_url(),
            }
        )

    order_data = fetch_razorpay_order(razorpay_order_id) or {}
    notes = order_data.get("notes") if isinstance(order_data, dict) else {}
    notes = notes if isinstance(notes, dict) else {}

    payment_for = (notes.get("payment_for") or "").strip().lower()
    order_user_id = (notes.get("user_id") or "").strip()
    course_id_raw = (notes.get("course_id") or "").strip()

    try:
        course_id = int(course_id_raw)
    except (TypeError, ValueError):
        course_id = None

    if payment_for != "scholarship_enrollment" or not course_id:
        payment.status = "failed"
        db.session.commit()
        return jsonify({"status": "error", "message": "Invalid scholarship payment order details."}), 400

    if order_user_id and str(current_user.id) != order_user_id:
        payment.status = "failed"
        db.session.commit()
        return jsonify({"status": "error", "message": "Payment user mismatch."}), 403

    course = Course.query.filter_by(id=course_id, is_active=True).first()
    if not course:
        payment.status = "failed"
        db.session.commit()
        return jsonify({"status": "error", "message": "Selected course is no longer active."}), 400

    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = "success"

    apply_scholarship_payment(
        user=current_user,
        course=course,
        amount_paid=payment.amount_inr,
        payment_mode="online",
        payment_reference=razorpay_payment_id,
    )

    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "message": "Payment successful. Enrollment has been marked as paid.",
            "redirect": _scholarship_redirect_url(),
        }
    )
