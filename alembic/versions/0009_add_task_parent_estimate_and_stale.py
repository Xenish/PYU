"""add parent task, estimate_sp and stale status

Revision ID: 0009_add_task_parent_estimate_and_stale
Revises: 0008_add_task_refinement_fields_and_dependencies
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0009_add_task_parent_estimate_and_stale"
down_revision = "0008_add_task_refinement_fields_and_dependencies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum(
                "todo", "in_progress", "done", "blocked", "ready_for_dev", name="taskstatus"
            ),
            type_=sa.Enum(
                "todo", "in_progress", "done", "blocked", "ready_for_dev", "stale", name="taskstatus"
            ),
            existing_nullable=False,
            server_default="todo",
        )
        batch_op.add_column(sa.Column("parent_task_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("estimate_sp", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tasks_parent_task_id_tasks",
            "tasks",
            ["parent_task_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    op.drop_constraint("fk_tasks_parent_task_id", "tasks", type_="foreignkey")
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint("fk_tasks_parent_task_id_tasks", type_="foreignkey")
        batch_op.drop_column("estimate_sp")
        batch_op.drop_column("parent_task_id")
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum(
                "todo", "in_progress", "done", "blocked", "ready_for_dev", "stale", name="taskstatus"
            ),
            type_=sa.Enum(
                "todo", "in_progress", "done", "blocked", "ready_for_dev", name="taskstatus"
            ),
            existing_nullable=False,
        )
