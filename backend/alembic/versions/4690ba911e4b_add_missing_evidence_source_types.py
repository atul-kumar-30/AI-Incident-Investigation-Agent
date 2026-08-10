"""add_missing_evidence_source_types

Revision ID: 4690ba911e4b
Revises: 0cc02233f33e
Create Date: 2026-08-10 14:58:15.820703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4690ba911e4b'
down_revision: Union[str, None] = '0cc02233f33e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'LOG'")
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'METRIC'")
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'TRACE'")
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'CODE'")
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'GIT_CHANGE'")
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'DOCUMENT'")
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'USER'")
        op.execute("ALTER TYPE evidencesourcetype ADD VALUE IF NOT EXISTS 'SYSTEM'")


def downgrade() -> None:
    pass
