"""add project suggestions table

Revision ID: 0017
Revises: 0016
Create Date: 2025-12-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0017_add_project_suggestions_table'
down_revision: Union[str, None] = '0016_add_decision_support_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("examples", sa.JSON(), nullable=True),
        sa.Column("is_selected", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("generation_round", sa.Integer(), server_default="1", nullable=False),
        # Decision support fields from EnhancedItemMixin
        sa.Column("priority_score", sa.Integer(), nullable=True),
        sa.Column("impact_level", sa.String(20), nullable=True),
        sa.Column("recommendation_type", sa.String(20), nullable=True),
        sa.Column("category_tags", sa.JSON(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("advantages", sa.JSON(), nullable=True),
        sa.Column("disadvantages", sa.JSON(), nullable=True),
        sa.Column("conflicts_with", sa.JSON(), nullable=True),
        sa.Column("requires", sa.JSON(), nullable=True),
        sa.Column("category_exclusive", sa.Boolean(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_suggestions_project_id", "project_suggestions", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_suggestions_project_id", "project_suggestions")
    op.drop_table("project_suggestions")
