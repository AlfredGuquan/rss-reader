"""add simhash dedup fields

Revision ID: e6f7g8h9i0j1
Revises: 99008f5ecdaa
Create Date: 2026-02-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6f7g8h9i0j1"
down_revision: Union[str, None] = "99008f5ecdaa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("entries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("simhash_title", sa.String(16), nullable=True))
        batch_op.add_column(sa.Column("simhash_content", sa.String(16), nullable=True))
        batch_op.add_column(sa.Column("duplicate_of_id", sa.Uuid(), nullable=True))
        batch_op.create_index("ix_entries_simhash_title", ["simhash_title"])
        batch_op.create_index("ix_entries_duplicate_of_id", ["duplicate_of_id"])
        batch_op.create_foreign_key(
            "fk_entries_duplicate_of_id",
            "entries",
            ["duplicate_of_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("entries", schema=None) as batch_op:
        batch_op.drop_constraint("fk_entries_duplicate_of_id", type_="foreignkey")
        batch_op.drop_index("ix_entries_duplicate_of_id")
        batch_op.drop_index("ix_entries_simhash_title")
        batch_op.drop_column("duplicate_of_id")
        batch_op.drop_column("simhash_content")
        batch_op.drop_column("simhash_title")
