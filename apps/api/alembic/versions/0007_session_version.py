"""Invalidate existing sessions when account credentials change."""

import sqlalchemy as sa

from alembic import op

revision = "0007_session_version"
down_revision = "0006_audit_events"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="0")
    )
    op.alter_column("users", "session_version", server_default=None)


def downgrade():
    op.drop_column("users", "session_version")
