import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class ProfileUpdateForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=60)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    enrolled_exam = SelectField(
        "Exam Preparing For",
        choices=[
            ("", "Select Exam"),
            ("CAT", "CAT"),
            ("CLAT", "CLAT"),
            ("IPMAT", "IPMAT"),
            ("GMAT", "GMAT"),
            ("CUET", "CUET"),
            ("Boards", "Boards"),
        ],
    )
    preferred_mode = SelectField(
        "Preferred Mode",
        choices=[
            ("", "Select Preferred Mode"),
            ("classroom", "Classroom"),
            ("online", "Online"),
            ("hybrid", "Hybrid"),
        ],
    )
    current_password = PasswordField(
        "Current Password (required to change password)",
        validators=[Optional()],
    )
    new_password = PasswordField(
        "New Password",
        validators=[Optional(), Length(min=8, max=128)],
    )
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[Optional()],
    )
    submit = SubmitField("Save Changes")

    def validate_phone(self, field):
        cleaned_phone = re.sub(r"[\s-]", "", field.data or "")
        if not cleaned_phone.isdigit():
            raise ValidationError("Phone number must contain only digits, spaces, or dashes.")
        if not 10 <= len(cleaned_phone) <= 15:
            raise ValidationError("Phone number must be between 10 and 15 digits.")
        field.data = cleaned_phone

    def validate(self, extra_validators=None):
        is_valid = super().validate(extra_validators=extra_validators)

        new_password = (self.new_password.data or "").strip()
        current_password = (self.current_password.data or "").strip()
        confirm_password = (self.confirm_new_password.data or "").strip()

        if new_password and not current_password:
            self.current_password.errors.append("Current password is required to change your password.")
            is_valid = False

        if new_password and confirm_password != new_password:
            self.confirm_new_password.errors.append("New password and confirmation do not match.")
            is_valid = False

        return is_valid
