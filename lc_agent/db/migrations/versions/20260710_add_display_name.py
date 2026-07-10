"""add display_name to agent_presets

Revision ID: 20260710_add_display_name
Revises: 20260708_add_general_purpose_subagent
Create Date: 2026-07-10
"""

import sqlalchemy as sa
from alembic import op


revision = "20260710_add_display_name"
down_revision = "20260708_add_general_purpose_subagent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(), nullable=True))
    op.execute("UPDATE agent_presets SET display_name = name WHERE display_name IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("display_name")
