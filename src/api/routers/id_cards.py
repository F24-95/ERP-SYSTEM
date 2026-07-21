import os

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.core.exceptions import ResourceNotFoundException
from src.database.connection import get_db
from src.domain.id_cards.schemas import StudentIDCardResponse
from src.domain.id_cards.service import StudentIDCardService

router = APIRouter(prefix="/student", tags=["Student ID Card"])


@router.get("/id-card/all")
async def list_all_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """ADMIN: list all cards.

    NOTE: registered before `/id-card/{student_profile_id}` on purpose. In
    legacy, `student_id` was a `str` path param, so `GET /id-card/all`
    always matched `view_id_card(student_id="all")` first (routes are
    matched in registration order) and this endpoint was unreachable dead
    code. Here `student_profile_id` is an `int`, which would 422 instead of
    silently shadowing -- but registering the literal path first avoids that
    entirely and actually makes the endpoint reachable, matching its
    evident intent.
    """
    items, total = await StudentIDCardService.list_all_cards(db, page, page_size)
    return {
        "success": True,
        "data": [StudentIDCardResponse.model_validate(c) for c in items],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.post("/id-card/{student_profile_id}")
async def generate_id_card(
    student_profile_id: int,
    regenerate: bool = False,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Admin/Teacher generates or regenerates a student's ID card."""
    card = await StudentIDCardService.generate_or_regenerate_card(
        db,
        student_profile_id,
        actor_user_id=current_user.id,
        regenerate=regenerate,
    )
    return {
        "success": True,
        "card_id": card.id,
        "student_profile_id": card.student_profile_id,
        "academic_sessions_id": card.academic_sessions_id,
        "pdf_path": card.pdf_path,
        "qr_code_path": card.qr_code_path,
    }


@router.get("/id-card/{student_profile_id}", response_model=StudentIDCardResponse)
async def view_id_card(
    student_profile_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """VIEW allowed for Admin/Teacher/Student (student can view own only)."""
    return await StudentIDCardService.get_card_for_view(
        db,
        student_profile_id,
        current_user,
    )


@router.get("/id-card/{student_profile_id}/download")
async def download_id_card(
    student_profile_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download generated PDF (front side only)."""
    card = await StudentIDCardService.get_card_for_download(
        db,
        student_profile_id,
        current_user,
    )

    if not card.pdf_path:
        raise ResourceNotFoundException("PDF not generated yet")

    path = card.pdf_path
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    if not os.path.exists(path):
        raise ResourceNotFoundException("PDF file not found on disk")

    filename = f"student_id_card_{student_profile_id}.pdf"
    return FileResponse(path, media_type="application/pdf", filename=filename)
