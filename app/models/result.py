from app.extensions import db


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    photo_url = db.Column(db.String(255), nullable=True)
    exam = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rank_percentile = db.Column(db.String(30), nullable=True)
    target_college = db.Column(db.String(120), nullable=True)
    testimonial = db.Column(db.Text, nullable=True)
    video_testimonial_url = db.Column(db.String(255), nullable=True)
    score_details = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    coaching_duration = db.Column(db.String(50), nullable=True)
    display_order = db.Column(db.Integer, nullable=True, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

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

        # Legacy rows may only store a filename such as "kavya-reddy.jpg".
        if "/" not in cleaned:
            cleaned = f"images/results/{cleaned}"

        return f"/static/{cleaned}"
