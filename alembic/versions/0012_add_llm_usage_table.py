"""add llm usage table

Revision ID: 0012_add_llm_usage_table
Revises: 0011_add_job_progress_and_cancel_fields
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0012_add_llm_usage_table"
down_revision = "0011_add_job_progress_and_cancel_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_usage",
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("date", sa.Date(), primary_key=True),
        sa.Column("call_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("llm_usage")
