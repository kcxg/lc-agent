"""add can_be_mcp to agent_presets

Revision ID: 20260910_add_can_be_mcp
Revises: 20260909_unique_preset_name
Create Date: 2026-09-10
"""

import sqlalchemy as sa
from alembic import op


revision = "20260910_add_can_be_mcp"
down_revision = "20260909_unique_preset_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(
            sa.Column("can_be_mcp", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("can_be_mcp")
