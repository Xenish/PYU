"""Add approval_status to project_steps."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0015_add_approval_status_to_project_steps"
down_revision = "0014_add_spec_lock_fields_to_projects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "project_steps",
        sa.Column(
            "approval_status",
            sa.Enum("pending", "approved", "rejected", name="approvalstatus"),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    op.drop_column("project_steps", "approval_status")
