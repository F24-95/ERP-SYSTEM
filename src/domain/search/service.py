from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.search.ranking_engine import (
    DEFAULT_RESULT_LIMIT,
    RawHit,
    rank_and_merge,
)
from src.domain.search.similarity_engine import (
    EMAIL_FUZZY_MIN_SCORE,
    FUZZY_CANDIDATE_POOL,
    rank_candidates,
)
from src.domain.search.text_utils import QueryType, build_search_text, normalize_text
from src.domain.search.validator import SearchQueryValidator
from src.domain.users.models import StudentProfile, TeacherProfile, User


class StudentSearchHit:
    def __init__(
        self,
        *,
        student,
        confidence,
        confidence_label,
        match_type,
        matched_field,
        signals,
    ):
        self.student = student
        self.confidence = confidence
        self.confidence_label = confidence_label
        self.match_type = match_type
        self.matched_field = matched_field
        self.signals = signals


class TeacherSearchHit:
    def __init__(
        self,
        *,
        teacher,
        confidence,
        confidence_label,
        match_type,
        matched_field,
        signals,
    ):
        self.teacher = teacher
        self.confidence = confidence
        self.confidence_label = confidence_label
        self.match_type = match_type
        self.matched_field = matched_field
        self.signals = signals


class StudentSearchService:
    """Merges legacy `StudentSearchRepository` + `StudentSearchService` into
    one async class (this project doesn't have a separate repository layer
    per search entity; `AsyncBaseCRUD` doesn't cover these bespoke
    exact+fuzzy queries so they live directly here, same granularity as
    every other domain's service.py talking straight to `db`).

    entity_key is `str(StudentProfile.id)` throughout -- legacy used the
    business `student_id` string; this project's StudentProfile has no such
    column, so the numeric PK (stringified, since RawHit.entity_key is
    typed `str` in the shared ranking engine) is the adapted equivalent,
    same choice made for ID cards in this same pass.
    """

    ENTITY_TYPE = "student"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        raw_query: str,
        *,
        limit: int = DEFAULT_RESULT_LIMIT,
    ) -> list[StudentSearchHit]:
        validated = SearchQueryValidator.validate(raw_query)

        hits: list[RawHit] = []
        hits.extend(await self._exact_hits(validated.normalized, validated.cleaned))

        if validated.query_type == QueryType.EMAIL:
            hits.extend(await self._fuzzy_email_hits(validated.cleaned))
        else:
            hits.extend(await self._fuzzy_name_hits(validated.cleaned))

        ranked = rank_and_merge(hits, limit=limit)
        return await self._hydrate(ranked)

    async def _exact_hits(self, normalized_query: str, raw_query: str) -> list[RawHit]:
        result = await self.db.execute(
            select(StudentProfile)
            .join(User, User.id == StudentProfile.user_id)
            .options(selectinload(StudentProfile.user))
            .filter(
                StudentProfile.is_active == True,  # noqa: E712
                or_(
                    func.lower(StudentProfile.student_name) == normalized_query,
                    func.lower(StudentProfile.admission_number) == normalized_query,
                    func.lower(StudentProfile.registration_number) == normalized_query,
                    func.lower(User.email) == normalized_query,
                    User.phone == raw_query.strip(),
                ),
            ),
        )
        rows = list(result.scalars().unique().all())

        hits = []
        for student in rows:
            matched_field = self._which_field_matched(student, normalized_query)
            hits.append(
                RawHit(
                    entity_key=str(student.id),
                    score=100.0,
                    match_type="exact",
                    matched_field=matched_field,
                ),
            )
        return hits

    @staticmethod
    def _which_field_matched(student: StudentProfile, normalized: str) -> str:
        if normalize_text(student.student_name or "") == normalized:
            return "student_name"
        if normalize_text(student.admission_number or "") == normalized:
            return "admission_number"
        if normalize_text(student.registration_number or "") == normalized:
            return "registration_number"
        if student.user and normalize_text(student.user.email or "") == normalized:
            return "email"
        return "phone"

    async def _fuzzy_name_hits(self, raw_query: str) -> list[RawHit]:
        result = await self.db.execute(
            select(
                StudentProfile.id,
                StudentProfile.student_name,
                StudentProfile.admission_number,
                StudentProfile.registration_number,
                StudentProfile.parent_name,
            )
            .filter(StudentProfile.is_active == True)  # noqa: E712
            .limit(FUZZY_CANDIDATE_POOL),
        )
        rows = result.all()
        candidates: list[tuple[str, str]] = [
            (
                str(r.id),
                build_search_text(
                    r.student_name,
                    r.admission_number,
                    r.registration_number,
                    r.parent_name,
                ),
            )
            for r in rows
        ]
        matches = rank_candidates(raw_query, candidates)
        return [
            RawHit(
                entity_key=key,
                score=score,
                match_type="fuzzy",
                matched_field="profile_text",
            )
            for key, score in matches
        ]

    async def _fuzzy_email_hits(self, raw_query: str) -> list[RawHit]:
        result = await self.db.execute(
            select(StudentProfile.id, User.email)
            .join(User, User.id == StudentProfile.user_id)
            .filter(StudentProfile.is_active == True, User.email.isnot(None))  # noqa: E712
            .limit(FUZZY_CANDIDATE_POOL),
        )
        candidates = [(str(r.id), r.email) for r in result.all()]
        matches = rank_candidates(
            raw_query,
            candidates,
            score_cutoff=EMAIL_FUZZY_MIN_SCORE,
        )
        return [
            RawHit(
                entity_key=key,
                score=score,
                match_type="fuzzy",
                matched_field="email",
            )
            for key, score in matches
        ]

    async def _hydrate(self, ranked) -> list[StudentSearchHit]:
        if not ranked:
            return []
        ids = [int(r.entity_key) for r in ranked]
        result = await self.db.execute(
            select(StudentProfile)
            .options(selectinload(StudentProfile.user))
            .filter(StudentProfile.id.in_(ids)),
        )
        by_id = {s.id: s for s in result.scalars().all()}

        hydrated = []
        for r in ranked:
            student = by_id.get(int(r.entity_key))
            if not student:
                continue
            hydrated.append(
                StudentSearchHit(
                    student=student,
                    confidence=round(r.confidence, 2),
                    confidence_label=r.confidence_label,
                    match_type=r.match_type,
                    matched_field=r.matched_field,
                    signals=r.signals,
                ),
            )
        return hydrated


