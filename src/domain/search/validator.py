from dataclasses import dataclass

from src.core.exceptions import BusinessLogicException
from src.domain.search.text_utils import (
    QueryType,
    classify_query,
    is_valid_email_format,
    normalize_text,
)

MIN_QUERY_LENGTH = 1
MAX_QUERY_LENGTH = 100


@dataclass
class ValidatedQuery:
    raw: str
    cleaned: str
    normalized: str
    query_type: QueryType
    is_well_formed_email: bool


class SearchQueryValidator:
    """Stateless validator, ported verbatim from legacy
    `app/validators/search_validator.py`. Raises `BusinessLogicException`
    (400) in place of legacy's dedicated `SearchValidationError` -- this
    project doesn't have a separate exception class for that, and
    `BusinessLogicException` already maps to the same HTTP 400 legacy used.
    """

    @staticmethod
    def validate(raw_query: str) -> ValidatedQuery:
        if raw_query is None:
            raise BusinessLogicException("Search query is required.")

        if not isinstance(raw_query, str):
            raise BusinessLogicException("Search query must be text.")

        cleaned = "".join(
            ch for ch in raw_query if ch.isprintable() or ch.isspace()
        ).strip()
        cleaned = " ".join(cleaned.split())

        if len(cleaned) < MIN_QUERY_LENGTH:
            raise BusinessLogicException("Search query cannot be empty.")

        if len(cleaned) > MAX_QUERY_LENGTH:
            raise BusinessLogicException(
                f"Search query is too long (max {MAX_QUERY_LENGTH} characters).",
            )

        query_type = classify_query(cleaned)
        is_well_formed_email = (
            is_valid_email_format(cleaned) if query_type == QueryType.EMAIL else False
        )

        return ValidatedQuery(
            raw=raw_query,
            cleaned=cleaned,
            normalized=normalize_text(cleaned),
            query_type=query_type,
            is_well_formed_email=is_well_formed_email,
        )
