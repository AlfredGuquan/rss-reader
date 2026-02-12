"""add platform detection fields to feeds and entries

Revision ID: d5e6f7g8h9i0
Revises: b3c4d5e6f7g8
Create Date: 2026-02-12 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd5e6f7g8h9i0'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('feeds', recreate='auto') as batch_op:
        batch_op.add_column(sa.Column('source_platform', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('source_identifier', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('filter_rules', sa.Text(), nullable=True))

    with op.batch_alter_table('entries', recreate='auto') as batch_op:
        batch_op.add_column(sa.Column('extra_metadata', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('entries', recreate='auto') as batch_op:
        batch_op.drop_column('extra_metadata')

    with op.batch_alter_table('feeds', recreate='auto') as batch_op:
        batch_op.drop_column('filter_rules')
        batch_op.drop_column('source_identifier')
        batch_op.drop_column('source_platform')
