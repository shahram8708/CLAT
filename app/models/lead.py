from datetime import datetime

from app.extensions import db


class Lead(db.Model):
    __tablename__ = "leads"
    __table_args__ = (
        db.CheckConstraint("status IN ('new', 'contacted', 'enrolled', 'dropped')", name="ck_leads_status"),
        db.CheckConstraint(
            "(preferred_mode IS NULL) OR preferred_mode IN ('classroom', 'online', 'hybrid', 'decide-after-demo')",
            name="ck_leads_preferred_mode",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    exam_interest = db.Column(db.String(50), nullable=True)
    preferred_mode = db.Column(db.String(30), nullable=True)
    source_page = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="new")
    notes = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    contacted_at = db.Column(db.DateTime, nullable=True)
