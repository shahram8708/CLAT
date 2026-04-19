from datetime import datetime

from app.extensions import db


class Announcement(db.Model):
    __tablename__ = "announcements"
    __table_args__ = (
        db.CheckConstraint(
            "announcement_type IN ('info', 'success', 'warning', 'urgent')",
            name="ck_announcements_type",
        ),
        db.CheckConstraint(
            "display_location IN ('homepage', 'all_pages', 'courses', 'banner')",
            name="ck_announcements_location",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(30), nullable=False, default="info")
    display_location = db.Column(db.String(50), nullable=False, default="homepage")
    cta_text = db.Column(db.String(100), nullable=True)
    cta_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    creator = db.relationship("User", backref="announcements")
