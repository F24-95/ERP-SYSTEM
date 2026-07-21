# Database Schema

**50 tables**, verified to `CREATE ALL` cleanly with zero FK/constraint
errors against a fresh SQLite/Postgres database. Grouped by domain below;
`→` reads "has a foreign key to".

---

## Core identity — `src/domain/users/models.py`

- **`users`** — the single account table for every role (`ADMIN`/`TEACHER`/`STUDENT`).
  Holds login credentials, JWT-relevant state (`last_login`, `login_count`,
  `failed_login_count`), email verification (`email_verified`, `email_otp`,
  `email_otp_expiry`), and password lifecycle (`password_changed_at`,
  `last_password_reset`).
- **`student_profiles`** → `users.id` — name, admission/registration numbers, KA integration hook (`ka_student_id`).
- **`teacher_profiles`** → `users.id` — name, designation, department, employee code.
- **`admin_profiles`** → `users.id` — name, department, `super_admin` flag (used by `require_super_admin`).

## Academics — `src/domain/academics/models.py`

- **`academic_sessions`** — school years (e.g. "2025-26"), one flagged `is_current`.
- **`classroom`** → `academic_sessions` — a class+section within a session.
- **`subjects`** — subject catalog (session-independent).
- **`class_subjects`** → `academic_sessions`, `classroom`, `subjects` — the mapping that
  almost every other domain (assignments, exams, study material, timetable,
  daily classes) hangs off of.

## Operations — `src/domain/operations/models.py`

- **`teacher_subjects`** → `users`(teacher), `academic_sessions`, `classroom`,
  `subjects`, `class_subjects` — "this teacher teaches this subject to this class
  this session".
- **`student_classes`** → `users`(student), `academic_sessions`, `classroom` — enrollment.
  `status` ∈ `ACTIVE`/`PROMOTED`/`WITHDRAWN`.
- **`student_promotion_history`** → `users`(student), `academic_sessions`(from/to),
  `classroom`(from/to), `users`(promoted_by) — audit trail; every promotion also
  creates a new `student_classes` row (fixed in this pass — see CHANGELOG).
- **`week_days`**, **`time_slots`** — timetable building blocks.
- **`class_timetable`** → `teacher_subjects`, `classroom`, `class_subjects`,
  `week_days`, `time_slots`, `academic_sessions` — the actual weekly grid.
- **`teacher_availability`** → `teacher_subjects`, `week_days`, `time_slots`, `academic_sessions`.
- **`daily_classes`** → `teacher_subjects`, `classroom`, `class_subjects`,
  `class_timetable`, `academic_sessions` — one row per actual class session held.
- **`daily_class_students`** → `daily_classes`, `student_classes`, `users`(marked_by) —
  per-student attendance for one daily class.
- **`student_attendance`** → `student_classes` (1-to-1) — running aggregate
  (`total_classes`/`present_classes`/`absent_classes`/`attendance_percentage`),
  recomputed by `DailyClassService.recalculate_attendance()` on every mark/edit/delete.

## Assignments — `src/domain/assignments/models.py`

- **`assignments`** → `academic_sessions`, `classroom`, `class_subjects`,
  `teacher_subjects`, `users`(uploaded_by/created_by/updated_by/deleted_by).
- **`assignment_results`** → `assignments`, `student_classes`, `users`(checked_by).

## Exams — `src/domain/exams/models.py`

- **`exams`** → `academic_sessions`, `classroom`, `class_subjects`, `teacher_subjects`, `users`(deleted_by).
- **`exam_results`** → `exams`, `student_classes`, `users`(checked_by).

## Fees — `src/domain/fees/models.py`

- **`fees`** → `academic_sessions`, `student_classes`, `users`(created_by/updated_by/deleted_by).

## Notices — `src/domain/notices/models.py`

- **`notices`** → `academic_sessions`, `classroom`, `users`(created_by/updated_by/deleted_by).

