from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date
from Domain.Repositories.IHomeRepository import IHomeRepository
from Domain.DomainServices.ManagementService import ManagementService
from Domain.SmartHome.Home import Home

from Domain import DomainException
import Response
import Domain
from Domain.SmartHome import Product



class HomeService:
 
    def __init__(self,
                 i_home_repository: IHomeRepository,
                 management_service: ManagementService):
        self.__i_home_repository: IHomeRepository = i_home_repository
        self.__management_service: ManagementService = management_service


    # ==========================================
    # 1. Home Management (House & Members)
    # ==========================================

    async def create_home(self, user_id: UUID, home_name: str) -> Dict:
        """Creates a new home and sets the creator as ADMIN."""
        # Authentication session should provide user_id
        
        # Validation of home_name can be added with home repository checks
        home: Home = await self.__i_home_repository.get_by_name(home_name)
        if home is not None:
            raise ValueError("Home name already exists.")
        
        # Create Home instance
        new_home: Home = self.__management_service.create_new_home(user_id,home_name)

        # Save to repository
        await self.__i_home_repository.save(new_home)

        return {
            "home name": home_name,
            "home id": str(new_home.__id),
            "join code": new_home.__join_code,
            "message": "Home created successfully."
        }


    async def view_home_code(self, user_id: UUID, home_id: UUID) -> str:
        """Retrieves the home join code (Admin only)."""
        # Authentication session should provide user_id

        # Check if home exists
        home: Home = await self.__i_home_repository.get_by_id(home_id)
        if home is None:
            raise ValueError("Home not found.")
        
        return self.__management_service.view_home_code(user_id, home)


    async def join_home(self, user_id: UUID, home_code: str) -> bool:
        """
        User requests to join a home using a code.
        Creates a 'join request' waiting for approval.
        """
        # Authentication session should provide user_id

        # Check if home exists
        home: Home = await self.__i_home_repository.get_by_code(home_code)
        if home is None:
            raise ValueError("Invalid home code.")
        
        return self.__management_service.join_home(user_id, home)


    async def answer_join_request(self, head_user_id: UUID, request_id: UUID, approved: bool) -> bool:
        """Head of House approves or denies a join request."""
        raise NotImplementedError("answer_join_request not implemented yet")

    async def remove_user(self, head_user_id: UUID, home_id: UUID, target_user_id: UUID) -> bool:
        """Head of House removes a user from the home."""
        raise NotImplementedError("remove_user not implemented yet")

    async def switch_home(self, user_id: UUID, target_home_id: UUID) -> Dict:
        """Switches user context to a different home (returns new home details)."""
        raise NotImplementedError("switch_home not implemented yet")

    async def leave_home(self, user_id: UUID, home_id: UUID) -> bool:
        """User voluntarily leaves a home."""
        raise NotImplementedError("leave_home not implemented yet")

    async def switch_home_head(self, current_head_id: UUID, home_id: UUID, new_head_id: UUID) -> bool:
        """Transfers 'Head of House' role to another member."""
        raise NotImplementedError("switch_home_head not implemented yet")

    async def delete_home(self, head_user_id: UUID, home_id: UUID) -> bool:
        """Permanently deletes the home and all associated data (Admin only)."""
        raise NotImplementedError("delete_home not implemented yet")

    # ==========================================
    # 2. Stock Management (Inventory)
    # ==========================================

    ################################ should date be a list of dates?
    async def add_product(self, user_id: UUID, home_id: UUID, product_name: str, quantity: int, 
                          expiration_date: Optional[date], location_id: Optional[UUID]) -> Response:
        is_logged_in = self.Authentication_Adapter.is_logged_in(user_id)      #check user is logged in 
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        user = self.user_repo.get_user_by_id(user_id)                            #check user exists in system
        if user is None:
            return Response(isOk = False, error_message = "User not found in system")
        home = self.home_repo.get_home_by_id(home_id)
        if home is None:
            return Response(isOk = False, error_message = "Home not found in system")     #check home exists in system
        product_to_add = Product(self.inventory_repo.get_next_id(), name = product_name, quantity = quantity, 
                                expiration_date = expiration_date, location_id = location_id)
        try:
            self.StockService.add_product(home, product_to_add)
        except DomainException as de:                               # catch domain logic error 
            return Response(isOk = False, error_message = str(de))
        except Exception as e:                                      # catch unexpected error
            return Response(isOk = False, error_message = "An internal error occurred while adding the product.")
        self.home_repo.save(home)
        return Response(isOk = True, data = home.inventory)
        
    async def scan_receipt(self, user_id: UUID, home_id: UUID, image_file: bytes) -> List[Dict]:
        """Processes a receipt image (OCR) and returns detected items for verification."""
        raise NotImplementedError("Not implemented yet")

    async def remove_product(self, user_id: UUID, product_id: UUID) -> bool:
        """Removes a product from inventory."""
        raise NotImplementedError("Not implemented yet")

    async def update_stock_quantity(self, user_id: UUID, product_id: UUID, new_quantity: int) -> Dict:
        """Updates the quantity of an existing inventory item."""
        raise NotImplementedError("Not implemented yet")

    async def update_expiration_date(self, user_id: UUID, product_id: UUID, new_date: date) -> Dict:
        """Updates the expiration date of an item."""
        raise NotImplementedError("Not implemented yet")

    async def update_nickname(self, user_id: UUID, product_id: UUID, new_nickname: str) -> Dict:
        """Updates the item's nickname/display name."""
        raise NotImplementedError("Not implemented yet")

    async def filter_by_expiration_type(self, home_id: UUID, filter_type: str) -> List[Dict]:
        """
        Filters inventory by expiration status.
        filter_type expected values: 'expired', 'soon', 'ok'.
        """
        raise NotImplementedError("Not implemented yet")

    async def filter_by_location(self, home_id: UUID, location_id: UUID) -> List[Dict]:
        """Filters inventory by storage location (e.g., Fridge, Pantry)."""
        raise NotImplementedError("Not implemented yet")

    async def filter_by_category(self, home_id: UUID, category_name: str) -> List[Dict]:
        """Filters inventory by product category."""
        raise NotImplementedError("Not implemented yet")

    async def search_product(self, home_id: UUID, query: str) -> List[Dict]:
        """Free text search in inventory."""
        raise NotImplementedError("Not implemented yet")

    # ==========================================
    # 3. Shopping List (Active & Base Mode)
    # ==========================================

    async def trigger_shopping_list_update(self, home_id: UUID):
        """Triggers a real-time update (WebSocket/Push) to all home members."""
        raise NotImplementedError("Not implemented yet")

    # --- Base Mode (Configuration) ---

    async def add_item_to_base_stock(self, head_user_id: UUID, home_id: UUID, 
                                     product_name: str, ideal_quantity: int) -> Dict:
        """Adds an item to the 'Base Mode' (ideal stock) configuration."""
        raise NotImplementedError("Not implemented yet")

    async def remove_item_from_base_stock(self, head_user_id: UUID, base_product_id: UUID) -> bool:
        """Removes an item from the 'Base Mode' configuration."""
        raise NotImplementedError("Not implemented yet")

    async def update_base_stock_quantity(self, head_user_id: UUID, base_product_id: UUID, new_quantity: int) -> Dict:
        """Updates the ideal quantity for a Base Mode item."""
        raise NotImplementedError("Not implemented yet")

    # --- Active Shopping List ---

    async def add_shopping_item(self, user_id: UUID, home_id: UUID, product_name: str, quantity: int) -> Dict:
        """Manually adds an item to the shopping list."""
        raise NotImplementedError("Not implemented yet")

    async def remove_shopping_item(self, user_id: UUID, list_product_id: UUID) -> bool:
        """Removes an item from the shopping list."""
        raise NotImplementedError("Not implemented yet")

    async def update_shopping_item_quantity(self, user_id: UUID, list_product_id: UUID, new_quantity: int) -> Dict:
        """Updates the quantity of an item in the shopping list."""
        raise NotImplementedError("Not implemented yet")

    # --- Shopping Mode ---

    async def enter_shopping_mode(self, user_id: UUID, home_id: UUID) -> bool:
        """Enters 'Shopping Mode' (locks external edits, prepares for checklist)."""
        raise NotImplementedError("Not implemented yet")

    async def mark_shopping_item(self, user_id: UUID, list_product_id: UUID, is_checked: bool) -> Dict:
        """Marks an item as 'in cart' (checked/unchecked)."""
        raise NotImplementedError("Not implemented yet")

    async def exit_shopping_mode(self, user_id: UUID, home_id: UUID, complete_purchase: bool) -> Dict:
        """
        Exits 'Shopping Mode'. 
        If complete_purchase is True, moves checked items to Inventory and clears them from the list.
        """
        raise NotImplementedError("Not implemented yet")