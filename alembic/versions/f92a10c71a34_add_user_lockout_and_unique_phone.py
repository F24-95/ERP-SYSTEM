"""add user lockout and unique phone constraint

Revision ID: f92a10c71a34
Revises: e8be2ca4a7a5
Create Date: 2026-08-22 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f92a10c71a34"
down_revision: Union[str, None] = "e8be2ca4a7a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add locked_until column for brute-force protection
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))

    # 2. Update phone index to unique=True and add unique constraint
    op.drop_index("ix_users_phone", table_name="users")
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_unique_constraint("uq_users_phone", "users", ["phone"])


def downgrade() -> None:
    op.drop_constraint("uq_users_phone", "users", type_="unique")
    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.create_index("ix_users_phone", "users", ["phone"], unique=False)
    op.drop_column("users", "locked_until")
