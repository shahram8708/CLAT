from app.extensions import db


class BatchSchedule(db.Model):
    __tablename__ = "batch_schedules"
    __table_args__ = (
        db.CheckConstraint(
            "mode IN ('classroom', 'online', 'hybrid')",
            name="ck_batch_schedules_mode",
        ),
        db.CheckConstraint(
            "total_seats >= 0 AND seats_filled >= 0",
            name="ck_batch_schedules_seat_values",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    batch_name = db.Column(db.String(100), nullable=False)
    timing = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    mode = db.Column(db.String(30), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False, default=25)
    seats_filled = db.Column(db.Integer, nullable=False, default=0)
    fee = db.Column(db.Integer, nullable=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.Text, nullable=True)

    course = db.relationship("Course", backref="batch_schedules")
    faculty = db.relationship("Faculty", backref="batches")

    @property
    def seats_available(self):
        total = int(self.total_seats or 0)
        filled = int(self.seats_filled or 0)
        return max(0, total - filled)

    @property
    def is_full(self):
        return int(self.seats_filled or 0) >= int(self.total_seats or 0)
