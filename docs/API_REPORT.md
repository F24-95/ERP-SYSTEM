# School ERP - Complete API Report

## Legend
- **Access:** Who can call this endpoint
- **Parameters:** Data types and whether required/optional
- Parameters marked `(path)` are URL path parameters
- Parameters marked `(query)` are query string parameters
- Parameters marked `(required)` or `(optional)` are request body fields

---

## Academics

### GET /academics/class-subjects
**Summary:** List Class Subjects

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |
| classroom_id | str | query |
| academic_sessions_id | str | query |

### POST /academics/class-subjects
**Summary:** Create Class Subject

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | required |
| classroom_id | integer | required |
| subject_id | integer | required |
| display_order | integer | optional |

### GET /academics/class-subjects/{class_subject_id}
**Summary:** Get Class Subject

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| class_subject_id | integer | path |

### PUT /academics/class-subjects/{class_subject_id}
**Summary:** Update Class Subject

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| class_subject_id | integer | path |
| display_order | str | optional |
| is_active | str | optional |

### DELETE /academics/class-subjects/{class_subject_id}
**Summary:** Deactivate Class Subject

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| class_subject_id | integer | path |

### GET /academics/classrooms
**Summary:** List Classrooms

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |
| academic_sessions_id | str | query |

### POST /academics/classrooms
**Summary:** Create Classroom

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| class_code | string | required |
| class_name | string | required |
| section | string | required |
| display_name | string | required |
| description | str | optional |
| academic_sessions_id | integer | required |
| class_teacher_id | str | optional |

### GET /academics/classrooms/{classroom_id}
**Summary:** Get Classroom

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | integer | path |

### PUT /academics/classrooms/{classroom_id}
**Summary:** Update Classroom

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | integer | path |
| class_code | str | optional |
| class_name | str | optional |
| section | str | optional |
| display_name | str | optional |
| description | str | optional |
| academic_sessions_id | str | optional |
| class_teacher_id | str | optional |
| is_active | str | optional |

### DELETE /academics/classrooms/{classroom_id}
**Summary:** Deactivate Classroom

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | integer | path |

### GET /academics/sessions
**Summary:** List Sessions

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |

### POST /academics/sessions
**Summary:** Create Session

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| session_code | string | required |
| session_name | string | required |
| start_year | integer | required |
| end_year | integer | required |
| start_date | string | required |
| end_date | string | required |
| is_current | boolean | optional |
| description | str | optional |

### GET /academics/sessions/{session_id}
**Summary:** Get Session

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| session_id | integer | path |

### PUT /academics/sessions/{session_id}
**Summary:** Update Session

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| session_id | integer | path |
| session_code | str | optional |
| session_name | str | optional |
| start_year | str | optional |
| end_year | str | optional |
| start_date | str | optional |
| end_date | str | optional |
| is_current | str | optional |
| description | str | optional |
| is_active | str | optional |

### DELETE /academics/sessions/{session_id}
**Summary:** Deactivate Session

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| session_id | integer | path |

### GET /academics/subjects
**Summary:** List Subjects

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |

### POST /academics/subjects
**Summary:** Create Subject

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| subject_code | string | required |
| subject_name | string | required |
| description | str | optional |
| display_order | integer | optional |
| subject_type | string | optional |

### GET /academics/subjects/{subject_id}
**Summary:** Get Subject

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| subject_id | integer | path |

### PUT /academics/subjects/{subject_id}
**Summary:** Update Subject

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| subject_id | integer | path |
| subject_code | str | optional |
| subject_name | str | optional |
| description | str | optional |
| display_order | str | optional |
| subject_type | str | optional |
| is_active | str | optional |

### DELETE /academics/subjects/{subject_id}
**Summary:** Deactivate Subject

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| subject_id | integer | path |


## Admin

### GET /admin/admins
**Summary:** List Admin Profiles

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |

### GET /admin/admins/{profile_id}
**Summary:** Get Admin Profile

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |

### PATCH /admin/admins/{profile_id}
**Summary:** Update Admin Profile

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |
| admin_name | str | optional |
| department | str | optional |
| is_super_admin | str | optional |
| is_active | str | optional |

### DELETE /admin/admins/{profile_id}
**Summary:** Deactivate Admin Profile

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |

### GET /admin/students
**Summary:** List Student Profiles

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |

### GET /admin/students/{profile_id}
**Summary:** Get Student Profile

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |

