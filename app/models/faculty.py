import json

from app.extensions import db


class Faculty(db.Model):
    __tablename__ = "faculty"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(120), nullable=True)
    qualification = db.Column(db.String(200), nullable=True)
    exam_score = db.Column(db.String(100), nullable=True)
    experience_yrs = db.Column(db.Integer, nullable=True)
    subjects = db.Column(db.Text, nullable=True)
    exam_tags = db.Column(db.Text, nullable=True)
    bio_short = db.Column(db.Text, nullable=True)
    bio_long = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    youtube_url = db.Column(db.String(255), nullable=True)
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
    def subjects_list(self):
        return self._parse_json_list(self.subjects)

    @property
    def exam_tags_list(self):
        return self._parse_json_list(self.exam_tags)
