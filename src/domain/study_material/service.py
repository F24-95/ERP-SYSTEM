import asyncio
import os
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import MaterialType
from src.core.exceptions import (
    BusinessLogicException,
    ResourceNotFoundException,
    ValidationException,
)
from src.core.logger import get_logger
from src.domain.study_material.crud import study_material_crud
from src.domain.study_material.models import StudyMaterial

logger = get_logger(__name__)

MAX_STUDY_MATERIAL_FILE_SIZE = int(
    os.getenv("MAX_STUDY_MATERIAL_FILE_SIZE", 50 * 1024 * 1024)
)

# Ported verbatim from legacy StudyMaterialService.ALLOWED_EXTENSIONS.
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".zip",
    ".rar",
    ".mp4",
}


def _upload_root() -> str:
    return "uploads/study_materials"


def _safe_ext(filename: str) -> str:
    _, ext = os.path.splitext(filename or "")
    return ext.lower()


def _validate_extension(filename: str) -> str:
    ext = _safe_ext(filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationException(
            f"Unsupported file extension '{ext}'. Allowed: {allowed}",
        )
    return ext


def _derive_material_type(filename: str) -> MaterialType:
    """NOTE: this preserves a legacy quirk verbatim, not a bug I introduced.
    The legacy `MaterialType` enum only ever had PDF/VIDEO/DOCUMENT/LINK/OTHER
    members, but `derive_material_type` mapped extensions to DOC/DOCX/PPT/
    PPTX/IMAGE/ARCHIVE — none of which exist on the enum. Every one of those
    lookups fails and falls through to a fallback loop whose first hit is
    "DOCUMENT". Net effect in production: only `.pdf` -> PDF and `.mp4` ->
    VIDEO are ever derived correctly; every other allowed extension
    (doc/docx/ppt/pptx/png/jpg/jpeg/zip/rar) silently becomes DOCUMENT.
    Preserved exactly so material_type values already in production data
    stay consistent with newly created rows.
    """
    ext = _safe_ext(filename)
    mapping = {".pdf": "PDF", ".mp4": "VIDEO"}
    enum_name = mapping.get(ext)
    if enum_name and hasattr(MaterialType, enum_name):
        return getattr(MaterialType, enum_name)
    return MaterialType.DOCUMENT


def _build_storage_name(material_id: str, filename: str) -> str:
    ext = _validate_extension(filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    rand = str(abs(hash((material_id, filename, timestamp))))[-8:]
    return f"{material_id}_{timestamp}_{rand}{ext}"


def _save_upload(
    file: UploadFile,
    absolute_path: str,
    max_size: int = MAX_STUDY_MATERIAL_FILE_SIZE,
) -> int:
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
    total_written = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(absolute_path, "wb") as buffer:
        while True:
            chunk = file.file.read(chunk_size)
            if not chunk:
                break
            total_written += len(chunk)
            if total_written > max_size:
                buffer.close()
                _safe_delete_file(absolute_path)
                raise BusinessLogicException(
                    f"File size exceeds maximum allowed limit of {max_size // (1024 * 1024)}MB"
                )
            buffer.write(chunk)
        buffer.flush()
    return total_written


def _safe_delete_file(path: str | None) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        logger.warning(f"Failed to delete file: {path}")


def _abs_path_from_url(file_url: str | None) -> str | None:
    if file_url and file_url.startswith("/uploads/"):
        return file_url.replace("/uploads/", "uploads/", 1)
    return None


class StudyMaterialService:
    @staticmethod
    async def get_by_id(db: AsyncSession, material_db_id: int) -> StudyMaterial:
        material = await db.scalar(
            select(StudyMaterial).filter_by(id=material_db_id, is_active=True),
        )
        if not material:
            raise ResourceNotFoundException("Study material not found")
        return material

    @staticmethod
    async def list_all(db: AsyncSession) -> list[StudyMaterial]:
        return await study_material_crud.get_many(
            db,
            filters={"is_active": True},
            order_by="created_at",
        )

    @staticmethod
    async def list_by_class_subject(
        db: AsyncSession,
        class_subject_id: int,
    ) -> list[StudyMaterial]:
        return await study_material_crud.get_many(
            db,
            filters={"class_subject_id": class_subject_id, "is_active": True},
            order_by="created_at",
        )

    @staticmethod
    async def create_material(
        db: AsyncSession,
        *,
        title: str,
        description: str | None,
        academic_sessions_id: int,
        classroom_id: int,
        class_subject_id: int,
        teacher_subject_id: int,
        uploaded_by: int,
        file: UploadFile,
        material_type: str | None = None,
    ) -> StudyMaterial:
        if file is None:
            raise ValidationException("file is required")

        _validate_extension(file.filename)
        mt = _derive_material_type(file.filename)
        if material_type:
            try:
                mt = MaterialType[material_type]
            except Exception:
                logger.warning(f"Unknown material_type: {material_type}")

        material = await study_material_crud.create(
            db,
            {
                "title": title,
                "description": description,
                "academic_sessions_id": academic_sessions_id,
                "classroom_id": classroom_id,
                "class_subject_id": class_subject_id,
                "teacher_subject_id": teacher_subject_id,
                "material_type": mt,
                "file_name": file.filename,
                "file_url": "",
                "file_size": 0,
                "mime_type": file.content_type,
                "uploaded_by": uploaded_by,
            },
        )

        stored_name = _build_storage_name(material.material_id, file.filename)
        abs_path = os.path.join(_upload_root(), stored_name)
        size = await asyncio.to_thread(_save_upload, file, abs_path)

        material.file_name = file.filename
        material.file_url = f"/uploads/study_materials/{stored_name}"
        material.file_size = size
        material.mime_type = file.content_type
        await db.flush()
        await db.refresh(material)

        logger.info(
            f"Study material created: {material.material_id} by user={uploaded_by}",
        )
        return material

    @staticmethod
    async def update_material(
        db: AsyncSession,
        material_db_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        academic_sessions_id: int | None = None,
        classroom_id: int | None = None,
        class_subject_id: int | None = None,
        teacher_subject_id: int | None = None,
        file: UploadFile | None = None,
        material_type: str | None = None,
    ) -> StudyMaterial:
        material = await StudyMaterialService.get_by_id(db, material_db_id)

        if title is not None:
            material.title = title
        if description is not None:
            material.description = description
        if academic_sessions_id is not None:
            material.academic_sessions_id = academic_sessions_id
        if classroom_id is not None:
            material.classroom_id = classroom_id
        if class_subject_id is not None:
            material.class_subject_id = class_subject_id
        if teacher_subject_id is not None:
            material.teacher_subject_id = teacher_subject_id

        old_abs_path = _abs_path_from_url(material.file_url)

        if file is not None:
            mt = _derive_material_type(file.filename)
            if material_type:
                try:
                    mt = MaterialType[material_type]
                except Exception:
                    logger.warning(f"Unknown material_type: {material_type}")

            material.material_type = mt
            stored_name = _build_storage_name(material.material_id, file.filename)
            abs_path = os.path.join(_upload_root(), stored_name)
            size = await asyncio.to_thread(_save_upload, file, abs_path)

            material.file_name = file.filename
            material.file_url = f"/uploads/study_materials/{stored_name}"
            material.file_size = size
            material.mime_type = file.content_type

            _safe_delete_file(old_abs_path)

        await db.flush()
        await db.refresh(material)
        logger.info(f"Study material updated: {material.material_id}")
        return material

    @staticmethod
    async def delete_material(db: AsyncSession, material_db_id: int) -> None:
        material = await StudyMaterialService.get_by_id(db, material_db_id)
        abs_path = _abs_path_from_url(material.file_url)

        material.is_active = False
        await db.flush()
        _safe_delete_file(abs_path)
        logger.info(f"Study material deleted: {material.material_id}")

    @staticmethod
    async def increment_download(db: AsyncSession, material_db_id: int) -> None:
        material = await StudyMaterialService.get_by_id(db, material_db_id)
        material.download_count = (material.download_count or 0) + 1
        await db.flush()
