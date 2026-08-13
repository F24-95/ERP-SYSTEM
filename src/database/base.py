# This file ensures all SQLAlchemy model modules are imported so that:
#   1) Alembic can detect every table for autogeneration
#   2) String-based relationship() references resolve at mapper-config time
#
# Scripts that run outside the FastAPI app (e.g. seed scripts) must
# import this module before executing any query so that every model
# is registered on Base.metadata before the first mapper configuration.
#
# ORDER SAFETY: circular imports exist (curriculum ↔ academics,
# curriculum ↔ khan_academy, users → curriculum) but are handled
# safely because all domains define their classes before any other
# domain tries to import from them.

import src.domain.academics.models  # noqa: F401
import src.domain.assignments.models  # noqa: F401
import src.domain.attachments.models  # noqa: F401
import src.domain.auth.models  # noqa: F401
import src.domain.chat.models  # noqa: F401
import src.domain.curriculum.models  # noqa: F401
import src.domain.exams.models  # noqa: F401
import src.domain.fees.models  # noqa: F401
import src.domain.id_cards.models  # noqa: F401
import src.domain.khan_academy.models  # noqa: F401
import src.domain.notices.models  # noqa: F401
import src.domain.operations.models  # noqa: F401
import src.domain.reports.models  # noqa: F401
import src.domain.study_material.models  # noqa: F401
import src.domain.users.models  # noqa: F401
import src.domain.zoom.models  # noqa: F401
