import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


class LoginForm(FlaskForm):
    email = EmailField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=60)])
    email = EmailField("Email Address", validators=[DataRequired(), Email()])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    exam_interest = SelectField(
        "Exam You're Preparing For",
        choices=[
            ("", "Select Exam"),
            ("CAT/MBA Entrance", "CAT/MBA Entrance"),
            ("CLAT/AILET/Law", "CLAT/AILET/Law"),
            ("IPMAT/BBA", "IPMAT/BBA"),
            ("GMAT/GRE", "GMAT/GRE"),
            ("CUET", "CUET"),
            ("Class XI–XII Mathematics", "Class XI–XII Mathematics"),
        ],
    )
    preferred_mode = SelectField(
        "Preferred Learning Mode",
        choices=[
            ("", "Select Preferred Mode"),
            ("Classroom – Navrangpura Centre", "Classroom – Navrangpura Centre"),
            ("Online – AFA (Attend From Anywhere)", "Online – AFA (Attend From Anywhere)"),
            ("Decide After Demo", "Decide After Demo"),
        ],
    )
    submit = SubmitField("Create Account")

    def validate_phone(self, field):
        cleaned_phone = re.sub(r"[\s-]", "", field.data or "")

        if not cleaned_phone.isdigit():
            raise ValidationError("Phone number must contain only digits, spaces, or dashes.")

        if not 10 <= len(cleaned_phone) <= 15:
            raise ValidationError("Phone number must be between 10 and 15 digits.")

        field.data = cleaned_phone

    def validate_password(self, field):
        password = field.data or ""

        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must include at least one uppercase letter.")

        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must include at least one lowercase letter.")

        if not re.search(r"\d", password):
            raise ValidationError("Password must include at least one number.")
