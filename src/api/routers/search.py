from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.search.ranking_engine import DEFAULT_RESULT_LIMIT, MAX_RESULT_LIMIT
from src.domain.search.schemas import (
    StudentSearchResponse,
    StudentSearchResultItem,
    TeacherSearchResponse,
    TeacherSearchResultItem,
)
from src.domain.search.service import StudentSearchService, TeacherSearchService
from src.domain.search.text_utils import classify_query

router = APIRouter(tags=["Search"])


@router.get("/students/search", response_model=StudentSearchResponse)
async def search_students(
    q: str = Query(
        ...,
        min_length=1,
        description="Name, email, admission/registration number, or phone",
    ),
    limit: int = Query(DEFAULT_RESULT_LIMIT, ge=1, le=MAX_RESULT_LIMIT),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Natural-language search for students: name, email, admission/
    registration number, or phone -> a ranked list of candidates. Always
    returns a ranked list (never auto-resolves a single "best" match, since
    names are never assumed unique) -- the caller picks the right one and
    uses `internal_id` with the existing student endpoints.

    Access: Admin and Teacher only, matching legacy (searching across the
    whole student body is a staff operation).
    """
    service = StudentSearchService(db)
    hits = await service.search(q, limit=limit)

    results = [
        StudentSearchResultItem(
            display_name=hit.student.student_name,
            email=hit.student.user.email if hit.student.user else None,
            student_code=hit.student.admission_number,
            internal_id=str(hit.student.id),
            registration_number=hit.student.registration_number,
            phone=hit.student.user.phone if hit.student.user else None,
            profile_photo=None,
            score=hit.confidence,
            confidence_label=hit.confidence_label,
            match_type=hit.match_type,
            matched_field=hit.matched_field,
            signals=hit.signals,
        )
        for hit in hits
    ]

    return StudentSearchResponse(
        query=q,
        query_type=classify_query(q).value,
        result_count=len(results),
        results=results,
    )


@router.get("/teachers/search", response_model=TeacherSearchResponse)
async def search_teachers(
    q: str = Query(
        ...,
        min_length=1,
        description="Name, email, employee code, or phone",
    ),
    limit: int = Query(DEFAULT_RESULT_LIMIT, ge=1, le=MAX_RESULT_LIMIT),
    current_user=Depends(
        require_role(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT),
    ),
    db: AsyncSession = Depends(get_db),
):
    """Natural-language search for teachers."""
    service = TeacherSearchService(db)
    hits = await service.search(q, limit=limit)

    results = [
        TeacherSearchResultItem(
            display_name=hit.teacher.teacher_name,
            email=hit.teacher.user.email if hit.teacher.user else None,
            teacher_code=hit.teacher.employee_code,
            internal_id=str(hit.teacher.id),
            department=hit.teacher.department,
            designation=hit.teacher.designation,
            phone=hit.teacher.user.phone if hit.teacher.user else None,
            profile_photo=None,
            score=hit.confidence,
            confidence_label=hit.confidence_label,
            match_type=hit.match_type,
            matched_field=hit.matched_field,
            signals=hit.signals,
        )
        for hit in hits
    ]

    return TeacherSearchResponse(
        query=q,
        query_type=classify_query(q).value,
        result_count=len(results),
        results=results,
    )
