# Career Launcher Ahmedabad — Full-Stack Web Platform

## 1. Project Overview
Career Launcher Ahmedabad — Full-Stack Web Platform is a production-ready Flask application built for Career Launcher Ahmedabad, a competitive exam coaching institute under the CL Educate brand.

The platform includes a complete public website and core institute operations in one system.

It supports public marketing pages, demo class booking, blog publishing, scholarship test workflow, student dashboard, admin panel operations, and Razorpay powered INR payments for paid test series.

### Tech Stack
| Layer | Technology |
| --- | --- |
| Backend | Python, Flask |
| Database ORM | SQLAlchemy |
| Databases | SQLite for development, PostgreSQL for production |
| Templates | Jinja2 |
| Frontend UI | Bootstrap 5.3 |
| Authentication | Flask-Login |
| Payments | Razorpay |
| PDF Generation | WeasyPrint |

## 2. Features
### Public Pages
1. Homepage with institute highlights, courses, faculty, and results
2. About, Contact, Free Resources, Privacy Policy, and Terms pages
3. Courses listing and course detail pages
4. Faculty listing and profile pages
5. Results and toppers showcase
6. Blog listing, category filters, and article pages
7. Test series listing and exam specific test pages
8. Scholarship information page
9. SEO endpoints for sitemap.xml and robots.txt

### Student Features
1. Secure registration and login
2. Student dashboard with overview, courses, tests, resources, and profile
3. Demo booking workflow with confirmation and WhatsApp integration
4. Scholarship workflow: register, take test, result, certificate download
5. Test attempt tracking with scores and percentile history

### Admin Features
1. Admin dashboard with lead, student, enrollment, blog, and payment metrics
2. Lead management with filters, search, status updates, and CSV export
3. Student management with profile details, enrollment history, test attempts, and payment history
4. Course management with edit form and visibility control
5. Blog management with create, edit, delete, draft/published status, and Quill editor
6. Results management with active toggle
7. Payment monitoring with status filters and revenue stats

### Integrations
1. Razorpay order creation and signature verification using HMAC SHA256
2. Flask-Mail email workflows for leads, demo, and scholarship results
3. WhatsApp deep link generation for inquiry and support flows
4. WeasyPrint based scholarship certificate PDF generation

## 3. Project Structure
```text
.
├── .env
├── .env.example
├── .flaskenv
├── .gitignore
├── Procfile
├── README.md
├── requirements.txt
├── wsgi.py
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── forms
│   │   ├── __init__.py
│   │   ├── admin_forms.py
│   │   ├── auth_forms.py
│   │   ├── blog_form.py
│   │   ├── contact_form.py
│   │   ├── demo_form.py
│   │   └── profile_form.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── blog.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   ├── faculty.py
│   │   ├── lead.py
│   │   ├── payment.py
│   │   ├── result.py
│   │   ├── scholarship_question.py
│   │   ├── test_series.py
│   │   └── user.py
│   ├── routes
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── blog.py
│   │   ├── courses.py
│   │   ├── dashboard.py
│   │   ├── demo.py
│   │   ├── faculty.py
│   │   ├── main.py
│   │   ├── payment.py
│   │   ├── results.py
│   │   ├── scholarship.py
│   │   ├── seo.py
│   │   └── tests.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── email_service.py
│   │   ├── payment.py
│   │   ├── scholarship.py
│   │   ├── seo_service.py
│   │   └── whatsapp.py
│   ├── static
│   │   ├── css
│   │   │   ├── components.css
│   │   │   ├── main.css
│   │   │   └── responsive.css
│   │   └── js
│   │       ├── counter.js
│   │       ├── filters.js
│   │       ├── main.js
│   │       └── modal.js
│   ├── templates
│   │   ├── admin
│   │   │   ├── base.html
│   │   │   ├── blog.html
│   │   │   ├── blog_edit.html
│   │   │   ├── course_edit.html
│   │   │   ├── courses.html
│   │   │   ├── dashboard.html
│   │   │   ├── leads.html
│   │   │   ├── payments.html
│   │   │   ├── results.html
│   │   │   ├── student_detail.html
│   │   │   └── students.html
│   │   ├── auth
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── blog
│   │   │   ├── article.html
│   │   │   └── listing.html
│   │   ├── components
│   │   │   ├── _blog_card.html
│   │   │   ├── _course_card.html
│   │   │   ├── _demo_modal.html
│   │   │   ├── _faculty_card.html
│   │   │   ├── _flash_messages.html
│   │   │   ├── _footer.html
│   │   │   ├── _form_errors.html
│   │   │   ├── _navbar.html
│   │   │   └── _result_card.html
│   │   ├── courses
│   │   │   ├── detail.html
│   │   │   └── listing.html
│   │   ├── dashboard
│   │   │   ├── base.html
│   │   │   ├── courses.html
│   │   │   ├── overview.html
│   │   │   ├── profile.html
│   │   │   ├── resources.html
│   │   │   └── tests.html
│   │   ├── errors
│   │   │   ├── 403.html
│   │   │   ├── 404.html
│   │   │   └── 500.html
│   │   ├── faculty
│   │   │   ├── listing.html
│   │   │   └── profile.html
│   │   ├── main
│   │   │   ├── about.html
│   │   │   ├── contact.html
│   │   │   ├── demo.html
│   │   │   ├── demo_success.html
│   │   │   ├── free_resources.html
│   │   │   └── index.html
│   │   ├── results
│   │   │   └── index.html
│   │   ├── scholarship
│   │   │   ├── info.html
│   │   │   ├── result.html
│   │   │   └── test.html
│   │   ├── seo
│   │   │   ├── privacy_policy.html
│   │   │   └── terms.html
│   │   ├── tests
│   │   │   ├── exam_tests.html
│   │   │   └── listing.html
│   │   └── base.html
│   └── utils
│       ├── __init__.py
│       └── decorators.py
├── instance
├── scripts
│   └── seed_data.py
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    └── test_routes.py
```

