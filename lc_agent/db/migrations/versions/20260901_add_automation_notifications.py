"""add automation notification targets and delivery summaries

Revision ID: 20260901_add_automation_notifications
Revises: 20260828_merge_heads
Create Date: 2026-09-01
"""

import sqlalchemy as sa
from alembic import op


revision = "20260901_add_automation_notifications"
down_revision = "20260828_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    task_columns = {column["name"] for column in inspector.get_columns("automation_tasks")}
    if "notification_targets" not in task_columns:
        op.add_column(
            "automation_tasks",
            sa.Column("notification_targets", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )

    run_columns = {column["name"] for column in inspector.get_columns("automation_runs")}
    if "notification_status" not in run_columns:
        op.add_column(
            "automation_runs",
            sa.Column("notification_status", sa.String(), nullable=False, server_default="not_configured"),
        )
    if "notification_error" not in run_columns:
        op.add_column("automation_runs", sa.Column("notification_error", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("automation_runs") as batch_op:
        batch_op.drop_column("notification_error")
        batch_op.drop_column("notification_status")
    with op.batch_alter_table("automation_tasks") as batch_op:
        batch_op.drop_column("notification_targets")
