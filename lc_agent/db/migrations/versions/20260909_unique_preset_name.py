"""add unique constraint on agent_presets.name

Revision ID: 20260909_unique_preset_name
Revises: 20260907_add_llm_usage
Create Date: 2026-09-09
"""

import sqlalchemy as sa
from alembic import op


revision = "20260909_unique_preset_name"
down_revision = "20260907_add_llm_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # name 是 MCP 调用与内部委派的定位键，必须唯一。
    # 现有数据若存在重名，本迁移会在启动时直接失败并指明冲突行，需人工改数据。
    # SQLite 不支持 ALTER TABLE ADD CONSTRAINT，必须走 batch_alter_table 重建表。
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.create_unique_constraint("uq_agent_presets_name", ["name"])


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_constraint("uq_agent_presets_name", type_="unique")
