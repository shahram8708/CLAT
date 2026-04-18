from urllib.parse import quote_plus

from flask_mail import Message

from app.extensions import mail


def _clean_phone_number(phone):
    return "".join(ch for ch in str(phone or "") if ch.isdigit())


def _base_site_url():
    from flask import current_app

    return (current_app.config.get("SITE_URL") or "https://careerlauncherahmedabad.com").rstrip("/")


def send_lead_notification(lead):
    from flask import current_app

    try:
        admin_email = current_app.config.get("ADMIN_EMAIL")
        if not admin_email:
            current_app.logger.error("ADMIN_EMAIL is not configured")
            return False

        exam_interest = lead.exam_interest or "Not specified"
        preferred_mode = lead.preferred_mode or "Not specified"
        lead_email = lead.email or "Not provided"
        source_page = lead.source_page or "Not specified"
        submission_time = (
            lead.submitted_at.strftime("%d %b %Y, %I:%M %p") if lead.submitted_at else "Not available"
        )

        wa_phone = _clean_phone_number(lead.phone)
        wa_message = quote_plus(
            f"Hi {lead.first_name}, thank you for booking a free demo class with Career Launcher Ahmedabad. "
            "Our counsellor will connect with you shortly."
        )
        whatsapp_link = f"https://wa.me/{wa_phone}?text={wa_message}" if wa_phone else ""

        subject = f"🔔 New Demo Booking — {lead.first_name} {lead.last_name} ({lead.exam_interest or 'Not specified'})"

        plain_text = (
            "New demo booking received from Career Launcher Ahmedabad website\n\n"
            f"Name: {lead.first_name} {lead.last_name}\n"
            f"Phone: {lead.phone}\n"
            f"Email: {lead_email}\n"
            f"Exam Interest: {exam_interest}\n"
            f"Preferred Mode: {preferred_mode}\n"
            f"Source Page: {source_page}\n"
            f"Submission Time: {submission_time}\n"
            f"WhatsApp Quick Reply: {whatsapp_link or 'N/A'}\n"
        )

        html_content = f"""
        <div style="font-family: Inter, Arial, sans-serif; background: #f4f6fa; padding: 24px; color: #1c1c2e;">
          <div style="max-width: 720px; margin: 0 auto; background: #ffffff; border: 1px solid #dee2e6; border-radius: 12px; overflow: hidden;">
            <div style="background: #1a1a2e; color: #ffffff; padding: 18px 24px;">
              <h2 style="margin: 0; font-family: Poppins, Arial, sans-serif; font-size: 22px;">Career Launcher Ahmedabad</h2>
              <p style="margin: 6px 0 0; opacity: 0.9;">New Demo Booking Alert</p>
            </div>

            <div style="padding: 22px 24px;">
              <p style="margin-top: 0;">A new student has booked a free demo class.</p>
              <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr>
                  <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600; width: 36%;">Name</td>
                  <td style="border: 1px solid #dee2e6; padding: 10px;">{lead.first_name} {lead.last_name}</td>
                </tr>
                <tr>
                  <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600;">Phone</td>
                  <td style="border: 1px solid #dee2e6; padding: 10px;">{lead.phone}</td>
                </tr>
                <tr>
                  <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600;">Email</td>
                  <td style="border: 1px solid #dee2e6; padding: 10px;">{lead_email}</td>
                </tr>
                <tr>
                  <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600;">Exam Interest</td>
                  <td style="border: 1px solid #dee2e6; padding: 10px;">{exam_interest}</td>
                </tr>
                <tr>
                  <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600;">Preferred Mode</td>
                  <td style="border: 1px solid #dee2e6; padding: 10px;">{preferred_mode}</td>
                </tr>
                <tr>
                  <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600;">Source Page</td>
                  <td style="border: 1px solid #dee2e6; padding: 10px;">{source_page}</td>
                </tr>
                <tr>
                  <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: 600;">Submission Time</td>
                  <td style="border: 1px solid #dee2e6; padding: 10px;">{submission_time}</td>
                </tr>
              </table>

              <div style="margin-top: 18px;">
                <a href="{whatsapp_link}" style="display: inline-block; background: #25d366; color: #ffffff; text-decoration: none; padding: 11px 16px; border-radius: 8px; font-weight: 600;">Reply on WhatsApp</a>
              </div>
            </div>

            <div style="border-top: 1px solid #dee2e6; padding: 14px 24px; color: #6c757d; font-size: 13px;">
              Career Launcher Ahmedabad, A 102, Karmyog Heights, Navrangpura, Ahmedabad 380009
            </div>
          </div>
        </div>
        """

        msg = Message(subject=subject, recipients=[admin_email], body=plain_text, html=html_content)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(str(e))
        return False


