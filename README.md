<div align="center">

# 🏫 School ERP Backend API

### A Modern, Async-First School Management System

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-2.0.0-blueviolet?style=for-the-badge)

**Built with:** FastAPI + SQLAlchemy 2.0 (Async) + PostgreSQL + Alembic + Pydantic v2

[Features](#-features) • [Tech Stack](#-tech-stack) • [Quick Start](#-quick-start) • [API Docs](#-api-documentation) • [Project Structure](#-project-structure)

</div>

---

## 📖 About the Project

**School ERP Backend API** is a comprehensive, production-grade **Enterprise Resource Planning** system built exclusively for schools. It provides a powerful RESTful API that covers every aspect of school administration — from student enrollment and teacher management to examinations, fee collection, attendance tracking, and third-party integrations.

This is a **backend-only API** built with modern Python async patterns. It is designed to be consumed by any frontend (React, Next.js, Flutter, etc.) or mobile application.

### Why This Project?

- **Fully Async** — Built on FastAPI + asyncpg for high-concurrency, non-blocking I/O
- **Domain-Driven Design** — Clean, scalable architecture with 21 business domains
- **Role-Based Access** — Granular RBAC for Admin, Teacher, Student, and Parent roles
- **Production Ready** — JWT auth, structured logging, rate limiting, migrations, and test suite
- **Integration Friendly** — Webhook-based integrations with Exam Engine, Khan Academy, and Zoom

---

## ✨ Features

| Category | Capabilities |
|----------|-------------|
| 👨‍🎓 **Student Management** | Enrollment, profiles, attendance, exam results, fee tracking, ID cards with QR codes |
| 👩‍🏫 **Teacher Management** | Profiles, subject assignments, class assignments, attendance marking, availability |
| 📚 **Academics** | Academic sessions, classrooms, subjects, class-subject mappings |
| 📝 **Examinations** | Exam creation, scheduling, result recording, grading, Exam Engine integration |
| 📋 **Assignments** | Create, publish, submit, grade — full assignment lifecycle |
| 💰 **Fee Management** | Monthly fee generation, payment tracking, partial payments |
| 📊 **Attendance** | Daily class attendance, summary statistics |
| 🗓️ **Timetable** | Weekly schedules with time slots and teacher availability |
| 💬 **Communication** | Student-Teacher chat, notices & announcements |
| 🔗 **Integrations** | Zoom meetings/recordings/transcripts, Khan Academy progress, Exam Engine sync |
| 📄 **Reports** | Student progress reports with PDF/HTML generation |
| 🪪 **ID Cards** | Student ID card generation with QR codes and PDF rendering |
| 🔍 **Search** | Fuzzy search for students and teachers |
| 📈 **Dashboards** | Role-specific dashboards (Student, Teacher, Admin) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ |
| **Web Framework** | FastAPI 0.115 |
| **ASGI Server** | Uvicorn 0.30 |
| **ORM** | SQLAlchemy 2.0 (Async) |
| **Database** | PostgreSQL (via asyncpg) |
| **Migrations** | Alembic 1.18 |
| **Validation** | Pydantic v2 + pydantic-settings |
| **Authentication** | JWT (python-jose) + bcrypt |
| **PDF Generation** | ReportLab + Pillow + QRCode |
| **Search** | RapidFuzzy (fuzzy text matching) |
| **Testing** | pytest + pytest-asyncio + httpx |
| **Linting** | Ruff + Black + isort |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** installed
- **PostgreSQL** installed and running
- **Git** installed

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/school-erp-backend.git
cd school-erp-backend
```

### Step 2: Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` and configure the following **required** variables:

```env
# Database
DATABASE_URL=postgresql://erp_user:your-password@localhost:5432/school_erp

# Security (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-256-bit-secret-here

# SMTP (for email features)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Institute Info (for ID cards & reports)
INSTITUTE_NAME=Your School Name
INSTITUTE_CONTACT=+91-XXXXXXXXXX
```

### Step 5: Create the Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE school_erp;
CREATE USER erp_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE school_erp TO erp_user;
\q
```

### Step 6: Run Database Migrations

```bash
# Generate initial migration (if not already present)
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head
```

### Step 7: Seed User Accounts

```bash
python -m scripts.seed_accounts
```

This creates all user accounts: **3 Admins, 6 Teachers, 30 Students**.
After seeding, the admin can log in and manage everything else (academics, exams, fees, etc.) via the API.

**Default Credentials:**

| Role | Email | Password |
|------|-------|----------|
| Admin (Super) | `admin@school.com` | `password123` |
| Admin | `admin2@school.com` | `password123` |
| Teacher | `teacher1@school.com` | `password123` |
| Student | `student1@school.com` | `password123` |

### Step 8: Start the Server

```bash
# Development (with auto-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📡 API Documentation

Once the server is running, access:

| Resource | URL |
|----------|-----|
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) |

### Authentication Flow

