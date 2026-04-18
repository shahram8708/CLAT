import hashlib
import hmac
import time

import razorpay
from flask import current_app


def create_razorpay_order(amount_inr, currency="INR", notes=None):
    try:
        amount_paise = int(amount_inr) * 100
        client = razorpay.Client(
            auth=(
                current_app.config["RAZORPAY_KEY_ID"],
                current_app.config["RAZORPAY_KEY_SECRET"],
            )
        )

        order_data = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": f"cl_order_{int(time.time())}",
            "notes": notes or {},
        }

        return client.order.create(data=order_data)
    except Exception as exc:
        current_app.logger.error("Razorpay order creation failed: %s", exc)
        return None


def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    try:
        message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        key = (current_app.config.get("RAZORPAY_KEY_SECRET") or "").encode("utf-8")
        expected_signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_signature, razorpay_signature or "")
    except Exception:
        return False


def get_razorpay_key_id():
    return current_app.config.get("RAZORPAY_KEY_ID", "")
