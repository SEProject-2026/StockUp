import os
from sys import exception
from uuid import UUID, uuid4
from typing import Any, Callable, List, Optional, Dict
from datetime import date
from src.api.schemas.product_schemas import ProductDTO, ProductItemDTO
from src.domain.smart_home.product import Product
from src.repositories.i_product_repository import IProductRepository
from src.repositories.i_home_repository import IHomeRepository
from src.repositories.catalog_provider import ICatalogProvider
from src.repositories.catalog_provider import CatalogItem
from src.domain.smart_home.enums import ChainType, ExpirationType, LocationType
from src.infrastructure.scanner.receipt_scanner import ReceiptScanner
from src.domain.receipt import ReceiptItemDTO, ReceiptDTO

class StockService:
 
    def __init__(self, home_repository: IHomeRepository, product_repository: IProductRepository,
                  catalog_provider: ICatalogProvider):
        self._home_repository = home_repository
        self._product_repository = product_repository
        self._catalog_provider = catalog_provider

    # ==========================================
    # 2. Stock Management (Inventory)
    # ==========================================

    async def add_product(
        self, 
        name: str, 
        user_id: UUID, 
        home_id: UUID, 
        quantity: int,  
        barcode: Optional[str],
        expiration_date: Optional[date], 
        location: Optional[LocationType], 
        nickname: Optional[str]
    ) -> Product:
        
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_original_name(home_id, name)
        
        if not product:
            product = Product(
                id=uuid4(),
                home_id=home_id,
                original_name=name,
                barcode=barcode,
                nickname=nickname
            )
            
            product.add_item(quantity, location, expiration_date)
            
            await self._product_repository.save(product)
            
        else:
            if nickname:
                product.set_nickname(nickname)
                
            product.add_item(quantity, location, expiration_date)
            
            await self._product_repository.update(product)
            
        return product
        
    
    async def scan_receipt(
        self,
        user_id: UUID,
        home_id: UUID,
        file_path: str,                 
    ):
        """Processes a receipt and returns detected items for verification.
        If return_debug=True returns (ReceiptDTO, debug_dict)
        """
        await self._check_access(user_id, home_id)

        if not isinstance(file_path, (str, os.PathLike)):
            raise TypeError(f"file_path must be a path string, got: {type(file_path)}")

        scanner = ReceiptScanner()
        chain_name, scanned_items = scanner.parse_receipt(str(file_path))  # dict[barcode] -> (qty, unit)

        scanned_barcodes = list(scanned_items.keys())

        catalog_items = await self._catalog_provider.get_items_by_barcodes(
            scanned_barcodes,
            chain_name
        )
        catalog_items = catalog_items or []

        catalog_by_barcode = {
            ci.barcode: ci for ci in catalog_items if getattr(ci, "barcode", None)
        }

        receipt_items_dto: list[ReceiptItemDTO] = []
        for barcode in scanned_barcodes:
            qty, unit = scanned_items[barcode]
            ci = catalog_by_barcode.get(barcode)

            name = ci.name if ci else f"(לא נמצא בקטלוג) {barcode}"
            safe_unit = unit if unit else "יחידה" 
            storage_location = getattr(ci, "storage_location", None) if ci else None

            receipt_items_dto.append(
                ReceiptItemDTO(
                    barcode=barcode,
                    name=name,
                    quantity=float(qty),
                    unit=safe_unit,
                    storage_location=storage_location,
                )
            )

        receipt_dto = ReceiptDTO(
            id=uuid4(),
            home_id=home_id,
            user_id=user_id,
            chain=chain_name,
            items=receipt_items_dto,
        )

        return receipt_dto

        
    async def remove_item(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID) -> Optional[Product]:
        """
        Removes a specific item batch (line) from the product.
        If the product becomes empty (0 quantity), it deletes the product entity entirely.
        """
        await self._check_access(user_id, home_id)
        
        # 1. Get Product
        product = await self._product_repository.get_by_id(product_id)
        
        # Validation: Check existence and ownership
        if not product or product.home_id != home_id:
            raise ValueError("Product not found in this home")
        
        # 2. Domain Action (Delete logic is inside the Domain Entity)
        # This will raise ValueError if item_id doesn't exist
        product.remove_item(item_id)
        
        # 3. Persistence Logic
        if product.total_quantity > 0:
            # If items remain -> Update
            await self._product_repository.update(product)
            return product
        else:
            # If empty -> Delete the Aggregate Root
            await self._product_repository.delete(product_id)
            return None

    async def update_item_quantity(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_quantity: int) -> Optional[Product]:
        """
        Updates quantity. 
        Delegates the logic of "0 means delete" to the Product domain entity.
        """
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            raise ValueError("Product not found")

        # 1. Domain Action
        # The product itself handles whether to update or remove the item based on qty
        product.update_item_quantity(item_id, new_quantity)
        
        # 2. Persistence & Cleanup
        # If the Product is now empty (because we removed the last item), delete it.
        if product.total_quantity > 0:
            await self._product_repository.update(product)
            return product
        else:
            await self._product_repository.delete(product_id)
            return None

    async def update_item_date(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_date: Optional[date]) -> Product:
        """
        Updates the expiration date of a specific batch.
        The Product entity handles the logic: 
        If the new date matches an existing batch in the same location -> Merges them.
        """
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            raise ValueError("Product not found")

        # Domain Action (Handles Merge logic internally)
        product.update_item_date(item_id, new_date)
        
        await self._product_repository.update(product)
        return product
    
    async def update_item_location(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_location: LocationType) -> Product:
        """
        Moves a specific item to a new location (e.g. Pantry -> Fridge).
        """
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            raise ValueError("Product not found")

        # Domain Action
        product.update_item_location(item_id, new_location)
        
        await self._product_repository.update(product)
        return product
        

    async def update_nickname(self, user_id: UUID, home_id: UUID, product_id: UUID, new_nickname: str) -> Product:
        """
        Updates the display nickname of the product (e.g. 'Milk' -> 'Morning Coffee').
        """
        await self._check_access(user_id, home_id)

        product = await self._product_repository.get_by_id(product_id)
        
        # Validation: Direct property access
        if not product or product.home_id != home_id:
            raise ValueError("Product not found")

        # Domain Action
        product.set_nickname(new_nickname)
        
        await self._product_repository.update(product)
        return product


    async def filter_by_location(self, user_id: UUID, home_id: UUID, location: LocationType) -> List[ProductDTO]:
        """
        Returns products containing ONLY items in the specified location.
        Note: We still need 'warning_days' here to calculate the visual status (Red/Green) 
        for the returned items, even though we filter by location.
        """
        await self._check_access(user_id, home_id)
        
        products = await self._product_repository.list_all_by_home(home_id)
        
        # Future: warning_days = await self._home_repo.get_warning_days(home_id)
        warning_days = 3 
        
        dtos = []
        for p in products:
            # Filter condition: Item location must match
            dto = self._create_filtered_dto(
                product=p, 
                warning_days=warning_days,
                filter_func=lambda item: item.location == location
            )
            if dto:
                dtos.append(dto)
                
        return dtos

    async def filter_by_expiration_type(self, user_id: UUID, home_id: UUID, filter_type: ExpirationType) -> List[ProductDTO]:
        """
        Returns products containing ONLY items with the specified expiration status.
        """
        warning_days=await self._check_access(user_id, home_id)
        
        products = await self._product_repository.list_all_by_home(home_id)

        
        dtos = []
        for p in products:
            # Filter condition: Item status (calculated using warning_days) must match
            dto = self._create_filtered_dto(
                product=p,
                warning_days=warning_days, 
                filter_func=lambda item: item.get_status(warning_days) == filter_type
            )
            if dto:
                dtos.append(dto)
                
        return dtos

    # --- Private Helper Method ---

    def _create_filtered_dto(self, product: Product, warning_days: int, filter_func: Callable) -> Optional[ProductDTO]:
        """
        Internal helper to map Domain Entity to DTO while applying filters.
        Calculates the 'view_quantity' based only on the filtered items.
        """
        filtered_items_dtos = []
        view_total_quantity = 0

        for item in product.items:
            # 1. Apply the filter logic
            if filter_func(item):
                
                # 2. Calculate runtime status for display (Requires warning_days)
                status = item.get_status(warning_days)
                
                filtered_items_dtos.append(ProductItemDTO(
                    id=item.id,
                    quantity=item.quantity,
                    expiration_date=item.expiration_date,
                    location=item.location, 
                    status=status
                ))
                view_total_quantity += item.quantity

        # If all items were filtered out, do not return the product at all
        if not filtered_items_dtos:
            return None

        # Sort items: closest expiration date first (None/No-Date goes last)
        filtered_items_dtos.sort(key=lambda x: x.expiration_date or date.max)

        return ProductDTO(
            id=product.id,
            home_id=product.home_id,
            original_name=product.original_name,
            nickname=product.nickname,
            # display_name removed per request
            barcode=product.barcode,
            total_quantity=view_total_quantity, # Logical quantity (sum of filtered items)
            items=filtered_items_dtos
        )

    """searches for products based on product name or nickname."""
    async def search_product(self, user_id: UUID, home_id: UUID, query: str) -> List[Product]:
  
        await self._check_access(user_id, home_id)
        search_results = await self._product_repository.search_by_name(home_id, query)            
        return search_results


    async def search_product_by_name_external_db(self, user_id: UUID, home_id: UUID, query: str) -> List[CatalogItem]:

        await self._check_access(user_id, home_id)
        search_results = await self._catalog_provider.search_items_by_name(query)
        return search_results
    
    async def search_product_by_barcode_external_db(self, user_id: UUID, home_id: UUID, barcode: str, chain_name: Optional[ChainType] = None) -> Optional[CatalogItem]:

        await self._check_access(user_id, home_id)
        item = await self._catalog_provider.get_item_by_barcode(barcode, chain_name)
        return item
    
    async def get_home_products(self, user_id: UUID, home_id: UUID) -> List[Product]:
        """Retrieves all products in the home's inventory."""
        await self._check_access(user_id, home_id)
        products = await self._product_repository.list_all_by_home(home_id)
        return products
    
    #provides the expiration range for the home after verifying user access
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