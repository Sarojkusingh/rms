# RMS — Result Management System

A multi-tenant SaaS platform for educational institutions to manage students, faculty, examinations, marks, results, backlogs, and reporting — with built-in subscription billing and role-based access control.

## Features

- **Multi-Tenancy** — Each institution operates in its own isolated data space via a shared database.
- **Role-Based Access** — 7 roles: Super Admin, Institution Owner, Institution Admin, Exam Controller, HOD, Faculty, Student.
- **Academic Structure** — Departments, programs, semesters, subjects, and sections.
- **Student Management** — Profiles, enrollment, bulk import (Excel), and promotion.
- **Faculty Management** — Profiles and subject allocations.
- **Examination Scheduling** — Create exams, register students, generate admit cards.
- **Marks Entry** — Multi-stage workflow: Faculty → HOD → Exam Controller verification.
- **Result Calculation** — Automated SGPA, CGPA, and percentage computation.
- **Backlog Tracking** — Backlog registration and revaluation applications.
- **Reports & Analytics** — Per-student, per-subject, and institutional analytics with Excel/PDF export.
- **Notifications** — In-app notifications with real-time unread counts.
- **Support Tickets** — Ticketing system with messages and file attachments.
- **Subscription Billing** — Plan management, subscription lifecycle, and payment tracking.
- **Audit Trail** — Action logging across all modules.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x, Python 3.12 |
| Database | PostgreSQL 16 |
| Frontend | Bootstrap 5.3, Chart.js, Bootstrap Icons |
| PDF Generation | xhtml2pdf, ReportLab |
| Excel | openpyxl |
| QR Codes | qrcode |
| Forms | django-crispy-forms + crispy-bootstrap5 |
| Containerization | Docker, Docker Compose |

## Prerequisites

- Python 3.12+
- PostgreSQL 16+
- pip
- (Optional) Docker & Docker Compose

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/rms.git
cd rms

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values (at minimum: SECRET_KEY, DATABASE credentials)

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# (Optional) Seed demo data
python manage.py seed_demo

# Start the development server
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Docker Quick Start

```bash
docker compose up --build
```

This starts the Django app on port 8000 and a PostgreSQL 16 instance. The database is persisted in a Docker volume.

## Environment Variables

All variables are read from a `.env` file in the project root (see `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(insecure fallback)* | Django secret key — **required in production** |
| `DEBUG` | `True` | Enable/disable debug mode |
| `DATABASE_URL` | — | PostgreSQL connection (used by `DATABASES` override) |
| `DB_NAME` | `postgres` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | — | Database password |
| `DB_HOST` | `127.0.0.1` | Database host |
| `DB_PORT` | `5432` | Database port |
| `EMAIL_BACKEND` | `console` | `django.core.mail.backends.console.EmailBackend` for dev |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server host |
| `EMAIL_PORT` | `587` | SMTP server port |
| `EMAIL_USE_TLS` | `True` | Enable TLS for SMTP |
| `EMAIL_HOST_USER` | — | SMTP username |
| `EMAIL_HOST_PASSWORD` | — | SMTP password |
| `DEFAULT_FROM_EMAIL` | `RMS SaaS <noreply@rmssaas.com>` | Sender address |

## Project Structure

```
rms/
├── config/             # Django project settings, URLs, WSGI
├── accounts/           # Custom user model, auth, registration, password reset
├── tenants/            # Multi-tenancy: institutions, settings, context processor
├── academics/          # Departments, programs, semesters, subjects, sections
├── students/           # Student profiles, enrollment, import, promotion
├── faculty/            # Faculty profiles, subject allocations
├── examinations/       # Exam scheduling, registration, admit cards
├── marks/              # Marks entry and multi-stage approval workflow
├── results/            # Result calculation (SGPA/CGPA), transcripts, marksheets
├── backlogs/           # Backlog tracking and revaluation applications
├── reports/            # Analytics and report generation (Excel/PDF)
├── notifications/      # In-app notifications and context processor
├── subscriptions/      # Plans, subscriptions, usage tracking
├── payments/           # Payment records
├── support/            # Support tickets and messages
├── audit/              # Audit trail logging
├── templates/          # Global templates (67 templates, 16 directories)
├── static/             # CSS, JavaScript assets
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Multi-container orchestration
└── Makefile            # Common development commands
```

## User Roles

```
Super Admin
  └── Institution Owner
        └── Institution Admin
              ├── Exam Controller
              │     └── Faculty
              │           └── Student
              └── HOD
                    └── Faculty
                          └── Student
```

## Development Commands

| Command | Description |
|---|---|
| `make install` | Create venv and install dependencies |
| `make migrate` | Run database migrations |
| `make seed` | Load demo data |
| `make run` | Start development server |
| `make test` | Run test suite |
| `make shell` | Open Django shell |
| `make superuser` | Create a superuser |
| `make collectstatic` | Collect static files |
| `make docker-up` | Start Docker containers |
| `make docker-down` | Stop Docker containers |

## License

MIT License. See [LICENSE](LICENSE) for details.
