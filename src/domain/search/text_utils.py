# ============================================================
# app/helpers/search/text_utils.py
# ============================================================
#
# Pure text utilities shared by every *_search_service.py:
#   - normalize_text():   canonical form used for comparisons/hashing
#   - build_search_text(): concatenates several entity fields into one
#                          blob used as the fuzzy-match target
#   - classify_query():   decides whether the user typed a name or an
#                          email, so the repository/service layer never
#                          has to ask the caller to pick a mode
#
# No SQLAlchemy, no FastAPI, no entity-specific knowledge here.

import re
import unicodedata
from enum import Enum

# A deliberately permissive "does this look like an email" check, used
# only to decide WHICH fields to prioritise when searching - not to
# accept/reject the request. Strict RFC validation happens in
# app/helpers/validators.py::Validators.validate_email when we actually
# need a pass/fail verdict (e.g. before writing an email to the DB).
_EMAIL_LOOKALIKE_RE = re.compile(r"^[^\s@]+@[^\s@]+$")
_STRICT_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class QueryType(str, Enum):
    EMAIL = "email"
    NAME_OR_CODE = "name_or_code"


def normalize_text(value: str | None) -> str:
    """Trim, lowercase, strip accents, collapse whitespace, unicode-normalize.

    e.g. "  Zoë   Sharma " -> "zoe sharma"

    Used everywhere a fair, case/whitespace/accent-insensitive comparison
    is needed (exact-match filters, fuzzy-match input, content hashing).
    """
    if not value:
        return ""

    # NFKD then strip combining marks -> accent/diacritic removal.
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))

    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)

    return value


def build_search_text(*parts: str | None) -> str:
    """Concatenates multiple entity fields into one normalized blob used
    as the fuzzy-match target (e.g. name + codes + parent name).
    """
    cleaned = [normalize_text(p) for p in parts if p]
    return " | ".join(cleaned)


def looks_like_email(raw_query: str) -> bool:
    """Loose shape check (`something@something`) - used only for routing
    the query to the right matcher, never for accept/reject decisions.
    """
    return bool(_EMAIL_LOOKALIKE_RE.match((raw_query or "").strip()))


def is_valid_email_format(raw_query: str) -> bool:
    """Strict RFC-ish check, used to decide whether an email-shaped query
    is well-formed enough to be worth an exact-match email lookup.
    """
    return bool(_STRICT_EMAIL_RE.match((raw_query or "").strip()))


def classify_query(raw_query: str) -> QueryType:
    """Automatically determines whether the user typed a name/code or an
    email - no manual mode selection required from the caller.
    """
    if looks_like_email(raw_query):
        return QueryType.EMAIL
    return QueryType.NAME_OR_CODE
