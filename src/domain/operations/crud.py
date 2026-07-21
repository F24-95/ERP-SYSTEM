from src.database.base_crud import AsyncBaseCRUD
from src.domain.operations.models import (
    ClassTimeTable,
    DailyClass,
    DailyClassStudent,
    StudentAttendance,
    StudentClass,
    StudentPromotionHistory,
    TeacherAvailability,
    TeacherSubject,
    TimeSlot,
    WeekDay,
)

# Instantiate CRUD singletons
teacher_subject_crud = AsyncBaseCRUD[TeacherSubject](TeacherSubject)
student_class_crud = AsyncBaseCRUD[StudentClass](StudentClass)
promotion_crud = AsyncBaseCRUD[StudentPromotionHistory](StudentPromotionHistory)

# Timetable CRUD
weekday_crud = AsyncBaseCRUD[WeekDay](WeekDay)
timeslot_crud = AsyncBaseCRUD[TimeSlot](TimeSlot)
timetable_crud = AsyncBaseCRUD[ClassTimeTable](ClassTimeTable)
availability_crud = AsyncBaseCRUD[TeacherAvailability](TeacherAvailability)

# Attendance CRUD
daily_class_crud = AsyncBaseCRUD[DailyClass](DailyClass)
daily_student_crud = AsyncBaseCRUD[DailyClassStudent](DailyClassStudent)
attendance_crud = AsyncBaseCRUD[StudentAttendance](StudentAttendance)
