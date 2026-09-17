"""Added default value for embedding and summary status

Revision ID: 43d0fcde6de5
Revises: e5e4421ce013
Create Date: 2026-09-17 20:46:41.940893
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "43d0fcde6de5"
down_revision: Union[str, Sequence[str], None] = "e5e4421ce013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

jobstatus = sa.Enum(
    "queued",
    "processing",
    "completed",
    "failed",
    name="jobstatus",
)


def upgrade() -> None:
    """Upgrade schema."""

    # Create enum type if it doesn't already exist
    jobstatus.create(op.get_bind(), checkfirst=True)

    # Convert VARCHAR -> ENUM using explicit cast
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status
        TYPE jobstatus
        USING embedding_status::jobstatus
    """)

    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN summary_status
        TYPE jobstatus
        USING summary_status::jobstatus
    """)

    # Set defaults
    op.alter_column(
        "chunks",
        "embedding_status",
        server_default="queued",
        existing_type=jobstatus,
    )

    op.alter_column(
        "chunks",
        "summary_status",
        server_default="queued",
        existing_type=jobstatus,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove defaults
    op.alter_column(
        "chunks",
        "summary_status",
        server_default=None,
        existing_type=jobstatus,
    )

    op.alter_column(
        "chunks",
        "embedding_status",
        server_default=None,
        existing_type=jobstatus,
    )

    # Convert ENUM -> VARCHAR
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN summary_status
        TYPE VARCHAR
        USING summary_status::text
    """)

    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status
        TYPE VARCHAR
        USING embedding_status::text
    """)

    # Drop enum type
    jobstatus.drop(op.get_bind(), checkfirst=True)