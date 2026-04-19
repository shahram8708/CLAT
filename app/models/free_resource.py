from datetime import datetime
from urllib.parse import urlparse

from app.extensions import db


class FreeResource(db.Model):
    __tablename__ = "free_resources"
    STORAGE_DIRECTORY = "downloads/free_resources"
    __table_args__ = (
        db.CheckConstraint(
            "category IN ('clat', 'cat', 'ipmat', 'gmat', 'cuet', 'general')",
            name="ck_free_resources_category",
        ),
        db.CheckConstraint(
            "resource_type IN ('pdf', 'link', 'video', 'mock_test')",
            name="ck_free_resources_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(30), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.String(20), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    is_gated = db.Column(db.Boolean, nullable=False, default=False)
    download_count = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    display_order = db.Column(db.Integer, nullable=True, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def _normalized_local_path(raw_value):
        cleaned = (raw_value or "").strip().replace("\\", "/")
        if not cleaned:
            return None

        parsed = urlparse(cleaned)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return None

        cleaned = cleaned.lstrip("/")
        if cleaned.startswith("static/"):
            cleaned = cleaned[len("static/"):]

        if cleaned.startswith("downloads/free_resources/"):
            return cleaned
        if cleaned.startswith("free_resources/"):
            return f"downloads/{cleaned}"
        if "/" not in cleaned and cleaned.lower().endswith(".pdf"):
            return f"downloads/free_resources/{cleaned}"
        return None

    @property
    def external_url(self):
        value = (self.url or "").strip()
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
        return None

    @property
    def local_file_path(self):
        return self._normalized_local_path(self.url)

    @property
    def display_url(self):
        if self.external_url:
            return self.external_url
        if self.local_file_path:
            return f"/static/{self.local_file_path}"
        return (self.url or "").strip() or "#"

    @property
    def access_mode(self):
        if self.external_url:
            return "navigate"
        return "download"
