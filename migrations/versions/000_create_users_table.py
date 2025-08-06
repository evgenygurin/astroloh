"""Create users table

Revision ID: 000_create_users_table
Revises: 
Create Date: 2025-08-06 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '000_create_users_table'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('yandex_user_id', sa.String(length=255), nullable=True),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=True),
        sa.Column('google_user_id', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('birth_time', sa.Time(), nullable=True),
        sa.Column('birth_location', sa.String(length=500), nullable=True),
        sa.Column('timezone', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('zodiac_sign', sa.String(length=50), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('data_consent', sa.Boolean(), nullable=True, default=False),
        sa.Column('consent_date', sa.DateTime(), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=True, default=365),
        sa.Column('processing_restricted', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('yandex_user_id'),
        sa.UniqueConstraint('telegram_user_id'),
        sa.UniqueConstraint('google_user_id'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes for better performance
    op.create_index('idx_users_yandex_user_id', 'users', ['yandex_user_id'])
    op.create_index('idx_users_telegram_user_id', 'users', ['telegram_user_id'])
    op.create_index('idx_users_google_user_id', 'users', ['google_user_id'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_data_consent', 'users', ['data_consent'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_last_activity', 'users', ['last_activity'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_users_last_activity')
    op.drop_index('idx_users_created_at')
    op.drop_index('idx_users_data_consent')
    op.drop_index('idx_users_is_active')
    op.drop_index('idx_users_google_user_id')
    op.drop_index('idx_users_telegram_user_id')
    op.drop_index('idx_users_yandex_user_id')
    op.drop_index('idx_users_email')
    
    # Drop table
    op.drop_table('users')