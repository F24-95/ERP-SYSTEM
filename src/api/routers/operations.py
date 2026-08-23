from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.operations.schemas import (
    PromoteStudentRequest,
    StudentClassCreate,
    StudentClassResponse,
    StudentClassUpdate,
    StudentPromotionHistoryResponse,
    TeacherSubjectCreate,
    TeacherSubjectResponse,
    TeacherSubjectUpdate,
)
from src.domain.operations.service import EnrollmentService

router = APIRouter(prefix="/operations", tags=["Operations"])

# ===========================
# ENROLLMENT & ASSIGNMENT
# ===========================


@router.post(
    "/assign-teacher",
    response_model=TeacherSubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_teacher(
    data: TeacherSubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    """Assign a teacher to a subject for a specific class and session."""
    return await EnrollmentService.assign_teacher(db, data)


@router.get("/teacher-assignments", response_model=list[TeacherSubjectResponse])
async def list_teacher_assignments(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all teacher assignments."""
    return await EnrollmentService.list_teacher_assignments(db)


@router.get(
    "/teacher-assignments/{assignment_id}",
    response_model=TeacherSubjectResponse,
)
async def get_teacher_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single teacher assignment. Was missing entirely."""
    return await EnrollmentService.get_teacher_assignment(db, assignment_id)


@router.put(
    "/teacher-assignments/{assignment_id}",
    response_model=TeacherSubjectResponse,
)
async def update_teacher_assignment(
    assignment_id: int,
    data: TeacherSubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    """Update a teacher assignment (is_class_teacher/remarks/is_active)."""
    return await EnrollmentService.update_teacher_assignment(
        db,
        assignment_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete(
    "/teacher-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unassign_teacher(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    """Unassign a teacher from a subject/class. Was missing entirely --
    once assigned, there was no way to reverse it.
    """
    await EnrollmentService.unassign_teacher(db, assignment_id)


@router.post(
    "/enroll-student",
    response_model=StudentClassResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    data: StudentClassCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    """Enroll a student in a class for a given academic session."""
    return await EnrollmentService.enroll_student(db, data)


@router.get("/student-enrollments", response_model=list[StudentClassResponse])
async def list_student_enrollments(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all student enrollments."""
    return await EnrollmentService.list_student_enrollments(db)


@router.get("/student-enrollments/{enrollment_id}", response_model=StudentClassResponse)
async def get_student_enrollment(
    enrollment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single student enrollment. Was missing entirely."""
    return await EnrollmentService.get_student_enrollment(db, enrollment_id)


@router.put("/student-enrollments/{enrollment_id}", response_model=StudentClassResponse)
async def update_student_enrollment(
    enrollment_id: int,
    data: StudentClassUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    """Update a student enrollment (roll_number/status/remarks/is_active)."""
    return await EnrollmentService.update_student_enrollment(
        db,
        enrollment_id,
        data.model_dump(exclude_unset=True),
    )


@router.delete(
    "/student-enrollments/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unenroll_student(
    enrollment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    """Unenroll a student from a class. Was missing entirely -- once
    enrolled, there was no way to reverse it (short of the separate
    promote_student workflow, which is for moving to a *new* session,
    not correcting a mistaken enrollment).
    """
    await EnrollmentService.unenroll_student(db, enrollment_id)


# ===========================
# STUDENT PROMOTION
# ---------------------------
# EnrollmentService.promote_student existed with a complete, working
# implementation, but had zero router endpoint anywhere calling it --
# entirely inaccessible from the API. Also fixed in the same pass: the
# method itself recorded a StudentPromotionHistory row and marked the old
# enrollment "PROMOTED" but never actually created the *new* enrollment
# for the destination session, making promotion a no-op from the
# student's perspective even once wired up.
# ===========================


@router.post(
    "/promote-student",
    response_model=StudentPromotionHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def promote_student(
    data: PromoteStudentRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    """Promote a student from one academic session/classroom to another."""
    return await EnrollmentService.promote_student(
        db,
        student_id=data.student_id,
        from_session_id=data.from_session_id,
        to_session_id=data.to_session_id,
        to_classroom_id=data.to_classroom_id,
        new_roll=data.new_roll,
        promoted_by=current_user.id,
    )


@router.get(
    "/promote-student/{student_id}",
    response_model=list[StudentPromotionHistoryResponse],
)
async def get_promotion_history(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a student's promotion history. Was missing entirely."""
    return await EnrollmentService.get_promotion_history(db, student_id)


# ===========================
# TIMETABLE & DAILY CLASS
# ===========================
# Moved to dedicated routers in Phase 2f: `src/api/routers/daily_class.py`
# (prefix `/daily-class`, full CRUD + attendance, correct RBAC/ownership
# checks) and `src/api/routers/timetable.py` (weekdays, time slots,
# admin timetable CRUD, student/teacher timetable views, availability).
# The two endpoints that used to live here were an incomplete stub (wrong
# RBAC — allowed ADMIN as well as TEACHER, unlike legacy's teacher-only
# create; no teacher-assignment check; no duplicate-date check; no update/
# delete/attendance support) and would have collided on route registration
# with the new dedicated router, so they were removed rather than kept
# alongside it.
