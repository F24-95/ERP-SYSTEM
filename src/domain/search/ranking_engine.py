# ============================================================
# app/helpers/search/ranking_engine.py
# ============================================================
#
# Entity-agnostic merge/rank step. Each entity-specific search service
# (StudentSearchService, TeacherSearchService, ...) runs its own exact +
# fuzzy lookups against its own repository (fields differ per entity)
# and hands the raw hits here. This is the one piece of ranking logic
# that's identical across every entity, so it lives in exactly one
# place instead of being copy-pasted per service.
#
# No database code, no API/schema code here.

from dataclasses import dataclass, field

# A hand-typed exact match (ID, code, or exact email) is maximum confidence.
EXACT_MATCH_SCORE = 100.0

# Final blended confidence (0-100) below this is dropped entirely - it's
# not useful enough to show the user as a candidate.
FINAL_CONFIDENCE_FLOOR = 35.0

# Result shaping defaults (routers may allow the caller to override
# `limit` up to MAX_RESULT_LIMIT via a query parameter).
DEFAULT_RESULT_LIMIT = 10
MAX_RESULT_LIMIT = 50


def confidence_label(score: float) -> str:
    if score >= 90:
        return "high"
    if score >= 65:
        return "medium"
    return "low"


@dataclass
class RawHit:
    """One matcher's opinion about one record."""

    entity_key: str  # business ID, e.g. student_id / teacher_id
    score: float  # 0-100
    match_type: str  # "exact" | "fuzzy"
    matched_field: str  # which field produced this hit, e.g. "student_name"


@dataclass
class RankedResult:
    entity_key: str
    confidence: float
    confidence_label: str
    match_type: str
    matched_field: str
    signals: list[str] = field(
        default_factory=list,
    )  # e.g. ["exact:email", "fuzzy:student_name"]


def _normalize_score(hit: RawHit) -> float:
    """Puts every matcher's score on the same 0-100 confidence scale."""
    if hit.match_type == "exact":
        return EXACT_MATCH_SCORE
    return max(0.0, min(100.0, hit.score))  # fuzzy is already 0-100


def rank_and_merge(
    hits: list[RawHit],
    *,
    limit: int = DEFAULT_RESULT_LIMIT,
) -> list[RankedResult]:
    """Merges multiple raw hits for the same entity into one ranked list.

    Merge rule: an entity's final confidence is the MAX of its normalized
    signal scores ("the strongest single piece of evidence wins"), not a
    sum/average - this avoids penalizing a record that only matched one
    way versus one matching multiple ways, and avoids inflating
    confidence beyond what any single signal actually supports.

    Never silently collapses duplicate names into one result: each
    distinct entity_key gets its own RankedResult, so two different
    students both named "Mohammad" always both appear.
    """
    best_by_entity: dict[str, RankedResult] = {}

    for hit in hits:
        normalized = _normalize_score(hit)
        signal_label = f"{hit.match_type}:{hit.matched_field}"

        existing = best_by_entity.get(hit.entity_key)
        if existing is None:
            best_by_entity[hit.entity_key] = RankedResult(
                entity_key=hit.entity_key,
                confidence=normalized,
                confidence_label=confidence_label(normalized),
                match_type=hit.match_type,
                matched_field=hit.matched_field,
                signals=[signal_label],
            )
            continue

        existing.signals.append(signal_label)
        if normalized > existing.confidence:
            existing.confidence = normalized
            existing.confidence_label = confidence_label(normalized)
            existing.match_type = hit.match_type
            existing.matched_field = hit.matched_field

    results = [
        r for r in best_by_entity.values() if r.confidence >= FINAL_CONFIDENCE_FLOOR
    ]
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results[:limit]
