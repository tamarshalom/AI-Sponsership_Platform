"""IVFFlat index on sponsors.embedding for cosine search.

Revision ID: 20260407_0002
Revises: 20260407_0001
Create Date: 2026-04-07
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260407_0002"
down_revision: Union[str, None] = "20260407_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # lists=10 is reasonable for small dev datasets; increase for production scale.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sponsors_embedding_ivfflat
        ON sponsors
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_sponsors_embedding_ivfflat", table_name="sponsors")