### PATCH /admin/students/{profile_id}
**Summary:** Update Student Profile

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |
| student_name | str | optional |
| gender | str | optional |
| date_of_birth | str | optional |
| blood_group | str | optional |
| address | str | optional |
| city | str | optional |
| state | str | optional |
| parent_name | str | optional |
| parent_phone | str | optional |
| ka_student_id | str | optional |
| is_active | str | optional |

### DELETE /admin/students/{profile_id}
**Summary:** Deactivate Student Profile

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |

### GET /admin/teachers
**Summary:** List Teacher Profiles

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |

### GET /admin/teachers/{profile_id}
**Summary:** Get Teacher Profile

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |

### PATCH /admin/teachers/{profile_id}
**Summary:** Update Teacher Profile

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |
| teacher_name | str | optional |
| gender | str | optional |
| designation | str | optional |
| department | str | optional |
| experience_years | str | optional |
| is_active | str | optional |

### DELETE /admin/teachers/{profile_id}
**Summary:** Deactivate Teacher Profile

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| profile_id | integer | path |

### POST /admin/user
**Summary:** Create User

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| email | string | required |
| phone | string | required |
| role | str | required |
| password | string (hashed) | required |

### GET /admin/users
**Summary:** List Users

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| skip | integer | query |
| limit | integer | query |
| role | str | query |
| is_active | str | query |

### GET /admin/users/{public_id}
**Summary:** Get User

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| public_id | string | path |

### PATCH /admin/users/{public_id}
**Summary:** Update User

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| public_id | string | path |
| phone | string | optional |
| is_active | str | optional |

### DELETE /admin/users/{public_id}
**Summary:** Deactivate User

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| public_id | string | path |


## Assignments

### GET /assignments/
**Summary:** Get Assignments

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | str | query |
| status | str | query |

### POST /assignments/
**Summary:** Create Assignment

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| title | string | required |
| description | str | optional |
| instructions | str | optional |
| due_date | string | required |
| due_time | str | optional |
| total_marks | number | optional |
| passing_marks | number | optional |
| file_name | str | optional |
| file_path | str | optional |
| file_type | str | optional |
| file_size | str | optional |
| status | str | optional |
| publish_at | str | optional |
| close_at | str | optional |
| academic_sessions_id | integer | required |
| classroom_id | integer | required |
| class_subject_id | integer | required |
| teacher_subject_id | integer | required |

### GET /assignments/results/{result_id}
**Summary:** Get Assignment Result

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| result_id | integer | path |

### DELETE /assignments/results/{result_id}
**Summary:** Delete Assignment Result

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| result_id | integer | path |

### GET /assignments/{assignment_id}
**Summary:** Get Assignment

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |

### PUT /assignments/{assignment_id}
**Summary:** Update Assignment

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |
| title | str | optional |
| description | str | optional |
| instructions | str | optional |
| due_date | str | optional |
| due_time | str | optional |
| total_marks | str | optional |
| passing_marks | str | optional |
| file_name | str | optional |
| file_path | str | optional |
| file_type | str | optional |
| file_size | str | optional |
| status | str | optional |
| publish_at | str | optional |
| close_at | str | optional |
| is_active | str | optional |

### DELETE /assignments/{assignment_id}
**Summary:** Delete Assignment

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |

### GET /assignments/{assignment_id}/results
**Summary:** Get Assignment Results

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |

### POST /assignments/{assignment_id}/results
**Summary:** Grade Assignment

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |


## Attachments

### GET /attachments/entity/{entity_type}/{entity_id}
**Summary:** List Entity Attachments

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| entity_type | string | path |
| entity_id | integer | path |

### POST /attachments/upload
**Summary:** Upload Attachment

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| entity_type | string | required |
| entity_id | integer | required |
| file_name | string | required |
| mime_type | string | required |
| file_data | string | required |

### GET /attachments/{attachment_id}
**Summary:** Download Attachment

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| attachment_id | integer | path |

### DELETE /attachments/{attachment_id}
**Summary:** Delete Attachment

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| attachment_id | integer | path |


## Authentication

### POST /auth/change-password
**Summary:** Change Password

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| old_password | string | required |
| new_password | string | required |

### POST /auth/forgot-password
**Summary:** Forgot Password

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| email | string | required |

### POST /auth/login
**Summary:** Login

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| email | string | required |
| password | string (hashed) | required |

### POST /auth/logout
**Summary:** Logout

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| refresh_token | str | optional |

### POST /auth/refresh
**Summary:** Refresh Token

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| refresh_token | string | required |

### POST /auth/resend-otp
**Summary:** Resend Otp

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| purpose | string | query |

