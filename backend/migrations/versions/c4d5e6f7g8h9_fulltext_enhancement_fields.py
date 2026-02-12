"""add fulltext enhancement fields to feeds and entries

Revision ID: c4d5e6f7g8h9
Revises: b3c4d5e6f7g8
Create Date: 2026-02-12 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c4d5e6f7g8h9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Feed: add fulltext_config column
    with op.batch_alter_table('feeds') as batch_op:
        batch_op.add_column(sa.Column('fulltext_config', sa.Text(), nullable=True))

    # Entry: add cascade extraction tracking columns
    with op.batch_alter_table('entries') as batch_op:
        batch_op.add_column(
            sa.Column('content_fetch_status', sa.String(), server_default='pending', nullable=False)
        )
        batch_op.add_column(sa.Column('content_fetch_error', sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column('content_fetch_retries', sa.Integer(), server_default='0', nullable=False)
        )
        batch_op.add_column(sa.Column('extraction_method', sa.String(), nullable=True))

    # Data migration: sync content_fetch_status from existing content_fetched boolean
    op.execute("UPDATE entries SET content_fetch_status = 'success' WHERE content_fetched = 1")
    op.execute("UPDATE entries SET content_fetch_status = 'pending' WHERE content_fetched = 0")


def downgrade() -> None:
    with op.batch_alter_table('entries') as batch_op:
        batch_op.drop_column('extraction_method')
        batch_op.drop_column('content_fetch_retries')
        batch_op.drop_column('content_fetch_error')
        batch_op.drop_column('content_fetch_status')

    with op.batch_alter_table('feeds') as batch_op:
        batch_op.drop_column('fulltext_config')
