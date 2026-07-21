import os
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    AuthorizationException,
    BusinessLogicException,
    ResourceNotFoundException,
)
from src.core.logger import get_logger
from src.domain.academics.models import AcademicSession, ClassRoom
from src.domain.id_cards.generators import (
    generate_qr_image,
    load_institute_asset,
    render_student_id_pdf,
)
from src.domain.id_cards.models import StudentIDCard
from src.domain.operations.models import StudentClass
from src.domain.users.models import StudentProfile, User

logger = get_logger(__name__)


class StudentIDCardService:
    """Ported from legacy `app/services/student_id_card_service.py`.

    Scope note: legacy routes accept a `student_id` path param resolved
    through `IdentifierResolverService` (accepts an internal id, email, or
    name). That resolver service is out of scope for this pass (it isn't
    listed in Section 5 and pulls in identifier-fuzzy-matching concerns of
    its own) -- endpoints here take the `StudentProfile.id` directly instead,
    consistent with how every other adapted FK in this migration keys off
    the new integer primary keys rather than legacy business-ID strings.
    """

    @staticmethod
    def _profile_is_complete(student: StudentProfile) -> bool:
        return bool(
            student.student_name and student.date_of_birth and student.parent_name,
        )

    @staticmethod
    def _business_id_for(student: StudentProfile) -> str | None:
        # NOTE: legacy snapshots `StudentProfile.student_id` (a business-ID
        # string column not present on this project's StudentProfile).
        # Closest equivalents here are `registration_number` (preferred,
        # matches the "search-friendly business identifier" role legacy's
        # student_id played) falling back to `admission_number`.
        return student.registration_number or student.admission_number

    @staticmethod
    async def _get_academic_session_for_card(db: AsyncSession) -> AcademicSession:
        session = await db.scalar(select(AcademicSession).filter_by(is_current=True))
        if not session:
            raise ResourceNotFoundException("Current academic session not found")
        return session

    @staticmethod
    def _compute_doj_and_valid_till(
        student_class: StudentClass,
    ) -> tuple[date | None, date | None]:
        doj = student_class.admission_date
        valid_till = doj + timedelta(days=365) if doj else None
        return doj, valid_till

    @staticmethod
    async def generate_or_regenerate_card(
        db: AsyncSession,
        student_profile_id: int,
        actor_user_id: int | None,
        regenerate: bool,
    ) -> StudentIDCard:
        student = await db.get(StudentProfile, student_profile_id)
        if not student:
            raise ResourceNotFoundException("Student not found")

        if not StudentIDCardService._profile_is_complete(student):
            raise BusinessLogicException(
                "Student profile is missing required details (name, date of birth, or parent name)",
            )

        business_id = StudentIDCardService._business_id_for(student)
        if not business_id:
            raise BusinessLogicException(
                "Student has no registration/admission number to print on the card",
            )

        current_session = await StudentIDCardService._get_academic_session_for_card(db)

        student_class = await db.scalar(
            select(StudentClass).filter(
                StudentClass.student_id == student.user_id,
                StudentClass.academic_sessions_id == current_session.id,
                StudentClass.status == "ACTIVE",
            ),
        )
        if not student_class:
            raise ResourceNotFoundException(
                "Student not enrolled in current academic session",
            )

        classroom = await db.get(ClassRoom, student_class.classroom_id)

        institute_logo_path, institute_name, institute_contact = load_institute_asset()

        existing = await db.scalar(
            select(StudentIDCard).filter_by(
                student_profile_id=student.id,
                academic_sessions_id=current_session.id,
            ),
        )
        if existing and not regenerate:
            return existing

        base_dir = os.path.join(
            "uploads",
            "student_id_cards",
            str(current_session.id),
            str(student.id),
        )
        os.makedirs(base_dir, exist_ok=True)
        qr_path = os.path.join(base_dir, "qr.png")
        pdf_path = os.path.join(base_dir, "student_id_card.pdf")

        qr_payload = f"SCHOOL_ERP|student_id={business_id}|session_id={current_session.id}|card_type=STUDENT_ID"
        generate_qr_image(qr_payload, qr_path)

        doj, valid_till = StudentIDCardService._compute_doj_and_valid_till(
            student_class,
        )

        # NOTE: legacy also embeds `student.profile_photo` in the render and
        # stores it as `student_photo_path`. This project's `StudentProfile`
        # has no photo column at all (a gap between the old and new user
        # schema, not something to silently paper over) -- so the photo slot
        # is simply left empty here (both in the render call and the stored
        # path) until that field exists.
        student_photo_path = None

        render_student_id_pdf(
            {
                "institute_logo_path": institute_logo_path,
                "institute_name": institute_name,
                "institute_contact_number": institute_contact,
                "academic_session_label": current_session.session_name,
                "date_of_joining": doj,
                "valid_till": valid_till,
                "student_photo_path": student_photo_path,
                "student_name": student.student_name,
                "parent_name": student.parent_name,
                "class_display_name": classroom.display_name if classroom else None,
                "student_id_business": business_id,
                "qr_code_path": qr_path,
            },
            pdf_path,
        )

        if existing:
            existing.institute_logo_path = institute_logo_path
            existing.institute_name = institute_name
            existing.institute_contact_number = institute_contact
            existing.academic_session_label = current_session.session_name
            existing.date_of_joining = doj
            existing.valid_till = valid_till
            existing.student_photo_path = student_photo_path
            existing.student_name = student.student_name
            existing.parent_name = student.parent_name
            existing.class_display_name = classroom.display_name if classroom else None
            existing.qr_code_path = qr_path
            existing.pdf_path = pdf_path
            existing.student_id_business = business_id
            existing.updated_by = actor_user_id
            await db.flush()
            return existing

        card = StudentIDCard(
            student_profile_id=student.id,
            academic_sessions_id=current_session.id,
            student_name=student.student_name,
            parent_name=student.parent_name,
            class_display_name=classroom.display_name if classroom else None,
            institute_name=institute_name,
            institute_contact_number=institute_contact,
            academic_session_label=current_session.session_name,
            date_of_joining=doj,
            valid_till=valid_till,
            institute_logo_path=institute_logo_path,
            student_photo_path=student_photo_path,
            qr_code_path=qr_path,
            pdf_path=pdf_path,
            student_id_business=business_id,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        db.add(card)
        await db.flush()
        logger.info(
            f"ID card generated for student_profile={student.id} session={current_session.id}",
        )
        return card

    @staticmethod
    async def backfill_missing_id_cards(
        db: AsyncSession,
        actor_user_id: int | None = None,
    ) -> dict:
        try:
            current_session = await StudentIDCardService._get_academic_session_for_card(
                db,
            )
        except ResourceNotFoundException:
            return {"generated": 0, "skipped": 0, "failed": 0}

        result = await db.execute(
            select(StudentClass).filter(
                StudentClass.academic_sessions_id == current_session.id,
                StudentClass.status == "ACTIVE",
            ),
        )
        enrollments = list(result.scalars().all())

        generated = skipped = failed = 0

        for enrollment in enrollments:
            student = await db.scalar(
                select(StudentProfile).filter_by(user_id=enrollment.student_id),
            )
            if not student:
                skipped += 1
                continue

            existing = await db.scalar(
                select(StudentIDCard).filter_by(
                    student_profile_id=student.id,
                    academic_sessions_id=current_session.id,
                ),
            )
            if existing:
                skipped += 1
                continue

            if not StudentIDCardService._profile_is_complete(
                student,
            ) or not StudentIDCardService._business_id_for(student):
                skipped += 1
                continue

            try:
                await StudentIDCardService.generate_or_regenerate_card(
                    db,
                    student_profile_id=student.id,
                    actor_user_id=actor_user_id,
                    regenerate=False,
                )
                generated += 1
            except Exception:
                await db.rollback()
                failed += 1

        return {"generated": generated, "skipped": skipped, "failed": failed}

    @staticmethod
    async def get_card_for_view(
        db: AsyncSession,
        student_profile_id: int,
        current_user: User,
    ) -> StudentIDCard:
        # NOTE: legacy's ownership check here is `if current_user.role ==
        # UserRole.STUDENT.value:` -- comparing an Enum member
        # (`current_user.role`) to a plain string (`.value`). Since the role
        # column is a native SQLAlchemy Enum, that comparison is always
        # False, so the "student can only view their own card" check never
        # actually runs -- any authenticated user could view any student's
        # ID card (name, parent name, class, DOB-derived validity dates).
        # This is a real authorization bypass, not a documented business
        # rule, so it's fixed here to compare the enum directly, matching
        # the enum-comparison style used everywhere else in this migration.
        if current_user.role == UserRole.STUDENT:
            own_profile = await db.scalar(
                select(StudentProfile).filter_by(user_id=current_user.id),
            )
            if not own_profile:
                raise ResourceNotFoundException("Student profile not found")
            if own_profile.id != student_profile_id:
                raise AuthorizationException("You can only view your own card")

        card = await db.scalar(
            select(StudentIDCard)
            .filter_by(student_profile_id=student_profile_id)
            .order_by(StudentIDCard.academic_sessions_id.desc()),
        )
        if not card:
            raise ResourceNotFoundException("Student ID card not found")
        return card

    @staticmethod
    async def get_card_for_download(
        db: AsyncSession,
        student_profile_id: int,
        current_user: User,
    ) -> StudentIDCard:
        return await StudentIDCardService.get_card_for_view(
            db,
            student_profile_id,
            current_user,
        )

    @staticmethod
    async def list_all_cards(
        db: AsyncSession,
        page: int,
        page_size: int,
    ) -> tuple[list[StudentIDCard], int]:
        total = await db.scalar(select(func.count()).select_from(StudentIDCard))
        offset = (page - 1) * page_size
        result = await db.execute(
            select(StudentIDCard)
            .order_by(StudentIDCard.created_at.desc())
            .offset(offset)
            .limit(page_size),
        )
        return list(result.scalars().all()), total or 0
