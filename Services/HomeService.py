from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date
from Domain.Repositories.IHomeRepository import IHomeRepository
from Domain.DomainServices.ManagementService import ManagementService
from Domain.DomainServices.StockService import StockService
from Domain.SmartHome.Home import Home

from Domain import DomainException
import Response
import Domain
from Domain.SmartHome import Product



class HomeService:
 
    def __init__(self,
                 i_home_repository: IHomeRepository,
                 management_service: ManagementService,
                 stock_service: StockService):
        self._i_home_repository: IHomeRepository = i_home_repository
        self._management_service: ManagementService = management_service
        self._stock_service: StockService = stock_service


    # ==========================================
    # 1. Home Management (House & Members)
    # ==========================================

    async def create_home(self, user_id: UUID, home_name: str) -> Response:
        """Creates a new home and sets the creator as ADMIN."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(user_id)      #check user is logged in 
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An error occurred while checking user login status: ")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        # Validation of home_name can be added with home repository checks
        try:
            home: Home = await self._i_home_repository.get_by_name(home_name)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking home name uniqueness.")
        
        if home is not None:
            return Response(isOk = False, error_message = "Home with the same name already exists.")
        
        # Create Home instance
        try:
            new_home: Home = self._management_service.create_new_home(user_id,home_name)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while creating the home.")

        # Save to repository
        try:
            await self._i_home_repository.save(new_home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while saving the home.")
        
        return Response(
            isOk = True,
            data = {
                "home name": home_name,
                "home id": str(new_home.get_id()),
                "join code": new_home.get_join_code(),
                "message": "Home created successfully."
            }
        )

    async def view_home_code(self, user_id: UUID, home_id: UUID) -> Response:
        """Retrieves the home join code (Admin only)."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(user_id) 
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        # Check if home exists
        try:
            home: Home = await self._i_home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            join_code = self._management_service.view_home_code(user_id, home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while viewing the home code.")
        
        return Response(
            isOk = True,
            data = {
                "home id": str(home_id),
                "join code": join_code
            }
        )

    async def join_home(self, user_id: UUID, home_code: str) -> Response:
        """
        User requests to join a home using a code.
        Creates a 'join request' waiting for approval.
        """
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        # Check if home exists
        try:
            home: Home = await self._i_home_repository.get_by_code(home_code)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            self._management_service.join_home(user_id, home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while joining the home.")
        
        try:
            await self._i_home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Join request sent successfully."})

    async def answer_join_request(self, home_id: UUID, head_user_id: UUID, user_id: UUID, approved: bool) -> Response:
        """Head of House approves or denies a join request."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(head_user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        try:
            home: Home = await self._i_home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            self._management_service.answer_join_request(head_user_id, home, user_id, approved)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while answering the join request.")
        
        try:
            await self._i_home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Join request answered successfully."})

    async def remove_member(self, head_user_id: UUID, home_id: UUID, target_user_id: UUID) -> Response:
        """Head of House removes a member from the home."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(head_user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        try:
            home: Home = await self._i_home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            self._management_service.remove_member(head_user_id, home, target_user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while removing the user.")
        
        try:
            await self._i_home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "User removed successfully."})

    async def switch_home(self, user_id: UUID, target_home_id: UUID) -> Response:
        """Switches user context to a different home (returns new home details)."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        try:
            target_home: Home = await self._i_home_repository.get_by_id(target_home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if target_home is None:
            return Response(isOk = False, error_message = "Home not found.")
        try:
            self._management_service.can_switch_home(user_id, target_home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while switching homes.")
        
        return Response(
            isOk = True,
            data = {
                "home id": str(target_home.get_id()),
                "home name": target_home.get_name(),
                "message": "Switched home successfully."
            }
        )

    async def leave_home(self, user_id: UUID, home_id: UUID) -> Response:
        """User voluntarily leaves a home."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        try:
            home: Home = await self._i_home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            self._management_service.leave_home(user_id, home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while leaving the home.")
        
        try:
            await self._i_home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Left home successfully."})

    async def switch_home_head(self, current_head_id: UUID, home_id: UUID, new_head_id: UUID) -> Response:
        """Transfers 'Head of House' role to another member."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(current_head_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        try:
            home: Home = await self._i_home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            self._management_service.switch_home_head(current_head_id, home, new_head_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while switching home head.")
        
        try:
            await self._i_home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Home head switched successfully."})

    async def delete_home(self, head_user_id: UUID, home_id: UUID) -> Response:
        """Permanently deletes the home and all associated data (Admin only)."""
        # Authentication session should provide user_id
        try:
            is_logged_in = self.Authentication_Adapter.is_logged_in(head_user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking user login status.")
        
        if not is_logged_in:
            return Response(isOk = False, error_message = "User not logged in")
        
        try:
            home: Home = await self._i_home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            self._management_service.can_delete_home(head_user_id, home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking delete permissions.")
        
        try:
            self._i_home_repository.delete(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while deleting the home.")
        
        return Response(isOk = True, data = {"message": "Home deleted successfully."})

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