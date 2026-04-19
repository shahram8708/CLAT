from datetime import datetime

from app.extensions import db


class Testimonial(db.Model):
    __tablename__ = "testimonials"
    __table_args__ = (
        db.CheckConstraint(
            "(rating IS NULL) OR (rating BETWEEN 1 AND 5)",
            name="ck_testimonials_rating",
        ),
        db.CheckConstraint(
            "display_location IN ('homepage', 'courses', 'results', 'all')",
            name="ck_testimonials_location",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_photo_url = db.Column(db.String(255), nullable=True)
    designation = db.Column(db.String(150), nullable=True)
    course = db.Column(db.String(50), nullable=True)
    exam = db.Column(db.String(50), nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    testimonial_text = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(255), nullable=True)
    display_location = db.Column(db.String(50), nullable=False, default="homepage")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    display_order = db.Column(db.Integer, nullable=True, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def student_photo_display_url(self):
        raw_value = (self.student_photo_url or "").strip()
        if not raw_value:
            return None

        if raw_value.startswith(("http://", "https://", "data:")):
            return raw_value

        cleaned = raw_value.lstrip("/")
        if cleaned.startswith("static/"):
            cleaned = cleaned[len("static/"):]

        if not cleaned:
            return None

        # Legacy records may only store a filename such as "student-name.jpg".
        if "/" not in cleaned:
            cleaned = f"images/testimonials/{cleaned}"

        return f"/static/{cleaned}"