## 4. Local Development Setup
1. Clone repository
```bash
git clone <repo-url>
cd cl-ahmedabad
```

2. Create and activate virtual environment
```bash
python -m venv venv
```

Windows PowerShell
```powershell
.\venv\Scripts\Activate.ps1
```

Mac and Linux
```bash
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Copy environment file and fill actual values
```bash
cp .env.example .env
```
Windows alternative
```powershell
Copy-Item .env.example .env
```

5. Run the application
```bash
python wsgi.py
```
On first run, startup will automatically create database tables, apply idempotent seed data, and ensure the default admin user exists.

6. Open the app
```text
http://localhost:5000
```

7. Access admin panel
Login
```text
http://localhost:5000/login
```
Credentials
```text
admin@clahmedabad.com
Admin@CL2025!
```
Admin panel
```text
http://localhost:5000/admin
```

## 5. Environment Variables
| Variable | Description | Example | Required |
| --- | --- | --- | --- |
| SECRET_KEY | Flask secret key for sessions and CSRF | your-minimum-32-byte-secret-key-here | Yes |
| DATABASE_URL | Database connection URL | sqlite:///instance/dev.db | Yes |
| MAIL_SERVER | SMTP server host | smtp.gmail.com | Yes for email features |
| MAIL_PORT | SMTP server port | 587 | Yes for email features |
| MAIL_USE_TLS | Enable TLS for SMTP | True | Yes for email features |
| MAIL_USERNAME | SMTP login username | your-email@gmail.com | Yes for email features |
| MAIL_PASSWORD | SMTP app password | abcd efgh ijkl mnop | Yes for email features |
| MAIL_DEFAULT_SENDER | Default sender address | noreply@clahmedabad.com | Yes for email features |
| ADMIN_EMAIL | Admin contact email reference | cl_ahmedabad@careerlauncher.com | Optional |
| WHATSAPP_NUMBER | WhatsApp support number | +919978559986 | Optional |
| RAZORPAY_KEY_ID | Razorpay key id used in checkout | rzp_test_xxxxx | Yes for payments |
| RAZORPAY_KEY_SECRET | Razorpay secret used for signing and verification | your-razorpay-key-secret | Yes for payments |
| GOOGLE_MAPS_API_KEY | Google Maps API key for map integrations | your-google-maps-api-key | Optional |
| FLASK_ENV | Flask environment mode | development | Yes |

## 6. Database Migrations
Flask-Migrate is supported for schema evolution.

Initialize once
```bash
flask db init
```

Create migration
```bash
flask db migrate -m "description"
```

Apply migration
```bash
flask db upgrade
```

Development note
In development, `wsgi.py` auto creates tables on startup. Migrations are still required for production schema changes.

## 7. Razorpay Setup
1. Create account at https://razorpay.com
2. Open Settings and then API Keys
3. Generate Test Mode keys
4. Copy Key ID and Key Secret into `.env`
5. For production, replace test keys with Live Mode keys
6. Optional webhook can point to `/payment/verify`

All payments in this platform are processed in INR only.

## 8. Email Configuration
For Gmail SMTP with two factor authentication

1. Enable 2FA on Google account
2. Open Google Account Security settings
3. Generate App Password for Mail
4. Put generated app password into `MAIL_PASSWORD` in `.env`
5. Ensure `MAIL_SERVER=smtp.gmail.com`, `MAIL_PORT=587`, `MAIL_USE_TLS=True`

Regular Gmail password should not be used when 2FA is enabled.

## 9. Production Deployment (Heroku or Render)
Recommended Render workflow

1. Create a new Web Service in Render dashboard or configure through `render.yaml`
2. Connect repository branch
3. Add environment variables from `.env.example`
4. Create and attach Render PostgreSQL database, then set `DATABASE_URL`
5. Set `FLASK_ENV=production`
6. Start command
```bash
gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:app
```

Static assets are served through WhiteNoise, already configured in app factory.

## 10. Admin Panel Usage
1. Login as admin and open `/admin`
2. Leads page supports search, status filters, inline status updates, and CSV export
3. Students page supports account lookup and active status toggling
4. Course management allows editing fee ranges, mode, and display order
5. Blog management supports draft and publish workflow with Quill rich text editor
6. Results page supports active visibility toggles
7. Payments page shows transaction status and revenue summary

## 11. Scholarship Test
Scholarship user flow

1. Student registers from scholarship page
2. Student takes 20 question scholarship test
3. System calculates band and scholarship percentage
4. Result page displays score, band, and scholarship benefit
5. Student downloads scholarship certificate PDF generated by WeasyPrint

## 12. Contributing
1. Fork and create a branch from `main`
2. Branch naming
   1. `feature/<short-name>` for new features
   2. `fix/<short-name>` for bug fixes
   3. `docs/<short-name>` for documentation updates
3. Commit with clear messages
4. Add or update tests for behavior changes
5. Open PR with scope summary, screenshots if UI changes, and testing notes
6. Wait for review and merge approval

## 13. License
MIT License — Career Launcher Ahmedabad
