from datetime import date, datetime, time

from pydantic import BaseModel, Field


# Generic Base Response to reduce LoC
class BaseResponse(BaseModel):
    id: int
    is_active: bool | None = None

    model_config = {"from_attributes": True}


# ===========================
# Teacher Subject
# ===========================
class TeacherSubjectBase(BaseModel):
    academic_sessions_id: int
    class_subject_id: int
    classroom_id: int
    subject_id: int
    teacher_id: int
    is_class_teacher: bool = False
    remarks: str | None = None


class TeacherSubjectCreate(TeacherSubjectBase):
    pass


class TeacherSubjectUpdate(BaseModel):
    is_class_teacher: bool | None = None
    remarks: str | None = None
    is_active: bool | None = None


class TeacherSubjectResponse(TeacherSubjectBase, BaseResponse):
    pass


# ===========================
# Student Class
# ===========================
class StudentClassBase(BaseModel):
    academic_sessions_id: int
    student_id: int
    classroom_id: int
    roll_number: int
    admission_date: date
    status: str = "ACTIVE"
    roll_number_locked: bool = False
    remarks: str | None = None


class StudentClassCreate(StudentClassBase):
    pass


class StudentClassUpdate(BaseModel):
    roll_number: int | None = None
    status: str | None = None
    roll_number_locked: bool | None = None
    remarks: str | None = None
    is_active: bool | None = None


class StudentClassResponse(StudentClassBase, BaseResponse):
    pass


# ===========================
# Student Promotion
# ===========================
class PromoteStudentRequest(BaseModel):
    student_id: int
    from_session_id: int
    to_session_id: int
    to_classroom_id: int
    new_roll: int


class StudentPromotionHistoryResponse(BaseModel):
    id: int
    student_id: int
    from_session_id: int
    to_session_id: int
    from_classroom_id: int
    to_classroom_id: int
    previous_roll_number: int
    new_roll_number: int
    promotion_date: date
    promotion_type: str
    remarks: str | None = None
    promoted_by_user_id: int | None = None

    model_config = {"from_attributes": True}


# ===========================
# Daily Class
# ===========================
class DailyClassBase(BaseModel):
    daily_class_id: str
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    timetable_id: int | None = None
    class_date: date
    topic: str | None = None
    description: str | None = None
    homework: str | None = None
    lecture_status: str = "Scheduled"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_minutes: int | None = None
    remarks: str | None = None


class DailyClassCreate(DailyClassBase):
    pass


class DailyClassResponse(DailyClassBase, BaseResponse):
    pass


class DailyClassUpdate(BaseModel):
    class_date: date | None = None
    topic: str | None = None
    description: str | None = None
    homework: str | None = None
    lecture_status: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_minutes: int | None = None
    remarks: str | None = None
    is_active: bool | None = None


# ===========================
# Daily Class Student (Attendance)
# ===========================
class DailyClassStudentBase(BaseModel):
    attendance_status: str = "Present"
    is_late: bool = False
    late_minutes: int = 0
    remarks: str | None = None


class DailyClassStudentCreate(DailyClassStudentBase):
    daily_class_id: int
    student_class_id: int
    marked_by: int | None = None


class DailyClassStudentUpdate(BaseModel):
    attendance_status: str | None = None
    is_late: bool | None = None
    late_minutes: int | None = None
    remarks: str | None = None


class DailyClassStudentResponse(DailyClassStudentBase):
    id: int
    daily_class_id: int
    student_class_id: int
    marked_by: int | None = None
    marked_at: datetime | None = None

    model_config = {"from_attributes": True}


# ===========================
# Student Attendance (aggregate)
# ===========================
class StudentAttendanceResponse(BaseModel):
    id: int | None = None
    student_class_id: int
    total_classes: int = 0
    present_classes: int = 0
    absent_classes: int = 0
    attendance_percentage: float = 0.0

    model_config = {"from_attributes": True}


# ===========================
# Week Day
# ===========================
class WeekDayBase(BaseModel):
    day_code: str
    day_name: str
    display_order: int = 1


class WeekDayCreate(WeekDayBase):
    pass


class WeekDayUpdate(BaseModel):
    day_code: str | None = None
    day_name: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class WeekDayResponse(WeekDayBase, BaseResponse):
    pass


# ===========================
# Time Slot
# ===========================
class TimeSlotBase(BaseModel):
    slot_code: str
    slot_name: str
    start_time: time
    end_time: time
    duration_minutes: int
    display_order: int
    is_break: bool = False


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeSlotUpdate(BaseModel):
    slot_code: str | None = None
    slot_name: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    display_order: int | None = None
    is_break: bool | None = None
    is_active: bool | None = None


class TimeSlotResponse(TimeSlotBase, BaseResponse):
    pass


# ===========================
# Class Timetable
# ===========================
class ClassTimeTableBase(BaseModel):
    room_number: str | None = None
    remarks: str | None = None


class ClassTimeTableCreate(ClassTimeTableBase):
    # NOTE: timetable_id is client-supplied here, matching legacy
    # `app/schemas/timetable.py::ClassTimeTableCreate` and the fact that
    # `generate_timetable_id()` in the legacy code generators is never
    # actually called anywhere -- the sequence-based generator exists but
    # production behavior has always been client-supplied IDs. Same
    # precedent as ExamCreate.exam_id. Preserved as-is.
    timetable_id: str
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int


class ClassTimeTableUpdate(BaseModel):
    room_number: str | None = None
    remarks: str | None = None
    academic_sessions_id: int | None = None
    classroom_id: int | None = None
    class_subject_id: int | None = None
    teacher_subject_id: int | None = None
    week_day_id: int | None = None
    time_slot_id: int | None = None
    is_active: bool | None = None


class ClassTimeTableResponse(ClassTimeTableBase, BaseResponse):
    timetable_id: str
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int


# ===========================
# Teacher Availability
# ===========================
class TeacherAvailabilityBase(BaseModel):
    is_available: bool = True
    reason: str | None = None
    remarks: str | None = None


class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    # NOTE: availability_id is client-supplied -- same rationale as
    # ClassTimeTableCreate.timetable_id above (generate_availability_id()
    # exists but is never called in legacy production code).
    availability_id: str
    academic_sessions_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int


class TeacherAvailabilityUpdate(BaseModel):
    is_available: bool | None = None
    reason: str | None = None
    remarks: str | None = None
    academic_sessions_id: int | None = None
    teacher_subject_id: int | None = None
    week_day_id: int | None = None
    time_slot_id: int | None = None


class TeacherAvailabilityResponse(TeacherAvailabilityBase, BaseResponse):
    availability_id: str
    academic_sessions_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int


# ===========================
# Student / Teacher timetable views (read-only, computed)
# ===========================
class StudentTimetableItemResponse(BaseModel):
    day: str
    start_time: time
    end_time: time
    subject: str
    teacher: str


class TeacherTimetableItemResponse(BaseModel):
    # NOTE: legacy names this field `class_` in Python with a custom
    # model_dump() to rename it to `class` (a reserved word) on the way
    # out. We use an alias instead, which is the correct pydantic v2 way
    # to get the same "class" key in the JSON response while keeping a
    # legal Python attribute name.
    class_: str = Field(..., alias="class")
    subject: str
    day: str
    time: str

    model_config = {"populate_by_name": True}
