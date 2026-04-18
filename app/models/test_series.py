from datetime import datetime

from app.extensions import db


class TestSeries(db.Model):
    __tablename__ = "test_series"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    exam = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    total_tests = db.Column(db.Integer, nullable=True)
    duration_mins = db.Column(db.Integer, nullable=True)
    is_free = db.Column(db.Boolean, nullable=False, default=False)
    price = db.Column(db.Integer, nullable=True)
    razorpay_plan_id = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class TestAttempt(db.Model):
    __tablename__ = "test_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("test_series.id"), nullable=False)
    score = db.Column(db.Integer, nullable=True)
    max_score = db.Column(db.Integer, nullable=True)
    percentile = db.Column(db.Float, nullable=True)
    section_scores = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    time_taken_mins = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", backref="test_attempts")
    test = db.relationship("TestSeries", backref="attempts")
