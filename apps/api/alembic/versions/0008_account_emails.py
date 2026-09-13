"""Queue account email delivery transactionally."""

import sqlalchemy as sa

from alembic import op

revision = "0008_account_emails"
down_revision = "0007_session_version"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_emails",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_account_emails_user_id", "account_emails", ["user_id"])
    op.create_index("ix_account_emails_due", "account_emails", ["status", "next_attempt_at"])


def downgrade():
    op.drop_table("account_emails")
