from ast import List


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
        pass
    
    async def sync_list_with_base_mode(self, home_id: str):
        """
        Compares the Base Mode requirements with current stock levels.
        Identifies gaps and automatically populates the shopping list for the home.
        """
        pass

    async def add_item_to_list(self, home_id: str, item_name: str, quantity: int):
        """
        Adds a specific product definition to the shopping list.
        """
        pass

    async def remove_item_from_list(self, home_id: str, item_id: str):
        """
        Removes an item from the active shopping list.
        """
        pass

    async def update_item_quantity(self, home_id: str, item_id: str, new_quantity: int):
        """
        Updates the quantity of a specific item in the shopping list.
        """
        pass

    async def enter_shopping_mode(self, home_id: str):
        """
        Marks the shopping list as active/in-shopping mode.
        """
        pass

    async def exit_shopping_mode(self, home_id: str, bought_items: List[str]):
        """
        Marks the shopping list as inactive/not in shopping mode.
        """
        pass
#--------------- Base Mode Management ---------------

    async def get_base_mode_config(self, home_id: str):
        """
        Retrieves the current Base Mode configuration (required stock levels) for the home.
        """
        pass

    async def add_base_mode_item(self, home_id: str, item_name: str, required_quantity: int):
        """
        Adds a new product definition to the Base Mode configuration with a target quantity.
        """
        pass

    async def remove_base_mode_item(self, home_id: str, item_name: str):
        """
        Removes a product definition from the Base Mode configuration.
        """
        pass

    async def update_base_mode_quantity(self, home_id: str, item_name: str, new_quantity: int):
        """
        Updates the required quantity for an existing product definition in the Base Mode.
        """
        pass
