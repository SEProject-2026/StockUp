from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.repositories.i_shopping_list_repository import IShoppingListRepository
from src.domain.shopping_list.shopping_list import ShoppingList, ShoppingListItem
from src.infrastructure.db.models import ShoppingListModel

class DbShoppingListRepository(IShoppingListRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, shopping_list: ShoppingList) -> None:
        db_list = self.db.query(ShoppingListModel).filter(
            ShoppingListModel.id == str(shopping_list.id)
        ).first()

        items_data = [item.model_dump() for item in shopping_list.items]

        if not db_list:
            db_list = ShoppingListModel(id=str(shopping_list.id))
            self.db.add(db_list)

        db_list.home_id = str(shopping_list.home_id)
        db_list.name = getattr(shopping_list, 'name', "Shopping List")
        db_list.is_active_shopping_mode = shopping_list.is_active_shopping_mode
        db_list.items = items_data
        
        self.db.commit()

    async def get_by_id(self, list_id: UUID) -> Optional[ShoppingList]:
        db_list = self.db.query(ShoppingListModel).filter(
            ShoppingListModel.id == str(list_id)
        ).first()
        return self._to_domain(db_list) if db_list else None

    async def get_all_by_home(self, home_id: UUID) -> List[ShoppingList]:
        db_lists = self.db.query(ShoppingListModel).filter(
            ShoppingListModel.home_id == str(home_id)
        ).all()
        return [self._to_domain(dl) for dl in db_lists]

    async def delete(self, list_id: UUID) -> None:
        db_list = self.db.query(ShoppingListModel).filter(
            ShoppingListModel.id == str(list_id)
        ).first()
        if db_list:
            self.db.delete(db_list)
            self.db.commit()

    def _to_domain(self, db_list: ShoppingListModel) -> ShoppingList:
        items = [ShoppingListItem(**item) for item in db_list.items]
        return ShoppingList(
            id=UUID(db_list.id),
            home_id=UUID(db_list.home_id),
            name=db_list.name,
            is_active_shopping_mode=db_list.is_active_shopping_mode,
            items=items
        )