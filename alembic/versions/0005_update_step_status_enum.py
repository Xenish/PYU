"""update step status enum values

Revision ID: 0005_update_step_status_enum
Revises: 0004_add_story_points_capacity
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa

revision = "0005_update_step_status_enum"
down_revision = "0004_add_story_points_capacity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For SQLite, Enum is stored as CHECK on strings; update values to new set.
    with op.batch_alter_table("project_steps") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum(
                "not_started",
                "draft",
                "awaiting_approval",
                "approved",
                "stale",
                name="stepstatus",
            ),
            type_=sa.Enum(
                "planned",
                "in_progress",
                "completed",
                "stale",
                "locked",
                "failed",
                name="stepstatus",
            ),
            existing_nullable=False,
            nullable=False,
            server_default="planned",
        )
    # Attempt to map existing rows to new statuses
    op.execute(
        """
        UPDATE project_steps
        SET status = CASE status
            WHEN 'not_started' THEN 'planned'
            WHEN 'draft' THEN 'in_progress'
            WHEN 'awaiting_approval' THEN 'in_progress'
            WHEN 'approved' THEN 'completed'
            ELSE status
        END
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("project_steps") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum(
                "planned",
                "in_progress",
                "completed",
                "stale",
                "locked",
                "failed",
                name="stepstatus",
            ),
            type_=sa.Enum(
                "not_started",
                "draft",
                "awaiting_approval",
                "approved",
                "stale",
                name="stepstatus",
            ),
            existing_nullable=False,
        )
