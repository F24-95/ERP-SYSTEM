from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.core.exceptions import ResourceNotFoundException
from src.database.connection import get_db
from src.domain.reports.schemas import (
    StudentActivityReportCreate,
    StudentActivityReportResponse,
    StudentReportGenerateRequest,
    StudentReportResponse,
    SubjectProgressItemResponse,
    TopicProgressItemResponse,
    ZoomDurationReportCreate,
    ZoomDurationReportResponse,
    ZoomInteractionReportCreate,
    ZoomInteractionReportResponse,
)
from src.domain.reports.service import StudentReportService

router = APIRouter(prefix="/reports", tags=["Student Reports"])


def _to_response(report) -> StudentReportResponse:
    return StudentReportResponse(
        id=report.id,
        student_profile_id=report.student_profile_id,
        report_date=report.report_date,
        data_start_date=report.data_start_date,
        data_end_date=report.data_end_date,
        has_pdf=bool(report.pdf_document),
        has_html=bool(report.html_document),
        has_png=bool(report.png_document),
        subject_progress_count=len(report.subject_progress_items or []),
        topic_progress_count=len(report.topic_progress_items or []),
    )


@router.post("/generate", response_model=StudentReportResponse)
async def generate_report(
    data: StudentReportGenerateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or regenerate) a progress report for a student covering a
    date window, from whatever KA progress snapshots fall in that window.
    Students may only generate their own; Admin/Teacher may generate for
    any student.
    """
    report = await StudentReportService.generate_report(
        db,
        data.student_profile_id,
        data.data_start_date,
        data.data_end_date,
        current_user,
    )
    return _to_response(report)


@router.get("/student/{student_profile_id}", response_model=list[StudentReportResponse])
async def list_reports(
    student_profile_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List generated reports for a student."""
    reports = await StudentReportService.list_reports(
        db,
        student_profile_id,
        current_user,
    )
    return [_to_response(r) for r in reports]


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the generated PDF for a report."""
    report = await StudentReportService.get_report(db, report_id, current_user)
    if not report.pdf_document:
        raise ResourceNotFoundException("PDF not generated for this report")
    return Response(
        content=report.pdf_document,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"},
    )


# =============================================================================
# Manual sub-report management -- merged in from the other project variant.
# generate_report() auto-fills subject/topic progress from KA snapshots;
# these cover the pieces that still need a human (or an external feed) to
# set them -- activity aggregates and Zoom stats. Admin/Teacher only.
# =============================================================================


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await StudentReportService.delete_report(db, report_id, current_user)
    return {"success": True, "message": "Report deleted"}


@router.get("/{report_id}/activity", response_model=StudentActivityReportResponse)
async def get_activity_report(
    report_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await StudentReportService.get_activity_report(db, report_id, current_user)
    if not result:
        raise ResourceNotFoundException("Activity report not set for this report yet")
    return result


@router.put("/{report_id}/activity", response_model=StudentActivityReportResponse)
async def set_activity_report(
    report_id: int,
    data: StudentActivityReportCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentReportService.set_activity_report(
        db,
        report_id,
        data.model_dump(exclude_unset=True),
        current_user,
    )


@router.get(
    "/{report_id}/subject-progress",
    response_model=list[SubjectProgressItemResponse],
)
async def get_subject_progress_items(
    report_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StudentReportService.get_subject_progress_items(
        db,
        report_id,
        current_user,
    )


@router.delete("/subject-progress/{item_id}")
async def delete_subject_progress_item(
    item_id: int,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    await StudentReportService.delete_subject_progress_item(db, item_id, current_user)
    return {"success": True, "message": "Subject progress item deleted"}


@router.get(
    "/{report_id}/topic-progress",
    response_model=list[TopicProgressItemResponse],
)
async def get_topic_progress_items(
    report_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StudentReportService.get_topic_progress_items(
        db,
        report_id,
        current_user,
    )


@router.delete("/topic-progress/{item_id}")
async def delete_topic_progress_item(
    item_id: int,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    await StudentReportService.delete_topic_progress_item(db, item_id, current_user)
    return {"success": True, "message": "Topic progress item deleted"}


@router.get("/{report_id}/zoom-duration", response_model=ZoomDurationReportResponse)
async def get_zoom_duration_report(
    report_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await StudentReportService.get_zoom_duration_report(
        db,
        report_id,
        current_user,
    )
    if not result:
        raise ResourceNotFoundException(
            "Zoom duration report not set for this report yet",
        )
    return result


@router.put("/{report_id}/zoom-duration", response_model=ZoomDurationReportResponse)
async def set_zoom_duration_report(
    report_id: int,
    data: ZoomDurationReportCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentReportService.set_zoom_duration_report(
        db,
        report_id,
        data.model_dump(exclude_unset=True),
        current_user,
    )


@router.get(
    "/{report_id}/zoom-interaction",
    response_model=ZoomInteractionReportResponse,
)
async def get_zoom_interaction_report(
    report_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await StudentReportService.get_zoom_interaction_report(
        db,
        report_id,
        current_user,
    )
    if not result:
        raise ResourceNotFoundException(
            "Zoom interaction report not set for this report yet",
        )
    return result


@router.put(
    "/{report_id}/zoom-interaction",
    response_model=ZoomInteractionReportResponse,
)
async def set_zoom_interaction_report(
    report_id: int,
    data: ZoomInteractionReportCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    return await StudentReportService.set_zoom_interaction_report(
        db,
        report_id,
        data.model_dump(exclude_unset=True),
        current_user,
    )
