"""add driver account table

Revision ID: 5bb66c4ec8c1
Revises: 2803e774c676
Create Date: 2026-04-18 16:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '5bb66c4ec8c1'
down_revision = '2803e774c676'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'driver_account',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('driver_id', sa.BigInteger(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('driver_name', sa.String(), nullable=False),
        sa.Column('vehicle_type', sa.String(), nullable=False),
        sa.Column('driver_status', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('driver_id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_driver_account_driver_id'), 'driver_account', ['driver_id'], unique=False)
    op.create_index(op.f('ix_driver_account_email'), 'driver_account', ['email'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_driver_account_email'), table_name='driver_account')
    op.drop_index(op.f('ix_driver_account_driver_id'), table_name='driver_account')
    op.drop_table('driver_account')