### POST /auth/reset-password
**Summary:** Reset Password

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| token | string | required |
| new_password | string | required |

### POST /auth/send-login-otp
**Summary:** Send Login Otp

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| email | string | required |

### POST /auth/send-verification-otp
**Summary:** Send Verification Otp

**Access:** `Authenticated`

No parameters

### GET /auth/validate-token
**Summary:** Validate Token

**Access:** `Authenticated`

No parameters

### POST /auth/verify-email
**Summary:** Verify Email

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| otp | string | required |

### POST /auth/verify-login-otp
**Summary:** Verify Login Otp

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| email | string | required |
| otp | string | required |


## Timetable

### POST /availability
**Summary:** Create Availability

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| is_available | boolean | optional |
| reason | str | optional |
| remarks | str | optional |
| availability_id | string | required |
| academic_sessions_id | integer | required |
| teacher_subject_id | integer | required |
| week_day_id | integer | required |
| time_slot_id | integer | required |

### GET /availability/teacher/{teacher_subject_id}
**Summary:** Get Teacher Availability

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| teacher_subject_id | integer | path |
| session_id | integer | query |

### PUT /availability/{availability_id}
**Summary:** Update Availability

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| availability_id | integer | path |
| is_available | str | optional |
| reason | str | optional |
| remarks | str | optional |
| academic_sessions_id | str | optional |
| teacher_subject_id | str | optional |
| week_day_id | str | optional |
| time_slot_id | str | optional |

### DELETE /availability/{availability_id}
**Summary:** Delete Availability

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| availability_id | integer | path |


## Chat

### GET /chat/rooms
**Summary:** Get Chat Rooms

**Access:** `Authenticated`

No parameters

### POST /chat/rooms
**Summary:** Create Chat Room

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| last_message | str | optional |
| last_message_at | str | optional |
| student_unread | integer | optional |
| teacher_unread | integer | optional |
| chat_room_id | string | required |
| academic_sessions_id | integer | required |
| student_class_id | integer | required |
| teacher_subject_id | integer | required |

### GET /chat/rooms/{room_id}
**Summary:** Get Chat Room

**Access:** `Authenticated (participant)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_id | integer | path |

### PUT /chat/rooms/{room_id}
**Summary:** Update Chat Room

**Access:** `Authenticated (participant)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_id | integer | path |
| last_message | str | optional |
| last_message_at | str | optional |
| student_unread | str | optional |
| teacher_unread | str | optional |
| is_active | str | optional |

### DELETE /chat/rooms/{room_id}
**Summary:** Archive Chat Room

**Access:** `Authenticated (participant)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_id | integer | path |

### GET /chat/rooms/{room_id}/messages
**Summary:** Get Messages

**Access:** `Authenticated (participant)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_id | integer | path |
| limit | integer | query |
| before | str | query |

### POST /chat/rooms/{room_id}/messages
**Summary:** Send Message

**Access:** `Authenticated (participant)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_id | integer | path |
| message | string | required |
| is_edited | boolean | optional |
| edited_at | str | optional |

### PUT /chat/rooms/{room_id}/messages/{message_id}
**Summary:** Edit Message

**Access:** `Authenticated (owner)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_id | integer | path |
| message_id | integer | path |
| message | string | required |

### DELETE /chat/rooms/{room_id}/messages/{message_id}
**Summary:** Delete Message