## Study material — `src/domain/study_material/models.py`

- **`study_materials`** → `academic_sessions`, `classroom`, `class_subjects`, `teacher_subjects`, `users`(uploaded_by).

## Chat — `src/domain/chat/models.py`

- **`chat_rooms`** → `academic_sessions`, `teacher_subjects`, `student_classes`.
- **`chat_messages`** → `chat_rooms`, `users`(sender_id). Has `is_edited`/`edited_at`.

## ID cards — `src/domain/id_cards/models.py`

- **`student_id_cards`** → `academic_sessions`, `student_profiles`.

## Attachments — `src/domain/attachments/models.py`

- **`attachments`** — generic polymorphic file store (`entity_type` + `entity_id`,
  no FK — deliberately loose so any domain can attach files without a migration).

## Khan Academy tracking — `src/domain/ka_tracking/models.py`

- **`ka_topics`** → `subjects`, `classroom`(nullable), `users`(created_by/updated_by).
- **`ka_student_activities`** → `student_profiles` — daily activity summary.
- **`ka_subject_activities`** → `student_profiles`, `subjects`, `ka_topics`, `study_materials` — per-topic activity log.
- **`ka_subject_progress`** → `student_profiles`, `subjects` — cumulative points snapshot.
- **`ka_topic_progress`** → `student_profiles`, `ka_topics`, `subjects`, `study_materials` — cumulative points snapshot.

> **Fixed during porting:** these five tables originally FK'd to
> `student_profiles.student_id` — a column that doesn't exist on
> `StudentProfile` in this schema (the business-code `student_id` lives on
> `users`, not `student_profiles`). All corrected to FK `student_profiles.id`.

## Zoom — `src/domain/zoom/models.py`

- **`zoom_meetings`** (PK = Zoom's `uuid`) — master record from the Zoom API.
- **`zoom_recording_files`** → `zoom_meetings`.
- **`zoom_transcripts`** → `zoom_recording_files` — one row per timed speaker segment.
- **`zoom_student_interactions`** → `zoom_recording_files` — one row per student speaking turn.
- **`zoom_participants`** → `zoom_meetings`.
- **`processed_meetings`** / **`processed_participants`** → self / `processed_meetings` — cleaned/deduped reporting view.
- **`raw_meetings`** / **`raw_participants`** → self / `raw_meetings` — staging/archive, no API surface by design.
- **`zoom_files`** → `classroom`, `zoom_recording_files` — legacy API-independent session file bundle.

## Reports — `src/domain/reports/models.py`

- **`student_reports`** → `student_profiles` — master record per student per period;
  holds `pdf_document`/`html_document`/`png_document` binary blobs.
- **`student_activity_reports`** → `student_reports` (1-to-1) — KA activity aggregate.
- **`student_subject_progress_reports`** → `student_reports`, `subjects`, `ka_subject_progress` (1-to-many).
- **`student_topic_progress_reports`** → `student_reports`, `ka_topics`, `study_materials`, `ka_topic_progress` (1-to-many).
- **`zoom_duration_reports`**, **`zoom_interaction_reports`** → `student_reports` (1-to-1 each).

> Same FK fix applied here as `ka_tracking`: `student_id` corrected to
> `student_profiles.id`.

---

## Cross-cutting conventions

- **Soft delete over hard delete** almost everywhere a row might be
  referenced elsewhere (`is_active=False` via `ActiveMixin`), to avoid
  cascading data loss. Hard delete is only used for genuinely
  disposable rows (e.g. an individual chat message's underlying storage
  isn't reused elsewhere — even that one soft-deletes though, to preserve
  chat history integrity).
- **Audit columns** (`created_by`, `updated_by`, sometimes `deleted_by`) on
  most tables via `AuditMixin`, all FK'd to `users.id`.
- **Timestamps** (`created_at`, `updated_at`) via `TimestampMixin` on every table.
