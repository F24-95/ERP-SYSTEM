# School ERP Backend — `final_model_v3_refactored`

An async, domain-driven FastAPI backend for a school management system: users
& roles, academics, enrollment, attendance, assignments, exams, fees,
notices, study material, chat, ID cards, file attachments, dashboards,
search, Khan Academy progress tracking, Zoom class-recording data, and
generated student reports.

This is a full OOP/async rewrite of an earlier synchronous project
(`mmmmmm.zip` / legacy `FOLDER/app`), rebuilt around SQLAlchemy 2.0 async
ORM, a layered service architecture, and centralized error handling —
while preserving (and in several places fixing) the original's business
logic.

---

## 1. Architecture

Every feature lives in its own **domain** under `src/domain/<name>/`, with
four consistent layers:

```
Request
  │
  ▼
src/api/routers/<name>.py     — FastAPI routes: parse input, check auth/role, call service
  │
  ▼
src/domain/<name>/service.py  — business logic: validation, authorization rules,
  │                              orchestration across models, raises typed exceptions
  ▼
src/domain/<name>/crud.py     — thin AsyncBaseCRUD wrapper per model (generic get/create/
  │                              update/delete/paginate/search/upsert/bulk ops)
  ▼
src/domain/<name>/models.py   — SQLAlchemy 2.0 async ORM models (the actual tables)
```

Pydantic schemas for request/response validation live alongside each domain
in `schemas.py`.

### Why this shape

- **Routers stay thin.** They only do request parsing, dependency injection
  (auth/db session), and calling one service method. No business logic in
  routers.
- **Services own the rules.** Duplicate-checks, permission checks, cross-model
  orchestration (e.g. "promoting" a student = write history + close old
  enrollment + open new one) all live in `service.py`, as plain classes with
  `@staticmethod` methods — no framework coupling, easy to unit test.
- **CRUD is generic and reusable.** `AsyncBaseCRUD[Model]` (in
  `src/database/base_crud.py`) implements `get`, `get_or_raise`, `get_all`,
  `get_by`, `get_by_filters`, `get_many`, `create`, `update`, `delete`,
  `soft_delete`, `restore`, `exists`, `paginate`, `search`, `bulk_create`,
  `bulk_update`, `bulk_delete`, `first_or_create`, `upsert`, `with_relations`.
  Every domain's `crud.py` just instantiates it once per model — almost no
  domain ever needs custom CRUD code.
- **Errors are typed, not generic `HTTPException`s.** `src/core/exceptions.py`
  defines `ResourceNotFoundException`, `BusinessLogicException`,
  `AuthenticationException`, `AuthorizationException`, `ValidationException`,
  each mapping to the right HTTP status via a global exception handler — so
  services can `raise BusinessLogicException("...")` without importing
  FastAPI at all.

### Directory map

```
src/
├── main.py                     # FastAPI app factory, router registration, exception handlers
├── core/                       # cross-cutting: config-free helpers used by every domain
│   ├── security.py             #   password hashing, JWT create/verify (access/refresh/reset)
│   ├── exceptions.py           #   typed exception hierarchy
│   ├── enums.py                #   UserRole and other shared enums
│   ├── logger.py                #   structured logger (console + JSON file, request/user context)
│   ├── email.py                 #   email sending (OTP, reset link, verification)
│   └── id_generators.py         #   human-readable business IDs (student_id, teacher_id, ...)
├── database/
│   ├── connection.py            #   async engine/session factory, Base, get_db() dependency
│   ├── base.py                  #   imports every model so Base.metadata knows all 50 tables
│   └── base_crud.py             #   AsyncBaseCRUD[T] generic
├── api/
│   ├── dependencies.py          #   get_current_user, require_role(...), require_super_admin
│   └── routers/                 #   one file per domain, all included from main.py
└── domain/
    ├── users/                   #   User, StudentProfile, TeacherProfile, AdminProfile
    ├── auth/                    #   AuthService — login, tokens, password/email/OTP flows
    ├── academics/                #   AcademicSession, ClassRoom, Subject, ClassSubject
    ├── operations/                #   TeacherSubject, StudentClass, promotion, timetable,
    │                              #   daily classes, attendance
    ├── assignments/, exams/       #   + *Result child tables
    ├── fees/
    ├── notices/, study_material/, chat/, id_cards/, attachments/
    ├── dashboard/, search/
    ├── ka_tracking/               #   Khan Academy topic catalog + synced progress
    ├── zoom/                      #   Zoom meetings/recordings/transcripts/participants
    ├── reports/                    #   generated student progress reports
    └── common/                    #   shared Pydantic schemas (pagination, generic response)
```

---

