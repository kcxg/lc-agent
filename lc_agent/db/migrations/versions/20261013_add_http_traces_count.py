"""chat_ui_messages 增加 http_traces_count（只存条数，避免为取长度而加载数百 MB 追踪正文）

Revision ID: 20261013_http_traces_count
Revises: 20260911_pricing_single_row
Create Date: 2026-10-13

背景：http_traces 是 JSON 列，ORM 读出来会反序列化成 Python 对象。消息接口原本用
select(ChatUiMessage) 全列加载、再 len() 取条数，导致单个会话（实测 359MB 追踪正文）
每次请求多花约 3 秒、多占约 1GB 内存。改为：正文不进列表查询，条数读本列。

回填是一次全表扫描（本机 4.9GB 追踪正文，约 10 秒量级），只做一次。
"""

import sqlalchemy as sa
from alembic import op


revision = "20261013_http_traces_count"
down_revision = "20260911_pricing_single_row"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_ui_messages",
        sa.Column("http_traces_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    # 回填历史数据的实际条数（不删改任何原有数据）
    op.execute(
        "UPDATE chat_ui_messages SET http_traces_count = json_array_length(http_traces) "
        "WHERE http_traces IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("chat_ui_messages", "http_traces_count")
