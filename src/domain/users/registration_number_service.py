from datetime import date

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.id_generators import generate_registration_number
from src.core.logger import get_logger
from src.domain.users.models import StudentProfile

logger = get_logger(__name__)


class RegistrationNumberService:
    """Generates unique, human-searchable registration numbers
    (e.g. REG-2026-00001), scoped per calendar year.

    Async port of the legacy `RegistrationNumberService`. Sequence is
    derived from how many registration numbers already exist for that
    year, then generation retries on a rare unique-constraint collision
    (two concurrent signups in the same year) by bumping the sequence and
    trying again — same defensive pattern as the legacy implementation.
    """

    MAX_ATTEMPTS = 5

    @staticmethod
    async def _next_sequence_for_year(
        session: AsyncSession,
        year: int,
    ) -> int:
        prefix = f"REG-{year}-"
        query = select(func.count(StudentProfile.id)).where(
            StudentProfile.registration_number.like(f"{prefix}%"),
        )
        count = await session.scalar(query) or 0
        return count + 1

    @classmethod
    async def generate_for_student(
        cls,
        session: AsyncSession,
        student: StudentProfile,
        *,
        flush: bool = True,
    ) -> str:
        """Assigns a registration_number to `student` if it doesn't already
        have one. Returns the (possibly pre-existing) registration_number.
        """
        if student.registration_number:
            return student.registration_number

        year = date.today().year
        last_error = None

        for attempt in range(cls.MAX_ATTEMPTS):
            sequence = await cls._next_sequence_for_year(
                session,
                year,
            ) + attempt
            candidate = generate_registration_number(year, sequence)

            student.registration_number = candidate
            session.add(student)
            try:
                if flush:
                    await session.flush()
                    await session.refresh(student)
                return candidate
            except IntegrityError as exc:
                await session.rollback()
                last_error = exc
                continue

        raise RuntimeError(
            f"Could not generate a unique registration number after "
            f"{cls.MAX_ATTEMPTS} attempts",
        ) from last_error

    @classmethod
    async def backfill_missing_registration_numbers(
        cls,
        session: AsyncSession,
    ) -> dict:
        """Assigns registration numbers to every StudentProfile that
        doesn't have one yet. Safe to call repeatedly — students who
        already have one are skipped.
        """
        query = select(StudentProfile).where(
            StudentProfile.registration_number.is_(None),
        )
        result = await session.execute(query)
        students = list(result.scalars().all())

        generated, failed = 0, 0
        for student in students:
            try:
                await cls.generate_for_student(
                    session,
                    student,
                    flush=True,
                )
                generated += 1
            except Exception:
                await session.rollback()
                failed += 1
                logger.warning(
                    f"Failed to backfill registration_number for "
                    f"student id={student.id}",
                )

        return {
            "generated": generated,
            "failed": failed,
            "total_missing": len(students),
        }
