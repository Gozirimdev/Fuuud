"""Initial Phase 1 schema."""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None
verification = sa.Enum("pending", "verified", "rejected", name="verificationstatus")
availability = sa.Enum("available", "booked", "unavailable", name="availabilitystatus")
appointment_type = sa.Enum("online", "physical", name="appointmenttype")
appointment_status = sa.Enum(
    "pending", "confirmed", "completed", "cancelled", name="appointmentstatus"
)


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone_number", sa.String(32)),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("country", sa.String(80)),
        sa.Column("state", sa.String(80)),
        sa.Column("city", sa.String(80)),
        *timestamps(),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "healthcare_practitioners",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("specialty", sa.String(120), nullable=False),
        sa.Column("professional_title", sa.String(160), nullable=False),
        sa.Column("license_number", sa.String(100), nullable=False, unique=True),
        sa.Column("country", sa.String(80), nullable=False),
        sa.Column("state", sa.String(80), nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("consultation_fee", sa.Numeric(12, 2), nullable=False),
        sa.Column("years_of_experience", sa.Integer(), nullable=False),
        sa.Column("verification_status", verification, nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("rating", sa.Numeric(2, 1), nullable=False),
        sa.Column("profile_image_url", sa.String(500)),
        *timestamps(),
    )
    for col in ("specialty", "country", "state", "city", "verification_status"):
        op.create_index(f"ix_healthcare_practitioners_{col}", "healthcare_practitioners", [col])
    op.create_index("ix_practitioner_name", "healthcare_practitioners", ["first_name", "last_name"])
    op.create_table(
        "practitioner_availability",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "practitioner_id",
            sa.Uuid(),
            sa.ForeignKey("healthcare_practitioners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("status", availability, nullable=False),
        *timestamps(),
        sa.UniqueConstraint("practitioner_id", "date", "start_time", name="uq_practitioner_slot"),
    )
    op.create_index(
        "ix_practitioner_availability_practitioner_id",
        "practitioner_availability",
        ["practitioner_id"],
    )
    op.create_index("ix_practitioner_availability_date", "practitioner_availability", ["date"])
    op.create_index("ix_practitioner_availability_status", "practitioner_availability", ["status"])
    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "practitioner_id",
            sa.Uuid(),
            sa.ForeignKey("healthcare_practitioners.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "availability_id",
            sa.Uuid(),
            sa.ForeignKey("practitioner_availability.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("appointment_type", appointment_type, nullable=False),
        sa.Column("status", appointment_status, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        *timestamps(),
    )
    for col in ("user_id", "practitioner_id", "status", "scheduled_at"):
        op.create_index(f"ix_appointments_{col}", "appointments", [col])


def downgrade():
    op.drop_table("appointments")
    op.drop_table("practitioner_availability")
    op.drop_table("healthcare_practitioners")
    op.drop_table("users")
