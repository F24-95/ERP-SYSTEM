from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.core.exceptions import ResourceNotFoundException
from src.database.connection import get_db
from src.domain.common.schemas import MessageResponse
from src.domain.operations.schemas import (
    ClassTimeTableCreate,
    ClassTimeTableResponse,
    ClassTimeTableUpdate,
    StudentTimetableItemResponse,
    TeacherAvailabilityCreate,
    TeacherAvailabilityResponse,
    TeacherAvailabilityUpdate,
    TeacherTimetableItemResponse,
    TimeSlotCreate,
    TimeSlotResponse,
    TimeSlotUpdate,
    WeekDayCreate,
    WeekDayResponse,
    WeekDayUpdate,
)
from src.domain.operations.service import TimetableService

router = APIRouter(tags=["Timetable"])


# ==================== WEEK DAYS ====================


@router.get("/weekdays", response_model=list[WeekDayResponse])
async def get_weekdays(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all weekdays."""
    return await TimetableService.get_all_weekdays(db)


@router.post("/weekdays", response_model=WeekDayResponse)
async def create_weekday(
    data: WeekDayCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a weekday."""
    return await TimetableService.create_weekday(db, data.model_dump())


@router.put("/weekdays/{weekday_id}", response_model=WeekDayResponse)
async def update_weekday(
    weekday_id: int,
    data: WeekDayUpdate,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a weekday. Was missing entirely."""
    return await TimetableService.update_weekday(
        db,
        weekday_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete("/weekdays/{weekday_id}", response_model=MessageResponse)
async def deactivate_weekday(
    weekday_id: int,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a weekday. Was missing entirely."""
    await TimetableService.deactivate_weekday(db, weekday_id)
    return MessageResponse(message="Weekday deactivated")


# ==================== TIME SLOTS ====================


@router.get("/timeslots", response_model=list[TimeSlotResponse])
async def get_timeslots(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all time slots."""
    return await TimetableService.get_all_timeslots(db)


@router.post("/timeslots", response_model=TimeSlotResponse)
async def create_timeslot(
    data: TimeSlotCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a time slot."""
    return await TimetableService.create_timeslot(db, data.model_dump())


@router.put("/timeslots/{timeslot_id}", response_model=TimeSlotResponse)
async def update_timeslot(
    timeslot_id: int,
    data: TimeSlotUpdate,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a time slot. Was missing entirely."""
    return await TimetableService.update_timeslot(
        db,
        timeslot_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete("/timeslots/{timeslot_id}", response_model=MessageResponse)
async def deactivate_timeslot(
    timeslot_id: int,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a time slot. Was missing entirely."""
    await TimetableService.deactivate_timeslot(db, timeslot_id)
    return MessageResponse(message="Timeslot deactivated")


# ==================== TIMETABLE ====================


@router.get(
    "/timetable/class/{classroom_id}",
    response_model=list[ClassTimeTableResponse],
)
async def get_class_timetable(
    classroom_id: int,
    session_id: int = Query(..., description="Academic session ID"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get timetable for a class."""
    return await TimetableService.get_class_timetable(db, classroom_id, session_id)


# ==================== ADMIN TIMETABLE LIST ====================


@router.get("/timetables", response_model=list[ClassTimeTableResponse])
async def admin_get_timetables(
    class_id: int | None = Query(None, alias="class"),
    teacher_subject_id: int | None = Query(None, alias="teacher"),
    subject_id: int | None = Query(None, alias="subject"),
    day_id: int | None = Query(None, alias="day"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """List timetable entries with optional filters."""
    return await TimetableService.admin_get_timetables(
        db,
        classroom_id=class_id,
        teacher_subject_id=teacher_subject_id,
        class_subject_id=subject_id,
        week_day_id=day_id,
    )


@router.post("/timetable", response_model=ClassTimeTableResponse)
async def create_timetable_entry(
    data: ClassTimeTableCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a timetable entry."""
    return await TimetableService.create_timetable(db, data.model_dump())


@router.put("/timetable/{id}", response_model=ClassTimeTableResponse)
async def update_timetable_entry(
    id: int,
    data: ClassTimeTableUpdate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update a timetable entry."""
    updated = await TimetableService.admin_update_timetable(
        db,
        id,
        data.model_dump(exclude_unset=True),
    )
    if not updated:
        raise ResourceNotFoundException("Timetable entry not found")
    return updated


@router.delete("/timetable/{id}")
async def delete_timetable_entry(
    id: int,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Admin: Delete a timetable entry."""
    deleted = await TimetableService.admin_delete_timetable(db, id)
    if not deleted:
        raise ResourceNotFoundException("Timetable entry not found")
    return {"success": True, "message": "Timetable entry deleted"}


# ==================== STUDENT TIMETABLE ====================


@router.get("/student/timetable", response_model=list[StudentTimetableItemResponse])
async def get_student_timetable(
    current_user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Student: get ONLY own class timetable for current academic session."""
    return await TimetableService.student_get_timetable(db, current_user.id)


# ==================== TEACHER TIMETABLE ====================


@router.get("/teacher/timetable", response_model=list[TeacherTimetableItemResponse])
async def get_teacher_timetable(
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Teacher: get timetable for assigned classes for current academic session."""
    return await TimetableService.teacher_get_timetable(db, current_user.id)


# ==================== TEACHER AVAILABILITY ====================


@router.get(
    "/availability/teacher/{teacher_subject_id}",
    response_model=list[TeacherAvailabilityResponse],
)
async def get_teacher_availability(
    teacher_subject_id: int,
    session_id: int = Query(..., description="Academic session ID"),
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Get teacher availability."""
    return await TimetableService.get_teacher_availability(
        db,
        teacher_subject_id,
        session_id,
    )


@router.post("/availability", response_model=TeacherAvailabilityResponse)
async def create_availability(
    data: TeacherAvailabilityCreate,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create teacher availability."""
    return await TimetableService.create_availability(db, data.model_dump(), current_user)


@router.put(
    "/availability/{availability_id}",
    response_model=TeacherAvailabilityResponse,
)
async def update_availability(
    availability_id: int,
    data: TeacherAvailabilityUpdate,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update teacher availability."""
    updated = await TimetableService.update_availability(
        db,
        availability_id,
        data.model_dump(exclude_unset=True),
        current_user,
    )
    if not updated:
        raise ResourceNotFoundException("Availability not found")
    return updated


@router.delete("/availability/{availability_id}", response_model=MessageResponse)
async def delete_availability(
    availability_id: int,
    current_user=Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw a teacher availability slot. Was missing entirely."""
    updated = await TimetableService.deactivate_availability(db, availability_id, current_user)
    if not updated:
        raise ResourceNotFoundException("Availability not found")
    return MessageResponse(message="Availability deleted")
