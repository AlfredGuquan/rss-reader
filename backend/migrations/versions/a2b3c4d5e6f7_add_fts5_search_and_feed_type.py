"""add fts5 search and feed type columns

Revision ID: a2b3c4d5e6f7
Revises: 961476f54aed
Create Date: 2026-02-10 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = '961476f54aed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add feed_type and email_account_id to feeds
    with op.batch_alter_table('feeds') as batch_op:
        batch_op.add_column(sa.Column('feed_type', sa.String(), server_default='rss', nullable=False))
        batch_op.add_column(sa.Column('email_account_id', sa.String(), nullable=True))

    # Create email_accounts table
    op.create_table(
        'email_accounts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('email_address', sa.String(), nullable=False),
        sa.Column('app_password', sa.String(), nullable=False),
        sa.Column('imap_host', sa.String(), server_default='imap.gmail.com', nullable=False),
        sa.Column('imap_port', sa.Integer(), server_default='993', nullable=False),
        sa.Column('label', sa.String(), server_default='Newsletters', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # FTS5 virtual table + triggers
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            entry_id UNINDEXED, title, content, tokenize='unicode61'
        )
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_fts_insert AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(entry_id, title, content)
            VALUES (NEW.id, NEW.title, COALESCE(NEW.content, NEW.summary, ''));
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_fts_update AFTER UPDATE OF title, content, summary ON entries BEGIN
            DELETE FROM entries_fts WHERE entry_id = OLD.id;
            INSERT INTO entries_fts(entry_id, title, content)
            VALUES (NEW.id, NEW.title, COALESCE(NEW.content, NEW.summary, ''));
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_fts_delete AFTER DELETE ON entries BEGIN
            DELETE FROM entries_fts WHERE entry_id = OLD.id;
        END
    """)
    # Backfill existing data
    op.execute("""
        INSERT INTO entries_fts(entry_id, title, content)
        SELECT id, title, COALESCE(content, summary, '') FROM entries
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS entries_fts_delete")
    op.execute("DROP TRIGGER IF EXISTS entries_fts_update")
    op.execute("DROP TRIGGER IF EXISTS entries_fts_insert")
    op.execute("DROP TABLE IF EXISTS entries_fts")
    op.drop_table('email_accounts')
    with op.batch_alter_table('feeds') as batch_op:
        batch_op.drop_column('email_account_id')
        batch_op.drop_column('feed_type')
