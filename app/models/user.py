from datetime import datetime

from flask_login import UserMixin

from app.extensions import bcrypt, db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint("role IN ('student', 'admin', 'faculty')", name="ck_users_role"),
        db.CheckConstraint(
            "(preferred_mode IS NULL) OR preferred_mode IN ('classroom', 'online', 'hybrid')",
            name="ck_users_preferred_mode",
        ),
        db.CheckConstraint(
            "(scholarship_pct IS NULL) OR (scholarship_pct BETWEEN 0 AND 50)",
            name="ck_users_scholarship_pct",
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    enrolled_exam = db.Column(db.String(50), nullable=True)
    preferred_mode = db.Column(db.String(30), nullable=True)
    scholarship_pct = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password, rounds=12).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_admin(self):
        return self.role == "admin"

    def get_active_exam_session(self):
        from app.models.exam_session import ExamSession

        sessions = (
            ExamSession.query.filter_by(user_id=self.id, is_submitted=False)
            .order_by(ExamSession.started_at.desc())
            .all()
        )

        for exam_session in sessions:
            if not exam_session.is_expired():
                return exam_session

        return None


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
