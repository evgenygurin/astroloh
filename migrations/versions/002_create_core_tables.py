"""Create core database tables

Revision ID: 002_create_core_tables
Revises: 001_add_iot_tables
Create Date: 2025-08-08 02:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "002_create_core_tables"
down_revision: Union[str, None] = "001_add_iot_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column(
            "current_state",
            sa.String(length=50),
            nullable=False,
            default="initial",
        ),
        sa.Column("context_data", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    # Create horoscope_requests table
    op.create_table(
        "horoscope_requests",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("request_type", sa.String(length=50), nullable=False),
        sa.Column("encrypted_target_date", sa.LargeBinary(), nullable=True),
        sa.Column("encrypted_partner_data", sa.LargeBinary(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create data_deletion_requests table
    op.create_table(
        "data_deletion_requests",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, default="pending"
        ),
        sa.Column("request_reason", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("verification_code", sa.String(length=32), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create security_logs table
    op.create_table(
        "security_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=True),
        sa.Column(
            "communication_style",
            sa.String(length=20),
            nullable=True,
            default="balanced",
        ),
        sa.Column(
            "complexity_level",
            sa.String(length=20),
            nullable=True,
            default="intermediate",
        ),
        sa.Column("preferred_time_slots", sa.JSON(), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        sa.Column("cultural_context", sa.String(length=20), nullable=True),
        sa.Column(
            "language_preference",
            sa.String(length=10),
            nullable=True,
            default="ru",
        ),
        sa.Column(
            "content_length_preference",
            sa.String(length=20),
            nullable=True,
            default="medium",
        ),
        sa.Column(
            "detail_level",
            sa.String(length=20),
            nullable=True,
            default="standard",
        ),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create user_interactions table
    op.create_table(
        "user_interactions",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("interaction_type", sa.String(length=50), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("content_id", sa.String(length=255), nullable=True),
        sa.Column("session_duration", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("astronomical_data", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create recommendations table
    op.create_table(
        "recommendations",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_type", sa.String(length=50), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recommendation_data", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=True, default=1),
        sa.Column("algorithm_used", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=20), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=True, default="active"
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("shown_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create user_clusters table
    op.create_table(
        "user_clusters",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("cluster_id", sa.String(length=50), nullable=False),
        sa.Column("cluster_name", sa.String(length=100), nullable=True),
        sa.Column("cluster_features", sa.JSON(), nullable=True),
        sa.Column("similarity_score", sa.Integer(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create ab_test_groups table
    op.create_table(
        "ab_test_groups",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("test_name", sa.String(length=100), nullable=False),
        sa.Column("group_name", sa.String(length=50), nullable=False),
        sa.Column("test_parameters", sa.JSON(), nullable=True),
        sa.Column("test_start_date", sa.DateTime(), nullable=False),
        sa.Column("test_end_date", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create recommendation_metrics table
    op.create_table(
        "recommendation_metrics",
        sa.Column("id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metric_name", sa.String(length=50), nullable=False),
        sa.Column("metric_value", sa.Integer(), nullable=False),
        sa.Column("context_data", sa.JSON(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for better performance
    op.create_index("idx_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index(
        "idx_user_sessions_session_id", "user_sessions", ["session_id"]
    )
    op.create_index(
        "idx_user_sessions_is_active", "user_sessions", ["is_active"]
    )
    op.create_index(
        "idx_horoscope_requests_user_id", "horoscope_requests", ["user_id"]
    )
    op.create_index(
        "idx_horoscope_requests_type", "horoscope_requests", ["request_type"]
    )
    op.create_index(
        "idx_user_preferences_user_id", "user_preferences", ["user_id"]
    )
    op.create_index(
        "idx_user_interactions_user_id", "user_interactions", ["user_id"]
    )
    op.create_index(
        "idx_user_interactions_type", "user_interactions", ["interaction_type"]
    )
    op.create_index(
        "idx_recommendations_user_id", "recommendations", ["user_id"]
    )
    op.create_index(
        "idx_recommendations_status", "recommendations", ["status"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_recommendations_status")
    op.drop_index("idx_recommendations_user_id")
    op.drop_index("idx_user_interactions_type")
    op.drop_index("idx_user_interactions_user_id")
    op.drop_index("idx_user_preferences_user_id")
    op.drop_index("idx_horoscope_requests_type")
    op.drop_index("idx_horoscope_requests_user_id")
    op.drop_index("idx_user_sessions_is_active")
    op.drop_index("idx_user_sessions_session_id")
    op.drop_index("idx_user_sessions_user_id")

    # Drop tables
    op.drop_table("recommendation_metrics")
    op.drop_table("ab_test_groups")
    op.drop_table("user_clusters")
    op.drop_table("recommendations")
    op.drop_table("user_interactions")
    op.drop_table("user_preferences")
    op.drop_table("security_logs")
    op.drop_table("data_deletion_requests")
    op.drop_table("horoscope_requests")
    op.drop_table("user_sessions")
