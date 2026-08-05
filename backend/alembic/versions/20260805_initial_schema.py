"""Initial schema for Propel.

Revision ID: 20260805_initial
Revises:
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa

revision = "20260805_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feeders",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("metadata", sa.Text(), nullable=True),
    )
    op.create_table(
        "transformers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("feeder_id", sa.Integer(), sa.ForeignKey("feeders.id"), nullable=True),
        sa.Column("parent_pole_id", sa.Integer(), sa.ForeignKey("poles.id"), nullable=True),
        sa.Column("topology_confidence", sa.Numeric(precision=4, scale=3), nullable=False, server_default="1.000"),
    )
    op.create_table(
        "poles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("feeder_id", sa.Integer(), sa.ForeignKey("feeders.id"), nullable=True),
        sa.Column("transformer_id", sa.Integer(), sa.ForeignKey("transformers.id"), nullable=True),
        sa.Column("parent_pole_id", sa.Integer(), sa.ForeignKey("poles.id"), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("firmware_version", sa.String(length=32), nullable=False, server_default="1.2"),
        sa.Column("is_sensor_online", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("topology_confidence", sa.Numeric(precision=4, scale=3), nullable=False, server_default="1.000"),
        sa.Column("metadata", sa.Text(), nullable=True),
    )
    op.create_table(
        "telemetry",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("pole_id", sa.Integer(), sa.ForeignKey("poles.id"), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("power_lost", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("power_restored", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("voltage", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("current", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("temperature", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("firmware_version", sa.String(length=32), nullable=False, server_default="1.2"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="simulator"),
        sa.Column("stale_packet", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", sa.Text(), nullable=True),
    )
    op.create_table(
        "faults",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("fault_type", sa.String(length=32), nullable=False),
        sa.Column("source_pole_id", sa.Integer(), sa.ForeignKey("poles.id"), nullable=True),
        sa.Column("affected_pole_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=False, server_default="0.000"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="Detected"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("topology_confidence", sa.Numeric(precision=4, scale=3), nullable=False, server_default="1.000"),
        sa.Column("metadata", sa.Text(), nullable=True),
    )
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("fault_id", sa.Integer(), sa.ForeignKey("faults.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="Detected"),
        sa.Column("crew_assigned", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.Text(), nullable=True),
    )
    op.create_table(
        "scheduled_outages",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("feeder_id", sa.Integer(), sa.ForeignKey("feeders.id"), nullable=True),
        sa.Column("pole_id", sa.Integer(), sa.ForeignKey("poles.id"), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "simulation_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("simulation_logs")
    op.drop_table("scheduled_outages")
    op.drop_table("tickets")
    op.drop_table("faults")
    op.drop_table("telemetry")
    op.drop_table("poles")
    op.drop_table("transformers")
    op.drop_table("feeders")
