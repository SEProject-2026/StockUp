from uuid import UUID
from typing import List, Optional, Dict
from datetime import date
from src.domain.smart_home.product import Product
from src.repositories.i_catalog_repositoy import ICatalogRepository
from src.repositories.i_product_repository import IProductRepository
from src.repositories.i_home_repository import IHomeRepository
from src.domain.smart_home.enums import ChainType, ExpirationType, LocationType
from src.response import Response

class StockService:
 
    def __init__(self, home_repository: IHomeRepository, product_repository: IProductRepository,
                  catalog_repository: ICatalogRepository):
        self._home_repository = home_repository
        self._product_repository = product_repository
        self._catalog_repository = catalog_repository

    # ==========================================
    # 2. Stock Management (Inventory)
    # ==========================================

    async def add_product(self, chain: Optional[ChainType], name: str, user_id: UUID, home_id: UUID, quantity: int,  barcode: Optional[str],
                          expiration_date: Optional[date], location: Optional[LocationType], nickname: Optional[str]) -> Response[str]:
        
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response
        except Exception as e:
            print(e)
            return Response(isOk=False, error_message=f"Permission validation failed: {e}")
        
        try:
            # checking catalog only if product name not found in local DB
            # assuming if no barcode return value is none
            catalog_product = await self._catalog_repository.get_product_details(barcode, chain)
            
    
            if not catalog_product:
                await self._catalog_repository.save(barcode=barcode, chain=chain, name=name)
                catalog_product_name = name
            else:
                catalog_product_name = catalog_product.name
        except Exception as e:
            print(f"Catalog Error: {e}")
            return Response(isOk=False, error_message="Error retrieving product details")

        try:
            home = await self._home_repository.get_by_id(home_id)
            expiration_range = home.get_expiration_range()
            new_product_entity = (
                Product.builder(
                    home_id=home_id,
                    name=catalog_product_name,
                    quantity=quantity,
                    expiration_range=expiration_range
                )
                .with_barcode(barcode)
                .with_nickname(nickname)
                .with_location(location)
                .with_expiration_date(expiration_date)
                .build()
            )
        except ValueError as ve:
             return Response(isOk=False, error_message=str(ve))
        except Exception as e:
             return Response(isOk=False, error_message=f"Domain logic error: {e}")
        try:
            await self._product_repository.save(new_product_entity)
            return Response(isOk=True, data="Product added successfully")
        except Exception as e:
            return Response(isOk=False, error_message=f"Database save error: {e}")
        
    ##########################################################################################
    async def scan_receipt(self, user_id: UUID, home_id: UUID, image_file: bytes) -> List[Dict]:
        """Processes a receipt image (OCR) and returns detected items for verification."""
        raise NotImplementedError("Not implemented yet")
    ###########################################################################################

    async def remove_product(self, user_id: UUID, home_id: UUID, product_id: UUID) -> Response:
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response
            product = await self._product_repository.get_by_id(product_id)
            if not product or product.get_home_id() != home_id:
                return Response(isOk=False, error_message="Product not found in this home")
            try:
                await self._product_repository.delete(product_id)
                return Response(isOk=True, data="Product removed successfully.")
            except Exception as e:
                return Response(isOk=False, error_message=f"Error removing product: {e}")
        except Exception as e:
            print(e)
            return Response(isOk=False, error_message=f"Permission validation failed: {e}")

    async def update_stock_quantity(self, user_id: UUID, home_id: UUID, product_id: UUID, new_quantity: int) -> Response:
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response
            
            product = await self._product_repository.get_by_id(product_id)
            if not product or product.get_home_id() != home_id:
                return Response(isOk=False, error_message="Product not found")
            
            product.set_quantity(new_quantity)
            await self._product_repository.update(product)
            return Response(isOk=True, data="Quantity updated successfully.")
        
        except ValueError as ve:
             return Response(isOk=False, error_message=str(ve))
        except Exception as e:
            return Response(isOk=False, error_message=f"Error updating quantity: {e}")

    async def update_expiration_date(self, user_id: UUID,  home_id: UUID, product_id: UUID, old_date: date, new_date: date) -> Response[str]:
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response

            product = await self._product_repository.get_by_id(product_id)
            if not product or product.get_home_id() != home_id:
                return Response(isOk=False, error_message="Product not found in this home")

            expiration_range = await self._home_repository.get_by_id(home_id).get_default_expiration_range()
            product.update_expiration_date(old_date, new_date, expiration_range)
            await self._product_repository.update(product)
            return Response(isOk=True, data="Expiration date updated successfully.")
        
        except ValueError as ve:
             return Response(isOk=False, error_message=str(ve))
        except Exception as e:
            return Response(isOk=False, error_message=f"Error updating expiration date: {e}")
        
    async def update_nickname(self, user_id: UUID, home_id: UUID, product_id: UUID, new_nickname: str) -> Response[str]:
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response

            product = await self._product_repository.get_by_id(product_id)
            if not product or product.get_home_id() != home_id:
                return Response(isOk=False, error_message="Product not found in this home")

            product.set_nickname(new_nickname)
            await self._product_repository.update(product)
            return Response(isOk=True, data="Nickname updated successfully.")
        
        except ValueError as ve:
             return Response(isOk=False, error_message=str(ve))
        except Exception as e:
            return Response(isOk=False, error_message=f"Error updating nickname: {e}")

    async def filter_by_expiration_type(self, user_id: UUID, home_id: UUID, filter_type: ExpirationType) -> Response:
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response

            filtered_products = await self._product_repository.get_by_expiration_filter(home_id, filter_type)
            
            data = [p.to_dict() for p in filtered_products]
            return Response(isOk=True, data=data)
        
        except Exception as e:
            return Response(isOk=False, error_message=f"Error filtering products: {e}")

    async def filter_by_location(self, user_id: UUID, home_id: UUID, location: LocationType) -> Response[List[Dict]]:
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response

            filtered_products = await self._product_repository.get_by_location(home_id, location)
            
            data = [p.to_dict() for p in filtered_products]
            return Response(isOk=True, data=data)
        except Exception as e:
            return Response(isOk=False, error_message=f"Error filtering products by location: {e}")

    """searches for products based on product name or nickname."""
    async def search_product(self, user_id: UUID, home_id: UUID, query: str) -> Response:
        try:
            valid_member_response = await self._check_access(user_id, home_id)
            if valid_member_response.isError():
                return valid_member_response

            search_results = await self._product_repository.search_by_name(home_id, query)
            
            data = [p.to_dict() for p in search_results]
            return Response(isOk=True, data=data)

        except Exception as e:
            return Response(isOk=False, error_message=f"Error searching products: {e}")
    
    async def _check_access(self, user_id: UUID, home_id: UUID) -> Response:
        """Helper to verify user exists, logged in, and member of the home"""
        home = await self._home_repository.get_by_id(home_id)
        if not home: 
            return Response(isOk=False, error_message="Home not found")
        #error message for non-members, caller will check isError()
        return Response(isOk=home.is_member(user_id), error_message="User is not a member of the home")
    
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