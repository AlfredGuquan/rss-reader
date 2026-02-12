"""merge_batch2_fulltext_and_nonrss

Revision ID: 99008f5ecdaa
Revises: c4d5e6f7g8h9, d5e6f7g8h9i0
Create Date: 2026-02-12 11:11:57.536468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99008f5ecdaa'
down_revision: Union[str, Sequence[str], None] = ('c4d5e6f7g8h9', 'd5e6f7g8h9i0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
