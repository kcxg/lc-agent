"""add automation task and run tables

Revision ID: 20260827_add_automation_tasks
Revises: 20260801_add_prompt_library
Create Date: 2026-08-27
"""

import sqlalchemy as sa
from alembic import op


revision = "20260827_add_automation_tasks"
down_revision = "20260801_add_prompt_library"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "automation_tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, server_default=""),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("prompt", sa.String(), nullable=False),
        sa.Column("schedule_type", sa.String(), nullable=False),
        sa.Column("schedule_config", sa.JSON(), nullable=False),
        sa.Column("timezone", sa.String(), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_automation_tasks_user_id", "automation_tasks", ["user_id"])
    op.create_index("ix_automation_tasks_agent_id", "automation_tasks", ["agent_id"])
    op.create_index("ix_automation_tasks_next_run_at", "automation_tasks", ["next_run_at"])

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False, server_default=""),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_automation_runs_task_id", "automation_runs", ["task_id"])
    op.create_index("ix_automation_runs_user_id", "automation_runs", ["user_id"])
    op.create_index("ix_automation_runs_session_id", "automation_runs", ["session_id"])
    op.create_index(
        "uq_automation_runs_active_task",
        "automation_runs",
        ["task_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('pending', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("uq_automation_runs_active_task", table_name="automation_runs")
    op.drop_index("ix_automation_runs_session_id", table_name="automation_runs")
    op.drop_index("ix_automation_runs_user_id", table_name="automation_runs")
    op.drop_index("ix_automation_runs_task_id", table_name="automation_runs")
    op.drop_table("automation_runs")
    op.drop_index("ix_automation_tasks_next_run_at", table_name="automation_tasks")
    op.drop_index("ix_automation_tasks_agent_id", table_name="automation_tasks")
    op.drop_index("ix_automation_tasks_user_id", table_name="automation_tasks")
    op.drop_table("automation_tasks")
