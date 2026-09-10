"""model_pricing 改为单行制：一个 (model, kind) 只留一条

Revision ID: 20260911_pricing_single_row
Revises: 20260910_add_can_be_mcp
Create Date: 2026-09-11

- 同 (model, kind) 有多条时只留 effective_from 最新的一条，其余删除
- 加唯一约束 (model, kind)，后端改为 upsert
"""

import sqlalchemy as sa
from alembic import op


revision = "20260911_pricing_single_row"
down_revision = "20260910_add_can_be_mcp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # 同 (model, kind) 只留 effective_from 最新一条（id 最大的兜底），其余删除
    conn.execute(
        sa.text(
            """
            DELETE FROM model_pricing
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY model, kind
                               ORDER BY effective_from DESC, id DESC
                           ) AS rn
                    FROM model_pricing
                ) WHERE rn = 1
            )
            """
        )
    )
    with op.batch_alter_table("model_pricing") as batch_op:
        batch_op.create_unique_constraint(
            "uq_model_pricing_model_kind", ["model", "kind"]
        )


def downgrade() -> None:
    with op.batch_alter_table("model_pricing") as batch_op:
        batch_op.drop_constraint("uq_model_pricing_model_kind", type_="unique")
