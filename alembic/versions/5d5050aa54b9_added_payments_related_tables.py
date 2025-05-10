"""added payments related tables

Revision ID: 5d5050aa54b9
Revises: aa3a1c3f8828
Create Date: 2025-05-09 02:28:37.764992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5d5050aa54b9'
down_revision: Union[str, None] = 'aa3a1c3f8828'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Create plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=32), nullable=False, unique=True),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('strike_price_cents', sa.Integer(), nullable=False),
        sa.Column('billing_interval', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.execute("DROP INDEX IF EXISTS ix_plans_billing_interval;")
    op.create_index('ix_plans_billing_interval', 'plans', ['billing_interval'])

    # 2) Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('gateway_subscription_id', sa.String(length=128), unique=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='SET NULL'),
    )
    # ensure clean slate for subscriptions indexes
    op.execute("DROP INDEX IF EXISTS ix_subscriptions_user_id;")
    op.execute("DROP INDEX IF EXISTS ix_subscriptions_plan_id;")
    op.execute("DROP INDEX IF EXISTS ix_subscriptions_status;")
    op.execute("DROP INDEX IF EXISTS ix_subscriptions_current_period_end;")
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_plan_id', 'subscriptions', ['plan_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_current_period_end', 'subscriptions', ['current_period_end'])

    # 3) Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('subscription_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gateway_order_id', sa.String(length=128), nullable=False),
        sa.Column('gateway_payment_id', sa.String(length=128), nullable=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='created'),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('raw_payload', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
    )
    # ensure clean slate for payments indexes
    op.execute("DROP INDEX IF EXISTS ix_payments_subscription_id;")
    op.execute("DROP INDEX IF EXISTS ix_payments_gateway_order_id;")
    op.execute("DROP INDEX IF EXISTS ix_payments_status;")
    op.create_index('ix_payments_subscription_id', 'payments', ['subscription_id'])
    op.create_index('ix_payments_gateway_order_id', 'payments', ['gateway_order_id'], unique=True)
    op.create_index('ix_payments_status', 'payments', ['status'])


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_gateway_order_id', table_name='payments')
    op.drop_index('ix_payments_subscription_id', table_name='payments')
    op.drop_table('payments')

    op.drop_index('ix_subscriptions_current_period_end', table_name='subscriptions')
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_plan_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')
    op.drop_table('subscriptions')

    op.drop_index('ix_plans_billing_interval', table_name='plans')
    op.drop_table('plans')