## 2. Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0, async engine (`asyncpg` for Postgres) |
| Validation | Pydantic v2 |
| Auth | JWT (access + refresh + password-reset, each with its own `type` claim), OAuth2 password flow, `passlib`/`bcrypt` hashing |
| Migrations | Alembic (`alembic/`, `alembic.ini`) |
| Docs | Auto-generated OpenAPI/Swagger at `/docs`, ReDoc at `/redoc` |

See `requirements.txt` for exact pinned versions.

---

## 3. Running locally

```bash
pip install -r requirements.txt --break-system-packages   # or use a venv

# configure DB connection, JWT secret, SMTP, etc. via environment variables
# (see src/core/security.py and src/core/email.py for the variable names)

alembic upgrade head          # apply migrations
uvicorn src.main:app --reload # start the API
```

Interactive API docs: `http://localhost:8000/docs`

---

## 4. Domains at a glance

| Domain | Purpose | Key tables |
|---|---|---|
| `users` | Accounts + role profiles | `users`, `student_profiles`, `teacher_profiles`, `admin_profiles` |
| `auth` | Login, tokens, password/email/OTP flows | (writes to `users`) |
| `academics` | Sessions, classes, subjects, subject↔class mapping | `academic_sessions`, `classroom`, `subjects`, `class_subjects` |
| `operations` | Teacher assignment, enrollment, promotion, timetable, daily classes, attendance | `teacher_subjects`, `student_classes`, `student_promotion_history`, `week_days`, `time_slots`, `class_timetable`, `teacher_availability`, `daily_classes`, `daily_class_students`, `student_attendance` |
| `assignments` | Homework + grading | `assignments`, `assignment_results` |
| `exams` | Exams + grading | `exams`, `exam_results` |
| `fees` | Fee records + payments | `fees` |
| `notices` | School-wide announcements | `notices` |
| `study_material` | Uploaded learning material | `study_materials` |
| `chat` | Class-scoped chat rooms | `chat_rooms`, `chat_messages` |
| `id_cards` | Generated student ID cards | `student_id_cards` |
| `attachments` | Generic polymorphic file store | `attachments` |
| `dashboard` | Aggregated summaries per role | (reads across domains) |
| `search` | Student/teacher search | (reads `users`/profiles) |
| `ka_tracking` | Khan Academy topic catalog + synced activity/progress | `ka_topics`, `ka_student_activities`, `ka_subject_activities`, `ka_subject_progress`, `ka_topic_progress` |
| `zoom` | Zoom meetings/recordings/transcripts/participants + legacy session-file bundle | `zoom_meetings`, `zoom_recording_files`, `zoom_transcripts`, `zoom_student_interactions`, `zoom_participants`, `processed_meetings`, `processed_participants`, `raw_meetings`, `raw_participants`, `zoom_files` |
| `reports` | Generated per-student progress reports (PDF/HTML/PNG) | `student_reports` + 5 child aggregate tables |

Full endpoint list: see **`API_REFERENCE.md`**.
Full table/relationship list: see **`DATABASE_SCHEMA.md`**.
What changed in the port from the legacy sync project: see **`CHANGELOG.md`**.

---

## 5. Authentication model

- **Access token** (`type=access`, short-lived) — required on every
  protected endpoint via `Authorization: Bearer <token>`.
- **Refresh token** (`type=refresh`, 7 days) — only accepted by
  `POST /auth/refresh`; cannot be used to call any other endpoint, and an
  access token cannot be replayed against `/auth/refresh` either (each
  token type is verified against its own `type` claim).
- **Reset token** (`type=reset`, short-lived, single purpose) — issued by
  `POST /auth/forgot-password`, only accepted by `POST /auth/reset-password`.
- **Roles**: `ADMIN`, `TEACHER`, `STUDENT` — enforced via
  `Depends(require_role(UserRole.ADMIN))` (or multiple roles) on each route.
  `require_super_admin` additionally checks `AdminProfile.super_admin`.
- Forgot-password and login-by-OTP endpoints always return a generic success
  message, whether or not the email exists, to prevent account enumeration.

---

## 6. Known gaps / deliberately out of scope

- The `ka_tracking` and `zoom` sync-write endpoints (`/ka-tracking/sync/*`,
  `/zoom/sync/*`) assume an external job pushes Khan Academy / Zoom API data
  in — the sync job itself is not part of this backend.
- `reports` document *generation* (turning aggregated metrics into an actual
  PDF/HTML/PNG) is external — this backend stores/serves the generated
  bytes via `attach_document`/`download_document`, it doesn't render them.
- `raw_meetings` / `raw_participants` are staging/archive tables with no
  API surface by design (matches legacy: never read by any feature).
