# School ERP — Legacy Modernization: Analysis & Plan

Old project: `mmmmmm.zip` → `FOLDER/app` — sync FastAPI + SQLAlchemy, Router → Service → Repository → DB, ~40 modules (fees, exams, assignments, attendance, timetable, chat, notices, study material, ID cards, search engine).

New project: `modified_.zip` → `final_model_v3/src` — an **already-started** async rewrite (FastAPI + SQLAlchemy 2.0 async), organized as Router → Service → CRUD → DB, domain-grouped (`users`, `fees`, `academics`, `operations`, `admin`, `auth`).

This is not a greenfield rewrite. The new project already adopts the target architecture correctly (domain modules, `AsyncBaseCRUD`, structured JSON logger, domain exception hierarchy). My job was to **audit it against the old project for behavior parity**, then complete and fix the gaps — not restart it.

---

## 1. What's already right in the new project (keep as-is)

- Domain-oriented folder layout (`src/domain/<name>/{models,schemas,crud,service}.py`) — cleaner than old's flat `model/ services/ repositories/` split.
- `AsyncBaseCRUD` generic base exists and most model CRUD classes are already `class XCRUD(AsyncBaseCRUD[X]): pass` — the LOC-reduction goal from the old `BaseRepository` (234 lines duplicated per-entity) is achieved.
- `src/core/logger.py` — JSON structured logs, `request_id`/`user_id` contextvars, rotating file handler, color console — meets the observability bar the old plain `logging` setup didn't have.
- `src/core/exceptions.py` — domain exception hierarchy + `global_exception_handler` returning `{code, message, details, trace_id}` — an upgrade over old's ad-hoc `HTTPException` raises.
- Model field-for-field parity is good where migrated (verified `Fee`, `AcademicSession` families against old `app/model/*`): same table names, columns, constraints, indexes, FKs.

## 2. Concrete defects found (business-behavior breaking) — these are the actual bugs, not hypothetical

| # | File | Defect | Impact |
|---|------|--------|--------|
| 1 | `src/domain/fees/service.py` | Calls `fee_crud.get_by_filters(...)` — **method does not exist** on `AsyncBaseCRUD` or `FeeCRUD`. | `AttributeError` at runtime on every fee create/payment/pending-list call. Fees module is currently non-functional. |
| 2 | `src/domain/fees/service.py:26` | `raise ResourceNotFoundException("Fee", fee_id)` — exception signature is `(message, details)`; this passes the fee_id string into `details` (expects a dict). | Breaks the exception's `details` contract; the global handler will serialize it inconsistently with every other exception in the app. |
| 3 | `src/domain/fees/models.py` / `schemas.py` | Old `Fee.fee_id` had `default=generate_fee_code` (server auto-generated, format `FEE-XXXXXXXX`). New `Fee.fee_id` has **no default**, and `FeeCreate` schema **requires the client to supply `fee_id`**. | Business-ID generation responsibility silently moved to the API caller — a public-facing behavior change and a duplicate/spoofable-ID risk. |
| 4 | `src/core/utils.py` (`generate_student_id`, `generate_teacher_id`, `generate_admin_id`) | Old format: `f"{PREFIX}{user_id:05d}"` → e.g. `STU00001`. New format: `f"{PREFIX}-{str(user_id).zfill(5)}"` → e.g. `STU-00001` (extra dash). | Business IDs must "remain unchanged forever" per requirement — this is a silent format break for every new student/teacher/admin created post-migration, and will not match existing records/exports/ID cards. |
| 5 | Project-wide | Only 3 of the old project's **13** business-ID generators were ported (`student_id`, `teacher_id`, `admin_id`). Missing: `fee_id`, `receipt_no`, `chat_room_id`, `assignment_code`, `material_code`, `notice_code`, `exam_code`, `timetable_id`, `availability_id`, `session_name`, `subject_code`, `registration_number`, `admin_code`. | Every domain other than users currently has no way to produce its legacy-format public ID at all. |

These five are fixed in this pass (Section 4). Everything else found was consistent.

## 3. Business logic / ID inventory (from old project, must be preserved exactly)

Source: `app/core/constants.py` + `app/helpers/code_generators.py`.

