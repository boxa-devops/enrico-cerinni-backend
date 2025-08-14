"""add_telegram_chat_id_to_clients

Revision ID: 2a1e9c1d9f3a
Revises: 98502dc54697
Create Date: 2025-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a1e9c1d9f3a'
down_revision: Union[str, None] = '98502dc54697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('telegram_chat_id', sa.String(length=64), nullable=True))
    op.create_index('ix_clients_telegram_chat_id', 'clients', ['telegram_chat_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_clients_telegram_chat_id', table_name='clients')
    op.drop_column('clients', 'telegram_chat_id')


