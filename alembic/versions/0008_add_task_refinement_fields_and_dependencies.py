"""add pass2 task refinement fields and dependency table

Revision ID: 0008_add_task_refinement_fields_and_dependencies
Revises: 0007_update_task_granularity_enum
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0008_add_task_refinement_fields_and_dependencies"
down_revision = "0007_update_task_granularity_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("dod_focus", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("nfr_focus", sa.JSON(), nullable=True))

    op.create_table(
        "task_dependencies",
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "depends_on_task_id",
            sa.Integer(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("task_dependencies")
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("nfr_focus")
        batch_op.drop_column("dod_focus")
