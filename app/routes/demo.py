from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from app.extensions import db
from app.forms import DemoBookingForm
from app.models.lead import Lead
from app.services.email_service import send_demo_confirmation, send_lead_notification
from app.services.whatsapp import generate_whatsapp_link, get_default_demo_link


demo_bp = Blueprint("demo", __name__)

PREFERRED_MODE_MAP = {
    "Classroom – Navrangpura Centre": "classroom",
    "Online – AFA (Attend From Anywhere)": "online",
    "Decide After Demo": "decide-after-demo",
}


def _is_ajax_request():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@demo_bp.get("")
@demo_bp.get("/")
def demo():
    form = DemoBookingForm()
    return render_template(
        "main/demo.html",
        form=form,
        whatsapp_link=get_default_demo_link(),
    )


@demo_bp.post("")
@demo_bp.post("/")
def demo_submit():
    form = DemoBookingForm()

    if not form.validate_on_submit():
        if _is_ajax_request():
            return jsonify({"status": "error", "errors": form.errors}), 400

        return render_template(
            "main/demo.html",
            form=form,
            whatsapp_link=get_default_demo_link(),
        )

    lead = Lead(
        first_name=(form.first_name.data or "").strip(),
        last_name=(form.last_name.data or "").strip(),
        phone=(form.phone.data or "").strip(),
        email=(form.email.data or "").strip().lower(),
        exam_interest=form.exam_interest.data,
        preferred_mode=PREFERRED_MODE_MAP.get(form.preferred_mode.data),
        source_page="demo",
        status="new",
    )

    db.session.add(lead)
    db.session.commit()

    try:
        send_lead_notification(lead)
    except Exception as exc:
        current_app.logger.error("Lead notification email failed: %s", exc)

    try:
        send_demo_confirmation(lead)
    except Exception as exc:
        current_app.logger.error("Demo confirmation email failed: %s", exc)

    whatsapp_link = generate_whatsapp_link(
        phone=lead.phone,
        custom_message=(
            f"Hi, I am {lead.first_name} {lead.last_name}. "
            f"I just booked a free demo class for {lead.exam_interest} at Career Launcher Ahmedabad."
        ),
    )

    session["demo_lead_id"] = lead.id

    if _is_ajax_request():
        return jsonify({"status": "success", "redirect": url_for("demo.demo_success"), "whatsapp_link": whatsapp_link})

    return redirect(url_for("demo.demo_success"))


@demo_bp.get("/success")
def demo_success():
    lead_id = session.get("demo_lead_id")
    if not lead_id:
        return redirect(url_for("demo.demo"))

    lead = db.session.get(Lead, lead_id)
    if not lead:
        session.pop("demo_lead_id", None)
        return redirect(url_for("demo.demo"))

    whatsapp_link = generate_whatsapp_link(
        phone=lead.phone,
        custom_message=(
            f"Hi, I am {lead.first_name}. I booked a free demo at Career Launcher Ahmedabad "
            "and I want instant confirmation details."
        ),
    )

    session.pop("demo_lead_id", None)
    return render_template("main/demo_success.html", lead=lead, whatsapp_link=whatsapp_link)