**Access:** `Authenticated (owner)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_id | integer | path |
| message_id | integer | path |

### GET /chat/unread
**Summary:** Get Unread Counts

**Access:** `Authenticated`

No parameters


## Daily Class

### GET /daily-class/
**Summary:** Get Daily Classes

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | str | query |
| class_date | str | query |
| lecture_status | str | query |

### POST /daily-class/
**Summary:** Create Daily Class

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| daily_class_id | string | required |
| academic_sessions_id | integer | required |
| classroom_id | integer | required |
| class_subject_id | integer | required |
| teacher_subject_id | integer | required |
| timetable_id | str | optional |
| class_date | string | required |
| topic | str | optional |
| description | str | optional |
| homework | str | optional |
| lecture_status | string | optional |
| started_at | str | optional |
| ended_at | str | optional |
| total_minutes | str | optional |
| remarks | str | optional |

### POST /daily-class/attendance/recalculate/{student_class_id}
**Summary:** Recalculate Attendance Summary

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_class_id | integer | path |

### GET /daily-class/attendance/summary/{student_class_id}
**Summary:** Get Attendance Summary

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_class_id | integer | path |

### GET /daily-class/classroom/{classroom_id}/summary
**Summary:** Get Class Summary

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | integer | path |
| start_date | string | query |
| end_date | string | query |

### GET /daily-class/students/{record_id}
**Summary:** Get Attendance Record

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| record_id | integer | path |

### PUT /daily-class/students/{record_id}
**Summary:** Update Attendance Record

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| record_id | integer | path |
| attendance_status | str | optional |
| is_late | str | optional |
| late_minutes | str | optional |
| remarks | str | optional |

### DELETE /daily-class/students/{record_id}
**Summary:** Delete Attendance Record

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| record_id | integer | path |

### GET /daily-class/{daily_class_id}
**Summary:** Get Daily Class

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| daily_class_id | integer | path |

### PUT /daily-class/{daily_class_id}
**Summary:** Update Daily Class

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| daily_class_id | integer | path |
| class_date | str | optional |
| topic | str | optional |
| description | str | optional |
| homework | str | optional |
| lecture_status | str | optional |
| started_at | str | optional |
| ended_at | str | optional |
| total_minutes | str | optional |
| remarks | str | optional |
| is_active | str | optional |

### DELETE /daily-class/{daily_class_id}
**Summary:** Delete Daily Class

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| daily_class_id | integer | path |

### GET /daily-class/{daily_class_id}/students
**Summary:** Get Attendance

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| daily_class_id | integer | path |

### POST /daily-class/{daily_class_id}/students
**Summary:** Mark Attendance

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| daily_class_id | integer | path |


## Dashboard

### GET /dashboard/admin
**Summary:** Get Admin Dashboard

**Access:** `Admin`

No parameters

### GET /dashboard/student
**Summary:** Get Student Dashboard

**Access:** `Student`

No parameters

### GET /dashboard/teacher
**Summary:** Get Teacher Dashboard

**Access:** `Teacher`

No parameters


## Exams

### GET /exams/
**Summary:** Get Exams

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | str | query |
| status | str | query |

### POST /exams/
**Summary:** Create Exam

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| exam_name | string | required |
| exam_type | string | required |
| description | str | optional |
| exam_date | string | required |
| start_time | str | optional |
| end_time | str | optional |
| duration_minutes | str | optional |
| room_number | str | optional |
| total_marks | number | required |
| passing_marks | number | required |
| status | str | optional |
| publish_at | str | optional |
| completed_at | str | optional |
| exam_id | string | required |
| academic_sessions_id | integer | required |
| classroom_id | integer | required |
| class_subject_id | integer | required |
| teacher_subject_id | integer | required |

### GET /exams/results/{result_id}
**Summary:** Get Exam Result

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| result_id | integer | path |

### DELETE /exams/results/{result_id}
**Summary:** Delete Exam Result

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| result_id | integer | path |

### GET /exams/{exam_id}
**Summary:** Get Exam

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| exam_id | integer | path |

### PUT /exams/{exam_id}
**Summary:** Update Exam

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| exam_id | integer | path |
| exam_name | str | optional |
| exam_type | str | optional |
| description | str | optional |
| exam_date | str | optional |
| start_time | str | optional |
| end_time | str | optional |
| duration_minutes | str | optional |
| room_number | str | optional |
| total_marks | str | optional |
| passing_marks | str | optional |
| status | str | optional |
| publish_at | str | optional |
| completed_at | str | optional |
| is_active | str | optional |

### DELETE /exams/{exam_id}
**Summary:** Delete Exam

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| exam_id | integer | path |

### GET /exams/{exam_id}/results
**Summary:** Get Exam Results

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| exam_id | integer | path |

### POST /exams/{exam_id}/results
**Summary:** Upload Exam Results

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| exam_id | integer | path |


## Fees

### GET /fees
**Summary:** List Fees

**Access:** `Admin`

No parameters

### POST /fees
**Summary:** Create Fee

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | required |
| student_class_id | integer | required |
| fee_month | integer | required |
| fee_year | integer | required |
| total_amount | str | required |
| due_date | string | required |
| remarks | str | optional |
| discount_amount | str | optional |
| fine_amount | str | optional |

### GET /fees/my
**Summary:** Get My Fees

**Access:** `Student`

No parameters

### GET /fees/pending
**Summary:** Pending Fees

**Access:** `Admin`

No parameters

### GET /fees/student/{student_class_id}
**Summary:** Get Fees For Student

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_class_id | integer | path |

### GET /fees/{fee_id}
**Summary:** Get Fee

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| fee_id | string | path |

### PUT /fees/{fee_id}
**Summary:** Update Fee

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| fee_id | string | path |
| due_date | str | optional |
| discount_amount | str | optional |
| fine_amount | str | optional |
| remarks | str | optional |
| is_active | str | optional |

### DELETE /fees/{fee_id}
**Summary:** Deactivate Fee

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| fee_id | string | path |

### POST /fees/{fee_id}/pay
**Summary:** Pay Fee

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| fee_id | string | path |
| amount | str | required |
| remarks | str | optional |


## System

### GET /health
**Summary:** Health Check

**Access:** `Anyone`

No parameters


## Khan Academy

### POST /khan-academy/activity/student
**Summary:** Ingest Student Activity

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | required |
| from_date | string | required |
| to_date | string | required |
| worked_on | integer | optional |
| attempted | integer | optional |
| familiar | integer | optional |
| proficient | integer | optional |
| leveled_to_proficient | integer | optional |
| leveled_up | integer | optional |
| mastered | integer | optional |
| minutes | integer | optional |
| minutes_target_status | str | optional |

### GET /khan-academy/activity/student/{student_profile_id}
**Summary:** Get Student Activity

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | path |

### POST /khan-academy/activity/subject
**Summary:** Ingest Subject Activity

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | required |
| subject_id | str | optional |
| topic_id | str | optional |
| study_material_id | str | optional |
| activity_date | string | required |

### GET /khan-academy/progress/student/{student_profile_id}
**Summary:** Get Student Progress

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | path |

### POST /khan-academy/progress/subject
**Summary:** Ingest Subject Progress

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | required |
| subject_id | str | optional |
| point_available | integer | optional |
| point_earned | integer | optional |
| percentage_earned | number | optional |
| snapshot_date | string | required |

### POST /khan-academy/progress/topic
**Summary:** Ingest Topic Progress

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | required |
| subject_id | str | optional |
| topic_id | str | optional |
| study_material_id | str | optional |
| point_available | integer | optional |
| point_earned | integer | optional |
| percentage_earned | number | optional |
| snapshot_date | string | required |

### GET /khan-academy/topics
**Summary:** List Topics

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| subject_id | str | query |
| classroom_id | str | query |

### POST /khan-academy/topics
**Summary:** Create Topic

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| ka_topic_id | string | required |
| topic_name | string | required |
| description | str | optional |
| display_order | integer | optional |
| subject_id | integer | required |
| classroom_id | str | optional |

### GET /khan-academy/topics/{topic_id}
**Summary:** Get Topic

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| topic_id | integer | path |

### PUT /khan-academy/topics/{topic_id}
**Summary:** Update Topic

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| topic_id | integer | path |
| topic_name | str | optional |
| description | str | optional |
| display_order | str | optional |
| classroom_id | str | optional |
| is_active | str | optional |

### DELETE /khan-academy/topics/{topic_id}
**Summary:** Delete Topic

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| topic_id | integer | path |


## Notice Board

### GET /notices/
**Summary:** Get Notices

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_type | str | query |
| audience | str | query |
| is_pinned | str | query |

### POST /notices/
**Summary:** Create Notice

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| title | string | required |
| description | string | required |
| notice_type | str | optional |
| audience | str | optional |
| publish_date | string | required |
| expiry_date | str | optional |
| is_pinned | boolean | optional |
| academic_sessions_id | integer | required |
| classroom_id | str | optional |
| file | str | optional |

### GET /notices/{notice_id}
**Summary:** Get Notice

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_id | integer | path |

### PUT /notices/{notice_id}
**Summary:** Update Notice

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_id | integer | path |
| title | str | optional |
| description | str | optional |
| notice_type | str | optional |
| audience | str | optional |
| publish_date | str | optional |
| expiry_date | str | optional |
| is_pinned | str | optional |
| classroom_id | str | optional |
| file | str | optional |

### DELETE /notices/{notice_id}
**Summary:** Delete Notice

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_id | integer | path |

### GET /notices/{notice_id}/download
**Summary:** Download Notice File

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_id | integer | path |

### POST /notices/{notice_id}/pin
**Summary:** Pin Notice

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_id | integer | path |

### POST /notices/{notice_id}/unpin
**Summary:** Unpin Notice

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_id | integer | path |

### GET /notices/{notice_id}/view
**Summary:** View Notice File

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| notice_id | integer | path |


## Operations

### POST /operations/assign-teacher
**Summary:** Assign Teacher

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | required |
| class_subject_id | integer | required |
| classroom_id | integer | required |
| subject_id | integer | required |
| teacher_id | integer | required |
| is_class_teacher | boolean | optional |
| remarks | str | optional |

### POST /operations/enroll-student
**Summary:** Enroll Student

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | required |
| student_id | integer | required |
| classroom_id | integer | required |
| roll_number | integer | required |
| admission_date | string | required |
| status | string | optional |
| roll_number_locked | boolean | optional |
| remarks | str | optional |

### POST /operations/promote-student
**Summary:** Promote Student

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_id | integer | required |
| from_session_id | integer | required |
| to_session_id | integer | required |
| to_classroom_id | integer | required |
| new_roll | integer | required |

### GET /operations/promote-student/{student_id}
**Summary:** Get Promotion History

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_id | integer | path |

### GET /operations/student-enrollments
**Summary:** List Student Enrollments

**Access:** `Anyone`

No parameters

### GET /operations/student-enrollments/{enrollment_id}
**Summary:** Get Student Enrollment

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| enrollment_id | integer | path |

### PUT /operations/student-enrollments/{enrollment_id}
**Summary:** Update Student Enrollment

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| enrollment_id | integer | path |
| roll_number | str | optional |
| status | str | optional |
| roll_number_locked | str | optional |
| remarks | str | optional |
| is_active | str | optional |

### DELETE /operations/student-enrollments/{enrollment_id}
**Summary:** Unenroll Student

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| enrollment_id | integer | path |

### GET /operations/teacher-assignments
**Summary:** List Teacher Assignments

**Access:** `Anyone`

No parameters

### GET /operations/teacher-assignments/{assignment_id}
**Summary:** Get Teacher Assignment

**Access:** `Anyone`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |

### PUT /operations/teacher-assignments/{assignment_id}
**Summary:** Update Teacher Assignment

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |
| is_class_teacher | str | optional |
| remarks | str | optional |
| is_active | str | optional |

### DELETE /operations/teacher-assignments/{assignment_id}
**Summary:** Unassign Teacher

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| assignment_id | integer | path |


## Student Reports

### POST /reports/generate
**Summary:** Generate Report

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | required |
| data_start_date | string | required |
| data_end_date | string | required |

### GET /reports/student/{student_profile_id}
**Summary:** List Reports

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | path |

### DELETE /reports/subject-progress/{item_id}
**Summary:** Delete Subject Progress Item

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| item_id | integer | path |

### DELETE /reports/topic-progress/{item_id}
**Summary:** Delete Topic Progress Item

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| item_id | integer | path |

### DELETE /reports/{report_id}
**Summary:** Delete Report

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |

### GET /reports/{report_id}/activity
**Summary:** Get Activity Report

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |

### PUT /reports/{report_id}/activity
**Summary:** Set Activity Report

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |
| mean_duration_minutes | str | optional |
| total_duration_minutes | str | optional |
| total_worked_hours | str | optional |
| total_attempted | str | optional |
| total_familiar | str | optional |
| total_proficient | str | optional |
| total_leveled_up | str | optional |
| total_mastered | str | optional |

### GET /reports/{report_id}/download
**Summary:** Download Report

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |

### GET /reports/{report_id}/subject-progress
**Summary:** Get Subject Progress Items

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |

### GET /reports/{report_id}/topic-progress
**Summary:** Get Topic Progress Items

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |

### GET /reports/{report_id}/zoom-duration
**Summary:** Get Zoom Duration Report

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |

### PUT /reports/{report_id}/zoom-duration
**Summary:** Set Zoom Duration Report

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |
| mean_duration_minutes | str | optional |
| min_duration_minutes | str | optional |
| max_duration_minutes | str | optional |

### GET /reports/{report_id}/zoom-interaction
**Summary:** Get Zoom Interaction Report

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |

### PUT /reports/{report_id}/zoom-interaction
**Summary:** Set Zoom Interaction Report

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| report_id | integer | path |
| mean_interaction_count | str | optional |
| min_interaction_count | str | optional |
| max_interaction_count | str | optional |


## Student

### GET /student/assignments
**Summary:** Get Student Assignments

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | query |
| subject_id | str | query |

### GET /student/attendance/daily
**Summary:** Get Daily Attendance

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | query |
| start_date | str | query |
| end_date | str | query |

### GET /student/attendance/summary
**Summary:** Get Attendance Summary

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | query |

### GET /student/classes
**Summary:** Get Student Classes

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | str | query |

### GET /student/exams
**Summary:** Get Student Exams

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | query |
| subject_id | str | query |

### GET /student/fees
**Summary:** Get Student Fees

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | query |
| status | str | query |

### GET /student/fees/summary
**Summary:** Get Fee Summary

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | query |


## Student ID Card

### GET /student/id-card/all
**Summary:** List All Cards

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| page | integer | query |
| page_size | integer | query |

### GET /student/id-card/{student_profile_id}
**Summary:** View Id Card

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | path |

### POST /student/id-card/{student_profile_id}
**Summary:** Generate Id Card

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | path |
| regenerate | boolean | query |

### GET /student/id-card/{student_profile_id}/download
**Summary:** Download Id Card

**Access:** `Authenticated (filtered)`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_profile_id | integer | path |


## Student

### GET /student/profile
**Summary:** Get Student Profile

**Access:** `Student`

No parameters

### PUT /student/profile
**Summary:** Update Student Profile

**Access:** `Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| student_name | str | optional |
| gender | str | optional |
| date_of_birth | str | optional |
| blood_group | str | optional |
| address | str | optional |
| city | str | optional |
| state | str | optional |
| parent_name | str | optional |
| parent_phone | str | optional |
| ka_student_id | str | optional |
| is_active | str | optional |


