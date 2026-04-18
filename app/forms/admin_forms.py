from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class CourseAdminForm(FlaskForm):
    title = StringField("Course Title", validators=[DataRequired(), Length(min=2, max=120)])
    exam_category = SelectField(
        "Exam Category",
        validators=[DataRequired()],
        choices=[
            ("CAT", "CAT"),
            ("CLAT", "CLAT"),
            ("IPMAT", "IPMAT"),
            ("GMAT", "GMAT"),
            ("CUET", "CUET"),
            ("Boards", "Boards"),
        ],
    )
    description = TextAreaField("Short Description", validators=[DataRequired(), Length(min=10, max=300)])
    duration = StringField("Duration (e.g., 10–12 Months)", validators=[DataRequired()])
    mode = SelectField(
        "Mode",
        validators=[DataRequired()],
        choices=[
            ("classroom", "Classroom"),
            ("online", "Online"),
            ("hybrid", "Hybrid"),
        ],
    )
    batch_size = IntegerField("Max Batch Size", validators=[DataRequired()])
    fee_min = IntegerField("Minimum Fee (INR)", validators=[DataRequired()])
    fee_max = IntegerField("Maximum Fee (INR)", validators=[DataRequired()])
    icon = StringField("Emoji Icon", validators=[Optional()])
    is_active = BooleanField("Active (visible on website)")
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Course")

    def validate_fee_max(self, field):
        if self.fee_min.data is None or field.data is None:
            return
        if field.data < self.fee_min.data:
            raise ValidationError("Maximum fee must be greater than or equal to minimum fee.")
