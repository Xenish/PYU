"""Add decision support fields to all item types."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = "0016_add_decision_support_fields"
down_revision = "0015_add_approval_status_to_project_steps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add decision support fields to project_objectives
    op.add_column("project_objectives", sa.Column("priority_score", sa.Integer(), nullable=True))
    op.add_column("project_objectives", sa.Column("impact_level", sa.String(20), nullable=True))
    op.add_column("project_objectives", sa.Column("recommendation_type", sa.String(20), nullable=True))
    op.add_column("project_objectives", sa.Column("category_tags", sa.JSON(), nullable=True))
    op.add_column("project_objectives", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("project_objectives", sa.Column("advantages", sa.JSON(), nullable=True))
    op.add_column("project_objectives", sa.Column("disadvantages", sa.JSON(), nullable=True))
    op.add_column("project_objectives", sa.Column("conflicts_with", sa.JSON(), nullable=True))
    op.add_column("project_objectives", sa.Column("requires", sa.JSON(), nullable=True))
    op.add_column("project_objectives", sa.Column("category_exclusive", sa.Boolean(), nullable=False, server_default="0"))

    # Add decision support fields to tech_stack_options
    op.add_column("tech_stack_options", sa.Column("priority_score", sa.Integer(), nullable=True))
    op.add_column("tech_stack_options", sa.Column("impact_level", sa.String(20), nullable=True))
    op.add_column("tech_stack_options", sa.Column("recommendation_type", sa.String(20), nullable=True))
    op.add_column("tech_stack_options", sa.Column("category_tags", sa.JSON(), nullable=True))
    op.add_column("tech_stack_options", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("tech_stack_options", sa.Column("advantages", sa.JSON(), nullable=True))
    op.add_column("tech_stack_options", sa.Column("disadvantages", sa.JSON(), nullable=True))
    op.add_column("tech_stack_options", sa.Column("conflicts_with", sa.JSON(), nullable=True))
    op.add_column("tech_stack_options", sa.Column("requires", sa.JSON(), nullable=True))
    op.add_column("tech_stack_options", sa.Column("category_exclusive", sa.Boolean(), nullable=False, server_default="0"))

    # Add decision support fields to features
    op.add_column("features", sa.Column("priority_score", sa.Integer(), nullable=True))
    op.add_column("features", sa.Column("impact_level", sa.String(20), nullable=True))
    op.add_column("features", sa.Column("recommendation_type", sa.String(20), nullable=True))
    op.add_column("features", sa.Column("category_tags", sa.JSON(), nullable=True))
    op.add_column("features", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("features", sa.Column("advantages", sa.JSON(), nullable=True))
    op.add_column("features", sa.Column("disadvantages", sa.JSON(), nullable=True))
    op.add_column("features", sa.Column("conflicts_with", sa.JSON(), nullable=True))
    op.add_column("features", sa.Column("requires", sa.JSON(), nullable=True))
    op.add_column("features", sa.Column("category_exclusive", sa.Boolean(), nullable=False, server_default="0"))

    # Add decision support fields to architecture_components
    op.add_column("architecture_components", sa.Column("priority_score", sa.Integer(), nullable=True))
    op.add_column("architecture_components", sa.Column("impact_level", sa.String(20), nullable=True))
    op.add_column("architecture_components", sa.Column("recommendation_type", sa.String(20), nullable=True))
    op.add_column("architecture_components", sa.Column("category_tags", sa.JSON(), nullable=True))
    op.add_column("architecture_components", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("architecture_components", sa.Column("advantages", sa.JSON(), nullable=True))
    op.add_column("architecture_components", sa.Column("disadvantages", sa.JSON(), nullable=True))
    op.add_column("architecture_components", sa.Column("conflicts_with", sa.JSON(), nullable=True))
    op.add_column("architecture_components", sa.Column("requires", sa.JSON(), nullable=True))
    op.add_column("architecture_components", sa.Column("category_exclusive", sa.Boolean(), nullable=False, server_default="0"))

    # Add decision support fields to dod_items
    op.add_column("dod_items", sa.Column("priority_score", sa.Integer(), nullable=True))
    op.add_column("dod_items", sa.Column("impact_level", sa.String(20), nullable=True))
    op.add_column("dod_items", sa.Column("recommendation_type", sa.String(20), nullable=True))
    op.add_column("dod_items", sa.Column("category_tags", sa.JSON(), nullable=True))
    op.add_column("dod_items", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("dod_items", sa.Column("advantages", sa.JSON(), nullable=True))
    op.add_column("dod_items", sa.Column("disadvantages", sa.JSON(), nullable=True))
    op.add_column("dod_items", sa.Column("conflicts_with", sa.JSON(), nullable=True))
    op.add_column("dod_items", sa.Column("requires", sa.JSON(), nullable=True))
    op.add_column("dod_items", sa.Column("category_exclusive", sa.Boolean(), nullable=False, server_default="0"))

    # Add decision support fields to nfr_items
    op.add_column("nfr_items", sa.Column("priority_score", sa.Integer(), nullable=True))
    op.add_column("nfr_items", sa.Column("impact_level", sa.String(20), nullable=True))
    op.add_column("nfr_items", sa.Column("recommendation_type", sa.String(20), nullable=True))
    op.add_column("nfr_items", sa.Column("category_tags", sa.JSON(), nullable=True))
    op.add_column("nfr_items", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("nfr_items", sa.Column("advantages", sa.JSON(), nullable=True))
    op.add_column("nfr_items", sa.Column("disadvantages", sa.JSON(), nullable=True))
    op.add_column("nfr_items", sa.Column("conflicts_with", sa.JSON(), nullable=True))
    op.add_column("nfr_items", sa.Column("requires", sa.JSON(), nullable=True))
    op.add_column("nfr_items", sa.Column("category_exclusive", sa.Boolean(), nullable=False, server_default="0"))

    # Add decision support fields to risk_items
    op.add_column("risk_items", sa.Column("priority_score", sa.Integer(), nullable=True))
    op.add_column("risk_items", sa.Column("impact_level", sa.String(20), nullable=True))
    op.add_column("risk_items", sa.Column("recommendation_type", sa.String(20), nullable=True))
    op.add_column("risk_items", sa.Column("category_tags", sa.JSON(), nullable=True))
    op.add_column("risk_items", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column("risk_items", sa.Column("advantages", sa.JSON(), nullable=True))
    op.add_column("risk_items", sa.Column("disadvantages", sa.JSON(), nullable=True))
    op.add_column("risk_items", sa.Column("conflicts_with", sa.JSON(), nullable=True))
    op.add_column("risk_items", sa.Column("requires", sa.JSON(), nullable=True))
    op.add_column("risk_items", sa.Column("category_exclusive", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    # Remove decision support fields from all tables
    tables = [
        "project_objectives",
        "tech_stack_options",
        "features",
        "architecture_components",
        "dod_items",
        "nfr_items",
        "risk_items",
    ]

    columns = [
        "priority_score",
        "impact_level",
        "recommendation_type",
        "category_tags",
        "rationale",
        "advantages",
        "disadvantages",
        "conflicts_with",
        "requires",
        "category_exclusive",
    ]

    for table in tables:
        for column in columns:
            op.drop_column(table, column)
