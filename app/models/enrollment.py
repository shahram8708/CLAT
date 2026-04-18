from datetime import datetime

from app.extensions import db


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (
        db.CheckConstraint("status IN ('active', 'completed', 'paused')", name="ck_enrollments_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    batch_name = db.Column(db.String(60), nullable=True)
    fee_paid = db.Column(db.Integer, nullable=True)
    scholarship_pct = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="active")

    user = db.relationship("User", backref="enrollments")
    course = db.relationship("Course", backref="enrollments")
