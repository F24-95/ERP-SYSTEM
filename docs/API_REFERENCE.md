# API Reference

**234 endpoints** across 21 routers. Auth: `Bearer <access_token>` unless
noted. `ADMIN`/`TEACHER`/`STUDENT` = required role via `require_role(...)`.
Live interactive docs are always at `/docs` (Swagger) and `/redoc` — this
file is a stable, greppable index alongside them.

---

## Auth — `/auth` (public except where noted)

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/login` | Email/phone + password → tokens + profile |
| POST | `/auth/token` | OAuth2-form login (for Swagger's "Authorize" button) |
| POST | `/auth/refresh` | Refresh token → new access token |
| POST | `/auth/logout` | 🔒 clears device token (single device or all) |
| POST | `/auth/change-password` | 🔒 requires current password |
| POST | `/auth/forgot-password` | Sends reset link by email; generic response always |
| POST | `/auth/reset-password` | Consumes reset token |
| POST | `/auth/send-verification-otp` | Emails a 6-digit OTP |
| POST | `/auth/verify-email` | Consumes the OTP, sets `email_verified=True` |
| POST | `/auth/resend-otp` | Alias of send-verification-otp |
| POST | `/auth/send-login-otp` | Passwordless login step 1; generic response always |
| POST | `/auth/verify-login-otp` | Passwordless login step 2 → tokens |
| GET | `/auth/validate-token` | 🔒 confirms token + returns user/profile |
| GET | `/auth/health` | Liveness check |

## Admin — `/admin` (🔒 ADMIN)

| Method | Path | Notes |
|---|---|---|
| POST | `/admin/user` | Create user (auto-creates role profile) |
| GET | `/admin/user` | Paginated list, filter by role/is_active/search |
| GET | `/admin/user/{user_id}` | |
| PUT | `/admin/user/{user_id}` | |
| DELETE | `/admin/user/{user_id}` | Soft or hard delete (`?soft_delete=`) |
| GET/{PUT,DELETE} | `/admin/student-profiles[/{id}]` | Full CRUD on `StudentProfile` |
| GET/{PUT,DELETE} | `/admin/teacher-profiles[/{id}]` | Full CRUD on `TeacherProfile` |
| GET/{PUT,DELETE} | `/admin/admin-profiles[/{id}]` | Full CRUD on `AdminProfile` (can't deactivate self) |
| GET | `/admin/system/health` | DB connectivity check |
| GET | `/admin/system/statistics` | Counts: users/students/teachers/classes/subjects |
| GET | `/admin/teachers` | Paginated, joined view (name, classes, department...) |
| GET | `/admin/students` | Paginated, joined view (name, class, section...) |

## Academics — `/academics`

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST/GET/{GET,PUT,DELETE} | `/academics/sessions[/{id}]` | ADMIN for write | Academic years |
| POST/GET/{GET,PUT,DELETE} | `/academics/classrooms[/{id}]` | ADMIN for write | |
| POST/GET/{GET,PUT,DELETE} | `/academics/subjects[/{id}]` | ADMIN for write | Delete = deactivate |
| POST/GET | `/academics/class-subjects` | ADMIN for write | Assign subject to class |
| GET | `/academics/classes/{classroom_id}/subjects` | | Subjects taught in a class |
| DELETE | `/academics/class-subjects/{mapping_id}` | ADMIN | |

## Operations — `/operations` (🔒 ADMIN for writes)

| Method | Path | Notes |
|---|---|---|
| POST/GET/{GET,PUT,DELETE} | `/operations/assign-teacher`, `/operations/teacher-assignments[/{id}]` | Teacher↔subject↔class assignment |
| POST/GET/{GET,PUT,DELETE} | `/operations/enroll-student`, `/operations/student-enrollments[/{id}]` | Student↔class enrollment |
| POST | `/operations/promote-student` | Writes history **and** creates the new enrollment |
| GET | `/operations/promotion-history` | Optional `?student_id=` filter |

## Timetable — `/` (no common prefix; see paths)

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET/POST/{PUT,DELETE} | `/weekdays[/{id}]` | ADMIN for write | |
| GET/POST/{PUT,DELETE} | `/timeslots[/{id}]` | ADMIN for write | |
| GET | `/timetable/class/{classroom_id}` | | |
| GET | `/timetables` | | All entries |
| POST/{PUT,DELETE} | `/timetable[/{id}]` | ADMIN | |
| GET | `/student/timetable` | STUDENT | Own timetable |
| GET | `/teacher/timetable` | TEACHER | Own timetable |
| GET | `/availability/teacher/{teacher_subject_id}` | | |
| POST/{PUT,DELETE} | `/availability[/{id}]` | TEACHER | |

## Daily Class & Attendance — `/daily-class`

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST/GET/{GET,PUT,DELETE} | `/daily-class/[/{id}]` | TEACHER for write | |
| POST/GET | `/daily-class/{daily_class_id}/students` | TEACHER for POST | Bulk mark attendance; recalculates `StudentAttendance` |
| GET/{PUT,DELETE} | `/daily-class/students/{record_id}` | ADMIN/TEACHER for write | Single attendance record; keeps aggregate in sync |
| POST | `/daily-class/attendance/recalculate/{student_class_id}` | ADMIN | Manual force-recompute |
| GET | `/daily-class/classroom/{classroom_id}/summary` | | Class-level date-range summary |

## Assignments — `/assignments`

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST/GET/{GET,PUT,DELETE} | `/assignments/[/{id}]` | TEACHER for write | |
| POST/GET | `/assignments/{id}/results` | TEACHER for POST | Bulk grade (create-or-update) |
| GET/DELETE | `/assignments/{id}/results/{result_id}` | owner TEACHER/ADMIN for delete | Single result |

## Exams — `/exams`

Same shape as Assignments (`/exams/`, `/exams/{id}/results[/{result_id}]`).

## Fees — `/fees` (🔒 ADMIN)

| Method | Path | Notes |
|---|---|---|
| POST/GET | `/fees` | Create / list all |
| GET | `/fees/pending` | |
| GET/PUT/DELETE | `/fees/{fee_id}` | Delete blocked if payments already recorded |
| POST | `/fees/{fee_id}/pay` | Record a payment |

## Notices — `/notices`

Full CRUD + `POST .../pin`, `POST .../unpin`, `GET .../view`, `GET .../download`.

## Study Material — `/study-materials`

Full CRUD + `GET .../class-subject/{id}` (list by class+subject), `.../view`, `.../download`.

## Chat — `/chat`

| Method | Path | Notes |
|---|---|---|
| POST/GET | `/chat/rooms` | |
| GET/DELETE | `/chat/rooms/{room_id}` | DELETE = archive (ADMIN) |
| POST/GET | `/chat/rooms/{room_id}/messages` | |
| PUT/DELETE | `/chat/rooms/{room_id}/messages/{message_id}` | Own messages only (or ADMIN for delete) |
| GET | `/chat/unread` | Unread counts for current user |

## ID Cards — `/student/id-card`

`POST/GET .../{student_profile_id}`, `GET .../{id}/download`, `GET .../all`.

## Attachments — `/attachments` (generic polymorphic file store)

| Method | Path | Notes |
|---|---|---|
| POST | `/attachments/upload` | base64 body; 10MB cap; PDF/txt/jpeg/png only |
| GET | `/attachments/{attachment_id}` | Download |
| GET | `/attachments/entity/{entity_type}/{entity_id}` | List files for e.g. `entity_type="assignment"` |
| DELETE | `/attachments/{attachment_id}` | Owner or ADMIN |

## Dashboard — `/dashboard`

`GET /dashboard/student`, `/dashboard/teacher`, `/dashboard/admin` — role-matched aggregate summaries.

## Search — `/`

`GET /students/search`, `GET /teachers/search`.

## Khan Academy Tracking — `/ka-tracking`

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST/GET/{GET,PUT,DELETE} | `/ka-tracking/topics[/{id}]` | ADMIN for write | Topic catalog |
| POST | `/ka-tracking/sync/student-activity` \| `subject-activity` \| `subject-progress` \| `topic-progress` | ADMIN | Called by the external KA sync job |
| GET | `/ka-tracking/my-activity` \| `my-subject-progress` \| `my-topic-progress` \| `my-activity-timeline` | STUDENT | Self-service reports |
| GET | `/ka-tracking/students/{id}/activity` \| `topic-progress` \| `activity-timeline` | ADMIN/TEACHER | Same reports for a specific student |

## Zoom — `/zoom`

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/zoom/sync/meeting` \| `recording-file` \| `participant` \| `transcript` \| `interaction` \| `processed-meeting` \| `processed-participant` | ADMIN | External Zoom sync job writes |
| GET | `/zoom/meetings[/{uuid}]`, `.../recordings`, `.../participants` | ADMIN/TEACHER | |
| GET | `/zoom/recordings/{id}/transcripts` \| `interactions` | ADMIN/TEACHER | |
| GET | `/zoom/processed-meetings[/{id}][/participants]` | ADMIN/TEACHER | Cleaned/deduped reporting view |
| POST/GET/{GET,PUT,DELETE} | `/zoom/files[/{id}]` | ADMIN/TEACHER for write | Legacy session file bundle, independent of the Zoom API |

