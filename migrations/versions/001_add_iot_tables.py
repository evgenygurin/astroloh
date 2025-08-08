"""Add IoT integration tables

Revision ID: 001_add_iot_tables
Revises: 
Create Date: 2025-08-06 08:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001_add_iot_tables"
down_revision: Union[str, None] = "000_create_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create iot_devices table
    op.create_table(
        "iot_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("device_type", sa.String(length=50), nullable=False),
        sa.Column("protocol", sa.String(length=50), nullable=False),
        sa.Column("manufacturer", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("firmware_version", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("room", sa.String(length=255), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )

    # Create home_automations table
    op.create_table(
        "home_automations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_conditions", sa.JSON(), nullable=True),
        sa.Column("actions", sa.JSON(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=True),
        sa.Column("last_executed", sa.DateTime(), nullable=True),
        sa.Column("execution_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["iot_devices.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create device_data table
    op.create_table(
        "device_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("data_type", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("device_metadata", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["iot_devices.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create wearable_data table
    op.create_table(
        "wearable_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column("sleep_quality", sa.Float(), nullable=True),
        sa.Column("activity_level", sa.Float(), nullable=True),
        sa.Column("stress_level", sa.Float(), nullable=True),
        sa.Column("mood_score", sa.Float(), nullable=True),
        sa.Column("lunar_correlation", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["iot_devices.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for better performance
    op.create_index("idx_iot_devices_user_id", "iot_devices", ["user_id"])
    op.create_index(
        "idx_iot_devices_device_type", "iot_devices", ["device_type"]
    )
    op.create_index("idx_iot_devices_status", "iot_devices", ["status"])
    op.create_index(
        "idx_home_automations_user_id", "home_automations", ["user_id"]
    )
    op.create_index(
        "idx_home_automations_trigger_type",
        "home_automations",
        ["trigger_type"],
    )
    op.create_index("idx_device_data_device_id", "device_data", ["device_id"])
    op.create_index("idx_device_data_timestamp", "device_data", ["timestamp"])
    op.create_index("idx_wearable_data_user_id", "wearable_data", ["user_id"])
    op.create_index(
        "idx_wearable_data_timestamp", "wearable_data", ["timestamp"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_wearable_data_timestamp")
    op.drop_index("idx_wearable_data_user_id")
    op.drop_index("idx_device_data_timestamp")
    op.drop_index("idx_device_data_device_id")
    op.drop_index("idx_home_automations_trigger_type")
    op.drop_index("idx_home_automations_user_id")
    op.drop_index("idx_iot_devices_status")
    op.drop_index("idx_iot_devices_device_type")
    op.drop_index("idx_iot_devices_user_id")

    # Drop tables
    op.drop_table("wearable_data")
    op.drop_table("device_data")
    op.drop_table("home_automations")
    op.drop_table("iot_devices")