## Timetable

### GET /student/timetable
**Summary:** Get Student Timetable

**Access:** `Student`

No parameters


## Search

### GET /students/search
**Summary:** Search Students

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| q | string | query |
| limit | integer | query |


## Study Materials

### GET /study-materials
**Summary:** List Study Materials

**Access:** `Authenticated`

No parameters

### POST /study-materials
**Summary:** Create Study Material

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| title | string | required |
| description | str | optional |
| material_type | str | optional |
| academic_sessions_id | integer | required |
| classroom_id | integer | required |
| class_subject_id | integer | required |
| teacher_subject_id | integer | required |
| file | string | required |

### GET /study-materials/class-subject/{class_subject_id}
**Summary:** Get Materials For Class Subject

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| class_subject_id | integer | path |

### GET /study-materials/{id}
**Summary:** Get Study Material

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| id | integer | path |

### PUT /study-materials/{id}
**Summary:** Update Study Material

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| id | integer | path |
| title | str | optional |
| description | str | optional |
| material_type | str | optional |
| academic_sessions_id | str | optional |
| classroom_id | str | optional |
| class_subject_id | str | optional |
| teacher_subject_id | str | optional |
| file | str | optional |

### DELETE /study-materials/{id}
**Summary:** Delete Study Material

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| id | integer | path |

