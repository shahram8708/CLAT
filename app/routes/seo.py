from xml.sax.saxutils import escape

from flask import Blueprint, Response, current_app, render_template

from app.services.seo_service import generate_sitemap


seo_bp = Blueprint("seo", __name__)


@seo_bp.get("/sitemap.xml")
def sitemap_xml():
    sitemap_entries = generate_sitemap(current_app._get_current_object())

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for entry in sitemap_entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(entry['loc'])}</loc>")
        lines.append(f"    <lastmod>{entry['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{entry['changefreq']}</changefreq>")
        lines.append(f"    <priority>{entry['priority']}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>")

    return Response("\n".join(lines), mimetype="application/xml")


@seo_bp.get("/robots.txt")
def robots_txt():
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /dashboard/",
            "Disallow: /login",
            "Disallow: /register",
            "Sitemap: https://careerlauncherahmedabad.com/sitemap.xml",
        ]
    )
    return Response(content, mimetype="text/plain")


@seo_bp.get("/privacy-policy")
def privacy_policy():
    return render_template("seo/privacy_policy.html")


@seo_bp.get("/terms")
def terms():
    return render_template("seo/terms.html")