def send_demo_confirmation(lead):
    from flask import current_app

    try:
        if not lead.email or not str(lead.email).strip():
            return False

        whatsapp_link = (
            "https://wa.me/919978559986?text="
            "Hi%2C%20I%20booked%20a%20free%20demo%20class%20at%20Career%20Launcher%20Ahmedabad."
        )
        subject = "Your Free Demo Class is Confirmed — Career Launcher Ahmedabad"

        plain_text = (
            f"Hi {lead.first_name},\n\n"
            "Your free demo class booking is confirmed with Career Launcher Ahmedabad.\n\n"
            "What happens next:\n"
            "1. Our counsellor will call you shortly.\n"
            "2. We will discuss your exam goals and suitable batch.\n"
            "3. Demo details will be shared via SMS and WhatsApp.\n\n"
            "Centre Address:\n"
            "A 102, Karmyog Heights, Navrangpura, Ahmedabad 380009\n"
            "Phone: +91 9978559986 / +91 6353842725\n"
            f"WhatsApp: {whatsapp_link}\n\n"
            "Thank you,\nCareer Launcher Ahmedabad"
        )

        html_content = f"""
        <div style="font-family: Inter, Arial, sans-serif; background: #f4f6fa; padding: 24px; color: #1c1c2e;">
          <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border: 1px solid #dee2e6; border-radius: 12px; overflow: hidden;">
            <div style="background: #1a1a2e; color: #ffffff; padding: 18px 24px;">
              <h2 style="margin: 0; font-family: Poppins, Arial, sans-serif;">Your Demo Booking is Confirmed</h2>
            </div>

            <div style="padding: 22px 24px;">
              <p>Hi {lead.first_name},</p>
              <p>Thank you for booking a free demo class with <strong>Career Launcher Ahmedabad</strong>. We are excited to support your preparation journey.</p>

              <h4 style="font-family: Poppins, Arial, sans-serif; color: #1a1a2e; margin-bottom: 8px;">What to expect next</h4>
              <ol style="padding-left: 18px; margin-top: 0;">
                <li style="margin-bottom: 8px;">Our counsellor will call you within the next few hours.</li>
                <li style="margin-bottom: 8px;">We will discuss your exam target and recommend the right batch.</li>
                <li style="margin-bottom: 8px;">Demo class details will be shared via SMS and WhatsApp.</li>
              </ol>

              <p style="margin-bottom: 6px;"><strong>Centre Address:</strong> A 102, Karmyog Heights, Navrangpura, Ahmedabad 380009</p>
              <p style="margin-bottom: 6px;"><strong>Call:</strong> <a href="tel:+919978559986">+91 9978559986</a> | <a href="tel:+916353842725">+91 6353842725</a></p>
              <p style="margin-top: 14px;">
                <a href="{whatsapp_link}" style="display: inline-block; background: #25d366; color: #ffffff; text-decoration: none; padding: 10px 15px; border-radius: 8px; font-weight: 600;">Connect on WhatsApp</a>
              </p>
            </div>

            <div style="border-top: 1px solid #dee2e6; padding: 14px 24px; color: #6c757d; font-size: 13px;">
              Team Career Launcher Ahmedabad
            </div>
          </div>
        </div>
        """

        msg = Message(subject=subject, recipients=[lead.email.strip().lower()], body=plain_text, html=html_content)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(str(e))
        return False


