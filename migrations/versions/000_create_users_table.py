"""Create users table

Revision ID: 000_create_users_table
Revises: 
Create Date: 2025-08-06 07:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "000_create_users_table"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("yandex_user_id", sa.String(length=255), nullable=False),
        # Encrypted personal data fields
        sa.Column("encrypted_birth_date", sa.LargeBinary(), nullable=True),
        sa.Column("encrypted_birth_time", sa.LargeBinary(), nullable=True),
        sa.Column("encrypted_birth_location", sa.LargeBinary(), nullable=True),
        sa.Column("encrypted_name", sa.LargeBinary(), nullable=True),
        # Unencrypted data fields
        sa.Column("zodiac_sign", sa.String(length=20), nullable=True),
        sa.Column("gender", sa.String(length=10), nullable=True),
        # Privacy settings
        sa.Column("data_consent", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "data_retention_days", sa.Integer(), nullable=False, default=365
        ),
        # User preferences (JSON)
        sa.Column("preferences", sa.JSON(), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("yandex_user_id"),
    )

    # Create indexes for better performance
    op.create_index("idx_users_yandex_user_id", "users", ["yandex_user_id"])
    op.create_index("idx_users_data_consent", "users", ["data_consent"])
    op.create_index("idx_users_created_at", "users", ["created_at"])
    op.create_index("idx_users_last_accessed", "users", ["last_accessed"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_users_last_accessed")
    op.drop_index("idx_users_created_at")
    op.drop_index("idx_users_data_consent")
    op.drop_index("idx_users_yandex_user_id")

    # Drop table
    op.drop_table("users")
