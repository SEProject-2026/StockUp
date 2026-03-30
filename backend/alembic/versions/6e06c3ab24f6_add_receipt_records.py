"""add receipt records

Revision ID: 6e06c3ab24f6
Revises: 5e06c3ab24f6
Create Date: 2026-03-24 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e06c3ab24f6'
down_revision: Union[str, Sequence[str], None] = '5e06c3ab24f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('receipt_records',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('home_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('chain', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['home_id'], ['homes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receipt_records_id'), 'receipt_records', ['id'], unique=False)
    op.create_index(op.f('ix_receipt_records_home_id'), 'receipt_records', ['home_id'], unique=False)

    op.create_table('receipt_record_items',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('receipt_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('barcode', sa.String(), nullable=True),
    sa.Column('quantity', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['receipt_id'], ['receipt_records.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receipt_record_items_id'), 'receipt_record_items', ['id'], unique=False)
    op.create_index(op.f('ix_receipt_record_items_receipt_id'), 'receipt_record_items', ['receipt_id'], unique=False)
    op.create_index(op.f('ix_receipt_record_items_barcode'), 'receipt_record_items', ['barcode'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_receipt_record_items_barcode'), table_name='receipt_record_items')
    op.drop_index(op.f('ix_receipt_record_items_receipt_id'), table_name='receipt_record_items')
    op.drop_index(op.f('ix_receipt_record_items_id'), table_name='receipt_record_items')
    op.drop_table('receipt_record_items')

    op.drop_index(op.f('ix_receipt_records_home_id'), table_name='receipt_records')
    op.drop_index(op.f('ix_receipt_records_id'), table_name='receipt_records')
    op.drop_table('receipt_records')
