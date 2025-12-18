from sys import exception
from uuid import UUID
from typing import List, Optional, Dict
from datetime import date
from src.domain.smart_home.catalog_item import CatalogItem
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

    async def add_product(self, name: str, user_id: UUID, home_id: UUID, quantity: int,  barcode: Optional[str],
                          expiration_date: Optional[date], location: Optional[LocationType], nickname: Optional[str]) -> Product:

        home_expr_range = await self._check_access(user_id, home_id)
        products = await self._product_repository.search_by_name(home_id, name)
        if len(products) == 0:
            new_product_entity = (
                Product.builder(
                    home_id=home_id,
                    name=name,
                    quantity=quantity,
                    expiration_range=home_expr_range
                )
                .with_barcode(barcode)
                .with_nickname(nickname)
                .with_location(location)
                .with_expiration_date(expiration_date)
                .build()
            )
            await self._product_repository.save(new_product_entity)
        else:
            existing_product = products[0]
            await existing_product.update_quantity(quantity + existing_product.get_quantity(), expiration_date)
            await self._product_repository.update(existing_product)

        
    ##########################################################################################
    async def scan_receipt(self, user_id: UUID, home_id: UUID, image_file: bytes) -> List[Dict]:
        """Processes a receipt image (OCR) and returns detected items for verification."""
        raise NotImplementedError("Not implemented yet")
    ###########################################################################################

    async def remove_product(self, user_id: UUID, home_id: UUID, product_id: UUID, date: date) -> Optional[Product]:
        valid_member_response = await self._check_access(user_id, home_id)
        if valid_member_response.isError():
            raise ValueError(valid_member_response.get_error_message())
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            raise ValueError("Product not found in this home")
        
        product_total_quantity = await product.update_quantity_and_removal(date)
        if product_total_quantity > 0:
            await self._product_repository.update(product)
            return product
        else:
            await self._product_repository.delete(product_id)
            return None


    async def update_stock_quantity(self, user_id: UUID, home_id: UUID, product_id: UUID, date: date, new_quantity: int) -> Optional[Product]:

        await self._check_access(user_id, home_id)
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            raise ValueError("Product not found")
        
        product_total_quantity = await product.update_quantity(date, new_quantity)
        if product_total_quantity > 0:
            await self._product_repository.update(product)
            return product
        else:
            await self._product_repository.delete(product_id)
            return None


    async def update_expiration_date(self, user_id: UUID,  home_id: UUID, product_id: UUID, old_date: date, new_date: date) -> Product:

        expiration_range = await self._check_access(user_id, home_id)
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            raise ValueError("Product not found in this home")

        product.update_expiration_date(old_date, new_date, expiration_range)
        await self._product_repository.update(product)
        

    async def update_nickname(self, user_id: UUID, home_id: UUID, product_id: UUID, new_nickname: str) -> Product:

        await self._check_access(user_id, home_id)

        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            raise ValueError("Product not found in this home")
        product.set_nickname(new_nickname)
        await self._product_repository.update(product)
        return product


    async def filter_by_expiration_type(self, user_id: UUID, home_id: UUID, filter_type: ExpirationType) -> List[Product]:
       
        await self._check_access(user_id, home_id)
        filtered_products = await self._product_repository.get_by_expiration_filter(home_id, filter_type)
        return filtered_products


    async def filter_by_location(self, user_id: UUID, home_id: UUID, location: LocationType) -> List[Product]:
 
        await self._check_access(user_id, home_id)
        filtered_products = await self._product_repository.get_by_location(home_id, location)
        return filtered_products


    """searches for products based on product name or nickname."""
    async def search_product(self, user_id: UUID, home_id: UUID, query: str) -> List[Product]:
  
        await self._check_access(user_id, home_id)
        search_results = await self._product_repository.search_by_name(home_id, query)
            
        return search_results
    

    async def search_product_external_db(self, user_id: UUID, home_id: UUID, query: str) -> List[str]:

        await self._check_access(user_id, home_id)
        search_results = await self._catalog_repository.search_by_name(query)
        return [ci.__repr__() for ci in search_results]
    
    async def _check_access(self, user_id: UUID, home_id: UUID) -> int:
        """Helper to verify user exists, logged in, and member of the home"""
        home = await self._home_repository.get_by_id(home_id)
        if not home:
            raise ValueError("Home retrieval failed.")
        if not home.is_member(user_id):
            raise ValueError("User is not a member of the home")
        return home.get_expiration_range()
    
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