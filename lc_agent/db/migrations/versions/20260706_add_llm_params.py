"""Add llm_params to agent_presets

Revision ID: 20260706_add_llm_params
"""
import sqlalchemy as sa
from alembic import op

revision = "20260706_add_llm_params"
down_revision = "20260704_add_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("llm_params", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("llm_params")
