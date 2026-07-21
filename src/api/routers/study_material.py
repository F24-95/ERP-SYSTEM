import os

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.core.exceptions import AuthorizationException, ResourceNotFoundException
from src.core.logger import get_logger
from src.database.connection import get_db
from src.domain.study_material.schemas import StudyMaterialResponse
from src.domain.study_material.service import StudyMaterialService
from src.domain.users.models import User

logger = get_logger(__name__)

router = APIRouter(prefix="/study-materials", tags=["Study Materials"])


def _material_abs_path(file_url: str | None) -> str | None:
    if not file_url:
        return None
    if file_url.startswith("/uploads/"):
        return file_url.replace("/uploads/", "uploads/", 1)
    if file_url.startswith("uploads/"):
        return file_url
    return None


@router.post("", response_model=StudyMaterialResponse)
async def create_study_material(
    title: str = Form(...),
    description: str | None = Form(None),
    material_type: str | None = Form(None),
    academic_sessions_id: int = Form(...),
    classroom_id: int = Form(...),
    class_subject_id: int = Form(...),
    teacher_subject_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Upload study material files (multipart/form-data)."""
    return await StudyMaterialService.create_material(
        db,
        title=title,
        description=description,
        material_type=material_type,
        academic_sessions_id=academic_sessions_id,
        classroom_id=classroom_id,
        class_subject_id=class_subject_id,
        teacher_subject_id=teacher_subject_id,
        uploaded_by=current_user.id,
        file=file,
    )


@router.get("", response_model=list[StudyMaterialResponse])
async def list_study_materials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get study materials."""
    return await StudyMaterialService.list_all(db)


@router.get(
    "/class-subject/{class_subject_id}",
    response_model=list[StudyMaterialResponse],
)
async def get_materials_for_class_subject(
    class_subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get study materials for a specific class-subject mapping."""
    return await StudyMaterialService.list_by_class_subject(db, class_subject_id)


@router.get("/{id}", response_model=StudyMaterialResponse)
async def get_study_material(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await StudyMaterialService.get_by_id(db, id)


@router.get("/{id}/view")
async def view_study_material(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Students must be able to view study materials."""
    material = await StudyMaterialService.get_by_id(db, id)

    if current_user.role not in (UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN):
        raise AuthorizationException("Permission denied")

    abs_path = _material_abs_path(material.file_url)
    if not abs_path or not os.path.exists(abs_path):
        raise ResourceNotFoundException("File not found on server")

    filename = material.file_name or os.path.basename(abs_path)
    return FileResponse(
        abs_path,
        media_type=material.mime_type or "application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/{id}/download")
async def download_study_material(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Students must be able to download study materials."""
    material = await StudyMaterialService.get_by_id(db, id)

    if current_user.role not in (UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN):
        raise AuthorizationException("Permission denied")

    try:
        await StudyMaterialService.increment_download(db, id)
    except Exception:
        logger.warning(f"Failed to increment download count for material id={id}")

    abs_path = _material_abs_path(material.file_url)
    if not abs_path or not os.path.exists(abs_path):
        raise ResourceNotFoundException("File not found on server")

    filename = material.file_name or os.path.basename(abs_path)
    return FileResponse(
        abs_path,
        media_type=material.mime_type or "application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.put("/{id}", response_model=StudyMaterialResponse)
async def update_study_material(
    id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    material_type: str | None = Form(None),
    academic_sessions_id: int | None = Form(None),
    classroom_id: int | None = Form(None),
    class_subject_id: int | None = Form(None),
    teacher_subject_id: int | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Update study material metadata and optionally replace the file."""
    return await StudyMaterialService.update_material(
        db,
        id,
        title=title,
        description=description,
        material_type=material_type,
        academic_sessions_id=academic_sessions_id,
        classroom_id=classroom_id,
        class_subject_id=class_subject_id,
        teacher_subject_id=teacher_subject_id,
        file=file,
    )


@router.delete("/{id}")
async def delete_study_material(
    id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await StudyMaterialService.delete_material(db, id)
    return {"success": True, "message": "Study material deleted"}
