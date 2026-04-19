import re
from datetime import datetime
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    EmailField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError


SLUG_REGEX = re.compile(r"^[a-z0-9-]+$")


def _validate_slug(value):
    slug_value = (value or "").strip()
    if not SLUG_REGEX.fullmatch(slug_value):
        raise ValidationError("Slug can contain only lowercase letters, numbers, and hyphens.")
    return slug_value


def _validate_indian_mobile(value):
    cleaned = re.sub(r"\D", "", value or "")
    if len(cleaned) != 10 or cleaned[0] not in {"6", "7", "8", "9"}:
        raise ValidationError("Enter a valid 10-digit Indian mobile number.")
    return cleaned


def _validate_youtube_embed_url(value):
    cleaned = (value or "").strip()
    if cleaned and not cleaned.startswith("https://www.youtube.com/embed/"):
        raise ValidationError("Please provide a valid YouTube embed URL.")
    return cleaned


class CourseCreateForm(FlaskForm):
    title = StringField("Course Title", validators=[DataRequired(), Length(min=2, max=120)])
    slug = StringField("Slug", validators=[DataRequired(), Length(min=2, max=120)])
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
    exams_covered = StringField("Exams Covered (comma-separated)", validators=[Optional(), Length(max=300)])
    description = TextAreaField("Short Description", validators=[DataRequired(), Length(min=10, max=300)])
    long_description = TextAreaField("Long Description (HTML)", validators=[Optional()])
    duration = StringField("Duration", validators=[DataRequired(), Length(min=2, max=50)])
    mode = SelectField(
        "Mode",
        validators=[DataRequired()],
        choices=[("classroom", "Classroom"), ("online", "Online"), ("hybrid", "Hybrid")],
    )
    batch_size = IntegerField("Batch Size", validators=[DataRequired()])
    fee_min = IntegerField("Minimum Fee (INR)", validators=[DataRequired()])
    fee_max = IntegerField("Maximum Fee (INR)", validators=[DataRequired()])
    icon = StringField("Icon", validators=[Optional(), Length(max=10)])
    is_active = BooleanField("Is Active", default=True)
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    meta_title = StringField("Meta Title", validators=[Optional(), Length(max=160)])
    meta_description = TextAreaField("Meta Description", validators=[Optional(), Length(max=320)])
    certificate_offered = BooleanField("Certificate Offered")
    emi_available = BooleanField("EMI Available", default=True)
    prerequisite = TextAreaField("Prerequisite", validators=[Optional()])
    submit = SubmitField("Save Course")

    def validate_slug(self, field):
        field.data = _validate_slug(field.data)

    def validate_fee_max(self, field):
        if self.fee_min.data is None or field.data is None:
            return
        if int(field.data) < int(self.fee_min.data):
            raise ValidationError("Maximum fee must be greater than or equal to minimum fee.")


class CourseEditForm(CourseCreateForm):
    submit = SubmitField("Update Course")


class FacultyForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=100)])
    slug = StringField("Slug", validators=[DataRequired(), Length(min=2, max=120)])
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=120)])
    qualification = StringField("Qualification", validators=[Optional(), Length(max=200)])
    exam_score = StringField("Exam Score", validators=[Optional(), Length(max=100)])
    experience_yrs = IntegerField("Experience (Years)", validators=[Optional()])
    subjects_input = StringField("Subjects (comma-separated)", validators=[Optional(), Length(max=500)])
    exam_tags_input = StringField(
        "Exams Covered (comma-separated, e.g.: CAT, CLAT, IPMAT)",
        validators=[Optional(), Length(max=500)],
    )
    bio_short = TextAreaField("Short Bio", validators=[Optional(), Length(max=500)])
    bio_long = TextAreaField("Long Bio", validators=[Optional()])
    photo_upload = FileField(
        "Photo Upload",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Only JPG, JPEG, or PNG files are allowed.")],
    )
    youtube_url = StringField("YouTube Embed URL", validators=[Optional(), Length(max=255)])
    instagram_url = StringField("Instagram URL", validators=[Optional(), Length(max=255)])
    linkedin_url = StringField("LinkedIn URL", validators=[Optional(), Length(max=255)])
    total_students_trained = IntegerField("Total Students Trained", validators=[Optional()])
    joining_year = IntegerField("Joining Year", validators=[Optional()])
    achievements_input = TextAreaField("Key Achievements (one per line)", validators=[Optional()])
    is_active = BooleanField("Is Active", default=True)
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Faculty")

    def validate_slug(self, field):
        field.data = _validate_slug(field.data)

    def validate_youtube_url(self, field):
        field.data = _validate_youtube_embed_url(field.data)

    def validate_joining_year(self, field):
        if field.data is None:
            return
        current_year = datetime.utcnow().year
        if field.data < 1990 or field.data > current_year:
            raise ValidationError(f"Joining year must be between 1990 and {current_year}.")


