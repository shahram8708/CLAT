import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class BlogPostForm(FlaskForm):
    title = StringField("Post Title", validators=[DataRequired(), Length(min=5, max=200)])
    slug = StringField("URL Slug", validators=[DataRequired(), Length(min=5, max=200)])
    category = SelectField(
        "Category",
        validators=[DataRequired()],
        choices=[
            ("cat", "CAT/MBA"),
            ("clat", "CLAT/Law"),
            ("ipmat", "IPMAT/BBA"),
            ("gmat", "GMAT/GRE"),
            ("cuet", "CUET"),
            ("general", "General"),
        ],
    )
    content = TextAreaField("Content (HTML)", validators=[DataRequired()])
    excerpt = TextAreaField("Short Excerpt (for listing cards)", validators=[Optional(), Length(max=300)])
    featured_image = StringField("Featured Image URL", validators=[Optional()])
    meta_title = StringField("SEO Meta Title (max 160 chars)", validators=[Optional(), Length(max=160)])
    meta_description = TextAreaField(
        "SEO Meta Description (max 320 chars)",
        validators=[Optional(), Length(max=320)],
    )
    is_published = BooleanField("Publish Immediately")
    submit = SubmitField("Save Post")

    def validate_slug(self, field):
        slug_value = (field.data or "").strip()

        if not re.fullmatch(r"[a-z0-9-]+", slug_value):
            raise ValidationError("Slug can contain only lowercase letters, numbers, and hyphens.")

        field.data = slug_value