def send_scholarship_result(user, scholarship_pct):
    from flask import current_app

    try:
        if not user.email:
            return False

        base_url = _base_site_url()
        scholarship_value = int(scholarship_pct or 10)
        band_map = {
            50: "Gold Scholar",
            35: "Silver Scholar",
            25: "Merit Scholar",
            15: "Achiever Scholar",
            10: "Participation Benefit",
        }
        band_name = band_map.get(scholarship_value, "Participation Benefit")

        certificate_link = f"{base_url}/scholarship/certificate"
        counselling_link = (
            "https://wa.me/919978559986?text="
            "Hi%2C%20I%20want%20to%20book%20a%20counselling%20call%20for%20my%20scholarship%20enrollment."
        )
        programs_link = f"{base_url}/courses"
        subject = f"Your Scholarship Result — {scholarship_value}% Discount Awarded | CL Ahmedabad"

        body = (
            f"Hi {user.first_name},\n\n"
            f"Congratulations. You have been awarded a {scholarship_value}% scholarship at Career Launcher Ahmedabad.\n"
            f"Scholarship Band: {band_name}\n\n"
            f"Download your scholarship certificate: {certificate_link}\n"
            "Valid for enrollment within 30 days.\n\n"
            "Next Steps:\n"
            f"1. Book a counselling call: {counselling_link}\n"
            f"2. Explore programs: {programs_link}\n"
            "3. Complete enrollment with scholarship applied\n\n"
            "Career Launcher Ahmedabad\n"
            "A 102, Karmyog Heights, Navrangpura, Ahmedabad - 380009\n"
            "+91 9978559986 | +91 6353842725\n"
            "cl_ahmedabad@careerlauncher.com"
        )

        html = f"""
        <div style="font-family: Inter, Arial, sans-serif; background: #f4f6fa; padding: 24px; color: #1c1c2e;">
          <div style="max-width: 700px; margin: 0 auto; background: #ffffff; border: 1px solid #dee2e6; border-radius: 12px; overflow: hidden;">
            <div style="background: #1a1a2e; color: #ffffff; padding: 20px 24px;">
              <h2 style="margin: 0; font-family: Poppins, Arial, sans-serif;">Your Scholarship Result</h2>
            </div>

            <div style="padding: 24px;">
              <p style="margin-top: 0;">Hi {user.first_name},</p>
              <p>Congratulations. You have been awarded a scholarship at Career Launcher Ahmedabad.</p>

              <div style="background: #fdf2f1; border: 1px solid #c0392b; border-radius: 10px; padding: 16px; text-align: center; margin: 18px 0;">
                <p style="margin: 0; font-size: 14px; color: #6c757d;">Scholarship Awarded</p>
                <p style="margin: 4px 0 0; font-size: 36px; font-weight: 800; color: #c0392b;">{scholarship_value}%</p>
                <p style="margin: 6px 0 0; font-size: 15px;"><strong>{band_name}</strong></p>
              </div>

              <p style="margin: 0 0 14px;">
                <a href="{certificate_link}" style="display: inline-block; background:#1A1A2E; color:#fff; padding:10px 14px; border-radius:6px; text-decoration:none; font-weight:600;">
                  Download Scholarship Certificate
                </a>
              </p>

              <p style="margin-bottom: 14px;"><strong>Valid for enrollment within 30 days.</strong></p>

              <p style="margin-bottom: 8px;"><strong>Next Steps</strong></p>
              <ol style="margin-top: 0; padding-left: 18px;">
                <li style="margin-bottom: 6px;"><a href="{counselling_link}" style="color: #1a1a2e;">Book a counselling call on WhatsApp</a></li>
                <li style="margin-bottom: 6px;"><a href="{programs_link}" style="color: #1a1a2e;">Explore programs</a></li>
                <li>Complete enrollment and secure your scholarship seat</li>
              </ol>
            </div>

            <div style="border-top: 1px solid #dee2e6; padding: 14px 24px; font-size: 13px; color: #6c757d;">
              Career Launcher Ahmedabad, A 102, Karmyog Heights, Navrangpura, Ahmedabad - 380009<br>
              +91 9978559986 | +91 6353842725 | cl_ahmedabad@careerlauncher.com
            </div>
          </div>
        </div>
        """

        msg = Message(subject=subject, recipients=[user.email], body=body, html=html)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error("Scholarship result email failed: %s", e)
        return False