class ResultForm(FlaskForm):
    student_name = StringField("Student Name", validators=[DataRequired(), Length(min=2, max=100)])
    exam = SelectField(
        "Exam",
        validators=[DataRequired()],
        choices=[("CAT", "CAT"), ("CLAT", "CLAT"), ("IPMAT", "IPMAT"), ("GMAT", "GMAT"), ("CUET", "CUET"), ("General", "General")],
    )
    year = IntegerField("Year", validators=[DataRequired()])
    rank_percentile = StringField("Rank or Percentile", validators=[DataRequired(), Length(min=1, max=30)])
    target_college = StringField("Target College", validators=[Optional(), Length(max=120)])
    testimonial = TextAreaField("Testimonial", validators=[Optional()])
    photo_upload = FileField(
        "Photo Upload",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Only JPG, JPEG, or PNG files are allowed.")],
    )
    score_details = StringField("Score Details", validators=[Optional(), Length(max=200)])
    city = StringField("City", validators=[Optional(), Length(max=100)])
    coaching_duration = StringField("Coaching Duration", validators=[Optional(), Length(max=50)])
    video_testimonial_url = StringField("Video Testimonial URL", validators=[Optional(), Length(max=255)])
    is_active = BooleanField("Is Active", default=True)
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Result")

    def validate_year(self, field):
        current_year = datetime.utcnow().year
        if field.data is None or field.data < 2015 or field.data > current_year + 1:
            raise ValidationError(f"Year must be between 2015 and {current_year + 1}.")


class TestSeriesForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=100)])
    exam = SelectField(
        "Exam",
        validators=[DataRequired()],
        choices=[("CAT", "CAT"), ("CLAT", "CLAT"), ("IPMAT", "IPMAT"), ("CUET", "CUET"), ("GMAT", "GMAT"), ("General", "General")],
    )
    description = TextAreaField("Description", validators=[Optional()])
    total_tests = IntegerField("Total Tests", validators=[Optional()])
    duration_mins = IntegerField("Duration (mins)", validators=[Optional()])
    is_free = BooleanField("Is Free")
    price = IntegerField("Price (INR)", validators=[Optional()])
    razorpay_plan_id = StringField("Razorpay Plan ID", validators=[Optional(), Length(max=100)])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Test Series")

    def validate_price(self, field):
        if not self.is_free.data and (field.data is None or int(field.data) <= 0):
            raise ValidationError("Price is required for paid test series.")


class ScholarshipQuestionForm(FlaskForm):
    question_text = TextAreaField("Question", validators=[DataRequired(), Length(min=10, max=1000)])
    option_a = StringField("Option A", validators=[DataRequired(), Length(min=1, max=300)])
    option_b = StringField("Option B", validators=[DataRequired(), Length(min=1, max=300)])
    option_c = StringField("Option C", validators=[DataRequired(), Length(min=1, max=300)])
    option_d = StringField("Option D", validators=[DataRequired(), Length(min=1, max=300)])
    correct_answer = SelectField(
        "Correct Answer",
        validators=[DataRequired()],
        choices=[("a", "Option A"), ("b", "Option B"), ("c", "Option C"), ("d", "Option D")],
    )
    subject = SelectField(
        "Subject",
        validators=[DataRequired()],
        choices=[
            ("arithmetic", "Arithmetic"),
            ("reasoning", "Reasoning"),
            ("verbal", "Verbal"),
            ("general_awareness", "General Awareness"),
        ],
    )
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Question")


class FreeResourceForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    category = SelectField(
        "Category",
        validators=[DataRequired()],
        choices=[
            ("clat", "CLAT"),
            ("cat", "CAT"),
            ("ipmat", "IPMAT"),
            ("gmat", "GMAT"),
            ("cuet", "CUET"),
            ("general", "General"),
        ],
    )
    resource_type = SelectField(
        "Resource Type",
        validators=[DataRequired()],
        choices=[("pdf", "PDF"), ("link", "Link"), ("video", "Video"), ("mock_test", "Mock Test")],
    )
    delivery_mode = SelectField(
        "Delivery Source",
        validators=[DataRequired()],
        choices=[("upload", "Upload PDF"), ("link", "External Link")],
        default="upload",
    )
    external_url = StringField("External URL", validators=[Optional(), Length(max=500)])
    pdf_upload = FileField(
        "PDF Upload",
        validators=[Optional(), FileAllowed(["pdf"], "Only PDF files are allowed.")],
    )
    url = StringField("Resolved URL", validators=[Optional(), Length(max=500)])
    file_size = StringField("File Size", validators=[Optional(), Length(max=20)])
    year = IntegerField("Year", validators=[Optional()])
    is_gated = BooleanField("Email Gated")
    is_active = BooleanField("Is Active", default=True)
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Resource")

    @staticmethod
    def _is_valid_external_url(value):
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _looks_like_local_resource_path(value):
        cleaned = (value or "").strip().lstrip("/")
        if cleaned.startswith("static/"):
            cleaned = cleaned[len("static/"):]
        return cleaned.startswith("downloads/free_resources/")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        mode = (self.delivery_mode.data or "").strip()
        external_url = (self.external_url.data or "").strip()
        existing_url = (self.url.data or "").strip()
        uploaded_pdf = self.pdf_upload.data

        if mode == "link":
            if not external_url:
                self.external_url.errors.append("External URL is required when source is External Link.")
                return False
            if not self._is_valid_external_url(external_url):
                self.external_url.errors.append("Enter a valid external URL.")
                return False
            self.external_url.data = external_url
            return True

        if mode == "upload":
            has_uploaded_file = bool(uploaded_pdf and getattr(uploaded_pdf, "filename", ""))
            has_existing_local_file = self._looks_like_local_resource_path(existing_url)
            if not has_uploaded_file and not has_existing_local_file:
                self.pdf_upload.errors.append("Please upload a PDF file.")
                return False
            return True

        self.delivery_mode.errors.append("Select a valid delivery source.")
        return False


