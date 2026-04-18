from datetime import datetime

from flask import current_app
from weasyprint import HTML


def calculate_scholarship_band(score, max_score):
    try:
        numeric_score = float(score or 0)
        numeric_max = float(max_score or 0)
        percentage_raw = (numeric_score / numeric_max) * 100 if numeric_max > 0 else 0.0
    except (TypeError, ValueError, ZeroDivisionError):
        percentage_raw = 0.0

    percentage = round(percentage_raw, 1)

    if percentage >= 90:
        scholarship_pct = 50
        band_name = "Gold Scholar"
        message = (
            "Outstanding performance. You have unlocked the Gold Scholar benefit. "
            "Complete your enrollment quickly because limited seats are available under this band."
        )
    elif percentage >= 75:
        scholarship_pct = 35
        band_name = "Silver Scholar"
        message = "Congratulations on a strong performance. You have earned an excellent scholarship benefit."
    elif percentage >= 60:
        scholarship_pct = 25
        band_name = "Merit Scholar"
        message = "Great work. Your score reflects solid preparation and earns you a meaningful scholarship."
    elif percentage >= 45:
        scholarship_pct = 15
        band_name = "Achiever Scholar"
        message = "Good effort. Keep building momentum and use this scholarship to move ahead with confidence."
    else:
        scholarship_pct = 10
        band_name = "Participation Benefit"
        message = (
            "Thank you for attempting the scholarship test. "
            "You still receive a participation scholarship to support your preparation journey."
        )

    return {
        "percentage": percentage,
        "scholarship_pct": scholarship_pct,
        "band_name": band_name,
        "message": message,
    }


def generate_certificate_pdf(user, scholarship_pct, band_name):
    try:
        issue_date = datetime.utcnow().strftime("%d %B %Y")
        program_name = (getattr(user, "enrolled_exam", None) or "selected").strip() if getattr(user, "enrolled_exam", None) else "selected"
        student_name = user.get_full_name()

        html_content = f"""
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
          <meta charset=\"utf-8\">
          <title>CL Ahmedabad Scholarship Certificate</title>
          <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
            * {{ box-sizing: border-box; }}
            body {{
              margin: 0;
              padding: 0;
              font-family: 'Poppins', Arial, sans-serif;
              color: #1C1C2E;
              background: #FFFFFF;
            }}
            .page {{
              width: 100%;
              min-height: 100vh;
              border: 10px solid #1A1A2E;
              padding: 28px 36px 32px;
            }}
            .header {{
              background: #1A1A2E;
              color: #FFFFFF;
              text-align: center;
              padding: 26px 20px;
              border-radius: 8px;
              margin-bottom: 28px;
            }}
            .header h1 {{
              margin: 0;
              font-size: 30px;
              font-weight: 800;
              letter-spacing: 0.4px;
            }}
            .title {{
              text-align: center;
              color: #C0392B;
              font-size: 28px;
              font-weight: 700;
              margin: 2px 0 26px;
            }}
            .text-center {{
              text-align: center;
            }}
            .line1 {{
              font-size: 18px;
              margin: 0;
            }}
            .student-name {{
              margin: 14px 0 18px;
              font-size: 42px;
              font-weight: 800;
              color: #1A1A2E;
            }}
            .award-text {{
              font-size: 17px;
              line-height: 1.7;
              margin: 0 auto 20px;
              max-width: 92%;
            }}
            .band-box {{
              margin: 20px auto 24px;
              background: #FDF2F1;
              border: 2px solid #C0392B;
              border-radius: 10px;
              padding: 14px 16px;
              display: inline-block;
              font-size: 20px;
              font-weight: 700;
              color: #C0392B;
            }}
            .meta {{
              margin-top: 10px;
              text-align: center;
              font-size: 15px;
              color: #2C3E7A;
            }}
            .validity {{
              margin-top: 10px;
              text-align: center;
              font-size: 14px;
              color: #6C757D;
            }}
            .footer {{
              margin-top: 42px;
              border-top: 1px solid #DEE2E6;
              padding-top: 18px;
              display: table;
              width: 100%;
            }}
            .footer-left,
            .footer-right {{
              display: table-cell;
              vertical-align: top;
              width: 50%;
            }}
            .footer-left {{
              font-size: 13px;
              color: #1C1C2E;
              line-height: 1.7;
            }}
            .signature-wrap {{
              text-align: center;
              padding-left: 28px;
            }}
            .signature-line {{
              margin: 34px auto 6px;
              width: 220px;
              border-top: 1px solid #1C1C2E;
            }}
            .signature-label {{
              font-size: 13px;
              color: #1C1C2E;
              font-weight: 600;
            }}
          </style>
        </head>
        <body>
          <div class=\"page\">
            <div class=\"header\">
              <h1>Career Launcher Ahmedabad</h1>
            </div>

            <div class=\"title\">Merit Scholarship Certificate</div>

            <div class=\"text-center\">
              <p class=\"line1\">This is to certify that</p>
              <p class=\"student-name\">{student_name}</p>
              <p class=\"award-text\">
                has been awarded a <strong>{int(scholarship_pct)}%</strong> scholarship on the tuition fee
                for the <strong>{program_name}</strong> program at Career Launcher Ahmedabad.
              </p>
              <div class=\"band-box\">{band_name} - {int(scholarship_pct)}% Fee Waiver</div>
            </div>

            <div class=\"meta\">Date of Issuance: {issue_date}</div>
            <div class=\"validity\">This certificate is valid for enrollment within 30 days of the date of issue.</div>

            <div class=\"footer\">
              <div class=\"footer-left\">
                Career Launcher Ahmedabad<br>
                A 102, Karmyog Heights, Navrangpura, Ahmedabad - 380009<br>
                +91 9978559986 | +91 6353842725<br>
                cl_ahmedabad@careerlauncher.com
              </div>
              <div class=\"footer-right signature-wrap\">
                <div class=\"signature-line\"></div>
                <div class=\"signature-label\">Director's Signature</div>
              </div>
            </div>
          </div>
        </body>
        </html>
        """

        return HTML(string=html_content).write_pdf()
    except Exception as exc:
        current_app.logger.error("Scholarship certificate PDF generation failed: %s", exc)
        return None
