from datetime import datetime

from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"
    __table_args__ = (
        db.CheckConstraint("status IN ('pending', 'success', 'failed')", name="ck_payments_status"),
        db.CheckConstraint(
            "(payment_method IS NULL) OR payment_method IN ('cash', 'cheque', 'bank_transfer', 'upi', 'razorpay_manual', 'razorpay', 'offline', 'online')",
            name="ck_payments_method",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_series_id = db.Column(db.Integer, db.ForeignKey("test_series.id"), nullable=True)
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    amount_inr = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(30), nullable=True)
    reference_number = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