### GET /study-materials/{id}/download
**Summary:** Download Study Material

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| id | integer | path |

### GET /study-materials/{id}/view
**Summary:** View Study Material

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| id | integer | path |


## Teacher

### GET /teacher/assignments
**Summary:** Get Teacher Assignments

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | str | query |
| classroom_id | str | query |
| status | str | query |

### POST /teacher/attendance/mark
**Summary:** Mark Attendance

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| daily_class_id | integer | query |

### GET /teacher/classes
**Summary:** Get Teacher Classes

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | str | query |

### GET /teacher/dashboard
**Summary:** Get Teacher Dashboard

**Access:** `Teacher`

No parameters

### GET /teacher/my-students
**Summary:** Get My Students

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | integer | query |
| classroom_id | str | query |

### GET /teacher/profile
**Summary:** Get Teacher Profile

**Access:** `Teacher`

No parameters

### PUT /teacher/profile
**Summary:** Update Teacher Profile

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| teacher_name | str | optional |
| gender | str | optional |
| designation | str | optional |
| department | str | optional |
| experience_years | str | optional |
| is_active | str | optional |

### GET /teacher/students
**Summary:** Get Class Students

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | integer | query |
| academic_sessions_id | integer | query |

### GET /teacher/subjects
**Summary:** Get Teacher Subjects

