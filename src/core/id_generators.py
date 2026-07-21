"""Business ID / public-code generators.

Ported verbatim (same prefixes, same padding, same random alphabet) from the
legacy project's `app/helpers/code_generators.py` so that IDs produced by
this system are byte-for-byte identical in format to IDs already present in
production data. Do NOT change output formats here without a data migration
plan — these are public, user-facing, permanent identifiers.
"""

import secrets
import string
import uuid

from src.core.enums import (
    ADMIN_PREFIX,
    ASSIGNMENT_PREFIX,
    AVAILABILITY_PREFIX,
    CHAT_PREFIX,
    EXAM_PREFIX,
    FEE_PREFIX,
    MATERIAL_PREFIX,
    NOTICE_PREFIX,
    RECEIPT_PREFIX,
    REGISTRATION_PREFIX,
    STUDENT_PREFIX,
    TEACHER_PREFIX,
    TIMETABLE_PREFIX,
    TOPIC_PREFIX,
    ZOOM_FILE_PREFIX,
)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def random_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ------------------------------------------------------------
# IDs that require the row's own primary key (assigned after
# the row is created/flushed, e.g. in AdminService)
# ------------------------------------------------------------


def generate_student_id(user_id: int) -> str:
    return f"{STUDENT_PREFIX}{user_id:05d}"


def generate_teacher_id(user_id: int) -> str:
    return f"{TEACHER_PREFIX}{user_id:05d}"


def generate_admin_id(user_id: int) -> str:
    return f"{ADMIN_PREFIX}{user_id:06d}"


def generate_business_id(prefix: str, user_id: int, width: int = 5) -> str:
    """Generic fallback for the STU/TEA-style no-dash, zero-padded pattern,
    kept for any call site still referencing the old `utils.generate_business_id`
    name. Prefer the specific generate_*_id functions above.
    """
    return f"{prefix}{user_id:0{width}d}"


# ------------------------------------------------------------
# No-arg generators (random suffix) — used at row-creation time
# ------------------------------------------------------------


def generate_admin_code() -> str:
    return f"{ADMIN_PREFIX}-{random_code(8)}"


def generate_assignment_id() -> str:
    return f"{ASSIGNMENT_PREFIX}-{random_code(8)}"


def generate_material_id() -> str:
    return f"{MATERIAL_PREFIX}-{random_code(8)}"


def generate_notice_code() -> str:
    return f"{NOTICE_PREFIX}-{random_code(8)}"


def generate_assignment_code() -> str:
    return f"{ASSIGNMENT_PREFIX}-{random_code(8)}"


def generate_exam_code() -> str:
    return f"{EXAM_PREFIX}-{random_code(8)}"


def generate_fee_code() -> str:
    return f"{FEE_PREFIX}-{random_code(8)}"


def generate_receipt_no() -> str:
    return f"{RECEIPT_PREFIX}-{random_code(10)}"


def generate_chat_room_id() -> str:
    return f"{CHAT_PREFIX}-{random_code(8)}"


def generate_topic_id() -> str:
    return f"{TOPIC_PREFIX}-{random_code(8)}"


def generate_zoom_file_id() -> str:
    return f"{ZOOM_FILE_PREFIX}-{random_code(8)}"


def generate_timetable_id(academic_sessions_id: int, sequence: int) -> str:
    return f"{TIMETABLE_PREFIX}-{academic_sessions_id}-{sequence:06d}"


def generate_availability_id(academic_sessions_id: int, sequence: int) -> str:
    return f"{AVAILABILITY_PREFIX}-{academic_sessions_id}-{sequence:06d}"


def generate_session_name(start_year: int, end_year: int) -> str:
    return f"{start_year}-{str(end_year)[-2:]}"


def generate_subject_code(subject_name: str, class_name: str) -> str:
    words = subject_name.upper().split()
    if len(words) == 1:
        prefix = words[0][:2]
    else:
        prefix = "".join(word[0] for word in words)[:2]
    digits = "".join(filter(str.isdigit, class_name))
    return f"{prefix}{digits}"


def generate_registration_number(year: int, sequence: int) -> str:
    """e.g. REG-2026-00001. `sequence` must be caller-computed (collision-safe
    generation loop lives in the registration-number service) — this
    function only formats it.
    """
    return f"{REGISTRATION_PREFIX}-{year}-{sequence:05d}"
