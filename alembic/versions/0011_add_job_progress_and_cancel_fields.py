"""add job progress and cancel fields

Revision ID: 0011_add_job_progress_and_cancel_fields
Revises: 0010_add_jobs_table
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0011_add_job_progress_and_cancel_fields"
down_revision = "0010_add_jobs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("progress_pct", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("current_step", sa.String(length=64), nullable=True))
        batch_op.add_column(
            sa.Column("cancellation_requested", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("locked_at")
        batch_op.drop_column("cancellation_requested")
        batch_op.drop_column("current_step")
        batch_op.drop_column("progress_pct")
