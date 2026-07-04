"""Add users table and user_id to sessions

Revision ID: 20260704_add_users
"""
from alembic import op
import sqlalchemy as sa

revision = "20260704_add_users"
down_revision = "20260704_drop_dangerous_tools"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "user_agent_access",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), primary_key=True),
    )

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(), server_default="", nullable=False))
        batch_op.create_index("ix_sessions_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_index("ix_sessions_user_id")
        batch_op.drop_column("user_id")
    op.drop_table("user_agent_access")
    op.drop_index("ix_users_username", "users")
    op.drop_table("users")
