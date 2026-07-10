"""rename builtin preset ids from __xxx__ to xxx

Revision ID: 20260710_rename_builtin_ids
Revises: 20260710_add_display_name
Create Date: 2026-07-10
"""

from alembic import op

revision = "20260710_rename_builtin_ids"
down_revision = "20260710_add_display_name"
branch_labels = None
depends_on = None

_RENAME_MAP = [
    ("__chat__", "chat"),
    ("__empty__", "empty"),
    ("__power__", "power"),
]


def upgrade() -> None:
    for old_id, new_id in _RENAME_MAP:
        op.execute(
            f"UPDATE sessions SET agent_id = '{new_id}' WHERE agent_id = '{old_id}'"
        )
        op.execute(
            f"UPDATE user_agent_access SET agent_id = '{new_id}' WHERE agent_id = '{old_id}'"
        )


def downgrade() -> None:
    for old_id, new_id in _RENAME_MAP:
        op.execute(
            f"UPDATE sessions SET agent_id = '{old_id}' WHERE agent_id = '{new_id}'"
        )
        op.execute(
            f"UPDATE user_agent_access SET agent_id = '{old_id}' WHERE agent_id = '{new_id}'"
        )
