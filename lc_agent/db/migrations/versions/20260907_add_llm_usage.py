"""add llm_usage and model_pricing tables

Revision ID: 20260907_add_llm_usage
Revises: 20260904_add_can_be_subagent
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op


revision = "20260907_add_llm_usage"
down_revision = "20260904_add_can_be_subagent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_usage",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False, server_default=""),
        sa.Column("session_id", sa.String(), nullable=False, server_default=""),
        sa.Column("parent_session_id", sa.String(), nullable=True),
        sa.Column("agent_id", sa.String(), nullable=False, server_default=""),
        sa.Column("model_id", sa.String(), nullable=False, server_default=""),
        sa.Column("raw_model_id", sa.String(), nullable=False, server_default=""),
        sa.Column("provider", sa.String(), nullable=False, server_default=""),
        sa.Column("role", sa.String(), nullable=False, server_default="main"),
        sa.Column("sub_session_id", sa.String(), nullable=False, server_default=""),
        sa.Column("source", sa.String(), nullable=False, server_default="chat"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_write_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("run_id", sa.String(), nullable=False, server_default=""),
        sa.Column("seq", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_llm_usage_ts", "llm_usage", ["ts"])
    op.create_index("ix_llm_usage_user_id", "llm_usage", ["user_id"])
    op.create_index("ix_llm_usage_session_id", "llm_usage", ["session_id"])
    op.create_index("ix_llm_usage_parent_session_id", "llm_usage", ["parent_session_id"])
    op.create_index("ix_llm_usage_agent_id", "llm_usage", ["agent_id"])
    op.create_index("ix_llm_usage_model_id", "llm_usage", ["model_id"])
    op.create_index("ix_llm_usage_run_id", "llm_usage", ["run_id"])
    op.create_index("ix_llm_usage_user_ts", "llm_usage", ["user_id", "ts"])
    op.create_index("ix_llm_usage_agent_ts", "llm_usage", ["agent_id", "ts"])
    op.create_index("ix_llm_usage_model_ts", "llm_usage", ["model_id", "ts"])
    op.create_index(
        "uq_llm_usage_run_seq", "llm_usage", ["run_id", "seq"], unique=True
    )

    op.create_table(
        "model_pricing",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False, server_default=""),
        sa.Column("price_per_1m", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=False, server_default="CNY"),
        sa.Column("effective_from", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(), nullable=False, server_default=""),
    )
    op.create_index("ix_model_pricing_model", "model_pricing", ["model"])
    op.create_index(
        "ix_model_pricing_model_kind_from", "model_pricing", ["model", "kind", "effective_from"]
    )


def downgrade() -> None:
    op.drop_table("model_pricing")
    op.drop_table("llm_usage")