## Reports — `/reports` (🔒 ADMIN for writes, ADMIN/TEACHER for reads)

| Method | Path | Notes |
|---|---|---|
| POST/GET/DELETE | `/reports`, `/reports/{id}` | Master report record per student per period |
| GET | `/reports/student/{student_id}` | All reports for one student |
| POST/GET | `/reports/{id}/documents/{doc_type}` | Attach/download rendered PDF/HTML/PNG (base64 in/binary out) |
| PUT/GET | `/reports/{id}/activity` | KA activity aggregate (1-to-1) |
| POST/GET | `/reports/{id}/subject-progress`, DELETE `/reports/subject-progress/{item_id}` | 1-to-many |
| POST/GET | `/reports/{id}/topic-progress`, DELETE `/reports/topic-progress/{item_id}` | 1-to-many |
| PUT/GET | `/reports/{id}/zoom-duration`, `/reports/{id}/zoom-interaction` | 1-to-1 each |

## Student self-service — `/student` (🔒 STUDENT)

`GET/PUT profile`, `GET classes`, `GET attendance/summary`, `GET attendance/daily`,
`GET assignments`, `GET exams`, `GET fees`, `GET fees/summary`.

## Teacher self-service — `/teacher` (🔒 TEACHER)

`GET/PUT profile`, `GET classes`, `GET students`, `GET my-students`, `GET subjects`,
`POST attendance/mark`, `GET assignments`, `GET dashboard`.
