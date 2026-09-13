"""Harden account uniqueness and availability invariants."""

import sqlalchemy as sa

from alembic import op

revision = "0002_hardening"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)
    op.create_check_constraint(
        "ck_availability_end_after_start", "practitioner_availability", "end_time > start_time"
    )


def downgrade():
    op.drop_constraint(
        "ck_availability_end_after_start", "practitioner_availability", type_="check"
    )
    op.drop_index("uq_users_email_lower", table_name="users")
