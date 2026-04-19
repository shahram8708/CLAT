from datetime import datetime

from app.extensions import db


class ExamSession(db.Model):
    __tablename__ = "exam_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    session_token = db.Column(db.String(64), nullable=False, unique=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    max_duration_seconds = db.Column(db.Integer, nullable=False, default=1260)
    is_submitted = db.Column(db.Boolean, nullable=False, default=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    violation_count = db.Column(db.Integer, nullable=False, default=0)
    exam_type = db.Column(db.String(50), nullable=False, default="scholarship")
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="exam_sessions")

    def is_expired(self):
        elapsed_seconds = (datetime.utcnow() - self.started_at).total_seconds()
        return elapsed_seconds > self.max_duration_seconds

    def seconds_remaining(self):
        elapsed_seconds = int((datetime.utcnow() - self.started_at).total_seconds())
        return max(0, self.max_duration_seconds - elapsed_seconds)

    def is_valid(self):
        return not self.is_submitted and not self.is_expired()
