# 🎓 Career Launcher Ahmedabad — Institute Management Platform

> A full-stack web application built for a competitive exam coaching institute — handling everything from course discovery and scholarship tests to Razorpay payments and a rich admin panel, all in one Flask-powered platform.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red)
![Razorpay](https://img.shields.io/badge/Payments-Razorpay-072654?logo=razorpay)
![License](https://img.shields.io/badge/License-Not%20Specified-lightgrey)
![Deployment](https://img.shields.io/badge/Deploy-Heroku%20%7C%20Render-purple)
![Tests](https://img.shields.io/badge/Tests-pytest-green)

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running the Project](#running-the-project)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact](#contact)

---

## About the Project

Running a coaching institute isn't just about teaching — it's a logistics puzzle. Prospective students need to discover courses, book demo classes, attempt scholarship tests, pay fees, and track their progress. Faculty profiles need to be showcased. Leads need to be followed up. Blog articles need to be published. Payments need to be reconciled.

This platform was built to solve exactly that — for **Career Launcher Ahmedabad**, a coaching centre preparing students for CAT, CLAT, IPMAT, GMAT, CUET, and Boards exams. It replaces a patchwork of spreadsheets, WhatsApp groups, and manual follow-ups with a single, unified web application.

The target audience is twofold: **students** who get a self-service portal for courses, tests, resources, and their own dashboard, and **admins** who get a comprehensive back-office to run the entire institute without touching a line of code.

What makes it interesting is the combination of a scholarship test engine with real anti-cheat mechanisms, PDF certificate generation, Razorpay-integrated payments, and a fully dynamic site settings system — all baked into a clean Flask application.

---

## ✨ Key Features

- **Multi-exam Course Catalog** — Browse and enroll in courses for CAT, CLAT, IPMAT, GMAT, CUET, and Boards, each with detailed syllabi, FAQs, fee ranges, and batch modes (classroom / online / hybrid).
- **Scholarship Test Engine** — Students take a timed online scholarship test; the system calculates their band (Gold, Silver, Merit, Achiever, Participation) and instantly generates a downloadable PDF scholarship certificate.
- **Anti-Cheat Exam Security** — The exam JavaScript enforces fullscreen mode, tracks tab switches, blocks right-click, copy attempts, keyboard shortcuts, and DevTools — each violation is recorded and reported to the server.
- **Razorpay Payment Integration** — Students can purchase paid test series directly from the platform; signature verification ensures tamper-proof payment confirmation.
- **Student Dashboard** — A personal portal showing enrolled courses, available tests with attempt history, downloadable free resources, and a profile editor.
- **Admin Panel** — A comprehensive back-office for managing students, courses, faculty, payments, leads, test series, blog posts, scholarship questions, announcements, free resources, and site-wide settings.
- **Lead CRM** — Demo booking forms capture prospect data; admins can track status (new → contacted → enrolled → dropped) with WhatsApp quick-reply links generated automatically.
- **Blog Engine** — Rich text blog with category filtering (per exam), slug-based URLs, and SEO meta fields — powered by Quill.js on the admin side.
- **Free Resources Library** — Tokenized, time-limited download links for PDFs and external resources, protecting content from hotlinking.
- **Dynamic Site Settings** — Contact info, social links, WhatsApp number, and other site-wide values are stored in the database and editable from the admin panel — no redeployment needed.
- **Email Notifications** — Rich HTML emails sent on demo bookings, scholarship results, and other events via Flask-Mail.
- **Security-first Architecture** — Flask-Talisman enforces a strict Content Security Policy and HTTPS in production; Flask-Limiter rate-limits sensitive endpoints; CSRF protection is enabled on all forms.

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.10+ | Core language |
| Flask | Web framework |
| Flask-SQLAlchemy | ORM |
| Flask-Migrate | Database migrations (Alembic) |
| Flask-Login | Session-based authentication |
| Flask-Bcrypt | Password hashing (bcrypt, 12 rounds) |
| Flask-WTF / WTForms | Form handling and CSRF protection |
| Flask-Mail | Email delivery |
| Flask-Limiter | Rate limiting |
| Flask-Talisman | HTTP security headers & CSP |
| Razorpay (Python SDK) | Payment gateway integration |
| WeasyPrint | Scholarship certificate PDF generation |
| python-slugify | URL slug generation |
| bleach | HTML sanitisation for blog content |
| python-dotenv | Environment variable loading |
| Pillow | Image handling for uploads |
| WhiteNoise | Static file serving in production |
| Gunicorn | WSGI production server |

### Frontend
| Technology | Purpose |
|---|---|
| Jinja2 | Server-side templating |
| Custom CSS | `main.css`, `components.css`, `responsive.css` |
| Vanilla JavaScript | Interactivity, modals, loading states, counter animations |
| Quill.js (CDN) | Rich text editor in admin blog form |
| Bootstrap (CDN) | Layout utilities |

### Database
| Technology | Purpose |
|---|---|
| SQLite | Development database |
| PostgreSQL (psycopg2-binary) | Production database |

### DevOps / Other
| Technology | Purpose |
|---|---|
| Gunicorn | Production WSGI server |
| Heroku / Render | Cloud deployment targets |
| pytest / pytest-flask | Test framework |
| email-validator | Email address validation |

---

## 📁 Project Structure

```
CLAT-main/
├── app/                          # Main application package
│   ├── __init__.py               # App factory — creates and configures the Flask app
│   ├── config.py                 # DevelopmentConfig, ProductionConfig, TestingConfig
│   ├── extensions.py             # Flask extension instances (db, login_manager, mail, etc.)
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py           # Exports all models for convenience
│   │   ├── user.py               # User model (student / admin / faculty roles)
│   │   ├── course.py             # Course model with JSON syllabus/FAQs/highlights
│   │   ├── enrollment.py         # Course enrollment with scholarship % and fee paid
│   │   ├── faculty.py            # Faculty profiles with social links and achievements
│   │   ├── test_series.py        # TestSeries and TestAttempt models
│   │   ├── exam_session.py       # Timed exam session with violation tracking
│   │   ├── scholarship_question.py # Scholarship test question bank
│   │   ├── payment.py            # Razorpay payment records
│   │   ├── lead.py               # Prospect/demo booking CRM
│   │   ├── blog.py               # Blog post model with slug and categories
│   │   ├── result.py             # Student result showcase (toppers)
│   │   ├── testimonial.py        # Student testimonials
│   │   ├── free_resource.py      # Free resource library (PDFs, links, videos)
│   │   ├── announcement.py       # Site-wide announcements with date scheduling
│   │   ├── batch_schedule.py     # Batch schedule entries
│   │   └── site_setting.py       # Dynamic key-value site settings stored in DB
│   │
│   ├── routes/                   # Flask Blueprints — one per feature area
│   │   ├── __init__.py
│   │   ├── main.py               # Homepage, about, contact, free resources
│   │   ├── auth.py               # Login, logout, registration
│   │   ├── courses.py            # Course listing and detail pages
│   │   ├── faculty.py            # Faculty listing and individual profiles
│   │   ├── blog.py               # Blog listing and article pages
│   │   ├── demo.py               # Demo class booking flow
│   │   ├── results.py            # Student results showcase
│   │   ├── tests.py              # Test series listing and exam-taking engine
│   │   ├── scholarship.py        # Scholarship test flow and certificate download
│   │   ├── dashboard.py          # Student dashboard (courses, tests, resources, profile)
│   │   ├── payment.py            # Razorpay order creation and webhook verification
│   │   ├── admin.py              # Full admin panel (90KB+ — the entire back-office)
│   │   └── seo.py                # Sitemap, robots.txt, privacy policy, terms
│   │
│   ├── forms/                    # WTForms form classes
│   │   ├── __init__.py
│   │   ├── admin_forms.py        # All admin panel forms (24KB — very comprehensive)
│   │   ├── auth_forms.py         # Login and registration forms
│   │   ├── blog_form.py          # Blog post creation/editing form
│   │   ├── contact_form.py       # Public contact form
│   │   ├── demo_form.py          # Demo booking lead capture form
│   │   └── profile_form.py       # Student profile update form
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── email_service.py      # HTML email templates and sending logic
│   │   ├── payment.py            # Razorpay SDK wrappers (order, verify, fetch)
│   │   ├── scholarship.py        # Band calculation and PDF certificate generation
│   │   ├── scholarship_enrollment.py # Applies scholarship discount to enrollment
│   │   ├── enrollment_service.py # Ensures student enrollments are consistent
│   │   ├── seo_service.py        # Sitemap generation helpers
│   │   └── whatsapp.py           # WhatsApp deep-link URL builder
│   │
│   ├── utils/                    # Small utilities
│   │   ├── __init__.py
│   │   ├── decorators.py         # @admin_required decorator
│   │   └── image_handler.py      # Image upload, resize, and delete helpers
│   │
│   ├── static/                   # Static assets
│   │   ├── css/
│   │   │   ├── main.css          # Core layout and typography styles
│   │   │   ├── components.css    # Reusable UI component styles (15KB)
│   │   │   └── responsive.css    # Mobile-first responsive breakpoints
│   │   ├── js/
│   │   │   ├── main.js           # General UI interactions and initialisation
│   │   │   ├── exam-security.js  # Anti-cheat exam monitor (22KB)
│   │   │   ├── modal.js          # Modal open/close logic
│   │   │   ├── counter.js        # Animated statistics counter
│   │   │   ├── filters.js        # Client-side filter/sort helpers
│   │   │   └── loading-states.js # Button loading states and UX feedback
│   │   └── images/               # Seeded sample images (faculty, results, testimonials)
│   │
│   └── templates/                # Jinja2 HTML templates
│       ├── base.html             # Public-facing base layout
│       ├── components/           # Reusable partials (navbar, footer, cards, modals)
│       ├── main/                 # Homepage, about, contact, demo, free resources
│       ├── auth/                 # Login and registration pages
│       ├── courses/              # Course listing and detail
│       ├── faculty/              # Faculty listing and profile
│       ├── blog/                 # Blog listing and article
│       ├── tests/                # Test series listing and exam-taking UI
│       ├── scholarship/          # Scholarship info, test, and result pages
│       ├── dashboard/            # Student dashboard pages
│       ├── results/              # Student results showcase
│       ├── admin/                # Complete admin panel templates (~40 files)
│       ├── errors/               # 403, 404, and 500 error pages
│       └── seo/                  # Privacy policy and terms of service
│
├── scripts/
│   └── seed_data.py              # Comprehensive seed script (66KB) for demo data
│
├── wsgi.py                       # WSGI entry point — also handles DB init and seeding
├── requirements.txt              # Python dependencies
├── Procfile                      # Heroku/Render deployment command
├── .env.example                  # Template for environment variables
├── .flaskenv                     # Flask CLI config (FLASK_APP, FLASK_ENV)
└── .gitignore                    # Ignores venv, .env, instance/, migrations/, uploads/
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed before you begin:

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **pip** — comes bundled with Python
- **Git** — [git-scm.com](https://git-scm.com/)
- **WeasyPrint dependencies** — WeasyPrint requires system-level Cairo/Pango libraries for PDF generation. See [weasyprint.org/docs/install](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) for platform-specific instructions.
- **PostgreSQL** (production only) — [postgresql.org](https://www.postgresql.org/) — SQLite is used automatically in development.

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/shahram8708/CLAT.git
cd CLAT
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
# Now edit .env with your actual values (see Environment Variables below)
```

**5. Initialise the database and seed demo data**
```bash
python wsgi.py
```

This command creates all database tables and runs `scripts/seed_data.py` to populate demo courses, faculty, blog posts, scholarship questions, test series, and more. It also creates a default admin account.

### Environment Variables

Copy `.env.example` to `.env` and fill in all values before running the app.

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Flask secret key — must be at least 32 random bytes | `a9f2e8c1d3b7...` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///dev.db` or `postgresql://user:pass@host/db` |
| `MAIL_SERVER` | SMTP server hostname | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Enable STARTTLS | `True` |
| `MAIL_USERNAME` | SMTP login email address | `yourname@gmail.com` |
| `MAIL_PASSWORD` | SMTP password or app-specific password | `xxxx xxxx xxxx xxxx` |
| `MAIL_DEFAULT_SENDER` | From address on outgoing emails | `noreply@clahmedabad.com` |
| `ADMIN_EMAIL` | Receives lead and booking notifications | `admin@clahmedabad.com` |
| `WHATSAPP_NUMBER` | Default WhatsApp contact number | `+919978559986` |
| `RAZORPAY_KEY_ID` | Razorpay API key ID | `rzp_test_xxxxxxxxxx` |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret | `your_secret_here` |
| `GOOGLE_MAPS_API_KEY` | Google Maps embed key (contact page) | `AIzaSy...` |
| `FLASK_ENV` | Runtime environment | `development` or `production` |
| `AUTO_CREATE_TABLES` | Auto-create tables on startup (recommended on first deploy) | `true` |
| `AUTO_RUN_SEEDS` | Auto-run seed data on startup | `true` |
| `SEED_DATA_VERSION` | Seed version marker; bump this to force re-seeding logic | `2026-04-19-v1` |
| `SEED_LOCK_STALE_MINUTES` | Minutes after which a stuck seed lock can be taken over | `20` |

> **Gmail tip:** Use an [App Password](https://support.google.com/accounts/answer/185833) rather than your main Gmail password. Two-factor authentication must be enabled on your account.

### Running the Project

**Development mode**
```bash
flask run
```
The app starts at `http://127.0.0.1:5000`. Hot reload is enabled automatically in development.

**Production mode (local)**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

For Render production deployment, keep `AUTO_RUN_SEEDS=true` and set a real PostgreSQL `DATABASE_URL`. The app now uses a DB-backed seed lock so only one worker seeds at a time, while others skip safely.

**Default admin credentials** (created automatically on first run):
```
Email:    admin@clahmedabad.com
Password: Admin@CL2026!
```
Change this immediately after your first login.

---

## 📖 Usage

### As a Student

1. **Register** at `/register` with your name, email, phone, and target exam.
2. **Browse courses** at `/courses` — filter by exam category, view syllabi, FAQs, fee ranges, and batch options.
3. **Take the Scholarship Test** at `/scholarship` — answer 25 questions in 21 minutes, receive your scholarship band instantly, and download a PDF certificate.
4. **Access the Dashboard** at `/dashboard` — see your enrolled courses, attempt paid or free test series, download free resources, and update your profile.
5. **Pay for Test Series** — click "Buy Now" on any paid test series; the Razorpay checkout handles payment and instantly unlocks access.

### As an Admin

Navigate to `/admin` after logging in with an admin account. The panel provides:

- **Dashboard** — snapshot of total students, enrollments, leads, and payments at a glance.
- **Students** — search, filter, and manage all registered users; view individual profiles with enrollment history.
- **Courses** — create and edit courses with a rich form covering syllabi (JSON), FAQs, fee ranges, batch modes, and SEO meta fields.
- **Test Series** — manage free and paid test series; set prices and link to Razorpay plans.
- **Scholarship Questions** — add and organise the question bank for scholarship tests.
- **Leads** — view all demo bookings, update their status, and jump to WhatsApp with a pre-filled message.
- **Payments** — record offline payments (cash, UPI, bank transfer) or review Razorpay transactions.
- **Faculty** — publish faculty profiles with bios, qualifications, social links, and photos.
- **Blog** — write rich-text articles using the Quill editor, assign categories and SEO metadata.
- **Free Resources** — upload PDFs or add external links for students to download from the dashboard.
- **Announcements** — publish time-bounded site-wide announcements with optional start/end dates.
- **Settings** — update contact info, social links, WhatsApp number, and other site-wide values live from the UI.
- **Analytics** — view charts of leads, enrollments, and payments over time.

---

## 📡 API Documentation

The application exposes a small set of JSON endpoints, primarily for the payment and exam flows.

### Payment Endpoints

#### Create Razorpay Order
```
POST /payment/create-order
Authorization: Login required
Content-Type: application/json
```

**Request body:**
```json
{
  "test_series_id": 3,
  "amount_inr": 499
}
```

**Response (success):**
```json
{
  "status": "created",
  "order_id": "order_Abc123xyz",
  "amount_paise": 49900,
  "key_id": "rzp_test_xxxx",
  "name": "CLAT Mock Test Series",
  "redirect": "/test-series/3/start"
}
```

**Response (already purchased):**
```json
{
  "status": "already_purchased",
  "message": "You already have access to this test series.",
  "redirect": "/test-series/3/start"
}
```

#### Verify Payment Signature
```
POST /payment/verify
Authorization: Login required
Content-Type: application/json
```

**Request body:**
```json
{
  "razorpay_order_id": "order_Abc123",
  "razorpay_payment_id": "pay_Xyz789",
  "razorpay_signature": "signature_hash"
}
```

**Response:**
```json
{
  "status": "success",
  "redirect": "/test-series/3/start"
}
```

### Scholarship Exam Endpoints

#### Report Exam Violation
```
POST /scholarship/report-violation
Authorization: Login required
Content-Type: application/json
```

**Request body:**
```json
{
  "type": "tab_switch",
  "session_token": "abc123..."
}
```

**Response:**
```json
{
  "status": "ok",
  "violation_count": 2,
  "max_violations": 3
}
```

---

## ⚙️ Configuration

### Config Classes (`app/config.py`)

| Class | When Used | Debug | CSRF |
|---|---|---|---|
| `DevelopmentConfig` | `FLASK_ENV=development` | ✅ | ✅ |
| `ProductionConfig` | `FLASK_ENV=production` | ❌ | ✅ |
| `TestingConfig` | `FLASK_ENV=testing` | ✅ | ❌ |

`ProductionConfig.validate()` raises a `RuntimeError` at startup if `SECRET_KEY` is missing — preventing accidental insecure deployments.

### Database URL Handling

The config module automatically:
- Rewrites `postgres://` to `postgresql://` (Heroku compatibility).
- Normalises `sqlite:///instance/` paths so SQLite files land in Flask's instance folder correctly.

### Site Settings (Live from Admin Panel)

Many values are stored in the `site_settings` database table and are editable from `/admin/settings` without a redeployment. These include institute name, address, phone numbers, email, WhatsApp number, office hours, and social media links. They are injected into every template via the `get_setting()` context processor.

### Static Files in Production

WhiteNoise is used to serve static files from the WSGI layer in production (`app.config["ENV"] == "production"`), eliminating the need for a separate Nginx/CDN configuration for static assets in simple deployments.

### Content Security Policy

A strict CSP is configured in `app/__init__.py` and enforced by Flask-Talisman. It explicitly whitelists Razorpay, Quill.js, Bootstrap, and Google Fonts CDNs. HTTPS is forced in production but not in development.

---

## 🧪 Testing

`pytest` and `pytest-flask` are listed in `requirements.txt`, and a `TestingConfig` class is defined with CSRF disabled for test requests. However, **no test files were found in this repository**. The test infrastructure is ready to be built on.

To run tests once they are written:
```bash
pytest
```

To run with verbose output:
```bash
pytest -v
```

What to test first:
- Payment signature verification logic in `app/services/payment.py`
- Scholarship band calculation in `app/services/scholarship.py`
- Auth routes (registration, login, logout)
- Admin access control (`@admin_required` decorator)

---

## 🚢 Deployment

### Heroku

The project includes a `Procfile` ready for Heroku:
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:app
```

**Deploy steps:**

```bash
# Install Heroku CLI and log in
heroku login

# Create a new app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set all required environment variables
heroku config:set SECRET_KEY="your-long-random-secret"
heroku config:set FLASK_ENV="production"
heroku config:set MAIL_SERVER="smtp.gmail.com"
heroku config:set MAIL_PORT="587"
heroku config:set MAIL_USE_TLS="True"
heroku config:set MAIL_USERNAME="your@email.com"
heroku config:set MAIL_PASSWORD="your-app-password"
heroku config:set MAIL_DEFAULT_SENDER="noreply@yourdomain.com"
heroku config:set ADMIN_EMAIL="admin@yourdomain.com"
heroku config:set RAZORPAY_KEY_ID="rzp_live_xxx"
heroku config:set RAZORPAY_KEY_SECRET="your_secret"

# Deploy
git push heroku main

# Initialise DB and seed data on first deploy
heroku run python wsgi.py
```

### Render

The codebase references `https://clahmedabad.onrender.com` as the default site URL, so Render is the primary production target.

In your Render service configuration:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:app`
- **Environment:** Add all variables from `.env.example`
- **Database:** Add a Render PostgreSQL service and set `DATABASE_URL` to its connection string.

### WeasyPrint on Production

WeasyPrint requires system libraries (Cairo, Pango, GLib). On Heroku, add the buildpack:
```bash
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
```

Create an `Aptfile` in the project root:
```
libpango-1.0-0
libpangoft2-1.0-0
libpangocairo-1.0-0
libgdk-pixbuf2.0-0
libffi-dev
libcairo2
libpq-dev
```

On Render, these libraries are typically pre-installed on the standard Python environment.

---

## 🤝 Contributing

Contributions are welcome. Here is how to get involved:

**1. Fork the repository**

**2. Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

**3. Make your changes and commit**
```bash
git add .
git commit -m "feat: describe what you added"
```

Commit message convention: use `feat:`, `fix:`, `docs:`, `refactor:`, `test:` prefixes.

**4. Push and open a Pull Request**
```bash
git push origin feature/your-feature-name
```

Then open a PR against `main` with a clear description of what changed and why.

**Reporting Bugs**

Please open an issue with the following:
```
**Describe the bug:** A clear description of what went wrong.
**To reproduce:** Steps to reproduce the behaviour.
**Expected behaviour:** What you expected to happen.
**Environment:** OS, Python version, Flask version.
**Logs:** Paste any traceback from the Flask server.
```

**Requesting Features**

Open an issue with the label `enhancement`. Describe the use case and why the existing code doesn't cover it.

**Code Style**

- Follow PEP 8. Use `black` for formatting if contributing Python code.
- Keep route handlers thin — push business logic into `app/services/`.
- Use WTForms for all form handling; do not process raw `request.form` directly.

---

## 🗺 Roadmap

Based on the codebase structure and patterns observed:

- [x] Course catalog with multi-exam support
- [x] Student registration and login
- [x] Scholarship test engine with anti-cheat
- [x] PDF scholarship certificate generation
- [x] Razorpay payment integration for test series
- [x] Student dashboard
- [x] Full admin panel
- [x] Blog with rich-text editor
- [x] Lead CRM with WhatsApp integration
- [x] Free resources library with tokenized downloads
- [x] Dynamic site settings from admin
- [x] Email notifications for leads and scholarship results
- [ ] Write test suite (pytest infrastructure is in place, no tests yet)
- [ ] Docker / docker-compose setup for easier local development
- [ ] Student progress tracking across test attempts (analytics dashboard for students)
- [ ] Batch schedule calendar view (model exists, frontend not yet built out)
- [ ] Email campaigns / bulk notification to enrolled students
- [ ] OTP-based login / password reset flow
- [ ] Result/rank leaderboards per test series
- [ ] Mobile app API layer

---

## 📄 License

No `LICENSE` file was found in this repository. The project's license terms are not specified. If you intend to use or distribute this code, contact the author for clarification.

---

## 🙏 Acknowledgements

This project makes use of the following excellent open-source libraries and services:

- [Flask](https://flask.palletsprojects.com/) — the Python web framework doing the heavy lifting
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) — clean ORM integration
- [Flask-Talisman](https://github.com/GoogleCloudPlatform/flask-talisman) — HTTP security headers made simple
- [WeasyPrint](https://weasyprint.org/) — beautiful PDF generation from HTML/CSS
- [Razorpay](https://razorpay.com/) — payment gateway
- [Quill.js](https://quilljs.com/) — rich text editor for the blog admin
- [Bootstrap](https://getbootstrap.com/) — frontend layout utilities
- [WhiteNoise](http://whitenoise.evans.io/) — static file serving without a separate web server
- [python-slugify](https://github.com/un33k/python-slugify) — URL slug generation
- [bleach](https://github.com/mozilla/bleach) — safe HTML sanitisation

---

## 📬 Contact

**Institute:** Career Launcher Ahmedabad

**Email:** cl_ahmedabad@careerlauncher.com

**WhatsApp:** [+91 99785 59986](https://wa.me/919978559986)

**Website:** [clahmedabad.onrender.com](https://clahmedabad.onrender.com)

---

If you're reading this and thinking about contributing or deploying it for your own institute — the groundwork is solid. The patterns are consistent, the models are well-constrained, and the admin panel covers more than most institutes will ever need. Clone it, run it, and make it yours.