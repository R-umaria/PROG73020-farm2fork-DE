"""add internal event record table

Revision ID: 4b8f4570b7d1
Revises: cac9c4e16db1
Create Date: 2026-04-09 15:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "4b8f4570b7d1"
down_revision = "cac9c4e16db1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "internal_event_record",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("aggregate_type", sa.String(), nullable=False),
        sa.Column("aggregate_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_internal_event_record_order_id"),
        "internal_event_record",
        ["order_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_internal_event_record_order_id"),
        table_name="internal_event_record",
    )
    op.drop_table("internal_event_record")
