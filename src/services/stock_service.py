from sys import exception
from uuid import UUID, uuid4
from typing import Any, List, Optional, Dict
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

    async def add_product(self, name: str, user_id: UUID, home_id: UUID, quantity: int,  barcode: Optional[str],
                          expiration_date: Optional[date], location: Optional[LocationType], nickname: Optional[str]) -> Product:

        home_expr_range = await self._check_access(user_id, home_id)
        product = await self._product_repository.get_by_name(home_id, name)
        if not product:
            product = (
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
            await self._product_repository.save(product)
        else:
            await product.add_to_existing_product(expiration_date, quantity, home_expr_range)
            await self._product_repository.update(product)
        return product
        
    
    async def scan_receipt(self, user_id: UUID, home_id: UUID, file_path: Any) -> ReceiptDTO:
        """Processes a receipt image (OCR) and returns detected items for verification."""
        await self._check_access(user_id, home_id)

        scanner = ReceiptScanner()
        chain_name, scanned_items = scanner.parse_receipt(file_path) 

        items = await self._catalog_provider.get_items_by_barcodes( 
            scanned_items.keys(),
            chain_name
        )

        receipt_items_dto = [
            ReceiptItemDTO(
                barcode=i.barcode,
                name=i.name,
                quantity=scanned_items[i.barcode][0],
                unit=scanned_items[i.barcode][1],
            )
            for i in items
            if i.barcode in scanned_items 
        ]

        receipt_dto = ReceiptDTO(
            id=uuid4(),
            home_id=home_id,
            user_id=user_id,
            chain=chain_name,          
            items=receipt_items_dto,
        )
        return receipt_dto

        
    async def remove_product(self, user_id: UUID, home_id: UUID, product_id: UUID, date: Optional[date]) -> Optional[Product]:
        
        await self._check_access(user_id, home_id)
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            raise ValueError("Product not found in this home")
        
        product = await product.remove_product_date(date)
        if product.get_quantity() > 0:
            await self._product_repository.update(product)
            return product
        else:
            await self._product_repository.delete(product_id)
            return None


    async def update_date_quantity(self, user_id: UUID, home_id: UUID, product_id: UUID, date: date, new_quantity: int) -> Optional[Product]:

        await self._check_access(user_id, home_id)
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            raise ValueError("Product not found")
        
        product = await product.update_date_quantity(date, new_quantity)
        if product.get_quantity() > 0:
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
        return product
        

    async def update_nickname(self, user_id: UUID, home_id: UUID, product_id: UUID, new_nickname: str) -> Product:

        await self._check_access(user_id, home_id)

        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            raise ValueError("Product not found in this home")
        product.set_nickname(new_nickname)
        await self._product_repository.update(product)
        return product


    async def filter_by_expiration_type(self, user_id: UUID, home_id: UUID, filter_type: ExpirationType) -> List[ProductDTO]:
       
        await self._check_access(user_id, home_id)
        products = await self._product_repository.list_all_by_home(home_id)
        filtered_dtos = []
        for p in products:
            dto = self._create_filtered_dto(p, filter_type)
            if dto:
                filtered_dtos.append(dto)
        return filtered_dtos
    

    def _create_filtered_dto(self, product: Product, filter_type: ExpirationType) -> Optional[ProductDTO]:

        product_dates = product.get_expiration_dates()
        filtered_items = []
        view_quantity = 0

        for exp_date, (date_quantity, exp_type) in product_dates.items():
            if exp_type == filter_type:
                filtered_items.append(ProductItemDTO(
                    expiration_date=exp_date,
                    quantity=date_quantity,
                    status=exp_type
                ))
                view_quantity += date_quantity

        if not filtered_items:
            return None
        filtered_items.sort(key=lambda x: x.expiration_date or date.max)

        # use view_quantity for  total, not product.get_quantity()
        return ProductDTO(
            id=product.get_id(),
            home_id=product.get_home_id(),
            original_name=product.get_original_name(),
            nickname=product.get_nickname(),
            barcode=product.get_barcode(),
            location=product.get_location(),
            quantity=view_quantity, 
            items=filtered_items
        )


    async def filter_by_location(self, user_id: UUID, home_id: UUID, location: LocationType) -> List[Product]:
 
        await self._check_access(user_id, home_id)
        filtered_products = await self._product_repository.get_by_location(home_id, location)
        return filtered_products

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