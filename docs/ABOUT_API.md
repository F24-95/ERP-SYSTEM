# School ERP - API Overview

## Base URL
```
http://127.0.0.1:8000
```

## Authentication
- **Login:** `POST /auth/login` with `email` (string) and `password` (string)
- Returns: `access_token` (JWT, 60min expiry), `refresh_token` (7 day expiry)
- **Header:** `Authorization: Bearer <access_token>` for all protected endpoints
- **Refresh:** `POST /auth/refresh` with `refresh_token`
- **Logout:** `POST /auth/logout` with `refresh_token`

## User Roles
| Role | Description |
|------|-------------|
| `ADMIN` | Full system access — create/manage users, sessions, classes, subjects, fees, etc. |
| `TEACHER` | Create/manage exams, assignments, daily classes, attendance, chat rooms, study materials, notices. Can view all student/teacher/admin profiles. |
| `STUDENT` | Self-service — view own profile, classes, attendance, fees, exams, assignments. Can view all student/teacher/admin profiles. |
| `PARENT` | Role defined but not yet used in any endpoint. |

## Database
- **Engine:** PostgreSQL (v17)
- **Database name:** `faizan20`
- **Connection:** `postgresql://postgres:Faizan9517@localhost:5432/faizan20`

## API Sections

### Authentication (`/auth`)
Login, logout, token refresh, OTP verification, password change/reset. Public or authenticated.

### Academics (`/academics`)
Manage academic sessions, classrooms, subjects, class-subject mappings. Create/Update: Admin, Teacher. View: Anyone.

### Admin (`/admin`)
User & profile management. Create/Update/Delete: Admin only. View profiles: Admin, Teacher, Student.

### Assignments (`/assignments`)
Create/grade assignments. Teacher creates and manages; students view their own.

### Attachments (`/attachments`)
Upload/download files attached to any entity. Any authenticated user.

### Chat (`/chat`)
Teacher creates chat rooms with students. Participants send/edit/delete messages.

### Daily Class (`/daily-class`)
Teacher creates daily class sessions, marks attendance, recalculates summaries.

### Dashboard (`/dashboard`)
Role-specific dashboards showing counts and summaries.

### Exams (`/exams`)
Teacher creates exams and uploads results. Students view their own results.

### Fees (`/fees`)
Admin/Teacher creates fee records and records payments. Students view their own.

### Khan Academy (`/khan-academy`)
Manage KA topics, ingest student progress/activity snapshots. Admin, Teacher.

### Notices (`/notices`)
Create notices with optional file attachments, pin/unpin. Admin, Teacher.

### Operations (`/operations`)
Assign teachers to subjects, enroll students in classes, promote students.

### Reports (`/reports`)
Generate student progress reports covering KA activity, zoom stats. Admin, Teacher.

### Search (`/search`)
Full-text, ranked search for students and teachers by name/email/phone/code.

### Student (`/student`)
Student self-service — profile, classes, attendance, fees, exams, assignments, timetable.

### Student ID Card (`/student/id-card`)
Generate, view, download student ID cards with QR codes.

### Study Materials (`/study-materials`)
Upload and manage study material files per class-subject. Admin, Teacher.

### Teacher (`/teacher`)
Teacher self-service — profile, classes, students, subjects, assignments, attendance marking, dashboard.

### Timetable (`/timetable`, `/timeslots`, `/weekdays`, `/availability`)
Create and manage class timetables, time slots, teacher availability.

### Users (`/users`)
Self-service user profile view/update. Any authenticated user.

### Zoom (`/zoom`)
Ingest Zoom meetings and file bundles (video/audio/transcript). Admin, Teacher.

## Key Design Decisions

- **Stateless JWT auth** — no server-side session storage
- **Role-based access** — checked via FastAPI dependency injection
- **Soft deletes** — all tables use `is_active`/`is_deleted` flags
- **UUID public IDs** — each user has a public_id for external references
- **Async** — all endpoints use async SQLAlchemy sessions
- **Swagger UI** — available at `http://127.0.0.1:8000/docs`
