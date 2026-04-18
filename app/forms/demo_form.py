import re

from flask_wtf import FlaskForm
from wtforms import EmailField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError


class DemoBookingForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=60)])
    phone = StringField("Phone Number", validators=[DataRequired()])
    email = EmailField("Email Address", validators=[DataRequired(), Email()])
    exam_interest = SelectField(
        "Course Interest",
        validators=[DataRequired()],
        choices=[
            ("", "— Select a Course —"),
            ("CAT/MBA Entrance", "CAT/MBA Entrance"),
            ("CLAT/AILET/Law", "CLAT/AILET/Law"),
            ("IPMAT/BBA", "IPMAT/BBA"),
            ("GMAT/GRE", "GMAT/GRE"),
            ("CUET", "CUET"),
            ("Class XI–XII Mathematics", "Class XI–XII Mathematics"),
        ],
    )
    preferred_mode = SelectField(
        "Preferred Mode",
        validators=[DataRequired()],
        choices=[
            ("", "— Select preferred mode —"),
            ("Classroom – Navrangpura Centre", "Classroom – Navrangpura Centre"),
            ("Online – AFA (Attend From Anywhere)", "Online – AFA (Attend From Anywhere)"),
            ("Decide After Demo", "Decide After Demo"),
        ],
    )
    submit = SubmitField("Book My Free Demo →")

    def validate_phone(self, field):
        cleaned_phone = re.sub(r"\D", "", field.data or "")

        if len(cleaned_phone) != 10:
            raise ValidationError("Phone number must be exactly 10 digits.")

        if cleaned_phone[0] not in {"6", "7", "8", "9"}:
            raise ValidationError("Enter a valid Indian mobile number starting with 6, 7, 8, or 9.")

        field.data = cleaned_phone
