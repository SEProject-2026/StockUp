from typing import List, Optional
from uuid import UUID
from src.domain.enums import LocationType
from src.domain.shopping_list.shopping_list import ShoppingList

class ShoppingListService:
    def __init__(self, shopping_repo):#, product_repo, analytics_repo):
        """
        Initializes the service with necessary repositories.
        :param shopping_repo: IShoppingListRepository - Handles shopping lists and base modes.
        :param product_repo: IProductRepository - Handles current inventory and nicknames.
        :param analytics_repo: IAnalyticsRepository - Handles access to generated insights.
        """
        self.shopping_repo = shopping_repo
        #self.product_repo = product_repo
        #self.analytics_repo = analytics_repo

    async def get_shopping_list(self, id: UUID) -> ShoppingList:
        """
        Retrieves a specific shopping list by its ID.
        """
        list= await self.shopping_repo.get_by_id(id)
        if not list:
            raise ValueError(f"Shopping list not found: {id}")
        return list
    async def get_all_shopping_lists_by_home(self, home_id: UUID) -> List[ShoppingList]:
        """
        Retrieves all shopping lists for a specific home.
        """
        return await self.shopping_repo.get_all_by_home(home_id)

    async def create_shopping_list(self, home_id: UUID, name: str) -> ShoppingList:
        """
        Creates a new shopping list for a specific home.
        """
        new_list = ShoppingList(home_id=home_id, name=name)
        await self.shopping_repo.save(new_list)
        return new_list
    
    async def delete_shopping_list(self, id: UUID) -> None:
        """
        Deletes the shopping list for a specific home.
        """
        await self.shopping_repo.delete(id)

    async def add_item_to_list(self, id: UUID, item_name: str, quantity: int, location: Optional[LocationType] = LocationType.OTHER) -> ShoppingList:
        """
        Adds a specific product definition to the shopping list.
        """
        list = await self.shopping_repo.get_by_id(id)
        if not list:
            raise ValueError(f"Shopping list not found: {id}")
        list.add_item(item_name, quantity, location)
        await self.shopping_repo.save(list)
        return list

    async def remove_item_from_list(self, id: UUID, item_name: str) -> ShoppingList:
        """
        Removes an item from the active shopping list.
        """
        list = await self.shopping_repo.get_by_id(id)
        if not list:
            raise ValueError(f"Shopping list not found: {id}")
        list.remove_item(item_name)
        await self.shopping_repo.save(list)
        return list

    async def update_item_quantity(self, id: UUID, item_name: str, new_quantity: int) -> ShoppingList:
        """
        Updates the quantity of a specific item in the shopping list.
        """
        list = await self.shopping_repo.get_by_id(id)
        if not list:
            raise ValueError(f"Shopping list not found: {id}")
        list.update_quantity(item_name, new_quantity)
        await self.shopping_repo.save(list)
        return list

    async def enter_shopping_mode(self, id: UUID)-> ShoppingList:
        """
        Marks the shopping list as active/in-shopping mode.
        """
        list = await self.shopping_repo.get_by_id(id)
        if not list:
            raise ValueError(f"Shopping list not found: {id}")
        list.enter_shopping_mode()
        await self.shopping_repo.save(list)
        return list

    async def check_item_as_bought(self, id: UUID, item_name: str) -> ShoppingList:
        """
        Marks a specific item in the shopping list as bought.
        """
        list = await self.shopping_repo.get_by_id(id)
        if not list:
            raise ValueError(f"Shopping list not found: {id}")
        list.check_item_as_bought(item_name)
        await self.shopping_repo.save(list)
        return list

    async def exit_shopping_mode(self, id: UUID,clear: bool = False) -> ShoppingList:
        """
        Marks the shopping list as inactive/not in shopping mode.
        If clear is True, removes the items that were marked as bought.
        """
        list = await self.shopping_repo.get_by_id(id)
        if not list:
            raise ValueError(f"Shopping list not found: {id}")
        list.exit_shopping_mode(clear)
        await self.shopping_repo.save(list)
        return list
