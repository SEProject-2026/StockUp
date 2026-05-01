from typing import List, Optional
from uuid import UUID
from src.domain.shopping_list.shopping_list import ShoppingList
from src.infrastructure.logger import app_logger
from src.services.security import require_house_access

class ShoppingListService:
    def __init__(self, shopping_repo, home_repository):
        """
        Initializes the service with necessary repositories.
        """
        self.shopping_repo = shopping_repo
        self._home_repository = home_repository

    @require_house_access
    async def get_shopping_list(self, user_id: UUID, id: UUID) -> ShoppingList:
        """
        Retrieves a specific shopping list by its ID.
        """
        list_obj = await self.shopping_repo.get_by_id(id)
        if not list_obj:
            raise ValueError(f"Shopping list not found: {id}")
        return list_obj

    @require_house_access
    async def get_all_shopping_lists_by_home(self, user_id: UUID, home_id: UUID) -> List[ShoppingList]:
        """
        Retrieves all shopping lists for a specific home.
        """
        return await self.shopping_repo.get_all_by_home(home_id)

    @require_house_access
    async def create_shopping_list(self, user_id: UUID, home_id: UUID, name: str) -> ShoppingList:
        """
        Creates a new shopping list for a specific home.
        """
        new_list = ShoppingList(home_id=home_id, name=name)
        await self.shopping_repo.save(new_list)
        return new_list
    
    @require_house_access
    async def delete_shopping_list(self, user_id: UUID, id: UUID) -> None:
        """
        Deletes the shopping list for a specific home.
        """
        await self.shopping_repo.delete(id)

    @require_house_access
    async def add_item_to_list(self, user_id: UUID, id: UUID, item_name: str, quantity: int, location: Optional[str] = "OTHER") -> ShoppingList:
        """
        Adds a specific product definition to the shopping list.
        """
        list_obj = await self.shopping_repo.get_by_id(id)
        if not list_obj:
            raise ValueError(f"Shopping list not found: {id}")
        list_obj.add_item(item_name, quantity, location)
        await self.shopping_repo.save(list_obj)
        return list_obj

    @require_house_access
    async def remove_item_from_list(self, user_id: UUID, id: UUID, item_name: str) -> ShoppingList:
        """
        Removes an item from the active shopping list.
        """
        app_logger.info(f"Attempting to remove item '{item_name}' from list {id}")
        list_obj = await self.shopping_repo.get_by_id(id)
        if not list_obj:
            raise ValueError(f"Shopping list not found: {id}")
        list_obj.remove_item(item_name)
        await self.shopping_repo.save(list_obj)
        return list_obj
    
    @require_house_access
    async def update_item_quantity(self, user_id: UUID, id: UUID, item_name: str, new_quantity: int) -> ShoppingList:
        """
        Updates the quantity of a specific item in the shopping list.
        """
        list_obj = await self.shopping_repo.get_by_id(id)
        if not list_obj:
            raise ValueError(f"Shopping list not found: {id}")
        list_obj.update_quantity(item_name, new_quantity)
        await self.shopping_repo.save(list_obj)
        return list_obj

    @require_house_access
    async def enter_shopping_mode(self, user_id: UUID, id: UUID)-> ShoppingList:
        """
        Marks the shopping list as active/in-shopping mode.
        """
        list_obj = await self.shopping_repo.get_by_id(id)
        if not list_obj:
            raise ValueError(f"Shopping list not found: {id}")
        list_obj.enter_shopping_mode()
        await self.shopping_repo.save(list_obj)
        return list_obj

    @require_house_access
    async def check_item_as_bought(self, user_id: UUID, id: UUID, item_name: str) -> ShoppingList:
        """
        Marks a specific item in the shopping list as bought.
        """
        list_obj = await self.shopping_repo.get_by_id(id)
        if not list_obj:
            raise ValueError(f"Shopping list not found: {id}")
        list_obj.check_item_as_bought(item_name)
        await self.shopping_repo.save(list_obj)
        return list_obj

    @require_house_access
    async def exit_shopping_mode(self, user_id: UUID, id: UUID, clear: bool = False) -> ShoppingList:
        """
        Marks the shopping list as inactive/not in shopping mode.
        If clear is True, removes the items that were marked as bought.
        """
        list_obj = await self.shopping_repo.get_by_id(id)
        if not list_obj:
            raise ValueError(f"Shopping list not found: {id}")
        list_obj.exit_shopping_mode(clear)
        await self.shopping_repo.save(list_obj)
        return list_obj
