"""add story points and capacity fields

Revision ID: 0004_add_story_points_capacity
Revises: 0003_add_epic_category
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0004_add_story_points_capacity"
down_revision = "0003_add_epic_category"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("epics", sa.Column("story_points", sa.Integer(), nullable=True))
    op.add_column("sprints", sa.Column("capacity_sp", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("sprints", "capacity_sp")
    op.drop_column("epics", "story_points")