**Access:** `Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| academic_sessions_id | str | query |


## Timetable

### GET /teacher/timetable
**Summary:** Get Teacher Timetable

**Access:** `Teacher`

No parameters


## Search

### GET /teachers/search
**Summary:** Search Teachers

**Access:** `Admin, Teacher, Student`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| q | string | query |
| limit | integer | query |


## Timetable

### GET /timeslots
**Summary:** Get Timeslots

**Access:** `Authenticated`

No parameters

### POST /timeslots
**Summary:** Create Timeslot

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| slot_code | string | required |
| slot_name | string | required |
| start_time | string | required |
| end_time | string | required |
| duration_minutes | integer | required |
| display_order | integer | required |
| is_break | boolean | optional |

### PUT /timeslots/{timeslot_id}
**Summary:** Update Timeslot

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| timeslot_id | integer | path |
| slot_code | str | optional |
| slot_name | str | optional |
| start_time | str | optional |
| end_time | str | optional |
| duration_minutes | str | optional |
| display_order | str | optional |
| is_break | str | optional |
| is_active | str | optional |

### DELETE /timeslots/{timeslot_id}
**Summary:** Deactivate Timeslot

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| timeslot_id | integer | path |

### POST /timetable
**Summary:** Create Timetable Entry

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| room_number | str | optional |
| remarks | str | optional |
| timetable_id | string | required |
| academic_sessions_id | integer | required |
| classroom_id | integer | required |
| class_subject_id | integer | required |
| teacher_subject_id | integer | required |
| week_day_id | integer | required |
| time_slot_id | integer | required |

### GET /timetable/class/{classroom_id}
**Summary:** Get Class Timetable

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | integer | path |
| session_id | integer | query |

### PUT /timetable/{id}
**Summary:** Update Timetable Entry

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| id | integer | path |
| room_number | str | optional |
| remarks | str | optional |
| academic_sessions_id | str | optional |
| classroom_id | str | optional |
| class_subject_id | str | optional |
| teacher_subject_id | str | optional |
| week_day_id | str | optional |
| time_slot_id | str | optional |
| is_active | str | optional |

### DELETE /timetable/{id}
**Summary:** Delete Timetable Entry

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| id | integer | path |

### GET /timetables
**Summary:** Admin Get Timetables

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| class | str | query |
| teacher | str | query |
| subject | str | query |
| day | str | query |


## Users

### GET /users/me
**Summary:** Get My Profile

**Access:** `Authenticated`

No parameters

### PATCH /users/me
**Summary:** Update My Profile

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| phone | string | optional |
| is_active | str | optional |

### GET /users/{public_id}
**Summary:** Get User

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| public_id | string | path |


## Timetable

### GET /weekdays
**Summary:** Get Weekdays

**Access:** `Authenticated`

No parameters

### POST /weekdays
**Summary:** Create Weekday

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| day_code | string | required |
| day_name | string | required |
| display_order | integer | optional |

### PUT /weekdays/{weekday_id}
**Summary:** Update Weekday

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| weekday_id | integer | path |
| day_code | str | optional |
| day_name | str | optional |
| display_order | str | optional |
| is_active | str | optional |

### DELETE /weekdays/{weekday_id}
**Summary:** Deactivate Weekday

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| weekday_id | integer | path |


## Zoom

### GET /zoom/files
**Summary:** List Zoom Files

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| classroom_id | str | query |
| date | str | query |

### POST /zoom/files
**Summary:** Create Zoom File

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| file_initial | string | required |
| transcript_file | str | optional |
| audio_file | str | optional |
| audio_duration | str | optional |
| video_file | str | optional |
| video_duration | str | optional |
| raw_date | string | required |
| raw_time | string | required |
| date | string | required |
| time | string | required |
| classroom_id | str | optional |
| recording_file_id | str | optional |

### GET /zoom/files/{zoom_file_id}
**Summary:** Get Zoom File

**Access:** `Authenticated`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| zoom_file_id | integer | path |

### PUT /zoom/files/{zoom_file_id}
**Summary:** Update Zoom File

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| zoom_file_id | integer | path |
| transcript_file | str | optional |
| audio_file | str | optional |
| audio_duration | str | optional |
| video_file | str | optional |
| video_duration | str | optional |
| classroom_id | str | optional |
| is_active | str | optional |

### DELETE /zoom/files/{zoom_file_id}
**Summary:** Delete Zoom File

**Access:** `Admin`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| zoom_file_id | integer | path |

### GET /zoom/meetings
**Summary:** List Zoom Meetings

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| host_id | str | query |

### POST /zoom/meetings
**Summary:** Ingest Zoom Meeting

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| uuid | string | required |
| meeting_id | str | optional |
| account_id | str | optional |
| host_id | str | optional |
| topic | str | optional |
| type | str | optional |
| start_time | str | optional |
| timezone | str | optional |
| duration | str | optional |
| total_size | str | optional |
| recording_count | str | optional |
| share_url | str | optional |
| recording_play_passcode | str | optional |

### GET /zoom/meetings/{uuid}
**Summary:** Get Zoom Meeting

**Access:** `Admin, Teacher`

**Parameters:**

| Name | Type | Required |
|------|------|----------|
| uuid | string | path |

