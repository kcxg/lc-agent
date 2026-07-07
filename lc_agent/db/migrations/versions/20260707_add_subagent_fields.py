"""Add subagent_ids and subsession fields

Revision ID: 20260707_subagent_fields
"""
import sqlalchemy as sa
from alembic import op

revision = "20260707_subagent_fields"
down_revision = "20260706_add_llm_params"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("subagent_ids", sa.JSON(), nullable=True))

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("parent_session_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("tool_call_id", sa.String(), nullable=True))
        batch_op.create_index("ix_sessions_parent_session_id", ["parent_session_id"])


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_index("ix_sessions_parent_session_id")
        batch_op.drop_column("tool_call_id")
        batch_op.drop_column("parent_session_id")

    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("subagent_ids")
