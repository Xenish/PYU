"""add epic category

Revision ID: 0003_add_epic_category
Revises: 0002_create_domain_models
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_add_epic_category"
down_revision = "0002_create_domain_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("epics", sa.Column("category", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("epics", "category")
