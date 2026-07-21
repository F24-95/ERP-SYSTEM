# Modern School ERP API Documentation

Base URL: `http://localhost:8000`

---

# Table of Contents

1. [System](#1-system)
2. [Authentication](#2-authentication)
3. [Admin](#3-admin)
4. [Users](#4-users)
5. [Academics](#5-academics)
6. [Operations](#6-operations)
7. [Fees](#7-fees)
8. [Exams](#8-exams)
9. [Assignments](#9-assignments)
10. [Study Materials](#10-study-materials)
11. [Notices](#11-notices)
12. [Daily Class & Attendance](#12-daily-class--attendance)
13. [Timetable](#13-timetable)
14. [Chat](#14-chat)
15. [Student ID Cards](#15-student-id-cards)
16. [Search](#16-search)
17. [Khan Academy](#17-khan-academy)
18. [Zoom](#18-zoom)
19. [Reports](#19-reports)
20. [Student Portal](#20-student-portal)
21. [Teacher Portal](#21-teacher-portal)
22. [Dashboard](#22-dashboard)
23. [Attachments](#23-attachments)
24. [Role Access Matrix](#24-role-access-matrix)

---

# 1. System

## GET /health

### Description
Health check endpoint. Returns API status and version.

### Access Role
Public (no authentication required)

### Authentication Required
No

### Required Headers
None

### Request Parameters
None

### Response Example
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Service is healthy |

### Database Tables Used
None

---

# 2. Authentication

## POST /auth/login

### Description
Authenticate user with email/phone and password. Returns access and refresh tokens.

### Access Role
Public

### Authentication Required
No

### Required Headers
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Content-Type | string | Yes | `application/json` |

### Request Parameters
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| email | string | Yes | Valid email or phone format | User's email address or phone number |
| password | string | Yes | Min 1 character | User's password |

### Response Example
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@school.com",
    "phone": "9999999999",
    "role": "admin",
    "public_id": "uuid-string",
    "is_active": true,
    "is_verified": false
  },
  "profile": {
    "admin_name": "Admin User"
  }
}
```

### Error Responses
| Code | Description |
|------|-------------|
| 401 | Invalid credentials |
| 401 | Account is disabled or deleted |
| 422 | Validation error (missing fields) |

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Login successful |
| 401 | Authentication failed |
| 422 | Validation error |

### Database Tables Used
`users`, `student_profiles`, `teacher_profiles`, `admin_profiles`

---

## POST /auth/token

### Description
OAuth2-compatible token endpoint (form-encoded). Used for Swagger UI authentication.

### Access Role
Public

### Authentication Required
No

### Required Headers
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Content-Type | string | Yes | `application/x-www-form-urlencoded` |

### Request Parameters (form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | Email or phone |
| password | string | Yes | Password |

### Response Example
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Token generated |
| 401 | Invalid credentials |

---

## POST /auth/refresh

### Description
Get a new access token using a refresh token.

### Access Role
Public (valid refresh token required)

### Authentication Required
No (uses refresh token in body)

### Required Headers
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Content-Type | string | Yes | `application/json` |

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh_token | string | Yes | Valid refresh token |

### Response Example
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Token refreshed |
| 401 | Invalid or revoked refresh token |

### Database Tables Used
`users`, `revoked_tokens`

---

## POST /auth/logout

### Description
Revoke current access and refresh tokens.

### Access Role
Authenticated

### Authentication Required
Yes (Bearer token)

### Required Headers
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Authorization | string | Yes | `Bearer <access_token>` |

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh_token | string | No | Optional refresh token to revoke |

### Status Codes
| Code | Description |
|------|-------------|
| 204 | Logout successful (no content) |
| 401 | Invalid or missing token |

### Database Tables Used
`revoked_tokens`

---

## POST /auth/change-password

### Description
Change password for authenticated user.

### Access Role
Authenticated

### Authentication Required
Yes (Bearer token)

### Required Headers
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Authorization | string | Yes | `Bearer <access_token>` |

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| old_password | string | Yes | Current password |
| new_password | string | Yes | New password (min 8 chars) |

### Status Codes
| Code | Description |
|------|-------------|
| 204 | Password changed |
| 401 | Authentication failed |
| 422 | Validation error |

### Database Tables Used
`users`

---

## POST /auth/forgot-password

### Description
Send password reset email. Always returns 204 to prevent email enumeration.

### Access Role
Public

### Authentication Required
No

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Registered email address |

### Status Codes
| Code | Description |
|------|-------------|
| 204 | Email sent (or not — always 204) |
| 422 | Validation error |

### Database Tables Used
`users`, `otp_codes`

---

## POST /auth/reset-password

### Description
Reset password using token from email.

### Access Role
Public

### Authentication Required
No

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| token | string | Yes | Reset token from email |
| new_password | string | Yes | New password (min 8 chars) |

### Status Codes
| Code | Description |
|------|-------------|
| 204 | Password reset |
| 401 | Invalid or expired token |
| 422 | Validation error |

### Database Tables Used
`users`, `revoked_tokens`

---

## POST /auth/send-verification-otp

### Description
Send email verification OTP to authenticated user.

### Access Role
Authenticated

### Authentication Required
Yes (Bearer token)

### Status Codes
| Code | Description |
|------|-------------|
| 204 | OTP sent |
| 401 | Not authenticated |

### Database Tables Used
`otp_codes`

---

## POST /auth/resend-otp

### Description
Resend OTP (email verification or login).

### Access Role
Authenticated

### Authentication Required
Yes (Bearer token)

### Query Parameters
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| purpose | string | No | `email_verify` | `email_verify` or `login` |

### Status Codes
| Code | Description |
|------|-------------|
| 204 | OTP resent |

### Database Tables Used
`otp_codes`

---

## POST /auth/verify-email

### Description
Verify email using OTP.

### Access Role
Authenticated

### Authentication Required
Yes (Bearer token)

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| otp | string | Yes | 6-digit OTP |

### Status Codes
| Code | Description |
|------|-------------|
| 204 | Email verified |
| 401 | Invalid OTP |

### Database Tables Used
`users`, `otp_codes`

---

## POST /auth/send-login-otp

### Description
Passwordless login step 1: send OTP to email.

### Access Role
Public

### Authentication Required
No

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Registered email |

### Status Codes
| Code | Description |
|------|-------------|
| 204 | OTP sent (always 204) |
| 422 | Validation error |

### Database Tables Used
`otp_codes`

---

## POST /auth/verify-login-otp

### Description
Passwordless login step 2: exchange OTP for tokens.

### Access Role
Public

### Authentication Required
No

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Registered email |
| otp | string | Yes | 6-digit OTP |

### Response Example
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { "...user object..." },
  "profile": { "...profile object..." }
}
```

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Login successful |
| 401 | Invalid OTP |

### Database Tables Used
`users`, `otp_codes`

---

## GET /auth/validate-token

### Description
Check if current token is valid.

### Access Role
Authenticated

### Authentication Required
Yes (Bearer token)

### Response Example
```json
{
  "valid": true,
  "user_id": 1,
  "role": "admin",
  "public_id": "uuid-string"
}
```

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Token is valid |
| 401 | Invalid or expired token |

---

# 3. Admin

## POST /admin/user

### Description
Create a new user with auto-created profile.

### Access Role
Admin

### Authentication Required
Yes

### Required Headers
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Authorization | string | Yes | `Bearer <access_token>` |

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Unique email |
| phone | string | Yes | 10-digit phone |
| password | string | Yes | Password |
| role | string | Yes | `admin`, `teacher`, `student`, or `parent` |
| {role}_name | string | Depends | Profile name (required for student/teacher) |
| admission_number | string | For student | Admission number |
| employee_code | string | For teacher | Employee code |

### Status Codes
| Code | Description |
|------|-------------|
| 201 | User created |
| 400 | Duplicate email/phone |
| 401 | Not authenticated |
| 403 | Not authorized |
| 422 | Validation error |

### Database Tables Used
`users`, `student_profiles`, `teacher_profiles`, `admin_profiles`

---

## GET /admin/users

### Description
List all users with optional filters.

### Access Role
Admin

### Authentication Required
Yes

### Query Parameters
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| skip | int | No | 0 | Pagination offset |
| limit | int | No | 100 | Max results (max 500) |
| role | string | No | — | Filter by role |
| is_active | bool | No | — | Filter by active status |

### Status Codes
| Code | Description |
|------|-------------|
| 200 | List of users |
| 401 | Not authenticated |
| 403 | Not authorized |

### Database Tables Used
`users`

---

## GET /admin/users/{public_id}

### Description
Get user by public ID.

### Access Role
Admin

### Path Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| public_id | string | Yes | User's public UUID |

### Status Codes
| Code | Description |
|------|-------------|
| 200 | User found |
| 404 | User not found |

---

## PATCH /admin/users/{public_id}

### Description
Update user (phone, is_active).

### Access Role
Admin

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| phone | string | No | Updated phone |
| is_active | bool | No | Toggle active status |

### Status Codes
| Code | Description |
|------|-------------|
| 200 | User updated |
| 404 | User not found |

---

## DELETE /admin/users/{public_id}

### Description
Deactivate a user (soft delete).

### Access Role
Admin

### Status Codes
| Code | Description |
|------|-------------|
| 204 | User deactivated |
| 404 | User not found |

---

## GET /admin/students

### Description
List all student profiles.

### Access Role
Admin, Teacher, Student

### Status Codes
| Code | Description |
|------|-------------|
| 200 | List of student profiles |

---

## GET /admin/students/{profile_id}

### Description
Get student profile by ID.

### Access Role
Admin, Teacher, Student

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Profile found |
| 404 | Profile not found |

---

## PATCH /admin/students/{profile_id}

### Description
Update student profile.

### Access Role
Admin

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_name | string | No | Updated name |
| date_of_birth | date | No | Date of birth |
| gender | string | No | Male/Female/Other |
| address | string | No | Address |
| phone | string | No | Contact phone |

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Profile updated |
| 404 | Profile not found |

---

## DELETE /admin/students/{profile_id}

### Description
Deactivate a student profile.

### Access Role
Admin

### Status Codes
| Code | Description |
|------|-------------|
| 204 | Profile deactivated |

---

## GET /admin/teachers

### Description
List all teacher profiles.

### Access Role
Admin, Teacher, Student

---

## GET /admin/teachers/{profile_id}

### Description
Get teacher profile by ID.

### Access Role
Admin, Teacher, Student

---

## PATCH /admin/teachers/{profile_id}

### Description
Update teacher profile.

### Access Role
Admin

---

## DELETE /admin/teachers/{profile_id}

### Description
Deactivate a teacher profile.

### Access Role
Admin

---

## GET /admin/admins

### Description
List all admin profiles.

### Access Role
Admin, Teacher, Student

---

## GET /admin/admins/{profile_id}

### Description
Get admin profile by ID.

### Access Role
Admin, Teacher, Student

---

## PATCH /admin/admins/{profile_id}

### Description
Update admin profile.

### Access Role
Admin

**⚠️ Security Note:** This endpoint allows updating `is_super_admin`. Any admin can grant super-admin privileges.

---

## DELETE /admin/admins/{profile_id}

### Description
Deactivate an admin profile.

### Access Role
Admin

---

# 4. Users

## GET /users/me

### Description
Get current authenticated user's profile.

### Access Role
Authenticated

### Authentication Required
Yes

### Status Codes
| Code | Description |
|------|-------------|
| 200 | Current user profile |
| 401 | Not authenticated |

---

## PATCH /users/me

### Description
Update own profile (self-service).

### Access Role
Authenticated

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| phone | string | No | Updated phone |

**Note:** `is_active` is excluded from self-service updates.

---

## GET /users/{public_id}

### Description
Get user by public ID.

### Access Role
Authenticated

---

# 5. Academics

## POST /academics/sessions

### Description
Create academic session.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Session name (e.g., "2024-2025") |
| start_date | date | Yes | Session start date |
| end_date | date | Yes | Session end date |
| is_active | bool | No | Default true |

---

## GET /academics/sessions

### Description
List academic sessions.

### Access Role
Public (no auth required)

---

## GET /academics/sessions/{session_id}

### Description
Get academic session by ID.

### Access Role
Public (no auth required)

---

## PUT /academics/sessions/{session_id}

### Description
Update academic session.

### Access Role
Admin, Teacher

---

## DELETE /academics/sessions/{session_id}

### Description
Deactivate academic session.

### Access Role
Admin

---

## POST /academics/classrooms

### Description
Create classroom.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Class name |
| academic_sessions_id | int | Yes | Associated session |
| section | string | No | Section (A, B, C) |
| is_active | bool | No | Default true |

---

## GET /academics/classrooms

### Description
List classrooms.

### Access Role
Public (no auth required)

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | No | Filter by session |

---

## GET /academics/classrooms/{classroom_id}

### Description
Get classroom by ID.

### Access Role
Public (no auth required)

---

## PUT /academics/classrooms/{classroom_id}

### Description
Update classroom.

### Access Role
Admin, Teacher

---

## DELETE /academics/classrooms/{classroom_id}

### Description
Deactivate classroom.

### Access Role
Admin

---

## POST /academics/subjects

### Description
Create subject.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Subject name |
| code | string | Yes | Subject code (e.g., "MATH101") |
| is_active | bool | No | Default true |

---

## GET /academics/subjects

### Description
List subjects.

### Access Role
Public (no auth required)

---

## GET /academics/subjects/{subject_id}

### Description
Get subject by ID.

### Access Role
Public (no auth required)

---

## PUT /academics/subjects/{subject_id}

### Description
Update subject.

### Access Role
Admin, Teacher

---

## DELETE /academics/subjects/{subject_id}

### Description
Deactivate subject.

### Access Role
Admin

---

## POST /academics/class-subjects

### Description
Create class-subject mapping.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| classroom_id | int | Yes | Classroom ID |
| subject_id | int | Yes | Subject ID |
| academic_sessions_id | int | Yes | Session ID |

---

## GET /academics/class-subjects

### Description
List class-subject mappings.

### Access Role
Public (no auth required)

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| classroom_id | int | No | Filter by classroom |
| academic_sessions_id | int | No | Filter by session |

---

## GET /academics/class-subjects/{class_subject_id}

### Description
Get class-subject mapping.

### Access Role
Public (no auth required)

---

## PUT /academics/class-subjects/{class_subject_id}

### Description
Update class-subject mapping.

### Access Role
Admin, Teacher

---

## DELETE /academics/class-subjects/{class_subject_id}

### Description
Deactivate class-subject mapping.

### Access Role
Admin

---

# 6. Operations

## POST /operations/assign-teacher

### Description
Assign teacher to a subject for a class/session.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| teacher_profile_id | int | Yes | Teacher profile ID |
| class_subject_id | int | Yes | Class-subject mapping ID |
| is_class_teacher | bool | No | Is class teacher? |
| remarks | string | No | Optional remarks |

---

## GET /operations/teacher-assignments

### Description
List all teacher assignments.

### Access Role
Public (no auth required)

---

## GET /operations/teacher-assignments/{assignment_id}

### Description
Get teacher assignment by ID.

### Access Role
Public (no auth required)

---

## PUT /operations/teacher-assignments/{assignment_id}

### Description
Update teacher assignment.

### Access Role
Admin, Teacher

---

## DELETE /operations/teacher-assignments/{assignment_id}

### Description
Unassign teacher.

### Access Role
Admin

---

## POST /operations/enroll-student

### Description
Enroll student in a class.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_profile_id | int | Yes | Student profile ID |
| classroom_id | int | Yes | Classroom ID |
| academic_sessions_id | int | Yes | Session ID |
| roll_number | int | No | Roll number |
| status | string | No | Enrollment status |

---

## GET /operations/student-enrollments

### Description
List all student enrollments.

### Access Role
Public (no auth required)

---

## GET /operations/student-enrollments/{enrollment_id}

### Description
Get student enrollment by ID.

### Access Role
Public (no auth required)

---

## PUT /operations/student-enrollments/{enrollment_id}

### Description
Update student enrollment.

### Access Role
Admin, Teacher

---

## DELETE /operations/student-enrollments/{enrollment_id}

### Description
Unenroll student.

### Access Role
Admin

---

## POST /operations/promote-student

### Description
Promote student to next session/class.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | int | Yes | Student profile ID |
| from_session_id | int | Yes | Current session ID |
| to_session_id | int | Yes | Target session ID |
| to_classroom_id | int | Yes | Target classroom ID |
| new_roll | int | No | New roll number |

---

## GET /operations/promote-student/{student_id}

### Description
Get promotion history for a student.

### Access Role
Public (no auth required)

---

# 7. Fees

## POST /fees

### Description
Create a fee record.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_class_id | int | Yes | Student enrollment ID |
| fee_type | string | Yes | Fee type (TUITION, etc.) |
| amount | float | Yes | Fee amount |
| due_date | date | Yes | Payment due date |
| discount | float | No | Discount amount |
| fine | float | No | Late fine |
| remarks | string | No | Remarks |

---

## GET /fees

### Description
List all fees.

### Access Role
Admin

---

## POST /fees/{fee_id}/pay

### Description
Record a payment against a fee.

### Access Role
Admin, Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| paid_amount | float | Yes | Amount paid |
| payment_date | date | No | Payment date |
| payment_mode | string | No | Cash/Cheque/Online |

---

## GET /fees/pending

### Description
List pending fees.

### Access Role
Admin

---

## GET /fees/my

### Description
Get own fee records (student self-service).

### Access Role
Student

---

## GET /fees/student/{student_class_id}

### Description
Get fees for a specific student enrollment.

### Access Role
Admin

---

## GET /fees/{fee_id}

### Description
Get fee by fee ID.

### Access Role
Authenticated (admins see all, students see own)

---

## PUT /fees/{fee_id}

### Description
Update fee record.

### Access Role
Admin

---

## DELETE /fees/{fee_id}

### Description
Deactivate a fee record.

### Access Role
Admin

---

# 8. Exams

## POST /exams/

### Description
Create a new exam.

### Access Role
Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Exam title |
| class_subject_id | int | Yes | Class-subject mapping ID |
| exam_date | date | Yes | Exam date |
| max_marks | float | Yes | Maximum marks |
| status | string | No | DRAFT/PUBLISHED/COMPLETED/CANCELLED |

---

## GET /exams/

### Description
List exams with filters.

### Access Role
Authenticated

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| classroom_id | int | No | Filter by classroom |
| status | string | No | Filter by status |

---

## GET /exams/{exam_id}

### Description
Get exam by ID.

### Access Role
Authenticated

---

## PUT /exams/{exam_id}

### Description
Update exam.

### Access Role
Teacher (creator or admin)

---

## DELETE /exams/{exam_id}

### Description
Soft-delete exam.

### Access Role
Teacher (creator or admin)

---

## POST /exams/{exam_id}/results

### Description
Upload results for an exam.

### Access Role
Teacher

### Request Parameters
```json
[
  {
    "student_profile_id": 1,
    "marks_obtained": 85.5,
    "remarks": "Good performance"
  }
]
```

---

## GET /exams/{exam_id}/results

### Description
Get results for an exam.

### Access Role
Authenticated (admins see all; teachers see own; students see own only)

---

## GET /exams/results/{result_id}

### Description
Get a single exam result.

### Access Role
Authenticated

---

## DELETE /exams/results/{result_id}

### Description
Delete a single exam result.

### Access Role
Teacher

---

# 9. Assignments

## POST /assignments/

### Description
Create a new assignment.

### Access Role
Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Assignment title |
| description | string | No | Description |
| class_subject_id | int | Yes | Class-subject mapping |
| due_date | date | Yes | Submission due date |
| max_marks | float | No | Maximum marks |
| status | string | No | DRAFT/PUBLISHED/CLOSED |

---

## GET /assignments/

### Description
List assignments.

### Access Role
Authenticated (teachers see own subjects'; students see own class')

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| classroom_id | int | No | Filter by classroom |
| status | string | No | Filter by status |

---

## GET /assignments/{assignment_id}

### Description
Get assignment by ID.

### Access Role
Authenticated

---

## PUT /assignments/{assignment_id}

### Description
Update assignment.

### Access Role
Teacher (creator or admin)

---

## DELETE /assignments/{assignment_id}

### Description
Soft-delete assignment.

### Access Role
Teacher (creator or admin)

---

## POST /assignments/{assignment_id}/results

### Description
Grade students for an assignment.

### Access Role
Teacher

---

## GET /assignments/{assignment_id}/results

### Description
Get assignment results.

### Access Role
Authenticated

---

## GET /assignments/results/{result_id}

### Description
Get single assignment result.

### Access Role
Authenticated

---

## DELETE /assignments/results/{result_id}

### Description
Delete an assignment result.

### Access Role
Teacher

---

# 10. Study Materials

## POST /study-materials

### Description
Upload study material file.

### Access Role
Admin, Teacher

### Request Parameters (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Material title |
| description | string | No | Description |
| material_type | string | No | PDF/VIDEO/DOCUMENT/LINK/OTHER |
| academic_sessions_id | int | Yes | Session ID |
| classroom_id | int | Yes | Classroom ID |
| class_subject_id | int | Yes | Class-subject ID |
| teacher_subject_id | int | Yes | Teacher-subject ID |
| file | file | Yes | Upload file |

---

## GET /study-materials

### Description
List all study materials.

### Access Role
Authenticated

---

## GET /study-materials/class-subject/{class_subject_id}

### Description
Get materials for a class-subject.

### Access Role
Authenticated

---

## GET /study-materials/{id}

### Description
Get study material by ID.

### Access Role
Authenticated

---

## GET /study-materials/{id}/view

### Description
View a study material file (inline).

### Access Role
Student, Teacher, Admin

---

## GET /study-materials/{id}/download

### Description
Download a study material file.

### Access Role
Student, Teacher, Admin

---

## PUT /study-materials/{id}

### Description
Update study material.

### Access Role
Admin, Teacher

---

## DELETE /study-materials/{id}

### Description
Delete study material.

### Access Role
Admin

---

# 11. Notices

## POST /notices/

### Description
Create a notice with optional file attachment.

### Access Role
Admin, Teacher

### Request Parameters (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Notice title |
| description | string | Yes | Notice content |
| notice_type | string | No | GENERAL/ACADEMIC/EXAM/FEE/EVENT |
| audience | string | No | ALL/CLASS/SECTION/TEACHER/STUDENT |
| publish_date | date | Yes | Publication date |
| expiry_date | date | No | Expiry date |
| is_pinned | bool | No | Pin to top |
| academic_sessions_id | int | Yes | Session ID |
| classroom_id | int | No | Target classroom (if audience=CLASS) |
| file | file | No | Attachment file |

---

## GET /notices/

### Description
Get notices with filters.

### Access Role
Authenticated

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| notice_type | string | No | Filter by type |
| audience | string | No | Filter by audience |
| is_pinned | bool | No | Filter pinned |

---

## GET /notices/{notice_id}

### Description
Get notice by ID.

### Access Role
Authenticated

---

## PUT /notices/{notice_id}

### Description
Update notice.

### Access Role
Admin, Teacher

---

## DELETE /notices/{notice_id}

### Description
Soft-delete notice.

### Access Role
Admin

---

## POST /notices/{notice_id}/pin

### Description
Pin a notice.

### Access Role
Admin, Teacher

---

## POST /notices/{notice_id}/unpin

### Description
Unpin a notice.

### Access Role
Admin, Teacher

---

## GET /notices/{notice_id}/view

### Description
View notice attachment.

### Access Role
Authenticated

---

## GET /notices/{notice_id}/download

### Description
Download notice attachment.

### Access Role
Authenticated

---

# 12. Daily Class & Attendance

## POST /daily-class/

### Description
Create a daily class record.

### Access Role
Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| teacher_subject_id | int | Yes | Teacher assignment ID |
| class_subject_id | int | Yes | Class-subject ID |
| class_date | date | Yes | Date of class |
| topic | string | No | Topic covered |
| lecture_status | string | No | Scheduled/Ongoing/Completed/Cancelled |

---

## GET /daily-class/

### Description
Get daily classes with filters.

### Access Role
Authenticated

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| classroom_id | int | No | Filter by classroom |
| class_date | date | No | Filter by date |
| lecture_status | string | No | Filter by status |

---

## GET /daily-class/{daily_class_id}

### Description
Get daily class by ID.

### Access Role
Authenticated

---

## PUT /daily-class/{daily_class_id}

### Description
Update daily class.

### Access Role
Teacher (owning teacher only)

---

## DELETE /daily-class/{daily_class_id}

### Description
Delete daily class.

### Access Role
Teacher (owning teacher only)

---

## POST /daily-class/{daily_class_id}/students

### Description
Mark attendance (bulk upsert).

### Access Role
Teacher

### Request Parameters
```json
[
  {
    "student_profile_id": 1,
    "attendance_status": "Present",
    "remarks": "On time"
  }
]
```

---

## GET /daily-class/{daily_class_id}/students

### Description
Get attendance for a daily class.

### Access Role
Authenticated (admin/teacher see all; student sees own only)

---

## GET /daily-class/students/{record_id}

### Description
Get single attendance record.

### Access Role
Authenticated

---

## PUT /daily-class/students/{record_id}

### Description
Update attendance record.

### Access Role
Authenticated (teacher or admin)

---

## DELETE /daily-class/students/{record_id}

### Description
Delete attendance record.

### Access Role
Authenticated

---

## POST /daily-class/attendance/recalculate/{student_class_id}

### Description
Recalculate attendance summary from history.

### Access Role
Teacher

---

## GET /daily-class/attendance/summary/{student_class_id}

### Description
Get cached attendance summary.

### Access Role
Authenticated

---

## GET /daily-class/classroom/{classroom_id}/summary

### Description
Get class summary for date range.

### Access Role
Authenticated

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| start_date | date | Yes | Range start |
| end_date | date | Yes | Range end |

---

# 13. Timetable

## GET /weekdays

### Description
List all weekdays.

### Access Role
Authenticated

---

## POST /weekdays

### Description
Create a weekday.

### Access Role
Admin, Teacher

---

## PUT /weekdays/{weekday_id}

### Description
Update a weekday.

### Access Role
Admin

---

## DELETE /weekdays/{weekday_id}

### Description
Deactivate a weekday.

### Access Role
Admin

---

## GET /timeslots

### Description
List all time slots.

### Access Role
Authenticated

---

## POST /timeslots

### Description
Create a time slot.

### Access Role
Admin, Teacher

---

## PUT /timeslots/{timeslot_id}

### Description
Update a time slot.

### Access Role
Admin

---

## DELETE /timeslots/{timeslot_id}

### Description
Deactivate a time slot.

### Access Role
Admin

---

## GET /timetable/class/{classroom_id}

### Description
Get timetable for a class.

### Access Role
Authenticated

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | int | Yes | Academic session ID |

---

## GET /timetables

### Description
List timetable entries with filters (admin/teacher view).

### Access Role
Admin, Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| class | int | No | Classroom ID |
| teacher | int | No | Teacher-subject ID |
| subject | int | No | Class-subject ID |
| day | int | No | Weekday ID |

---

## POST /timetable

### Description
Create a timetable entry.

### Access Role
Admin, Teacher

---

## PUT /timetable/{id}

### Description
Update a timetable entry.

### Access Role
Admin, Teacher

---

## DELETE /timetable/{id}

### Description
Delete a timetable entry.

### Access Role
Admin

---

## GET /student/timetable

### Description
Get own class timetable (student).

### Access Role
Student

---

## GET /teacher/timetable

### Description
Get assigned classes timetable (teacher).

### Access Role
Teacher

---

## GET /availability/teacher/{teacher_subject_id}

### Description
Get teacher availability.

### Access Role
Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | int | Yes | Academic session ID |

---

## POST /availability

### Description
Create teacher availability.

### Access Role
Teacher

---

## PUT /availability/{availability_id}

### Description
Update teacher availability.

### Access Role
Teacher

---

## DELETE /availability/{availability_id}

### Description
Withdraw availability slot.

### Access Role
Teacher

---

# 14. Chat

## POST /chat/rooms

### Description
Create a chat room between teacher and student.

### Access Role
Teacher

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_profile_id | int | Yes | Student profile ID |
| subject | string | No | Room subject/topic |

---

## GET /chat/rooms

### Description
Get chat rooms for current user.

### Access Role
Authenticated

---

## GET /chat/rooms/{room_id}

### Description
Get chat room by ID.

### Access Role
Authenticated (participant only)

---

## PUT /chat/rooms/{room_id}

### Description
Update a chat room.

### Access Role
Authenticated (participant)

---

## DELETE /chat/rooms/{room_id}

### Description
Archive a chat room.

### Access Role
Authenticated (participant)

---

## POST /chat/rooms/{room_id}/messages

### Description
Send a message.

### Access Role
Authenticated (participant)

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message | string | Yes | Message content |

---

## GET /chat/rooms/{room_id}/messages

### Description
Get messages in a room.

### Access Role
Authenticated (participant)

### Query Parameters
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| limit | int | No | 50 | Messages to fetch (max 200) |
| before | datetime | No | — | Fetch messages before this timestamp |

---

## PUT /chat/rooms/{room_id}/messages/{message_id}

### Description
Edit own message.

### Access Role
Authenticated (message owner)

---

## DELETE /chat/rooms/{room_id}/messages/{message_id}

### Description
Delete own message.

### Access Role
Authenticated (message owner)

---

## GET /chat/unread

### Description
Get unread message counts.

### Access Role
Authenticated

---

# 15. Student ID Cards

## GET /student/id-card/all

### Description
List all generated ID cards (paginated).

### Access Role
Admin

---

## POST /student/id-card/{student_profile_id}

### Description
Generate or regenerate ID card.

### Access Role
Admin, Teacher

### Query Parameters
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| regenerate | bool | No | false | Force regeneration |

---

## GET /student/id-card/{student_profile_id}

### Description
View ID card metadata.

### Access Role
Authenticated (student sees own; admin/teacher see any)

---

## GET /student/id-card/{student_profile_id}/download

### Description
Download ID card PDF.

### Access Role
Authenticated (student sees own; admin/teacher see any)

---

# 16. Search

## GET /students/search

### Description
Natural-language search for students.

### Access Role
Admin, Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | Search query (name, email, admission number, phone) |
| limit | int | No | Max results (default 10, max 50) |

---

## GET /teachers/search

### Description
Natural-language search for teachers.

### Access Role
Admin, Teacher, Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | Search query (name, email, employee code, phone) |
| limit | int | No | Max results |

---

# 17. Khan Academy

## POST /khan-academy/topics

### Description
Create a Khan Academy topic catalog entry.

### Access Role
Admin, Teacher

---

## GET /khan-academy/topics

### Description
List topics.

### Access Role
Authenticated

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| subject_id | int | No | Filter by subject |
| classroom_id | int | No | Filter by classroom |

---

## GET /khan-academy/topics/{topic_id}

### Description
Get topic by ID.

### Access Role
Authenticated

---

## PUT /khan-academy/topics/{topic_id}

### Description
Update topic.

### Access Role
Admin, Teacher

---

## DELETE /khan-academy/topics/{topic_id}

### Description
Soft-delete topic.

### Access Role
Admin

---

## POST /khan-academy/progress/subject

### Description
Upsert KA subject progress snapshot.

### Access Role
Admin, Teacher

---

## POST /khan-academy/progress/topic

### Description
Upsert KA topic progress snapshot.

### Access Role
Admin, Teacher

---

## GET /khan-academy/progress/student/{student_profile_id}

### Description
Get student's KA subject + topic progress.

### Access Role
Authenticated (student sees own; admin/teacher see any)

---

## POST /khan-academy/activity/student

### Description
Upsert student daily activity summary.

### Access Role
Admin, Teacher

---

## POST /khan-academy/activity/subject

### Description
Log per-topic KA activity event.

### Access Role
Admin, Teacher

---

## GET /khan-academy/activity/student/{student_profile_id}

### Description
Get student's KA activity logs.

### Access Role
Authenticated (student sees own; admin/teacher see any)

---

# 18. Zoom

## POST /zoom/files

### Description
Register a class session's file bundle.

### Access Role
Admin, Teacher

---

## GET /zoom/files

### Description
List session file bundles.

### Access Role
Authenticated

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| classroom_id | int | No | Filter by classroom |
| date | string | No | Filter by date |

---

## GET /zoom/files/{zoom_file_id}

### Description
Get file bundle by ID.

### Access Role
Authenticated

---

## PUT /zoom/files/{zoom_file_id}

### Description
Update file bundle.

### Access Role
Admin, Teacher

---

## DELETE /zoom/files/{zoom_file_id}

### Description
Soft-delete file bundle.

### Access Role
Admin

---

## POST /zoom/meetings

### Description
Upsert a Zoom meeting record.

### Access Role
Admin, Teacher

---

## GET /zoom/meetings

### Description
List Zoom meetings.

### Access Role
Admin, Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| host_id | string | No | Filter by Zoom host ID |

---

## GET /zoom/meetings/{uuid}

### Description
Get Zoom meeting by UUID.

### Access Role
Admin, Teacher

---

# 19. Reports

## POST /reports/generate

### Description
Generate progress report for a student.

### Access Role
Authenticated (student sees own; admin/teacher see any)

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_profile_id | int | Yes | Student ID |
| data_start_date | date | Yes | Data range start |
| data_end_date | date | Yes | Data range end |

---

## GET /reports/student/{student_profile_id}

### Description
List generated reports for a student.

### Access Role
Authenticated (student sees own; admin/teacher see any)

---

## GET /reports/{report_id}/download

### Description
Download report PDF.

### Access Role
Authenticated

---

## DELETE /reports/{report_id}

### Description
Delete a report.

### Access Role
Admin

---

## GET /reports/{report_id}/activity

### Description
Get activity report for a report.

### Access Role
Authenticated

---

## PUT /reports/{report_id}/activity

### Description
Set activity report data.

### Access Role
Admin, Teacher

---

## GET /reports/{report_id}/subject-progress

### Description
Get subject progress items for a report.

### Access Role
Authenticated

---

## DELETE /reports/subject-progress/{item_id}

### Description
Delete a subject progress item.

### Access Role
Admin, Teacher

---

## GET /reports/{report_id}/topic-progress

### Description
Get topic progress items for a report.

### Access Role
Authenticated

---

## DELETE /reports/topic-progress/{item_id}

### Description
Delete a topic progress item.

### Access Role
Admin, Teacher

---

## GET /reports/{report_id}/zoom-duration

### Description
Get Zoom duration report.

### Access Role
Authenticated

---

## PUT /reports/{report_id}/zoom-duration

### Description
Set Zoom duration report.

### Access Role
Admin, Teacher

---

## GET /reports/{report_id}/zoom-interaction

### Description
Get Zoom interaction report.

### Access Role
Authenticated

---

## PUT /reports/{report_id}/zoom-interaction

### Description
Set Zoom interaction report.

### Access Role
Admin, Teacher

---

# 20. Student Portal

## GET /student/profile

### Description
Get own student profile.

### Access Role
Student

---

## PUT /student/profile

### Description
Update own student profile.

### Access Role
Student

---

## GET /student/classes

### Description
Get own class enrollments.

### Access Role
Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | No | Filter by session |

---

## GET /student/attendance/summary

### Description
Get own attendance summary.

### Access Role
Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | Yes | Session ID |

---

## GET /student/attendance/daily

### Description
Get own daily attendance records.

### Access Role
Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | Yes | Session ID |
| start_date | datetime | No | Range start |
| end_date | datetime | No | Range end |

---

## GET /student/assignments

### Description
Get own assignment results.

### Access Role
Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | Yes | Session ID |
| subject_id | int | No | Filter by subject |

---

## GET /student/exams

### Description
Get own exam results.

### Access Role
Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | Yes | Session ID |
| subject_id | int | No | Filter by subject |

---

## GET /student/fees

### Description
Get own fee records.

### Access Role
Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | Yes | Session ID |
| status | string | No | Filter by status (PENDING/PAID/OVERDUE) |

---

## GET /student/fees/summary

### Description
Get own fee summary.

### Access Role
Student

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | Yes | Session ID |

---

# 21. Teacher Portal

## GET /teacher/profile

### Description
Get own teacher profile.

### Access Role
Teacher

---

## PUT /teacher/profile

### Description
Update own teacher profile.

### Access Role
Teacher

---

## GET /teacher/classes

### Description
Get assigned classes.

### Access Role
Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | No | Filter by session |

---

## GET /teacher/students

### Description
Get students in a class.

### Access Role
Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| classroom_id | int | Yes | Classroom ID |
| academic_sessions_id | int | Yes | Session ID |

---

## GET /teacher/my-students

### Description
Get all students across assigned classes.

### Access Role
Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | Yes | Session ID |
| classroom_id | int | No | Filter by classroom |

---

## GET /teacher/subjects

### Description
Get assigned subjects.

### Access Role
Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | No | Filter by session |

---

## POST /teacher/attendance/mark

### Description
Mark attendance for a daily class.

### Access Role
Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| daily_class_id | int | Yes | Daily class ID |

### Request Body
```json
[
  {
    "student_profile_id": 1,
    "attendance_status": "Present"
  }
]
```

---

## GET /teacher/assignments

### Description
Get own assignments.

### Access Role
Teacher

### Query Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| academic_sessions_id | int | No | Filter by session |
| classroom_id | int | No | Filter by classroom |
| status | string | No | Filter by status |

---

## GET /teacher/dashboard

### Description
Get teacher dashboard data.

### Access Role
Teacher

---

# 22. Dashboard

## GET /dashboard/student

### Description
Get student dashboard with aggregated data.

### Access Role
Student

---

## GET /dashboard/teacher

### Description
Get teacher dashboard with aggregated data.

### Access Role
Teacher

---

## GET /dashboard/admin

### Description
Get admin dashboard with school-wide aggregates.

### Access Role
Admin

---

# 23. Attachments

## POST /attachments/upload

### Description
Upload a base64-encoded file attachment.

### Access Role
Authenticated

### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| entity_type | string | Yes | Entity type identifier |
| entity_id | int | Yes | Entity ID |
| file_name | string | Yes | Original file name |
| mime_type | string | Yes | MIME type |
| file_data | string | Yes | Base64-encoded file content |

---

## GET /attachments/{attachment_id}

### Description
Download attachment file.

### Access Role
Authenticated

---

## GET /attachments/entity/{entity_type}/{entity_id}

### Description
List all attachments for an entity.

### Access Role
Authenticated

---

## DELETE /attachments/{attachment_id}

### Description
Delete an attachment.

### Access Role
Authenticated

---

# 24. Role Access Matrix

| # | Endpoint | Method | Public | Admin | Teacher | Student |
|---|----------|--------|--------|-------|---------|---------|
| 1 | `/health` | GET | ✅ | ✅ | ✅ | ✅ |
| 2 | `/auth/login` | POST | ✅ | ✅ | ✅ | ✅ |
| 3 | `/auth/token` | POST | ✅ | ✅ | ✅ | ✅ |
| 4 | `/auth/refresh` | POST | ✅ | ✅ | ✅ | ✅ |
| 5 | `/auth/logout` | POST | ❌ | ✅ | ✅ | ✅ |
| 6 | `/auth/change-password` | POST | ❌ | ✅ | ✅ | ✅ |
| 7 | `/auth/forgot-password` | POST | ✅ | ✅ | ✅ | ✅ |
| 8 | `/auth/reset-password` | POST | ✅ | ✅ | ✅ | ✅ |
| 9 | `/auth/send-verification-otp` | POST | ❌ | ✅ | ✅ | ✅ |
| 10 | `/auth/resend-otp` | POST | ❌ | ✅ | ✅ | ✅ |
| 11 | `/auth/verify-email` | POST | ❌ | ✅ | ✅ | ✅ |
| 12 | `/auth/send-login-otp` | POST | ✅ | ✅ | ✅ | ✅ |
| 13 | `/auth/verify-login-otp` | POST | ✅ | ✅ | ✅ | ✅ |
| 14 | `/auth/validate-token` | GET | ❌ | ✅ | ✅ | ✅ |
| 15 | `/admin/user` | POST | ❌ | ✅ | ❌ | ❌ |
| 16 | `/admin/users` | GET | ❌ | ✅ | ❌ | ❌ |
| 17 | `/admin/users/{public_id}` | GET | ❌ | ✅ | ❌ | ❌ |
| 18 | `/admin/users/{public_id}` | PATCH | ❌ | ✅ | ❌ | ❌ |
| 19 | `/admin/users/{public_id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 20 | `/admin/students` | GET | ❌ | ✅ | ✅ | ✅ |
| 21 | `/admin/students/{profile_id}` | GET | ❌ | ✅ | ✅ | ✅ |
| 22 | `/admin/students/{profile_id}` | PATCH | ❌ | ✅ | ❌ | ❌ |
| 23 | `/admin/students/{profile_id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 24 | `/admin/teachers` | GET | ❌ | ✅ | ✅ | ✅ |
| 25 | `/admin/teachers/{profile_id}` | GET | ❌ | ✅ | ✅ | ✅ |
| 26 | `/admin/teachers/{profile_id}` | PATCH | ❌ | ✅ | ❌ | ❌ |
| 27 | `/admin/teachers/{profile_id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 28 | `/admin/admins` | GET | ❌ | ✅ | ✅ | ✅ |
| 29 | `/admin/admins/{profile_id}` | GET | ❌ | ✅ | ✅ | ✅ |
| 30 | `/admin/admins/{profile_id}` | PATCH | ❌ | ✅ | ❌ | ❌ |
| 31 | `/admin/admins/{profile_id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 32 | `/users/me` | GET | ❌ | ✅ | ✅ | ✅ |
| 33 | `/users/me` | PATCH | ❌ | ✅ | ✅ | ✅ |
| 34 | `/users/{public_id}` | GET | ❌ | ✅ | ✅ | ✅ |
| 35-39 | `/academics/sessions` | CRUD | ✅/Admin | ✅ | ✅ | View |
| 40-44 | `/academics/classrooms` | CRUD | ✅/Admin | ✅ | ✅ | View |
| 45-49 | `/academics/subjects` | CRUD | ✅/Admin | ✅ | ✅ | View |
| 50-54 | `/academics/class-subjects` | CRUD | ✅/Admin | ✅ | ✅ | View |
| 55 | `/operations/assign-teacher` | POST | ❌ | ✅ | ✅ | ❌ |
| 56 | `/operations/teacher-assignments` | GET | ✅ | ✅ | ✅ | ✅ |
| 57 | `/operations/teacher-assignments/{id}` | GET | ✅ | ✅ | ✅ | ✅ |
| 58 | `/operations/teacher-assignments/{id}` | PUT | ❌ | ✅ | ✅ | ❌ |
| 59 | `/operations/teacher-assignments/{id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 60 | `/operations/enroll-student` | POST | ❌ | ✅ | ✅ | ❌ |
| 61 | `/operations/student-enrollments` | GET | ✅ | ✅ | ✅ | ✅ |
| 62 | `/operations/student-enrollments/{id}` | GET | ✅ | ✅ | ✅ | ✅ |
| 63 | `/operations/student-enrollments/{id}` | PUT | ❌ | ✅ | ✅ | ❌ |
| 64 | `/operations/student-enrollments/{id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 65 | `/operations/promote-student` | POST | ❌ | ✅ | ✅ | ❌ |
| 66 | `/operations/promote-student/{id}` | GET | ✅ | ✅ | ✅ | ✅ |
| 67 | `/fees` | POST | ❌ | ✅ | ✅ | ❌ |
| 68 | `/fees` | GET | ❌ | ✅ | ❌ | ❌ |
| 69 | `/fees/pending` | GET | ❌ | ✅ | ❌ | ❌ |
| 70 | `/fees/my` | GET | ❌ | ❌ | ❌ | ✅ |
| 71 | `/fees/{fee_id}` | GET | ❌ | ✅ | ✅ | Own Only |
| 72 | `/fees/{fee_id}` | PUT | ❌ | ✅ | ❌ | ❌ |
| 73 | `/fees/{fee_id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 74 | `/fees/{fee_id}/pay` | POST | ❌ | ✅ | ✅ | ❌ |
| 75 | `/exams/` | POST | ❌ | ❌ | ✅ | ❌ |
| 76-78 | `/exams/` | GET/Read | ❌ | ✅ | ✅ | Own |
| 79-80 | `/exams/{id}` | PUT/DELETE | ❌ | ❌ | ✅ | ❌ |
| 81-83 | `/exams/{id}/results` | CRUD | ❌ | ✅ | ✅ | Own |
| 84-86 | `/assignments/` | POST/GET | ❌ | ✅ | ✅ | Own |
| 87-88 | `/assignments/{id}` | PUT/DELETE | ❌ | ❌ | ✅ | ❌ |
| 89-91 | `/assignments/{id}/results` | CRUD | ❌ | ✅ | ✅ | Own |
| 92 | `/study-materials` | POST | ❌ | ✅ | ✅ | ❌ |
| 93-95 | `/study-materials` | GET | ❌ | ✅ | ✅ | ✅ |
| 96 | `/study-materials/{id}/view` | GET | ❌ | ✅ | ✅ | ✅ |
| 97 | `/study-materials/{id}/download` | GET | ❌ | ✅ | ✅ | ✅ |
| 98-99 | `/study-materials/{id}` | PUT/DELETE | ❌ | ✅ | ✅ | ❌ |
| 100 | `/notices/` | POST | ❌ | ✅ | ✅ | ❌ |
| 101-103 | `/notices/` | GET | ❌ | ✅ | ✅ | ✅ |
| 104-108 | `/notices/{id}` | PUT/PIN/UNPIN | ❌ | ✅ | ✅ | ❌ |
| 109-110 | `/notices/{id}/view` | GET | ❌ | ✅ | ✅ | ✅ |
| 111 | `/daily-class/` | POST | ❌ | ❌ | ✅ | ❌ |
| 112 | `/daily-class/` | GET | ❌ | ✅ | ✅ | ✅ |
| 113-114 | `/daily-class/{id}` | PUT/DELETE | ❌ | ❌ | ✅ | ❌ |
| 115 | `/daily-class/{id}/students` | POST | ❌ | ❌ | ✅ | ❌ |
| 116 | `/daily-class/{id}/students` | GET | ❌ | ✅ | ✅ | Own |
| 117-119 | `/daily-class/students/{id}` | RUD | ❌ | ✅ | ✅ | Own |
| 120 | `/daily-class/attendance/recalc/{id}` | POST | ❌ | ❌ | ✅ | ❌ |
| 121 | `/daily-class/attendance/summary/{id}` | GET | ❌ | ✅ | ✅ | ✅ |
| 122 | `/daily-class/classroom/{id}/summary` | GET | ❌ | ✅ | ✅ | ✅ |
| 123 | `/weekdays` | GET | ❌ | ✅ | ✅ | ✅ |
| 124 | `/weekdays` | POST | ❌ | ✅ | ✅ | ❌ |
| 125-126 | `/weekdays/{id}` | PUT/DELETE | ❌ | ✅ | ❌ | ❌ |
| 127 | `/timeslots` | GET | ❌ | ✅ | ✅ | ✅ |
| 128 | `/timeslots` | POST | ❌ | ✅ | ✅ | ❌ |
| 129-130 | `/timeslots/{id}` | PUT/DELETE | ❌ | ✅ | ❌ | ❌ |
| 131 | `/timetable/class/{id}` | GET | ❌ | ✅ | ✅ | ✅ |
| 132 | `/timetables` | GET | ❌ | ✅ | ✅ | ❌ |
| 133 | `/timetable` | POST | ❌ | ✅ | ✅ | ❌ |
| 134 | `/timetable/{id}` | PUT | ❌ | ✅ | ✅ | ❌ |
| 135 | `/timetable/{id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 136 | `/student/timetable` | GET | ❌ | ❌ | ❌ | ✅ |
| 137 | `/teacher/timetable` | GET | ❌ | ❌ | ✅ | ❌ |
| 138-141 | `/availability` | CRUD | ❌ | ❌ | ✅ | ❌ |
| 142-146 | `/chat/rooms` | CRUD | ❌ | ✅ | ✅ | ✅ |
| 147-150 | `/chat/rooms/{id}/messages` | CRUD | ❌ | ✅ | ✅ | ✅ |
| 151 | `/chat/unread` | GET | ❌ | ✅ | ✅ | ✅ |
| 152 | `/student/id-card/all` | GET | ❌ | ✅ | ❌ | ❌ |
| 153 | `/student/id-card/{id}` | POST | ❌ | ✅ | ✅ | ❌ |
| 154 | `/student/id-card/{id}` | GET | ❌ | ✅ | ✅ | Own |
| 155 | `/student/id-card/{id}/download` | GET | ❌ | ✅ | ✅ | Own |
| 156 | `/students/search` | GET | ❌ | ✅ | ✅ | ❌ |
| 157 | `/teachers/search` | GET | ❌ | ✅ | ✅ | ✅ |
| 158 | `/khan-academy/topics` | POST | ❌ | ✅ | ✅ | ❌ |
| 159-160 | `/khan-academy/topics` | GET | ❌ | ✅ | ✅ | ✅ |
| 161 | `/khan-academy/topics/{id}` | PUT | ❌ | ✅ | ✅ | ❌ |
| 162 | `/khan-academy/topics/{id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 163-166 | `/khan-academy/progress` | CRUD | ❌ | ✅ | ✅ | ❌ |
| 167 | `/khan-academy/progress/student/{id}` | GET | ❌ | ✅ | ✅ | Own |
| 168-169 | `/khan-academy/activity` | POST | ❌ | ✅ | ✅ | ❌ |
| 170 | `/khan-academy/activity/student/{id}` | GET | ❌ | ✅ | ✅ | Own |
| 171-176 | `/zoom/files` | CRUD | ❌ | ✅ | ✅ | ❌ |
| 177-179 | `/zoom/meetings` | CRUD | ❌ | ✅ | ✅ | ❌ |
| 180 | `/reports/generate` | POST | ❌ | ✅ | ✅ | Own |
| 181 | `/reports/student/{id}` | GET | ❌ | ✅ | ✅ | Own |
| 182 | `/reports/{id}/download` | GET | ❌ | ✅ | ✅ | Own |
| 183 | `/reports/{id}` | DELETE | ❌ | ✅ | ❌ | ❌ |
| 184-193 | `/reports/{id}/*` | CRUD | ❌ | ✅ | ✅ | ❌ |
| 194-195 | `/student/profile` | GET/PUT | ❌ | ❌ | ❌ | ✅ |
| 196-200 | `/student/*` | GET | ❌ | ❌ | ❌ | ✅ |
| 201 | `/teacher/profile` | GET/PUT | ❌ | ❌ | ✅ | ❌ |
| 202-208 | `/teacher/*` | GET/POST | ❌ | ❌ | ✅ | ❌ |
| 209 | `/dashboard/student` | GET | ❌ | ❌ | ❌ | ✅ |
| 210 | `/dashboard/teacher` | GET | ❌ | ❌ | ✅ | ❌ |
| 211 | `/dashboard/admin` | GET | ❌ | ✅ | ❌ | ❌ |
| 212-215 | `/attachments` | CRUD | ❌ | ✅ | ✅ | ✅ |
| 216 | `/teacher/attendance/mark` | POST | ❌ | ❌ | ✅ | ❌ |

**Legend:**
- ✅ = Full access (create/read/update/delete where applicable)
- Own = Can only access own data
- View = Can read/list but not modify
- ❌ = No access

---

## Common Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "trace_id": "uuid-for-request-tracing"
  }
}
```

### Standard Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| RESOURCE_NOT_FOUND | 404 | Resource does not exist |
| VALIDATION_ERROR | 422 | Request validation failed |
| BUSINESS_LOGIC_ERROR | 400 | Business rule violation |
| INTERNAL_SERVER_ERROR | 500 | Unexpected server error |
