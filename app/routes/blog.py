import bleach
from flask import Blueprint, abort, render_template
from sqlalchemy import desc

from app.models.blog import BlogPost


blog_bp = Blueprint("blog", __name__)

VALID_CATEGORIES = ["cat", "clat", "ipmat", "gmat", "cuet", "general"]
CATEGORY_LABELS = {
    "cat": "CAT/MBA",
    "clat": "CLAT/Law",
    "ipmat": "IPMAT/BBA",
    "gmat": "GMAT/GRE",
    "cuet": "CUET",
    "general": "General",
}

SEO_SLUG_OVERRIDES = {
    "cat-preparation-mistakes-2025": {
        "meta_title": "CAT Preparation Mistakes in 2025: 11 Errors That Hurt Your Percentile",
        "meta_description": "Avoid the biggest CAT 2025 preparation mistakes across VARC, DILR, QA, mocks, and revision. Use this practical checklist to improve accuracy and percentile.",
    }
}

ALLOWED_TAGS = [
    "p",
    "h2",
    "h3",
    "h4",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "a",
    "img",
    "table",
    "tr",
    "td",
    "th",
    "blockquote",
    "code",
    "pre",
    "br",
    "span",
    "div",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href"],
    "img": ["src", "alt"],
}


def _category_counts():
    counts = {category: 0 for category in VALID_CATEGORIES}
    published_posts = BlogPost.query.filter_by(is_published=True).all()

    for post in published_posts:
        if post.category in counts:
            counts[post.category] += 1

    return counts


@blog_bp.get("")
@blog_bp.get("/")
def listing():
    posts = (
        BlogPost.query.filter_by(is_published=True)
        .order_by(desc(BlogPost.published_at), desc(BlogPost.updated_at))
        .all()
    )

    category_counts = _category_counts()

    return render_template(
        "blog/listing.html",
        posts=posts,
        categories=category_counts,
        category_labels=CATEGORY_LABELS,
        active_category="all",
        total_posts=len(posts),
    )


@blog_bp.get("/<category>")
def by_category(category):
    if category not in VALID_CATEGORIES:
        abort(404)

    posts = (
        BlogPost.query.filter_by(is_published=True, category=category)
        .order_by(desc(BlogPost.published_at), desc(BlogPost.updated_at))
        .all()
    )

    category_counts = _category_counts()

    return render_template(
        "blog/listing.html",
        posts=posts,
        categories=category_counts,
        category_labels=CATEGORY_LABELS,
        active_category=category,
        total_posts=sum(category_counts.values()),
    )


@blog_bp.get("/<category>/<slug>")
def article(category, slug):
    if category not in VALID_CATEGORIES:
        abort(404)

    post = BlogPost.query.filter_by(slug=slug, category=category, is_published=True).first_or_404()

    sanitised_content = bleach.clean(
        post.content or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto", "data"],
        strip=True,
    )

    related_posts = (
        BlogPost.query.filter(
            BlogPost.is_published.is_(True),
            BlogPost.category == category,
            BlogPost.id != post.id,
        )
        .order_by(desc(BlogPost.published_at), desc(BlogPost.updated_at))
        .limit(3)
        .all()
    )

    seo_override = SEO_SLUG_OVERRIDES.get(post.slug, {})
    meta_title = post.meta_title or seo_override.get("meta_title") or f"{post.title} | Career Launcher Ahmedabad"
    meta_description = (
        post.meta_description
        or seo_override.get("meta_description")
        or post.excerpt
        or "Expert preparation guidance from Career Launcher Ahmedabad."
    )

    return render_template(
        "blog/article.html",
        post=post,
        sanitised_content=sanitised_content,
        related_posts=related_posts,
        category_labels=CATEGORY_LABELS,
        meta_title=meta_title,
        meta_description=meta_description,
    )
