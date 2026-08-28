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
    inspector = sa.inspect(op.get_bind())

    if not inspector.has_table("automation_tasks"):
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

    if not inspector.has_table("automation_runs"):
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

    inspector = sa.inspect(op.get_bind())
    task_indexes = {index["name"] for index in inspector.get_indexes("automation_tasks")}
    for name, column in (
        ("ix_automation_tasks_user_id", "user_id"),
        ("ix_automation_tasks_agent_id", "agent_id"),
        ("ix_automation_tasks_next_run_at", "next_run_at"),
    ):
        if name not in task_indexes:
            op.create_index(name, "automation_tasks", [column])

    run_indexes = {index["name"] for index in inspector.get_indexes("automation_runs")}
    for name, column in (
        ("ix_automation_runs_task_id", "task_id"),
        ("ix_automation_runs_user_id", "user_id"),
        ("ix_automation_runs_session_id", "session_id"),
    ):
        if name not in run_indexes:
            op.create_index(name, "automation_runs", [column])
    if "uq_automation_runs_active_task" not in run_indexes:
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
