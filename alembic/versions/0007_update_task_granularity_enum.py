"""update task granularity enum to coarse/medium/fine

Revision ID: 0007_update_task_granularity_enum
Revises: 0006_update_task_fields
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0007_update_task_granularity_enum"
down_revision = "0006_update_task_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # normalize old value before tightening enum
    op.execute(
        "UPDATE tasks SET granularity='fine' WHERE granularity='atomic'"
    )
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "granularity",
            existing_type=sa.Enum("coarse", "atomic", name="taskgranularity"),
            type_=sa.Enum("coarse", "medium", "fine", name="taskgranularity"),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "granularity",
            existing_type=sa.Enum("coarse", "medium", "fine", name="taskgranularity"),
            type_=sa.Enum("coarse", "atomic", name="taskgranularity"),
            existing_nullable=True,
        )
