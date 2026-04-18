import json

from app.extensions import db


class Course(db.Model):
    __tablename__ = "courses"
    __table_args__ = (
        db.CheckConstraint(
            "exam_category IN ('CAT', 'CLAT', 'IPMAT', 'GMAT', 'CUET', 'Boards')",
            name="ck_courses_exam_category",
        ),
        db.CheckConstraint(
            "(mode IS NULL) OR mode IN ('classroom', 'online', 'hybrid')",
            name="ck_courses_mode",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    title = db.Column(db.String(120), nullable=False)
    exam_category = db.Column(db.String(50), nullable=False)
    exams_covered = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    long_description = db.Column(db.Text, nullable=True)
    duration = db.Column(db.String(50), nullable=True)
    mode = db.Column(db.String(30), nullable=True)
    batch_size = db.Column(db.Integer, nullable=True)
    fee_min = db.Column(db.Integer, nullable=True)
    fee_max = db.Column(db.Integer, nullable=True)
    icon = db.Column(db.String(10), nullable=True)
    syllabus_json = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    display_order = db.Column(db.Integer, nullable=True, default=0)

    @staticmethod
    def _parse_json_list(raw_value):
        if not raw_value:
            return []
        try:
            parsed = json.loads(raw_value)
            return parsed if isinstance(parsed, list) else []
        except (TypeError, json.JSONDecodeError):
            return []

    @property
    def exams_list(self):
        return self._parse_json_list(self.exams_covered)

    @property
    def syllabus_list(self):
        return self._parse_json_list(self.syllabus_json)
