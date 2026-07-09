"""add general purpose subagent flag

Revision ID: 20260708_add_general_purpose_subagent
Revises: 20260707_subagent_fields
Create Date: 2026-07-08
"""

import sqlalchemy as sa
from alembic import op


revision = "20260708_add_general_purpose_subagent"
down_revision = "20260707_subagent_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("enable_general_purpose_subagent", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("enable_general_purpose_subagent")