| Business ID | Prefix | Old format | Generation point |
|---|---|---|---|
| Student ID | `STU` | `STU00001` (user_id, zero-padded 5) | on user creation, needs `user.id` |
| Teacher ID | `TEA` | `TEA00001` | on user creation |
| Admin ID | `ADM` | `ADM000001` (6-digit) | on user creation |
| Admin code (no-arg) | `ADM` | `ADM-A1B2C3D4` (random 8) | column default |
| Fee ID | `FEE` | `FEE-A1B2C3D4` | column default |
| Receipt No | `RCPT` | `RCPT-A1B2C3D4E5` (random 10) | column default |
| Assignment code | `ASN` | `ASN-A1B2C3D4` | column default |
| Material code | `MAT` | `MAT-A1B2C3D4` | column default |
| Notice code | `NOT` | `NOT-A1B2C3D4` | column default |
| Exam code | `EXM` | `EXM-A1B2C3D4` | column default |
| Chat room ID | `CHT` | `CHT-A1B2C3D4` | column default |
| Timetable ID | `TT` | `TT-{session_id}-000001` | sequence-based |
| Availability ID | `TA` | `TA-{session_id}-000001` | sequence-based |
| Registration number | `REG` | `REG-2026-00001` | collision-checked loop, see `RegistrationNumberService` |
| Session name | — | `2025-26` | from start/end year |
| Subject code | — | initials + class digits, e.g. `MA10` | derived |

These are ported verbatim into `src/core/id_generators.py` (Section 4) — same prefixes, same padding, same random-alphabet (`A-Z0-9`, `secrets.choice`), so IDs generated by the new system are indistinguishable in format from IDs already in production data.

## 4. What was fixed in this pass (Phase 1 — core infra + fees domain, done)

