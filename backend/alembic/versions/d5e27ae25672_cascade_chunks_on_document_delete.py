"""cascade chunks on document delete

Revision ID: d5e27ae25672
Revises: d9ec23b8a007
Create Date: 2026-09-21 17:59:23.084680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e27ae25672'
down_revision: Union[str, Sequence[str], None] = 'd9ec23b8a007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
