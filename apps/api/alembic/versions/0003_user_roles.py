"""Add user roles and account lifecycle states."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_user_roles"
down_revision = "0002_hardening"
branch_labels = None
depends_on = None

user_role = postgresql.ENUM(
    "patient", "doctor", "hospital_staff", "admin", name="userrole", create_type=False
)
account_status = postgresql.ENUM(
    "pending", "active", "suspended", name="accountstatus", create_type=False
)


def upgrade():
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    account_status.create(bind, checkfirst=True)
    op.add_column("users", sa.Column("role", user_role, nullable=False, server_default="patient"))
    op.add_column(
        "users",
        sa.Column("account_status", account_status, nullable=False, server_default="active"),
    )
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_account_status", "users", ["account_status"])
    op.alter_column("users", "role", server_default=None)
    op.alter_column("users", "account_status", server_default=None)


def downgrade():
    op.drop_index("ix_users_account_status", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "account_status")
    op.drop_column("users", "role")
    account_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
