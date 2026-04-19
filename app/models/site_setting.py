from datetime import datetime

from app.extensions import db


class SiteSetting(db.Model):
    __tablename__ = "site_settings"
    __table_args__ = (
        db.CheckConstraint(
            "setting_type IN ('text', 'textarea', 'url', 'phone', 'email', 'boolean', 'json')",
            name="ck_site_settings_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=True)
    setting_type = db.Column(db.String(30), nullable=False, default="text")
    label = db.Column(db.String(200), nullable=True)
    group = db.Column(db.String(50), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    updater = db.relationship("User", backref="updated_site_settings")

    @classmethod
    def get(cls, key, default=None):
        if not key:
            return default

        try:
            setting = cls.query.filter_by(key=key).first()
        except Exception:
            db.session.rollback()
            return default

        if not setting or setting.value is None:
            return default

        if setting.setting_type == "boolean":
            return str(setting.value).strip().lower() in {"1", "true", "yes", "on"}

        return setting.value

    @classmethod
    def set(cls, key, value, setting_type="text", label=None, group=None, updated_by=None):
        if not key:
            return None

        setting = cls.query.filter_by(key=key).first()
        if setting is None:
            setting = cls(key=key)
            db.session.add(setting)

        setting.setting_type = setting_type or setting.setting_type or "text"
        if label is not None:
            setting.label = label
        if group is not None:
            setting.group = group
        if updated_by is not None:
            setting.updated_by = updated_by

        if isinstance(value, bool):
            setting.value = "1" if value else "0"
            setting.setting_type = "boolean"
        elif value is None:
            setting.value = None
        else:
            setting.value = str(value)

        return setting
