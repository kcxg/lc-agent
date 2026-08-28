"""add prompt_templates and agent_prompt_bindings tables

Revision ID: 20260801_add_prompt_library
Revises: 20260710_rename_builtin_ids
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op


revision = "20260801_add_prompt_library"
down_revision = "20260710_rename_builtin_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if not inspector.has_table("prompt_templates"):
        op.create_table(
            "prompt_templates",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if not inspector.has_table("agent_prompt_bindings"):
        op.create_table(
            "agent_prompt_bindings",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("agent_id", sa.String(), nullable=False),
            sa.Column("prompt_id", sa.String(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        )

    inspector = sa.inspect(op.get_bind())
    binding_indexes = {index["name"] for index in inspector.get_indexes("agent_prompt_bindings")}
    if "ix_agent_prompt_bindings_agent_id" not in binding_indexes:
        op.create_index(
            "ix_agent_prompt_bindings_agent_id",
            "agent_prompt_bindings",
            ["agent_id"],
        )
    if "ix_agent_prompt_bindings_prompt_id" not in binding_indexes:
        op.create_index(
            "ix_agent_prompt_bindings_prompt_id",
            "agent_prompt_bindings",
            ["prompt_id"],
        )


def downgrade() -> None:
    op.drop_table("agent_prompt_bindings")
    op.drop_table("prompt_templates")
