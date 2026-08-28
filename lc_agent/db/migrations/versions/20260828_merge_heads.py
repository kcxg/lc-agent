"""merge parallel migration heads

Revision ID: 20260828_merge_heads
Revises: 20260715_content_json, 20260827_add_automation_tasks
Create Date: 2026-08-28
"""

revision = "20260828_merge_heads"
down_revision = (
    "20260715_content_json",
    "20260827_add_automation_tasks",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
