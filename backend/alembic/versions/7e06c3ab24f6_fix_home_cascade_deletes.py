"""fix home cascade deletes

Revision ID: 7e06c3ab24f6
Revises: d0a98d304073
Create Date: 2026-03-25 15:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7e06c3ab24f6'
down_revision: Union[str, Sequence[str], None] = 'd0a98d304073'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. receipt_records -> homes
    op.drop_constraint('receipt_records_home_id_fkey', 'receipt_records', type_='foreignkey')
    op.create_foreign_key('receipt_records_home_id_fkey', 'receipt_records', 'homes', ['home_id'], ['id'], ondelete='CASCADE')

    # 2. receipt_record_items -> receipt_records
    op.drop_constraint('receipt_record_items_receipt_id_fkey', 'receipt_record_items', type_='foreignkey')
    op.create_foreign_key('receipt_record_items_receipt_id_fkey', 'receipt_record_items', 'receipt_records', ['receipt_id'], ['id'], ondelete='CASCADE')

    # 3. products -> homes
    op.drop_constraint('products_home_id_fkey', 'products', type_='foreignkey')
    op.create_foreign_key('products_home_id_fkey', 'products', 'homes', ['home_id'], ['id'], ondelete='CASCADE')

    # 4. product_items -> products
    op.drop_constraint('product_items_product_id_fkey', 'product_items', type_='foreignkey')
    op.create_foreign_key('product_items_product_id_fkey', 'product_items', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    # 5. shopping_lists -> homes
    op.drop_constraint('shopping_lists_home_id_fkey', 'shopping_lists', type_='foreignkey')
    op.create_foreign_key('shopping_lists_home_id_fkey', 'shopping_lists', 'homes', ['home_id'], ['id'], ondelete='CASCADE')

    # 6. user_home association
    op.drop_constraint('user_home_home_id_fkey', 'user_home', type_='foreignkey')
    op.create_foreign_key('user_home_home_id_fkey', 'user_home', 'homes', ['home_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('user_home_user_id_fkey', 'user_home', type_='foreignkey')
    op.create_foreign_key('user_home_user_id_fkey', 'user_home', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 7. home_join_requests association
    op.drop_constraint('home_join_requests_home_id_fkey', 'home_join_requests', type_='foreignkey')
    op.create_foreign_key('home_join_requests_home_id_fkey', 'home_join_requests', 'homes', ['home_id'], ['id'], ondelete='CASCADE')
    # op.drop_constraint('home_join_requests_user_id_fkey', 'home_join_requests', type_='foreignkey')
    # op.create_foreign_key('home_join_requests_user_id_fkey', 'home_join_requests', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    pass
