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
    instagram_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    achievements = db.Column(db.Text, nullable=True)
    video_intro_url = db.Column(db.String(255), nullable=True)
    total_students_trained = db.Column(db.Integer, nullable=True)
    joining_year = db.Column(db.Integer, nullable=True)
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

    @property
    def achievements_list(self):
        return self._parse_json_list(self.achievements)

    @property
    def photo_display_url(self):
        raw_value = (self.photo_url or "").strip()
        if not raw_value:
            return None

        if raw_value.startswith(("http://", "https://", "data:")):
            return raw_value

        cleaned = raw_value.lstrip("/")
        if cleaned.startswith("static/"):
            cleaned = cleaned[len("static/"):]

        if not cleaned:
            return None

        # Legacy records may only store a filename, assume faculty image folder.
        if "/" not in cleaned:
            cleaned = f"images/faculty/{cleaned}"

        return f"/static/{cleaned}"