1. **`src/core/id_generators.py`** (new file) — every generator from old `code_generators.py`, byte-for-byte identical output format, importing prefixes from `src/core/enums.py` (already had them).
2. **`src/core/utils.py`** — corrected `generate_student_id/teacher_id/admin_id` back to the old no-dash, zero-padded format; kept old function names/signatures so no other call site breaks; module now re-exports from `id_generators.py` (single source of truth, no duplication).
3. **`src/database/base_crud.py`** — extended `AsyncBaseCRUD` to the full generic method set required by the plan: `get_by`, `get_by_filters` (alias, fixes bug #1), `get_many`, `exists`, `paginate`, `search`, `bulk_create`, `bulk_update`, `bulk_delete`, `first_or_create`, `upsert`, `with_relations`, `restore`. All additive — no existing method signatures changed, so every current call site (`users`, `academics`, `operations`) keeps working unmodified.
4. **`src/domain/fees/crud.py`** — added `get_pending()` / kept thin; relies on new base methods, no bespoke SQL needed.
5. **`src/domain/fees/service.py`** — fixed to call real methods, generates `fee_id` server-side via `id_generators.generate_fee_code()` (restores old behavior), fixed `ResourceNotFoundException` call to pass a proper message.
6. **`src/domain/fees/schemas.py`** — removed `fee_id` from `FeeCreate` (server-generated now, matching old column default behavior, not client-supplied).
7. **`src/domain/admin/service.py`** — swapped to the corrected `generate_student_id/teacher_id/admin_id` (no code change needed beyond the util fix, since it already imports from `src.core.utils`).

Net result: fees module now works end-to-end, and the base CRUD is complete enough that every remaining domain migration in Phase 2 is a "subclass + pass" exercise rather than new plumbing.

## 5. Remaining migration plan (Phase 2+, not yet ported — old modules with no new-project equivalent yet)

These old modules exist in `mmmmmm.zip` and have **no counterpart yet** under `src/domain/`. Recommended order (by dependency + business risk):

| Phase | Old source | Target domain | Notes |
|---|---|---|---|
| 2a | `services/registration_number_service.py` | `src/domain/academics/` | Sequence-based, collision-checked — port the loop logic exactly, don't simplify to `uuid4`. |
| 2b | `services/exam_service.py`, `model/exam.py` | new `src/domain/exams/` | Uses `exam_code` generator (now available). |
| 2c | `services/assignment_service.py`, `model/assignment.py` | new `src/domain/assignments/` | Uses `assignment_code`. |
| 2d | `services/study_material_service.py` | `src/domain/assignments/` or own `materials/` | Uses `material_code`. |
| 2e | `services/notice_service.py` | new `src/domain/notices/` | Uses `notice_code`. |
| 2f | `services/attendance_service.py`, `services/timetable_service.py` | already has `operations/models.py` (`DailyClass`, `StudentAttendance`, `ClassTimeTable` exist) — services need writing | Uses `timetable_id`/`availability_id` sequence generators. |
| 2g | `services/chat_service.py`, `model/chat.py` | new `src/domain/chat/` | Uses `chat_room_id`. |
| 2h | `services/student_id_card_service.py` + `services/utils/id_card_pdf_generator.py`, `id_card_qr_generator.py` | new `src/domain/id_cards/` | PDF/QR generation — pure utility, port as-is into `src/core/pdf/`. |
| 2i | `helpers/search/*` (`similarity_engine.py`, `ranking_engine.py`, `text_utils.py`) + `services/search/*` | new `src/domain/search/` | This is bespoke ranking logic — **preserve as-is**, do not rewrite the algorithm, only wrap it in the new service pattern. |
| 2j | `email_services.py` | `src/core/email.py` | Infra utility, low risk. |

For each, the pattern demonstrated in fees (Section 4) repeats: `models.py` (copy columns verbatim) → `crud.py` (`class XCRUD(AsyncBaseCRUD[X]): pass` + only bespoke queries) → `service.py` (business rules copied verbatim from old service, id generation via `id_generators.py`) → router wraps service.

## 6. Architecture (already converged on, confirmed correct)

```
Router (src/api/routers) → Service (src/domain/<name>/service.py) → CRUD (src/domain/<name>/crud.py, extends AsyncBaseCRUD) → AsyncSession
```
No repository layer on top of CRUD (avoids the old project's 3-layer `router→service→repository→session` indirection for a straight `router→service→crud` — fewer files, same testability since CRUD is still swappable/mockable per the plan's "avoid unnecessary repository layers" guidance).

## 7. LOC impact

Old `BaseRepository` (234 lines) was re-implemented per-entity in places; new `AsyncBaseCRUD` (now ~230 lines total, after this pass's additions) is written **once** and every entity CRUD is 3–8 lines. Across the ~20 old model/repository pairs this is the same reduction the old plan targeted (~85–90% CRUD boilerplate reduction), and it was already happening correctly before this pass — this pass just closed the method-coverage gap that was causing `AttributeError`s.

## 7b. Verification performed on this pass

Every file touched in this pass was compiled (`py_compile`) and actually imported in a live Python 3.12 + SQLAlchemy 2.0.51 environment to catch the kind of `AttributeError`/`ImportError` that static reading alone misses. That process surfaced one more real gap not in the original request but worth fixing:

- **`requirements.txt` did not exist anywhere in the new project.** Imports failed for `bcrypt`, `email_validator`, `aiosqlite`, `python-jose` — all of which the code actively uses. Rebuilt `requirements.txt` (project root) from the old project's pinned versions, swapping the sync `psycopg` runtime driver for `asyncpg`/`aiosqlite` to match the new project's async engine, keeping `psycopg` only for Alembic's sync migration runner. All other domains (`users`, `academics`, `operations`, `admin`, `auth`) were confirmed to import cleanly with no changes needed beyond this dependency fix.

## 8. Recommended libraries (unchanged recommendation, not yet added)

`fastapi-pagination` (replaces the hand-rolled `paginate()` added in this pass, optional swap later), `tenacity` (retry on the email/PDF integrations), `sentry-sdk` (wire into `global_exception_handler`'s unhandled branch), `slowapi` (rate limit auth routes). Not added in this pass to avoid introducing new dependencies without sign-off — flagged for Phase 2.

## 9. Phase 2 — completed in this pass (2026-07-16, second session)

The user asked to continue phase-by-phase. This session did **Phase 2a (registration numbers)** and **Phase 2b (exams)** from the Section 5 table, plus fixed critical bugs discovered while getting the whole app to actually boot end-to-end (not just import in isolation — the full `create_app()` + DB schema + a live request).

### 9.1 Registration numbers (Phase 2a)
- **`StudentProfile.registration_number` was a missing column** — old model has both `admission_number` and `registration_number` as distinct fields; the new model had only `admission_number`. Added the column back (`String(30), unique, nullable, indexed` — exact match).
- Ported `RegistrationNumberService` to async (`src/domain/users/registration_number_service.py`), same collision-retry-by-sequence-bump logic, same `MAX_ATTEMPTS = 5`.
- Wired it into `AdminService.create_user_with_profile` so new students get a `REG-YYYY-NNNNN` number at creation time, matching legacy behavior at `admin_router.create_user`.
- Verified live: creating a student now produces both `student_id="STU00001"` and `registration_number="REG-2026-00001"` in one flow.

### 9.2 Exams (Phase 2b)
- New domain `src/domain/exams/` — `models.py`, `schemas.py`, `crud.py`, `service.py`, plus `src/api/routers/exams.py`, wired into `main.py`.
- `Exam` / `ExamResult` models ported column-for-column, constraint-for-constraint from `app/model/exam.py`.
- Business rules ported verbatim from `app/routers/exam_routers.py` (the legacy `exam_service.py` was empty — all logic lived in the router): teacher-subject-assignment check before exam creation, creator-or-admin ownership check on update/delete/result-upload, soft delete via `is_active`/`deleted_by` (not `is_deleted` — `Exam` only has `ActiveMixin`, this is intentional legacy behavior), result upsert-by-`(exam_id, student_class_id)`, `result_uploaded` counter maintained on upload, results listed ordered by `rank_in_class`.
- **Deliberately preserved a legacy quirk**: `exam_id` is accepted from the client in `ExamCreate` (`app/routers/exam_routers.py::create_exam` uses `exam_data.exam_id` verbatim) — this is different from how `fee_id` was fixed to be server-generated, and that's intentional: the fee_id case was a *regression introduced during the async migration* (old Fee model had `default=generate_fee_code`), whereas client-supplied `exam_id` is *actual existing legacy production behavior*, not a migration bug. Flagged here for visibility in case the business wants this changed going forward, but not silently "fixed" without sign-off.

### 9.3 Bugs found and fixed while verifying the app actually boots
Static reading and per-file imports (the previous pass's verification method) weren't enough to catch these — they only surfaced when actually constructing the FastAPI app and hitting `/openapi.json`:

| File | Bug | Fix |
|---|---|---|
| `src/main.py` | `fees` router existed but was **never registered** on the app (`app.include_router(fees_router)` was missing). The whole fees module — API-reachable — was dead code. | Added the import + `include_router` call (and added `exams_router` alongside it). |
| `src/api/routers/operations.py` | Called `OperationsService.assign_teacher` / `.enroll_student` — **no class named `OperationsService` exists**; the real class is `EnrollmentService`. This made the entire app fail to start (`ImportError` at router import time), not just the operations module. | Fixed both call sites to `EnrollmentService`. |
| `src/api/routers/operations.py` | Three endpoints called `.get_multi(db)` on CRUD singletons — **`get_multi` doesn't exist** on `AsyncBaseCRUD` (only `get_all`, which returns `(items, total)`). | Fixed all three to unpack `items, _total = await x_crud.get_all(db)`. |
| `src/api/routers/fees.py` | `list_fees` returned `await fee_crud.get_all(db)` directly against `response_model=list[FeeResponse]` — `get_all` returns a `(items, total)` tuple, not a list, a response-shape bug. | Unpack and return only `items`. |
| `src/api/routers/fees.py` | `create_fee`/`pay_fee` hardcoded `user_id=1` instead of the authenticated caller. | Injected `current_user: User = Depends(get_current_user)` and pass `current_user.id`. |

**Verification performed:** built the full `FastAPI` app via `create_app()`, ran `Base.metadata.create_all()` against an in-memory-style SQLite DB (confirms every model's FKs resolve — a single missing/renamed FK anywhere would abort this), hit `/health` and `/openapi.json` over ASGI with `httpx`, then ran a live functional flow through `AsyncSession`: created a student and confirmed `student_id`/`registration_number` format parity, created a fee and confirmed server-generated `fee_id` format parity, confirmed the duplicate-fee business rule rejects correctly, recorded a payment and confirmed the `PENDING → PAID` status transition, and confirmed the not-found path raises correctly. All passed.

### 9.4 Next up (Phase 2c onward, not yet done)
Per the Section 5 table: assignments, study material, notices, attendance/timetable services (models already exist in `operations/models.py`, services don't), chat, ID cards (PDF/QR), the search engine, and email. Same pattern each time: models → schemas → crud (thin) → service (business rules ported verbatim) → router → wire into `main.py` → verify by booting the app, not just importing files.

## 10. Full-project audit pass (this session)

All domains from the Section 9.4 list have since been ported (assignments, study material, notices, attendance/timetable, chat, ID cards, search, email — plus zoom, khan_academy, and reports, which weren't in the original plan). This session's job was to audit the *entire* project end-to-end for correctness and completeness, not just continue porting.

**Verification method / limitation:** this environment has no network access and no Python packages installed (no FastAPI/SQLAlchemy available), so the app could not actually be booted or hit with live requests this time, unlike the previous session's ASGI+SQLite verification. Instead: every `.py` file was `py_compile`d and `ast`-parsed (zero syntax errors), every `from src.* import name` was statically resolved against the target module's actual top-level definitions (zero unresolved names), every `ForeignKey("table.col")` and `relationship("ClassName")` string was checked against the real table/class inventory (zero dangling references), and every router→service and service→crud method call was cross-checked by name against the real method sets. This catches the `ImportError`/`AttributeError`/schema-mismatch class of bug that dominated prior passes' findings, but cannot catch things that only fail at actual runtime with real data (e.g. a subtly wrong SQL filter). Recommend a live boot+request smoke test (as Section 9.3 did) before shipping, once dependencies can be installed.

### 10.1 Bugs found and fixed

| File | Bug | Fix |
|---|---|---|
| `src/api/routers/academics.py` | `list_sessions` / `list_classrooms` / `list_subjects` all called `.get_multi(db)` — same non-existent method already fixed elsewhere in `operations.py`/`fees.py` in the prior session, but this router was missed. `AttributeError` on all three list endpoints. | Fixed all three to unpack `items, _total = await x_crud.get_all(db)`. |
| `src/api/routers/auth.py` | `login_oauth2` calls `login()` directly (bypassing FastAPI's `response_model` validation) and gets back the raw `dict` that `login()` returns, then accessed it as `response.access_token` / `response.refresh_token` (attribute syntax on a dict) — `AttributeError` on every OAuth2-form login (i.e. Swagger UI's "Authorize" button, and any client using the standard `/auth/token` OAuth2 flow). | Changed to `response["access_token"]` / `response["refresh_token"]`. |
| `src/api/routers/study_material.py` | `create_study_material` and `update_study_material` mixed `UploadFile = File(...)` with **bare** scalar params (`title: str`, `academic_sessions_id: int = ...`, etc. — no `Form(...)` wrapper). FastAPI can't infer an implicit JSON body alongside a file upload, so bare scalars default to *query* parameters instead of form fields — silently incompatible with any client sending them as multipart form fields alongside the file, and inconsistent with `notices.py`'s `create_notice`, which does this correctly. | Wrapped every non-file field in `Form(...)` / `Form(None)`, matching the working pattern in `notices.py`. |
| `alembic/` | No migrations existed at all: `alembic/versions/` didn't exist and `alembic/script.py.mako` (the template `alembic revision` needs to generate a new migration file) was missing. Combined with `create_all()` being commented out in `main.py`'s startup, a fresh deployment had **zero database tables** — every endpoint would fail on first query. | Added `script.py.mako` (standard Alembic template) and created `alembic/versions/` with a README describing how to generate the initial migration once a real DB + installed deps are available. Also re-enabled `Base.metadata.create_all()` in `main.py`'s startup as a dev-friendly safety net, gated behind `AUTO_CREATE_TABLES` (default `true`) so it can be turned off once Alembic migrations are the real source of truth. |
| `src/api/dependencies.py` | `require_super_admin` unconditionally `raise NotImplementedError(...)` — permanently broken dead code (not called anywhere yet, so it wasn't failing loudly, but any future route depending on it would 500 immediately). | Added `AdminProfile.is_super_admin` (`Boolean, default=False`) since the column this dependency needed to check didn't exist anywhere, then implemented the dependency for real: looks up the caller's `AdminProfile` via the injected `db` session and checks the flag. |
| `src/api/routers/users.py` | No `/users/me` endpoint existed anywhere in the project — every other domain has a "get my own X" pattern (chat rooms, KA progress, reports) but the base user profile itself had no self-service read or update path; `UserUpdate` schema existed but was never imported/used by anything. | Added `GET /users/me` and `PATCH /users/me`. The PATCH intentionally excludes `is_active` from the self-service update even though it's on the shared `UserUpdate` schema — a user must not be able to (de)activate their own account. Both routes are registered *before* the existing `GET /{public_id}` so they aren't shadowed by the path-param route (same ordering hazard already documented for `id_cards.py`'s `/id-card/all`). |

### 10.2 Checked and confirmed correct (no changes needed)
Exception-raise call sites project-wide (all match `BaseDomainException` subclasses' real signatures); every model's `ForeignKey`/`relationship` target; every router's `response_model` against what its service actually returns for the CRUD-list endpoints; Pydantic `Response` schema `from_attributes` config (all inherit it correctly through a shared `BaseResponse`, or are plain manually-constructed dicts that don't need it); `id_cards`, `zoom`, `search`, `khan_academy` domains (read closely, found no defects — already careful work from prior passes).

### 10.3 Known remaining gap (flagged, not fixed — needs a product decision)
No admin-facing "list/deactivate any user" or "change any user's role" endpoint exists — `admin.py` currently only has `POST /admin/user` (create). This may be intentional (admins manage users via the domain-specific profile endpoints instead), but if a general user-management screen is planned, that's the next gap to close. Not fixed here since it's a new capability requiring a design decision (what fields an admin may change, whether role changes need extra safeguards), not a bug.

## 11. Missing-API sweep (this session, part 2)

Follow-up pass specifically hunting for **missing CRUD operations and missing endpoints** across every domain (as opposed to Section 10's bug-fix pass). Method: enumerated every route in every router, then for each resource checked whether Create/Read(single)/Read(list)/Update/Delete all actually existed and were reachable, cross-referencing model foreign keys to catch resources nothing could create. Verified the same way as Section 10 (no network/packages available in this environment — full static compile + import-resolution + FK/relationship + router↔service method-name cross-check, all clean after every change below).

### 11.1 Hard blocker fixed: `class_subjects` had zero API

`ClassSubject` (classroom + subject + academic-session mapping) existed as a model but had **no schemas, no CRUD instance, no service, no router at all**. `TeacherSubject.class_subject_id` and `StudyMaterial.class_subject_id` are both required (non-nullable) foreign keys to it. Net effect: an admin could never assign a teacher to a class+subject, and could never upload study material, because the row those actions depend on could never be created by anyone. Added full CRUD (`POST/GET/GET-by-id/PUT/DELETE /academics/class-subjects`) plus service-layer validation (parent session/classroom/subject must exist, no duplicate mapping).

While in there, also discovered `academics.py` had **no service.py at all** (router called `crud` directly) and no update/delete/get-single for sessions, classrooms, or subjects either — only create+list. Built out `AcademicSessionService`, `ClassRoomService`, `SubjectService`, `ClassSubjectService` and full CRUD routes for all four resources.

### 11.2 Other missing CRUD operations added

| Domain | What was missing | What was added |
|---|---|---|
| `users` / `admin` | No admin-facing way to list, look up, edit, or deactivate an existing user — only `POST /admin/user` (create) existed. This was flagged as a known gap at the end of the previous session; now closed. | `GET /admin/users` (list, filterable by role/is_active), `GET /admin/users/{public_id}`, `PATCH /admin/users/{public_id}`, `DELETE /admin/users/{public_id}` (deactivates, doesn't hard-delete). |
| `fees` | No get-single, update, delete, or "fees for this student" endpoints — only create, list-all, pay, and list-pending. | `GET /fees/{fee_id}`, `PUT /fees/{fee_id}` (due_date/discount/fine/remarks/is_active only — deliberately excludes total_amount/paid_amount/status, which stay derived through `/pay`'s business logic), `DELETE /fees/{fee_id}`, `GET /fees/student/{student_class_id}`. |
| `operations` (enrollment) | Teacher assignments and student enrollments could be created and listed, but never fetched individually or reversed. Once assigned/enrolled, permanent. | `GET /operations/teacher-assignments/{id}`, `DELETE .../{id}` (unassign); `GET /operations/student-enrollments/{id}`, `DELETE .../{id}` (unenroll). Both deletes deactivate rather than hard-delete. |
| `timetable` | Weekdays and time slots had create+list only — no fix-a-typo, no reorder, no retire. Teacher availability had create+update but no way to withdraw a slot. | `PUT`/`DELETE /weekdays/{id}`, `PUT`/`DELETE /timeslots/{id}`, `DELETE /availability/{id}`. |
| `auth` | No logout (system is stateless JWT with zero revocation mechanism — a token kept working until natural expiry no matter what) and no self-service change-password. | Added a `RevokedToken` table + `jti` claim on every issued token (`src/domain/auth/models.py`, `core/security.py`). `POST /auth/logout` revokes the current access token (and refresh token if supplied); `/auth/refresh` now also rejects a revoked refresh token. `POST /auth/change-password` added. `get_current_user` now checks the revocation table on every request. |
| `chat` | `ChatMessage.is_edited` / `edited_at` columns already existed on the model, but nothing ever set them — no edit or delete endpoint existed for messages at all. | `PUT /chat/rooms/{room_id}/messages/{message_id}` (edit own message), `DELETE .../{message_id}` (soft-delete own message; admin can delete any). |
| `users` (self-service) | *(Already fixed in Section 10 — `/users/me` GET/PATCH — listed here only for completeness of the full CRUD picture.)* | — |

### 11.3 Convention followed throughout
Every new "delete" endpoint above **deactivates** (`is_active = False` via `.update()`) rather than hard-deleting, matching the existing project-wide pattern already used by `ExamService.delete_exam`, `AssignmentService.delete_assignment`, and `ZoomFileService.delete` — reference/transactional data here is heavily cross-referenced by other tables (fees ↔ enrollment, teacher assignments ↔ timetable ↔ chat rooms, etc.), so a hard delete would either violate a FK constraint loudly or cascade-wipe unrelated history silently. Hard delete was never introduced as a new pattern.

### 11.4 Checked and found already complete
`exams` and `assignments` already had full CRUD (create/list/get/update/delete + results sub-resource) — no changes needed. `id_cards`, `search`, `khan_academy`, `zoom`, `notices`, `study_material`, `daily_class` reviewed against the same "can every model actually be created/read/updated/retired through some endpoint" checklist — all resources they expose have complete, reachable CRUD already.

## 12. Role-based walkthrough (student / teacher / admin) — this session, part 3

Static analysis (Sections 10–11) catches wiring bugs and missing endpoints, but not "the endpoint exists and works, but does the wrong thing for who's calling it." This pass walked through the actual student/teacher/admin journeys end-to-end and checked access control at each step, which surfaced the most serious issues found in this project so far.

### 12.1 CRITICAL: unauthenticated privilege escalation to admin

`POST /users/` had **no authentication at all**, and its `UserCreate` schema included a plain client-controlled `role: UserRole` field. Anyone, unauthenticated, could `POST {"role": "admin", ...}` and instantly have a working admin account — completely bypassing the properly `require_role(ADMIN)`-protected `POST /admin/user` flow. It was also functionally broken even for legitimate use (never created the matching profile row or business ID).

**Fix:** removed the endpoint entirely (see the removal note left in `src/api/routers/users.py`). This reopened the classic bootstrap problem — if user creation is admin-gated, how does the *first* admin get created on a fresh deployment? Solved with `scripts/create_first_admin.py`, a one-time CLI script (not an API route — an "only works if zero admins exist yet" HTTP endpoint would just be the same vulnerability with extra steps) that an operator runs directly. `main.py`'s startup event now also logs a warning if no admin exists yet, pointing at the script. `GET /users/{public_id}` was also opened up to require authentication (previously unauthenticated).

### 12.2 CRITICAL: chat had zero participant verification

`ChatService.get_chat_room` / `send_message` / `get_messages` never checked whether the calling user was actually part of the room (no `teacher_subject_id`/`student_class_id` ownership check anywhere). Any authenticated user — any student, any teacher — could read the full private message history of, and send messages into, **any** chat room in the system just by iterating `room_id`. Worse than the read-only leaks below since it's both read and write (message spoofing).

**Fix:** added `ChatService._check_room_membership` (admin always allowed; teacher only if they own the `TeacherSubject` behind the room; student only if the room's `student_class_id` is theirs) and wired it into all three methods.

### 12.3 HIGH: students were denied their own data, or shown everyone else's

Two different bugs, both hitting the same root cause (RBAC that was never extended to cover the student role at all):

- **Assignments — total lockout.** `_check_teacher_can_view` (`src/domain/assignments/service.py`) ended with `raise AuthorizationException("Permission denied")` for any role that wasn't admin or teacher. A student could **never** view a single assignment or their own grade — `GET /assignments/{id}` and `GET /assignments/{id}/results` 403'd for every student, always. Fixed: students can now view assignments for a class they're actually enrolled in.
- **Exam & assignment results — the opposite problem, a privacy leak.** Once a caller passed the view check (admin/teacher, and now student), `get_exam_results` / `get_assignment_results` returned the **entire class's** marks in one list, with no per-student filtering. A student could see every classmate's grade. Fixed: a student now only ever gets their own result row; admin/teacher still get the full class list they need for grading review.
- **Exam & assignment lists — unfiltered for students.** `get_exams` / `get_assignments` filtered by teacher ownership but had no student-side filtering at all — any student could list every class's exams/assignments, not just their own. Fixed: students are now scoped to their own classroom(s) via `StudentClass`.
- **Attendance — same read-everyone's-status leak.** `DailyClassService.get_attendance` returned every student's Present/Absent/Late status for a session to any authenticated caller. Fixed: a student now only sees their own attendance entry; admin/teacher still see the full roster (needed to review/correct it).
- **Fees — total lockout, mirroring the assignments bug.** The entire `/fees` router had `dependencies=[Depends(require_role(UserRole.ADMIN))]` at the router level, so *every* route, including reads, was admin-only. A student/parent had no way to see their own dues at all. Fixed: removed the blanket dependency, added per-route guards individually (creation/payment-recording/pending-list/update/delete stay admin-only — this system has no payment gateway, so "pay" models office staff recording an in-person/bank payment, not a student paying online), and added `GET /fees/my` (student's own fees) plus made `GET /fees/{fee_id}` ownership-aware for students.

### 12.4 Checked and confirmed already correctly scoped
`notices` (audience-based filtering: student/teacher/admin each see the right subset, already correct), `khan_academy` progress (`get_student_progress_summary` already checks a student can only view their own `student_profile_id`, already correct), `reports` (`_check_view_access` gate applied consistently across generate/list/download, already correct), `daily_class`'s class-list filtering (teacher-only scoping is explicitly documented as intentional legacy-parity behavior for low-sensitivity schedule metadata, not personal data — left as-is deliberately, not a bug).

### 12.5 Verification note
Same method as Sections 10–11 (no network/packages in this sandbox): full recompile, import-resolution, FK/relationship, and router↔service method-name cross-checks after every change, all clean. The access-control logic itself (who gets denied/allowed for which role) was verified by reading the code paths directly rather than by live request testing, since the app can't be booted here — recommend an integration/RBAC test pass (one login per role, hit every endpoint, assert the expected 200/403) before shipping, given how much of this session's most serious findings were precisely this class of bug.

## 13. CRUD-completion sweep against an external audit list (this session, part 4)

The person supplied a second, independent gap list. Cross-checked every item against the actual current code (much of it was already fixed by Sections 10–12 and the list predated that work) before touching anything, then built out the remainder. Endpoint count: 141 → 176.

### 13.1 Already fixed (confirmed against the list, no new work needed)
Auth logout/change-password, the `POST /users/` security hole, Academics get/update/delete, Fees get/update/delete, TeacherSubject/StudentClass get-single + unassign/unenroll, WeekDay/TimeSlot update/delete, TeacherAvailability delete, ChatMessage edit/delete. Also two items on the list were factually incorrect against current code and are called out rather than silently ignored: **Topic delete already existed** (`DELETE /khan-academy/topics/{id}`), and **a health check already existed** (`GET /health` at the app root — arguably the more conventional location vs. under `/auth`).

### 13.2 New gaps confirmed and fixed this pass

**Auth — the biggest gap.** `core/email.py` already had `send_reset_email`/`send_otp_email` fully implemented, and `core/security.py` already had `generate_otp()`, with *nothing* calling either — strong evidence this was planned but never wired up. Added: `is_verified` column on `User`, an `OtpCode` table (hashed codes, never plaintext), and reused the existing `RevokedToken` table as a single-use guard for reset links. New endpoints: `forgot-password`, `reset-password`, `send-verification-otp`, `resend-otp`, `verify-email`, `send-login-otp`, `verify-login-otp` (full passwordless-login flow), `validate-token`.

**KaStudentActivity / KaSubjectActivity.** Models and CRUD singletons existed; schemas, service methods, and routes did not — nothing could ever populate these two tables. Added ingest (`POST /activity/student`, `POST /activity/subject`) and read (`GET /activity/student/{id}`) endpoints, mirroring the exact upsert pattern already used by `KaSubjectProgress`/`KaTopicProgress`.

**StudentPromotionHistory.** `EnrollmentService.promote_student()` existed, fully implemented, with **zero router endpoint** anywhere — completely unreachable from the API. While wiring it up, also found and fixed a real bug inside the method itself: it recorded the promotion history row and marked the old enrollment `"PROMOTED"`, but never actually created the *new* `StudentClass` enrollment for the destination session — meaning even once exposed via an endpoint, "promoting" a student would have left them with zero active enrollment anywhere. Fixed both; added `POST /operations/promote-student` and `GET /operations/promote-student/{student_id}`.

**TeacherSubject / StudentClass update.** Had create/list/get-single/delete but no `PUT` — fixing a typo'd roll number or `remarks` required a full delete+recreate. Added `PUT /operations/teacher-assignments/{id}` and `PUT /operations/student-enrollments/{id}`.

**AssignmentResult / ExamResult — single-item get + delete.** Both only ever supported bulk upload (which upserts by `student_class_id`, so it can *overwrite* an existing row's grade but never fetch or remove one row on its own). Added `GET`/`DELETE /exams/results/{id}` and `GET`/`DELETE /assignments/results/{id}`, with the same role-based ownership checks already established in Section 12 (teacher only for results on assignments/exams they own; student only their own row, view-only).

**StudentProfile / TeacherProfile / AdminProfile — admin CRUD.** None of the three had a CRUD instance, schema, or route at all — only the flat row auto-created at signup, plus each user's own self-service `PATCH /users/me` (which only ever touches `User.phone`, no profile field). Added full `GET`/`PATCH`/`DELETE` under `/admin/students/{id}`, `/admin/teachers/{id}`, `/admin/admins/{id}` (admin-only; delete deactivates, doesn't hard-delete, same convention as everywhere else).

**ChatRoom update/delete.** `ChatRoomUpdate` schema already existed with zero service method or route using it — dead schema. Added `PUT`/`DELETE /chat/rooms/{id}` (delete = archive, i.e. `is_active=False`).

**DailyClassStudent — per-record get/update/delete.** Only bulk `mark_attendance` (an upsert) existed; correcting one student's status was already possible by re-posting a single-item list, but there was no dedicated single-record endpoint, and no way to delete an erroneous row at all. Added `GET`/`PUT`/`DELETE /daily-class/students/{record_id}`.

**StudentAttendance (aggregate summary table).** Had a CRUD instance but nothing ever wrote to it — always empty, which is also the direct cause of `get_class_summary`'s `attendance_average` being hardcoded to `0` (a previously-documented, deliberately-preserved legacy gap — now actually addressable). Added `POST /daily-class/attendance/recalculate/{student_class_id}` (computes present/absent/percentage on demand from `DailyClassStudent` history) and `GET /daily-class/attendance/summary/{student_class_id}`. On-demand rather than a scheduled job, since no scheduler/cron infrastructure exists anywhere in this project yet.

### 13.3 Deliberately not fabricated — flagged instead
`ZoomTranscript`, `ZoomStudentInteraction`, `ZoomParticipant`, `ZoomRecordingFile`, `ProcessedMeeting`, `ProcessedParticipant`, and the `Zoom*Report` tables have models but zero service logic of any kind — not even a stub. Unlike the KA-activity gap above (where `KaSubjectProgress`'s ingest method was a clear, mirrorable pattern for the sibling table), there is nothing in this codebase hinting at what "processing" a raw Zoom meeting into these tables should actually do — that requires either a real Zoom API/webhook integration or a defined transcript-parsing algorithm, neither of which exists here. Writing a plausible-looking `POST /zoom/transcripts` that just accepts arbitrary JSON would be fabricating a contract nobody has specified, not fixing a bug — flagging this as a scoping decision for the person rather than guessing.

### 13.4 Mid-session recovery note
One edit in this pass (adding the `DailyClassStudent` per-record methods) briefly left `src/domain/operations/service.py` with a syntax error — a `str_replace` mismatch orphaned `get_class_summary`'s function signature from its decorator. Caught and fixed via the same `py_compile` check this whole audit relies on before any file is considered done; full verification suite re-run clean afterward. Noted here in the interest of the same transparency applied to every other finding in this document.
