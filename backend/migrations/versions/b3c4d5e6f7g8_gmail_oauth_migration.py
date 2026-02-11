"""migrate email_accounts from IMAP to Gmail OAuth

Revision ID: b3c4d5e6f7g8
Revises: a2b3c4d5e6f7
Create Date: 2026-02-11 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3c4d5e6f7g8'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('email_accounts') as batch_op:
        batch_op.add_column(sa.Column('oauth_refresh_token', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('oauth_access_token', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('oauth_token_expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('gmail_label', sa.String(), server_default='Newsletters', nullable=False))
        batch_op.drop_column('app_password')
        batch_op.drop_column('imap_host')
        batch_op.drop_column('imap_port')
        batch_op.drop_column('label')


def downgrade() -> None:
    with op.batch_alter_table('email_accounts') as batch_op:
        batch_op.add_column(sa.Column('label', sa.String(), server_default='Newsletters', nullable=False))
        batch_op.add_column(sa.Column('imap_port', sa.Integer(), server_default='993', nullable=False))
        batch_op.add_column(sa.Column('imap_host', sa.String(), server_default='imap.gmail.com', nullable=False))
        batch_op.add_column(sa.Column('app_password', sa.String(), nullable=True))
        batch_op.drop_column('gmail_label')
        batch_op.drop_column('oauth_token_expires_at')
        batch_op.drop_column('oauth_access_token')
        batch_op.drop_column('oauth_refresh_token')
