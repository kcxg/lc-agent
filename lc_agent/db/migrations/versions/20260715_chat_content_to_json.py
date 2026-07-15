"""change chat_ui_messages.content from str to JSON list

Revision ID: 20260715_content_json
Revises: 20260710_rename_builtin_ids
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa

revision = "20260715_content_json"
down_revision = "20260710_rename_builtin_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 项目早期无历史包袱，直接清空老数据并改列类型
    op.execute("DELETE FROM chat_ui_messages")
    # SQLite 不支持 ALTER COLUMN，需要用 batch_alter_table 重建表
    with op.batch_alter_table("chat_ui_messages") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.String(),
            type_=sa.JSON(),
            existing_nullable=False,
            server_default="[]",
        )


def downgrade() -> None:
    with op.batch_alter_table("chat_ui_messages") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.JSON(),
            type_=sa.String(),
            existing_nullable=False,
            server_default="",
        )
