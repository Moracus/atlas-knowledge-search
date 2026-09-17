"""Added default value for embedding and summary status bug fix

Revision ID: 03bdac07732a
Revises: 43d0fcde6de5
Create Date: 2026-09-17 21:03:30.737345
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "03bdac07732a"
down_revision: Union[str, Sequence[str], None] = "43d0fcde6de5"
branch_labels = None
depends_on = None

old_enum = postgresql.ENUM(
    "queued", "processing", "completed", "failed",
    name="jobstatus"
)

new_enum = postgresql.ENUM(
    "pending", "processing", "completed", "failed",
    name="processingstatus"
)


def upgrade() -> None:
    # Create new enum
    new_enum.create(op.get_bind(), checkfirst=True)

    # Drop old defaults before type change
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status DROP DEFAULT,
        ALTER COLUMN summary_status DROP DEFAULT
    """)

    # Convert values + enum type
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status TYPE processingstatus
        USING (
            CASE embedding_status::text
                WHEN 'queued' THEN 'pending'
                ELSE embedding_status::text
            END
        )::processingstatus
    """)

    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN summary_status TYPE processingstatus
        USING (
            CASE summary_status::text
                WHEN 'queued' THEN 'pending'
                ELSE summary_status::text
            END
        )::processingstatus
    """)

    # New defaults
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status SET DEFAULT 'pending'::processingstatus,
        ALTER COLUMN summary_status SET DEFAULT 'pending'::processingstatus
    """)


def downgrade() -> None:
   

    # Drop defaults
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status DROP DEFAULT,
        ALTER COLUMN summary_status DROP DEFAULT
    """)

    # Convert back
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status TYPE jobstatus
        USING (
            CASE embedding_status::text
                WHEN 'pending' THEN 'queued'
                ELSE embedding_status::text
            END
        )::jobstatus
    """)

    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN summary_status TYPE jobstatus
        USING (
            CASE summary_status::text
                WHEN 'pending' THEN 'queued'
                ELSE summary_status::text
            END
        )::jobstatus
    """)

    # Restore defaults
    op.execute("""
        ALTER TABLE chunks
        ALTER COLUMN embedding_status SET DEFAULT 'queued'::jobstatus,
        ALTER COLUMN summary_status SET DEFAULT 'queued'::jobstatus
    """)