```bash
# 1. Login to get tokens
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@school.com&password=password123"

# 2. Use the access token in subsequent requests
curl http://localhost:8000/admin/students \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### API Endpoints Overview

| Prefix | Module | Auth |
|--------|--------|------|
| `/auth/*` | Login, Logout, Refresh, Password Reset, OTP | Public / JWT |
| `/admin/*` | User CRUD, Profile Management | Admin |
| `/users/*` | Self-service profile (GET/PATCH /me) | JWT |
| `/academics/*` | Sessions, Classrooms, Subjects | Admin |
| `/operations/*` | Teacher Assignments, Enrollments | Admin/Teacher |
| `/fees/*` | Fee CRUD, Payment Recording | Admin/Student |
| `/exams/*` | Exam CRUD, Result Upload | Admin/Teacher |
| `/assignments/*` | Assignment CRUD, Grading | Admin/Teacher |
| `/student/*` | Student Self-service | Student |
| `/teacher/*` | Teacher Self-service | Teacher |
| `/dashboard/*` | Role-specific Dashboards | JWT |
| `/notices/*` | Notices & Announcements | Admin/JWT |
| `/chat/*` | Student-Teacher Chat | JWT |
| `/curriculum/*` | Subjects & Topics | Admin |
| `/id_cards/*` | ID Card Generation (PDF+QR) | Admin |
| `/search/*` | Fuzzy Student/Teacher Search | JWT |
| `/study_material/*` | Study Material Uploads | Admin/Teacher |
| `/reports/*` | Progress Reports (PDF) | Admin/Teacher |
| `/zoom/*` | Zoom Meeting Data | Admin |
| `/khan_academy/*` | Khan Academy Sync | Admin |
| `/integration/*` | Exam Engine Inbound Sync | API Key |
| `/webhooks/*` | Exam Engine Webhooks | Webhook Token |

---

## 📁 Project Structure

```
merged/
├── alembic/                     # Database migration framework
│   ├── versions/                # Migration files
│   └── env.py                   # Async Alembic environment
│
├── scripts/                     # CLI utility scripts
│   ├── __init__.py
│   └── seed_accounts.py         # Seed all user accounts (admin, teacher, student)
│
├── src/                         # Main application source
│   ├── main.py                  # FastAPI app factory
│   │
│   ├── api/                     # HTTP Layer
│   │   ├── dependencies.py      # Auth & role dependencies
│   │   └── routers/             # 25 API router modules
│   │
│   ├── core/                    # Cross-cutting concerns
│   │   ├── security.py          # JWT, bcrypt, OTP
│   │   ├── email.py             # Async SMTP email
│   │   ├── exceptions.py        # Exception hierarchy
│   │   ├── enums.py             # Business constants
│   │   ├── id_generators.py     # Business ID formatting
│   │   └── logger.py            # Structured JSON logging
│   │
│   ├── database/                # Data access layer
│   │   ├── base.py              # Model registration
│   │   ├── base_crud.py         # Generic async CRUD (400+ lines)
│   │   └── connection.py        # Engine & session factory
│   │
│   └── domain/                  # Business domains (21 modules)
│       ├── academics/           # Sessions, classrooms, subjects
│       ├── admin/               # Admin service
│       ├── assignments/         # Assignments & results
│       ├── attachments/         # Polymorphic file store
│       ├── auth/                # Authentication & OTP
│       ├── chat/                # Chat rooms & messages
│       ├── curriculum/          # Subjects & topics
│       ├── dashboard/           # Dashboard aggregations
│       ├── exam_engine/         # Exam Engine integration
│       ├── exams/               # Exams & results
│       ├── fees/                # Fee management
│       ├── id_cards/            # ID card generation
│       ├── khan_academy/        # Khan Academy tracking
│       ├── notices/             # Notices & announcements
│       ├── operations/          # Enrollments, timetable, attendance
│       ├── reports/             # Progress reports (PDF)
│       ├── search/              # Fuzzy search
│       ├── study_material/      # Study material uploads
│       ├── users/               # User management
│       └── zoom/                # Zoom integration
│
├── tests/                       # Test suite
│   ├── conftest.py              # Fixtures & test DB setup
│   ├── test_admin.py            # Admin CRUD tests
│   ├── test_public.py           # Auth flow tests
│   ├── test_student.py          # Student permission tests
│   └── test_teacher.py          # Teacher permission tests
│
├── uploads/                     # File uploads directory
├── logs/                        # Application logs
├── docs/                        # Documentation
│
├── .env.example                 # Environment variable template
├── alembic.ini                  # Alembic configuration
├── pyproject.toml               # Ruff linter config
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | — | JWT signing secret (256-bit hex) |
| `APP_NAME` | ❌ | `Student ERP Backend` | Application name |
| `APP_VERSION` | ❌ | `1.0.0` | Version string |
| `APP_ENV` | ❌ | `production` | Environment mode |
| `DEBUG` | ❌ | `false` | Debug mode |
| `AUTO_CREATE_TABLES` | ❌ | `true` | Auto-create tables on startup |
| `SQL_ECHO` | ❌ | `false` | Log SQL queries |
| `ALGORITHM` | ❌ | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `60` | Token expiry (minutes) |
| `UPLOAD_DIR` | ❌ | `uploads` | File upload directory |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `SMTP_SERVER` | ❌ | `smtp.gmail.com` | SMTP host |
| `SMTP_PORT` | ❌ | `587` | SMTP port |
| `SMTP_EMAIL` | ❌ | — | Sender email |
| `SMTP_PASSWORD` | ❌ | — | SMTP app password |
| `FRONTEND_URL` | ❌ | — | Frontend URL for CORS |
| `CORS_ORIGINS` | ❌ | `*` | Comma-separated allowed origins |
| `INSTITUTE_NAME` | ❌ | — | School name (ID cards, reports) |
| `INSTITUTE_CONTACT` | ❌ | — | School phone (ID cards) |
| `INTEGRATION_API_KEY` | ❌ | — | Exam Engine API key |
| `EXAM_ENGINE_WEBHOOK_TOKEN` | ❌ | — | Exam Engine webhook token |

---

## 🔒 Security Features

- **JWT Authentication** — Access tokens (60min) + Refresh tokens (7 days)
- **Password Hashing** — bcrypt with salt
- **Token Revocation** — Logout invalidates tokens via jti tracking
- **OTP Flows** — Email verification, passwordless login, password reset (hashes stored, not plaintext)
- **Role-Based Access Control** — Admin, Teacher, Student, Parent roles
- **API Key Auth** — For external integration endpoints
- **Webhook Auth** — Token-based webhook verification
- **Rate Limiting** — 100 requests/minute on integration endpoints
- **Anti-Enumeration** — Forgot-password/login-OTP always return 204 regardless of email existence
- **Request Size Limits** — 1MB max on webhooks
- **Request Tracing** — UUID-based request IDs for debugging

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_admin.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

**Test Database:** Tests use a separate database (`faizan20_test`). Update the connection string in `tests/conftest.py` if needed.

**Test Coverage:**
- Admin CRUD & academics operations
- Public auth flows (login, refresh, logout, password change)
- Student self-service & role isolation
- Teacher self-service & role isolation

---

## 🗃️ Database

### Default Tables (17 model modules)

| Domain | Tables |
|--------|--------|
| Users | `users`, `student_profiles`, `teacher_profiles`, `admin_profiles` |
| Auth | `revoked_tokens`, `otp_codes` |
| Academics | `academic_sessions`, `classroom`, `class_subjects` |
| Curriculum | `subjects`, `ka_topics` |
| Operations | `teacher_subjects`, `student_classes`, `class_timetable`, `student_attendance` |
| Exams | `exams`, `exam_results` |
| Assignments | `assignments`, `assignment_results` |
| Fees | `fees` |
| Notices | `notices` |
| Chat | `chat_rooms`, `chat_messages` |
| Attachments | `attachments` |
| Zoom | `zoom_meetings`, `zoom_recording_files`, `zoom_transcripts` |
| Khan Academy | `ka_student_activities`, `ka_subject_progress` |
| Reports | `student_reports`, `student_activity_reports` |

### Useful Commands

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply latest migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## 🔗 Third-Party Integrations

### Exam Engine (ns-exam)
- **Inbound Sync:** REST API at `/integration/academic/*` (API Key auth)
- **Outbound Webhooks:** `/webhooks/*` for report-generated & student-at-risk events (Webhook Token auth)

### Khan Academy
- Student progress tracking and activity logs via `/khan_academy/*`

### Zoom
- Meeting recordings, transcripts, participant tracking, student interaction analysis via `/zoom/*`

---

## 🚢 Deployment

### Production Checklist

1. Set `AUTO_CREATE_TABLES=false` in `.env`
2. Use Alembic for schema management
3. Generate a strong `SECRET_KEY`
4. Configure `CORS_ORIGINS` with your frontend domain
5. Set `APP_ENV=production` and `DEBUG=false`
6. Use a production ASGI server (Uvicorn with workers)
7. Set up a reverse proxy (Nginx/Caddy)
8. Configure SSL/TLS
9. Set up database backups
10. Configure log rotation (already built-in: 5MB max, 5 backups)

### Run with Multiple Workers

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Formatting:** Black
- **Import Sorting:** isort
- **Linting:** Ruff

```bash
# Format code
black .

# Sort imports
isort .

# Lint
ruff check .
```

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 📞 Support

For issues and questions:
- Open an issue on [GitHub Issues](https://github.com/your-username/school-erp-backend/issues)
- Check the [API Documentation](http://localhost:8000/docs) (when server is running)

---

<div align="center">

**Built with ❤️ for Schools Everywhere**

</div>
