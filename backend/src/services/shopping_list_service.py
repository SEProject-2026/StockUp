from ast import List

from backend.src.domain.shopping_list.base_mode import BaseMode
from backend.src.domain.shopping_list.shopping_list import ShoppingList


class ShoppingListService:
    def __init__(self, shopping_repo, product_repo, analytics_repo):
        """
        Initializes the service with necessary repositories.
        :param shopping_repo: IShoppingListRepository - Handles shopping lists and base modes.
        :param product_repo: IProductRepository - Handles current inventory and nicknames.
        :param analytics_repo: IAnalyticsRepository - Handles access to generated insights.
        """
        self.shopping_repo = shopping_repo
        self.product_repo = product_repo
        self.analytics_repo = analytics_repo
        pass

    async def get_shopping_list(self, home_id: str):
        """
        Retrieves the current shopping list and enriches it with available 
        recommendations from the analytics repository.
        """
        list= await self.shopping_repo.get_list_by_home(home_id)
        if not list:
            list=ShoppingList(home_id=home_id)
            await self.shopping_repo.save_list(list)
        return list

    
    async def sync_list_with_base_mode(self, home_id: str):
        """
        Compares the Base Mode requirements with current stock levels.
        Identifies gaps and automatically populates the shopping list for the home.
        """
        pass

    async def add_item_to_list(self, home_id: str, item_name: str, quantity: int) -> ShoppingList:
        """
        Adds a specific product definition to the shopping list.
        """
        list = await self.shopping_repo.get_list_by_home(home_id)
        list.add_item(item_name, quantity)
        await self.shopping_repo.save_list(list)
        return list

    async def remove_item_from_list(self, home_id: str, item_id: str) -> ShoppingList:
        """
        Removes an item from the active shopping list.
        """
        list = await self.shopping_repo.get_list_by_home(home_id)
        list.remove_item(item_id)
        await self.shopping_repo.save_list(list)
        return list

    async def update_item_quantity(self, home_id: str, item_id: str, new_quantity: int) -> ShoppingList:
        """
        Updates the quantity of a specific item in the shopping list.
        """
        list = await self.shopping_repo.get_list_by_home(home_id)
        list.update_item_quantity(item_id, new_quantity)
        await self.shopping_repo.save_list(list)
        return list

    async def enter_shopping_mode(self, home_id: str)-> ShoppingList:
        """
        Marks the shopping list as active/in-shopping mode.
        """
        list = await self.shopping_repo.get_list_by_home(home_id)
        list.enter_shopping_mode()
        await self.shopping_repo.save_list(list)
        return list
    
    async def check_item_as_bought(self, home_id: str, item_name: str) -> ShoppingList:
        """
        Marks a specific item in the shopping list as bought.
        """
        list = await self.shopping_repo.get_list_by_home(home_id)
        list.check_item_as_bought(item_name)
        await self.shopping_repo.save_list(list)
        return list

    async def exit_shopping_mode(self, home_id: str, bought_items: List[str]) -> ShoppingList:
        """
        Marks the shopping list as inactive/not in shopping mode.
        """
        list = await self.shopping_repo.get_list_by_home(home_id)
        list.exit_shopping_mode(bought_items)
        await self.shopping_repo.save_list(list)
        return list
#--------------- Base Mode Management ---------------

    async def get_base_mode_config(self, home_id: str)-> BaseMode:
        """
        Retrieves the current Base Mode configuration (required stock levels) for the home.
        """
        base_mode= await self.shopping_repo.get_base_mode_by_home(home_id)
        if not base_mode:
            base_mode=BaseMode(home_id=home_id)
            await self.shopping_repo.save_base_mode(base_mode)
        return base_mode

    async def add_base_mode_item(self, home_id: str, item_name: str, required_quantity: int) -> BaseMode:
        """
        Adds a new product definition to the Base Mode configuration with a target quantity.
        """
        base_mode = await self.get_base_mode_config(home_id)
        base_mode.add_item(item_name, required_quantity)
        await self.shopping_repo.save_base_mode(base_mode)
        return base_mode

    async def remove_base_mode_item(self, home_id: str, item_name: str) -> BaseMode:
        """
        Removes a product definition from the Base Mode configuration.
        """
        base_mode = await self.get_base_mode_config(home_id)
        base_mode.remove_item(item_name)
        await self.shopping_repo.save_base_mode(base_mode)
        return base_mode

    async def update_base_mode_quantity(self, home_id: str, item_name: str, new_quantity: int)-> BaseMode:
        """
        Updates the required quantity for an existing product definition in the Base Mode.
        """
        base_mode = await self.get_base_mode_config(home_id)
        base_mode.update_item_quantity(item_name, new_quantity)
        await self.shopping_repo.save_base_mode(base_mode)
        return base_mode
