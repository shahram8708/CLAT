from flask import Blueprint, jsonify, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Payment, TestSeries
from app.services.payment import create_razorpay_order, get_razorpay_key_id, verify_payment_signature


payment_bp = Blueprint("payment", __name__)


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

    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = "success"
    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "message": "Payment successful! You can now access the test series.",
            "redirect": url_for("tests.listing"),
        }
    )
