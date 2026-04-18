from datetime import datetime

from app.extensions import db


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    __table_args__ = (
        db.CheckConstraint(
            "category IN ('cat', 'clat', 'ipmat', 'gmat', 'cuet', 'general')",
            name="ck_blog_posts_category",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    featured_image = db.Column(db.String(255), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    meta_title = db.Column(db.String(160), nullable=True)
    meta_description = db.Column(db.String(320), nullable=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship("User", backref="blog_posts")

    @property
    def read_time(self):
        word_count = len((self.content or "").split())
        return max(1, word_count // 200)
