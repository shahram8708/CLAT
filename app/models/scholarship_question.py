from app.extensions import db


class ScholarshipQuestion(db.Model):
    __tablename__ = "scholarship_questions"
    __table_args__ = (
        db.CheckConstraint(
            "correct_answer IN ('a', 'b', 'c', 'd')",
            name="ck_scholarship_questions_correct_answer",
        ),
        db.CheckConstraint(
            "(subject IS NULL) OR subject IN ('arithmetic', 'reasoning', 'verbal', 'general_awareness')",
            name="ck_scholarship_questions_subject",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    subject = db.Column(db.String(50), nullable=True)
    display_order = db.Column(db.Integer, nullable=True, default=0)