def send_registration_welcome(user):
    from flask import current_app

    try:
        if not user.email or not str(user.email).strip():
            return False

        base_url = _base_site_url()
        login_link = f"{base_url}/login"
        dashboard_link = f"{base_url}/dashboard"
        subject = "Welcome to CL Ahmedabad — Your Account is Ready"

        plain_text = (
            f"Hi {user.first_name},\n\n"
            "Welcome to Career Launcher Ahmedabad. Your account is now ready.\n\n"
            "From your dashboard, you can:\n"
            "1. Track enrolled courses and class updates\n"
            "2. Access test history and performance insights\n"
            "3. Manage your profile and preparation journey\n\n"
            f"Login here: {login_link}\n"
            f"Dashboard: {dashboard_link}\n\n"
            "Need help? Call +91 9978559986 / +91 6353842725\n"
            "Email: cl_ahmedabad@careerlauncher.com\n\n"
            "Team Career Launcher Ahmedabad"
        )

        html_content = f"""
        <div style="font-family: Inter, Arial, sans-serif; background: #f4f6fa; padding: 24px; color: #1c1c2e;">
          <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border: 1px solid #dee2e6; border-radius: 12px; overflow: hidden;">
            <div style="background: #1a1a2e; color: #ffffff; padding: 18px 24px;">
              <h2 style="margin: 0; font-family: Poppins, Arial, sans-serif;">Welcome to CL Ahmedabad</h2>
            </div>

            <div style="padding: 22px 24px;">
              <p>Hi {user.first_name},</p>
              <p>Your account has been created successfully and your student portal is ready.</p>

              <p style="margin-bottom: 8px;"><strong>You can now:</strong></p>
              <ul style="margin-top: 0; padding-left: 18px;">
                <li>Access your enrolled courses and schedules</li>
                <li>View mock test performance and progress</li>
                <li>Manage your profile and preparation resources</li>
              </ul>

              <p style="margin-top: 16px;">
                <a href="{login_link}" style="display: inline-block; background: #c0392b; color: #ffffff; text-decoration: none; padding: 11px 16px; border-radius: 8px; font-weight: 600;">Login to Your Account</a>
              </p>

              <p style="margin-bottom: 6px;"><strong>Dashboard:</strong> <a href="{dashboard_link}">{dashboard_link}</a></p>
              <p style="margin-bottom: 6px;"><strong>Phone:</strong> <a href="tel:+919978559986">+91 9978559986</a> | <a href="tel:+916353842725">+91 6353842725</a></p>
              <p style="margin-bottom: 0;"><strong>Email:</strong> <a href="mailto:cl_ahmedabad@careerlauncher.com">cl_ahmedabad@careerlauncher.com</a></p>
            </div>

            <div style="border-top: 1px solid #dee2e6; padding: 14px 24px; color: #6c757d; font-size: 13px;">
              Career Launcher Ahmedabad, A 102, Karmyog Heights, Navrangpura, Ahmedabad 380009
            </div>
          </div>
        </div>
        """

        msg = Message(subject=subject, recipients=[user.email.strip().lower()], body=plain_text, html=html_content)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(str(e))
        return False