class TeacherSearchService:
    """Mirror of StudentSearchService for teachers -- see that class's
    docstring for the entity_key / repository-merge rationale.
    """

    ENTITY_TYPE = "teacher"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        raw_query: str,
        *,
        limit: int = DEFAULT_RESULT_LIMIT,
    ) -> list[TeacherSearchHit]:
        validated = SearchQueryValidator.validate(raw_query)

        hits: list[RawHit] = []
        hits.extend(await self._exact_hits(validated.normalized, validated.cleaned))

        if validated.query_type == QueryType.EMAIL:
            hits.extend(await self._fuzzy_email_hits(validated.cleaned))
        else:
            hits.extend(await self._fuzzy_name_hits(validated.cleaned))

        ranked = rank_and_merge(hits, limit=limit)
        return await self._hydrate(ranked)

    async def _exact_hits(self, normalized_query: str, raw_query: str) -> list[RawHit]:
        result = await self.db.execute(
            select(TeacherProfile)
            .join(User, User.id == TeacherProfile.user_id)
            .options(selectinload(TeacherProfile.user))
            .filter(
                TeacherProfile.is_active == True,  # noqa: E712
                or_(
                    func.lower(TeacherProfile.teacher_name) == normalized_query,
                    func.lower(TeacherProfile.employee_code) == normalized_query,
                    func.lower(User.email) == normalized_query,
                    User.phone == raw_query.strip(),
                ),
            ),
        )
        rows = list(result.scalars().unique().all())

        hits = []
        for teacher in rows:
            matched_field = self._which_field_matched(teacher, normalized_query)
            hits.append(
                RawHit(
                    entity_key=str(teacher.id),
                    score=100.0,
                    match_type="exact",
                    matched_field=matched_field,
                ),
            )
        return hits

    @staticmethod
    def _which_field_matched(teacher: TeacherProfile, normalized: str) -> str:
        if normalize_text(teacher.teacher_name or "") == normalized:
            return "teacher_name"
        if normalize_text(teacher.employee_code or "") == normalized:
            return "employee_code"
        if teacher.user and normalize_text(teacher.user.email or "") == normalized:
            return "email"
        return "phone"

    async def _fuzzy_name_hits(self, raw_query: str) -> list[RawHit]:
        result = await self.db.execute(
            select(
                TeacherProfile.id,
                TeacherProfile.teacher_name,
                TeacherProfile.employee_code,
                TeacherProfile.designation,
                TeacherProfile.department,
            )
            .filter(TeacherProfile.is_active == True)  # noqa: E712
            .limit(FUZZY_CANDIDATE_POOL),
        )
        rows = result.all()
        candidates: list[tuple[str, str]] = [
            (
                str(r.id),
                build_search_text(
                    r.teacher_name,
                    r.employee_code,
                    r.designation,
                    r.department,
                ),
            )
            for r in rows
        ]
        matches = rank_candidates(raw_query, candidates)
        return [
            RawHit(
                entity_key=key,
                score=score,
                match_type="fuzzy",
                matched_field="profile_text",
            )
            for key, score in matches
        ]

    async def _fuzzy_email_hits(self, raw_query: str) -> list[RawHit]:
        result = await self.db.execute(
            select(TeacherProfile.id, User.email)
            .join(User, User.id == TeacherProfile.user_id)
            .filter(TeacherProfile.is_active == True, User.email.isnot(None))  # noqa: E712
            .limit(FUZZY_CANDIDATE_POOL),
        )
        candidates = [(str(r.id), r.email) for r in result.all()]
        matches = rank_candidates(
            raw_query,
            candidates,
            score_cutoff=EMAIL_FUZZY_MIN_SCORE,
        )
        return [
            RawHit(
                entity_key=key,
                score=score,
                match_type="fuzzy",
                matched_field="email",
            )
            for key, score in matches
        ]

    async def _hydrate(self, ranked) -> list[TeacherSearchHit]:
        if not ranked:
            return []
        ids = [int(r.entity_key) for r in ranked]
        result = await self.db.execute(
            select(TeacherProfile)
            .options(selectinload(TeacherProfile.user))
            .filter(TeacherProfile.id.in_(ids)),
        )
        by_id = {t.id: t for t in result.scalars().all()}

        hydrated = []
        for r in ranked:
            teacher = by_id.get(int(r.entity_key))
            if not teacher:
                continue
            hydrated.append(
                TeacherSearchHit(
                    teacher=teacher,
                    confidence=round(r.confidence, 2),
                    confidence_label=r.confidence_label,
                    match_type=r.match_type,
                    matched_field=r.matched_field,
                    signals=r.signals,
                ),
            )
        return hydrated
