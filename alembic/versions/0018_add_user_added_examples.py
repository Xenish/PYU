"""add user_added_examples to project_suggestions

Revision ID: 0018_add_user_added_examples
Revises: 0017_add_project_suggestions_table
Create Date: 2025-12-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0018_add_user_added_examples'
down_revision: Union[str, None] = '0017_add_project_suggestions_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project_suggestions",
        sa.Column("user_added_examples", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("project_suggestions", "user_added_examples")
