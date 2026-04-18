from flask_wtf import FlaskForm
from wtforms import EmailField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=10, max=15)])
    subject = SelectField(
        "Subject",
        validators=[DataRequired()],
        choices=[
            ("general", "General Inquiry"),
            ("course", "Course Information"),
            ("fee", "Fee Structure"),
            ("scholarship", "Scholarship"),
            ("technical", "Technical Support"),
        ],
    )
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField("Send Message")
