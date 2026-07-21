# ============================================================
# app/helpers/search/similarity_engine.py
# ============================================================
#
# The ENTIRE similarity computation lives here, and ONLY here. No
# database code, no API/schema code, no entity-specific knowledge.
#
# This project intentionally does all similarity computation in Python
# (RapidFuzz) rather than in PostgreSQL (pgvector is not used anywhere
# in this codebase - see README "Search Architecture" section). Every
# entity search service (StudentSearchService, TeacherSearchService,
# future ones) pulls a bounded candidate pool from its repository and
# hands it to `rank_candidates` here.
#
# Why RapidFuzz / WRatio:
#   - Pure Python + C extension, no native DB extension, no ML model to
#     download/host, trivial to run anywhere Python runs.
#   - WRatio blends simple ratio, partial ratio, and token-sort ratio,
#     which handles typos, word-order swaps ("Sharma Rahul" vs
#     "Rahul Sharma"), and partial/substring queries well - exactly the
#     shape of "search by name" input real users type.
#
# Swappable by design: everything below this comment is the only place
# that would need to change to swap RapidFuzz for a different algorithm
# (difflib, Levenshtein, cosine-similarity-on-embeddings, ...). No other
# module in the codebase imports rapidfuzz directly.


from rapidfuzz import fuzz, process

from src.domain.search.text_utils import normalize_text

# RapidFuzz WRatio score (0-100) below this is discarded before ranking.
# Chosen to tolerate a couple of typos in a short name while still
# rejecting genuinely unrelated candidates.
FUZZY_MIN_SCORE = 60.0

# Emails share long common substrings (domains: "@gmail.com", etc.), so
# WRatio naturally scores unrelated addresses higher than unrelated
# names would. Use a stricter cutoff for email fuzzy-matching so the
# result list stays meaningfully narrowed instead of "everyone on gmail".
EMAIL_FUZZY_MIN_SCORE = 80.0

# How many raw candidates the fuzzy matcher may contribute before the
# ranking engine merges/sorts everything (keeps things bounded regardless
# of table size - see *_search_repository.py for the query that fills
# this pool from the database).
FUZZY_CANDIDATE_POOL = 200


def rank_candidates(
    query: str,
    candidates: list[tuple[str, str]],
    *,
    limit: int = FUZZY_CANDIDATE_POOL,
    score_cutoff: float = FUZZY_MIN_SCORE,
) -> list[tuple[str, float]]:
    """candidates: list of (entity_key, text_to_match_against).
    Returns list of (entity_key, score 0-100), best first.

    Pure function: no I/O, no side effects, safe to unit test in
    isolation from the database.
    """
    if not query or not candidates:
        return []

    normalized_query = normalize_text(query)
    if not normalized_query:
        return []

    # dict comprehension collapses duplicate entity_keys onto their last
    # text - callers should pass one row per entity_key to avoid this.
    lookup = {key: normalize_text(text) for key, text in candidates if text}
    if not lookup:
        return []

    matches = process.extract(
        normalized_query,
        lookup,
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=score_cutoff,
    )

    # rapidfuzz.process.extract on a dict returns (matched_text, score, key)
    return [(key, score) for (_matched_text, score, key) in matches]
