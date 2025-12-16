"""add basic indexes"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0013_add_indexes"
down_revision = "0012_add_llm_usage_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_jobs_project_status", "jobs", ["project_id", "status"])
    op.create_index("ix_tasks_sprint_status", "tasks", ["sprint_id", "status"])
    op.create_index("ix_llm_usage_project_date", "llm_usage", ["project_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_llm_usage_project_date", table_name="llm_usage")
    op.drop_index("ix_tasks_sprint_status", table_name="tasks")
    op.drop_index("ix_jobs_project_status", table_name="jobs")