class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10, max=1000)])
    announcement_type = SelectField(
        "Type",
        validators=[DataRequired()],
        choices=[("info", "Info"), ("success", "Success"), ("warning", "Warning"), ("urgent", "Urgent")],
    )
    display_location = SelectField(
        "Display Location",
        validators=[DataRequired()],
        choices=[("homepage", "Homepage"), ("all_pages", "All Pages"), ("courses", "Courses"), ("banner", "Banner")],
    )
    cta_text = StringField("CTA Text", validators=[Optional(), Length(max=100)])
    cta_url = StringField("CTA URL", validators=[Optional(), Length(max=255)])
    start_date = DateTimeLocalField("Start Date", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    end_date = DateTimeLocalField("End Date", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Announcement")


class TestimonialForm(FlaskForm):
    student_name = StringField("Student Name", validators=[DataRequired(), Length(min=2, max=100)])
    designation = StringField("Designation", validators=[Optional(), Length(max=150)])
    course = SelectField(
        "Course",
        validators=[Optional()],
        choices=[
            ("", "Select Course"),
            ("CAT / MBA Entrance", "CAT / MBA Entrance"),
            ("CLAT / AILET / Law Entrance", "CLAT / AILET / Law Entrance"),
            ("IPMAT / BBA Entrance", "IPMAT / BBA Entrance"),
            ("GMAT / GRE Study Abroad", "GMAT / GRE Study Abroad"),
            ("CUET", "CUET"),
            ("Class XI–XII Mathematics", "Class XI–XII Mathematics"),
        ],
    )
    exam = SelectField(
        "Exam",
        validators=[Optional()],
        choices=[("", "Select Exam"), ("CAT", "CAT"), ("CLAT", "CLAT"), ("IPMAT", "IPMAT"), ("GMAT", "GMAT"), ("CUET", "CUET"), ("General", "General")],
    )
    rating = SelectField(
        "Rating",
        validators=[Optional()],
        choices=[("", "Select Rating"), ("1", "1 Star"), ("2", "2 Stars"), ("3", "3 Stars"), ("4", "4 Stars"), ("5", "5 Stars")],
    )
    testimonial_text = TextAreaField("Testimonial", validators=[DataRequired(), Length(min=20, max=1000)])
    photo_upload = FileField(
        "Photo Upload",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Only JPG, JPEG, or PNG files are allowed.")],
    )
    video_url = StringField("Video URL", validators=[Optional(), Length(max=255)])
    display_location = SelectField(
        "Display Location",
        validators=[DataRequired()],
        choices=[("homepage", "Homepage"), ("courses", "Courses"), ("results", "Results"), ("all", "All")],
    )
    is_active = BooleanField("Is Active", default=True)
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Testimonial")

    def validate_video_url(self, field):
        field.data = _validate_youtube_embed_url(field.data)


class BatchScheduleForm(FlaskForm):
    course_id = SelectField("Course", validators=[DataRequired()], coerce=int)
    batch_name = StringField("Batch Name", validators=[DataRequired(), Length(min=2, max=100)])
    timing = StringField("Timing", validators=[DataRequired(), Length(min=5, max=100)])
    start_date = DateField("Start Date", validators=[DataRequired()], format="%Y-%m-%d")
    end_date = DateField("End Date", validators=[Optional()], format="%Y-%m-%d")
    mode = SelectField(
        "Mode",
        validators=[DataRequired()],
        choices=[("classroom", "Classroom"), ("online", "Online"), ("hybrid", "Hybrid")],
    )
    total_seats = IntegerField("Total Seats", validators=[DataRequired()], default=25)
    seats_filled = IntegerField("Seats Filled", validators=[Optional()], default=0)
    fee = IntegerField("Fee Override (INR)", validators=[Optional()])
    faculty_id = SelectField("Faculty", validators=[Optional()], coerce=int, default=0)
    is_active = BooleanField("Is Active", default=True)
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Batch")

    def validate_end_date(self, field):
        if field.data and self.start_date.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before start date.")


class ManualLeadForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=60)])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=10, max=20)])
    email = EmailField("Email", validators=[Optional(), Email()])
    exam_interest = SelectField(
        "Exam Interest",
        validators=[Optional()],
        choices=[
            ("", "Select Exam"),
            ("CAT", "CAT"),
            ("CLAT", "CLAT"),
            ("IPMAT", "IPMAT"),
            ("GMAT", "GMAT"),
            ("CUET", "CUET"),
            ("Boards", "Boards"),
            ("Other", "Other"),
        ],
    )
    preferred_mode = SelectField(
        "Preferred Mode",
        validators=[Optional()],
        choices=[
            ("", "Select Mode"),
            ("classroom", "Classroom"),
            ("online", "Online"),
            ("hybrid", "Hybrid"),
            ("decide-after-demo", "Decide After Demo"),
        ],
    )
    source_page = SelectField(
        "Source",
        validators=[DataRequired()],
        choices=[
            ("demo", "Demo"),
            ("contact", "Contact"),
            ("walk_in", "Walk In"),
            ("phone_call", "Phone Call"),
            ("referral", "Referral"),
            ("instagram", "Instagram"),
            ("whatsapp", "WhatsApp"),
            ("other", "Other"),
        ],
    )
    notes = TextAreaField("Notes", validators=[Optional()])
    status = SelectField(
        "Status",
        validators=[DataRequired()],
        choices=[("new", "New"), ("contacted", "Contacted"), ("enrolled", "Enrolled"), ("dropped", "Dropped")],
    )
    submit = SubmitField("Save Lead")

    def validate_phone(self, field):
        field.data = _validate_indian_mobile(field.data)


