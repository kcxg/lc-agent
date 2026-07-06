"""drop dangerous_tools column

Revision ID: 20260704_drop_dangerous_tools
Revises: 20260623_http_traces
Create Date: 2026-07-04 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260704_drop_dangerous_tools"
down_revision: Union[str, Sequence[str], None] = "20260623_http_traces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets", schema=None) as batch_op:
        batch_op.drop_column("dangerous_tools")


def downgrade() -> None:
    with op.batch_alter_table("agent_presets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("dangerous_tools", sa.JSON(), nullable=True))
