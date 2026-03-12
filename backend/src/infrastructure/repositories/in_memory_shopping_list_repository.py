from typing import Optional
from uuid import UUID
from src.domain.shopping_list.shopping_list import ShoppingList
from src.repositories.i_shopping_list_repository import IShoppingListRepository

class InMemoryShoppingListRepository(IShoppingListRepository):
    def __init__(self):
        # key: id, value: ShoppingList object
        self._lists = {}

    async def save(self, shopping_list: ShoppingList) -> None:
        self._lists[shopping_list.id] = shopping_list

    async def get_by_id(self, id: UUID) -> Optional[ShoppingList]:
        return self._lists.get(id)
    
    async def get_all_by_home(self, home_id: UUID) -> list[ShoppingList]:
        return [lst for lst in self._lists.values() if lst.home_id == home_id]

    async def delete(self, id: UUID) -> None:
        if id in self._lists:
            del self._lists[id]