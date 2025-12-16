"""update task fields and status enum

Revision ID: 0006_update_task_fields
Revises: 0005_update_step_status_enum
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0006_update_task_fields"
down_revision = "0005_update_step_status_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # status enum extend
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum("todo", "in_progress", "done", name="taskstatus"),
            type_=sa.Enum(
                "todo", "in_progress", "done", "blocked", "ready_for_dev", name="taskstatus"
            ),
            existing_nullable=False,
            server_default="todo",
        )
        batch_op.add_column(sa.Column("project_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("order_index", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("order_index")
        batch_op.drop_column("project_id")
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum(
                "todo", "in_progress", "done", "blocked", "ready_for_dev", name="taskstatus"
            ),
            type_=sa.Enum("todo", "in_progress", "done", name="taskstatus"),
            existing_nullable=False,
        )
