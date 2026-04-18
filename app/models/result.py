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
    display_order = db.Column(db.Integer, nullable=True, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