class ManualEnrollmentForm(FlaskForm):
    user_id = SelectField("Student", validators=[DataRequired()], coerce=int)
    course_id = SelectField("Course", validators=[DataRequired()], coerce=int)
    batch_name = StringField("Batch Name", validators=[Optional(), Length(max=60)])
    fee_paid = IntegerField("Fee Paid (INR)", validators=[Optional()])
    scholarship_pct = IntegerField("Scholarship %", validators=[Optional()])
    status = SelectField(
        "Status",
        validators=[DataRequired()],
        choices=[("active", "Active"), ("completed", "Completed"), ("paused", "Paused")],
    )
    submit = SubmitField("Save Enrollment")

    def validate_scholarship_pct(self, field):
        if field.data is None:
            return
        if field.data < 0 or field.data > 50:
            raise ValidationError("Scholarship percentage must be between 0 and 50.")


class ManualStudentForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=60)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=10, max=20)])
    password = PasswordField("Password", validators=[Optional(), Length(min=8, max=128)])
    enrolled_exam = SelectField(
        "Enrolled Exam",
        validators=[Optional()],
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
        validators=[Optional()],
        choices=[("", "Select Mode"), ("classroom", "Classroom"), ("online", "Online"), ("hybrid", "Hybrid")],
    )
    scholarship_pct = IntegerField("Scholarship %", validators=[Optional()])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Student")

    def validate_phone(self, field):
        field.data = _validate_indian_mobile(field.data)

    def validate_scholarship_pct(self, field):
        if field.data is None:
            return
        if field.data < 0 or field.data > 50:
            raise ValidationError("Scholarship percentage must be between 0 and 50.")


class SiteSettingsForm(FlaskForm):
    institute_name = StringField("Institute Name", validators=[DataRequired(), Length(max=200)])
    address = TextAreaField("Address", validators=[DataRequired()])
    phone_primary = StringField("Primary Phone", validators=[DataRequired(), Length(max=20)])
    phone_secondary = StringField("Secondary Phone", validators=[Optional(), Length(max=20)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    whatsapp_number = StringField("WhatsApp Number", validators=[DataRequired(), Length(max=20)])
    hours_weekday = StringField("Weekday Hours", validators=[DataRequired(), Length(max=100)])
    hours_sunday = StringField("Sunday Hours", validators=[DataRequired(), Length(max=100)])

    instagram_url = StringField("Instagram URL", validators=[Optional(), Length(max=255)])
    youtube_url = StringField("YouTube URL", validators=[Optional(), Length(max=255)])
    facebook_url = StringField("Facebook URL", validators=[Optional(), Length(max=255)])
    linkedin_url = StringField("LinkedIn URL", validators=[Optional(), Length(max=255)])
    google_maps_embed_url = TextAreaField("Google Maps Embed URL", validators=[Optional()])

    homepage_meta_title = StringField("Homepage Meta Title", validators=[Optional(), Length(max=160)])
    homepage_meta_description = TextAreaField("Homepage Meta Description", validators=[Optional(), Length(max=320)])
    og_image_url = StringField("Open Graph Image URL", validators=[Optional(), Length(max=255)])

    hero_headline = StringField("Hero Headline", validators=[Optional(), Length(max=255)])
    hero_subheadline = TextAreaField("Hero Subheadline", validators=[Optional()])
    show_scholarship_banner = BooleanField("Show Scholarship Banner")
    scholarship_banner_text = StringField("Scholarship Banner Text", validators=[Optional(), Length(max=255)])

    submit = SubmitField("Save All Settings")


class ManualPaymentForm(FlaskForm):
    user_id = SelectField("Student", validators=[DataRequired()], coerce=int)
    test_series_id = SelectField("Test Series", validators=[Optional()], coerce=int, default=0)
    amount_inr = IntegerField("Amount (INR)", validators=[DataRequired()])
    payment_method = SelectField(
        "Payment Method",
        validators=[DataRequired()],
        choices=[
            ("cash", "Cash"),
            ("cheque", "Cheque"),
            ("bank_transfer", "Bank Transfer"),
            ("upi", "UPI"),
            ("razorpay_manual", "Razorpay Manual"),
        ],
    )
    reference_number = StringField("Reference Number", validators=[Optional(), Length(max=120)])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Record Payment")


class CourseAdminForm(CourseEditForm):
    pass
