"""Backward-compatible shim. The actual generator implementations now live in
`src.core.id_generators` (the single source of truth, ported verbatim from
the legacy project). This module re-exports the three that were already in
use so existing imports (`from src.core.utils import generate_student_id`)
keep working unchanged.

NOTE: the previous version of this file generated IDs as f"{PREFIX}-{id:05d}"
(e.g. "STU-00001"). The legacy project's actual format has no dash
(e.g. "STU00001"). That was a silent business-ID format break — fixed here
by delegating to id_generators.py, which matches the legacy format exactly.
"""

from src.core.id_generators import (
    generate_admin_id,
    generate_business_id,  # kept for compatibility if referenced elsewhere
    generate_student_id,
    generate_teacher_id,
)

__all__ = [
    "generate_admin_id",
    "generate_business_id",
    "generate_student_id",
    "generate_teacher_id",
]
