from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.repositories.i_shopping_list_repository import IShoppingListRepository
from src.domain.shopping_list.shopping_list import ShoppingList, ShoppingListItem
from src.infrastructure.db.models import ShoppingListModel

class DbShoppingListRepository(IShoppingListRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, shopping_list: ShoppingList) -> None:
        result = await self.db.execute(
            select(ShoppingListModel).where(ShoppingListModel.id == str(shopping_list.id))
        )
        db_list = result.scalars().first()
        items_data = [item.model_dump() for item in shopping_list.items]
        if not db_list:
            db_list = ShoppingListModel(id=str(shopping_list.id))
            self.db.add(db_list)
        db_list.home_id = str(shopping_list.home_id)
        db_list.name = getattr(shopping_list, 'name', "Shopping List")
        db_list.is_active_shopping_mode = shopping_list.is_active_shopping_mode
        db_list.items = items_data
        await self.db.commit()

    async def get_by_id(self, list_id: UUID) -> Optional[ShoppingList]:
        result = await self.db.execute(
            select(ShoppingListModel).where(ShoppingListModel.id == str(list_id))
        )
        db_list = result.scalars().first()
        return self._to_domain(db_list) if db_list else None

    async def get_all_by_home(self, home_id: UUID) -> List[ShoppingList]:
        result = await self.db.execute(
            select(ShoppingListModel).where(ShoppingListModel.home_id == str(home_id))
        )
        db_lists = result.scalars().all()
        return [self._to_domain(dl) for dl in db_lists]

    async def delete(self, list_id: UUID) -> None:
        result = await self.db.execute(
            select(ShoppingListModel).where(ShoppingListModel.id == str(list_id))
        )
        db_list = result.scalars().first()
        if db_list:
            await self.db.delete(db_list)
            await self.db.commit()

    def _to_domain(self, db_list: ShoppingListModel) -> ShoppingList:
        db_items = db_list.items if db_list.items is not None else []
        items = [ShoppingListItem(**item) for item in db_items if isinstance(item, dict)]
        return ShoppingList(
            id=UUID(db_list.id),
            home_id=UUID(db_list.home_id),
            name=db_list.name,
            is_active_shopping_mode=db_list.is_active_shopping_mode,
            items=items
        )