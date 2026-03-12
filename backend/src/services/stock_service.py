import asyncio
import os
from uuid import UUID, uuid4
from typing import Any, Callable, List, Optional, Dict
from datetime import date

from src.api.schemas.product_schemas import ProductDTO, ProductItemDTO
from src.domain.smart_home.product import Product
from src.repositories.i_product_repository import IProductRepository
from src.repositories.i_home_repository import IHomeRepository
from src.repositories.catalog_provider import ICatalogProvider
from src.repositories.catalog_provider import CatalogItem
from src.domain.smart_home.enums import ExpirationType, LocationType, UnitType
from src.infrastructure.scanner.receipt_scanner import ReceiptScanner
from src.domain.receipt import ReceiptItemDTO, ReceiptDTO
from src.infrastructure.logger import app_logger
from src.repositories.user_repository import IUserRepository
from src.services.notification_service import send_push_notification

class StockService:
 
    def __init__(self, home_repository: IHomeRepository, product_repository: IProductRepository,
                  catalog_provider: ICatalogProvider, user_repository: IUserRepository):
        self._home_repository = home_repository
        self._product_repository = product_repository
        self._catalog_provider = catalog_provider
        self._user_repository = user_repository

    # ==========================================
    # 2. Stock Management (Inventory)
    # ==========================================

    async def add_product(
        self, 
        name: str, 
        user_id: UUID, 
        home_id: UUID, 
        quantity: int,  
        barcode: Optional[str] = None,
        expiration_date: Optional[date] = None, 
        location: Optional[LocationType] = LocationType.OTHER, 
        nickname: Optional[str] = None
    ) -> Optional[Product]:
        """Standard operation for single item additions."""
        app_logger.debug(f"Starting add_product process for '{name}' (home_id: {home_id})")
        await self._check_access(user_id, home_id)
        
        if name == "Unknown Product":
            app_logger.warning(f"Add product rejected: Attempted to add 'Unknown Product' in home {home_id}")
            return None

        product = await self._product_repository.get_by_original_name(home_id, name)
        
        if not product:
            product = Product(id=uuid4(), home_id=home_id, original_name=name, barcode=barcode, nickname=nickname)
        
        if nickname:
            product.set_nickname(nickname)
            
        product.add_item(quantity, location, expiration_date)
        
        await self._product_repository.save(product)
        app_logger.info(f"Successfully added/updated product '{name}' with quantity {quantity} in home {home_id}")
        return product
        
    
    async def scan_receipt(
        self,
        user_id: UUID,
        home_id: UUID,
        files_paths: List[str],  
    ) -> ReceiptDTO:
        app_logger.debug(f"Starting receipt scan for home {home_id} with {len(files_paths)} files")
        await self._check_access(user_id, home_id)

        if not isinstance(files_paths, list) or not files_paths:
            app_logger.warning("Receipt scan failed: files_paths is empty or not a list")
            raise ValueError("files_paths must be a non-empty list of file paths")

        if not all(isinstance(fp, (str, os.PathLike)) for fp in files_paths):
            app_logger.warning("Receipt scan failed: Invalid file path types provided")
            raise TypeError("files_paths must contain only path strings")

        valid_paths = [str(fp) for fp in files_paths if fp and os.path.exists(str(fp))]
        if not valid_paths:
            app_logger.warning("Receipt scan failed: No valid existing files found in the provided paths")
            raise ValueError("No valid files found in files_paths")

        scanner = ReceiptScanner()

        first = valid_paths[0]
        rest = valid_paths[1:]
        
        app_logger.debug("Parsing receipt files through ML scanner...")
        chain_name, scanned_items = scanner.parse_receipt(first, *rest)

        receipt_items_dto: list[ReceiptItemDTO] = []

        for barcode, (qty, unit_str) in scanned_items.items():
            unit = UnitType(unit_str) if unit_str in UnitType.__members__ else UnitType.UNIT
            ci = await self._catalog_provider.get_item_by_barcode(barcode, chain_name)

            if ci:
                avg_unit_weight = 1
                if unit == UnitType.KG:
                    avg_unit_weight = ci.weight
                    new_qty = qty / avg_unit_weight if avg_unit_weight else 1
                else:
                    new_qty = qty

                receipt_items_dto.append(
                    ReceiptItemDTO(
                        barcode=barcode,
                        name=ci.name,
                        quantity=int(new_qty),
                        unit=unit,
                        location=ci.location,
                        weight=qty if unit == UnitType.KG else None,
                    )
                )
            else:
                receipt_items_dto.append(
                    ReceiptItemDTO(
                        name="Unknown Product",
                        barcode=barcode,
                        quantity=int(qty) if unit == UnitType.UNIT else 1,
                        unit=unit,
                    )
                )

        app_logger.info(f"Successfully scanned receipt from '{chain_name}' with {len(receipt_items_dto)} items")
        return ReceiptDTO(
            id=uuid4(),
            home_id=home_id,
            user_id=user_id,
            chain=chain_name,
            items=receipt_items_dto,
        )

    async def add_receipt(self, receipt_dto: ReceiptDTO) -> int:
        """High-performance operation for full receipts."""
        app_logger.debug(f"Processing receipt addition for home {receipt_dto.home_id} with {len(receipt_dto.items)} items")
        await self._check_access(receipt_dto.user_id, receipt_dto.home_id)
        
        existing_products = await self._product_repository.list_all_by_home(receipt_dto.home_id)
        products_map = {p.original_name: p for p in existing_products}
        
        products_to_save = {}
        catalog_updated = False
        count = 0
        
        for item in receipt_dto.items:
            if item.name == "Unknown Product":
                continue
            
            if item.unit == UnitType.KG and item.quantity > 0:
                current_measured_avg = item.weight / item.quantity
                self._catalog_provider.update_weighted_mem_only(
                    barcode=item.barcode,
                    chain_name=receipt_dto.chain,
                    measured_weight=current_measured_avg
                )
                catalog_updated = True
            
            product = products_map.get(item.name)
            if not product:
                product = Product(
                    id=uuid4(),
                    home_id=receipt_dto.home_id,
                    original_name=item.name,
                    barcode=item.barcode,
                    nickname=item.nickname
                )
                products_map[item.name] = product
                
            if item.nickname:
                product.set_nickname(item.nickname)
                
            product.add_item(item.quantity, item.location, item.expiration_date)
            
            products_to_save[product.id] = product
            count += 1

        if products_to_save:
            await self._product_repository.save_all(list(products_to_save.values()))
            app_logger.info(f"Bulk saved {len(products_to_save)} products to DB for home {receipt_dto.home_id}")
        
        if catalog_updated:
            self._catalog_provider.persist()
            app_logger.debug("Catalog weights persisted successfully")

        try:
            home = await self._home_repository.get_by_id(receipt_dto.home_id)
            scanner_user = await self._user_repository.get_by_id(receipt_dto.user_id)
            
            scanner_name = scanner_user.name if scanner_user else "אחד השותפים"
            home_name = home.get_name()
            members = home.get_members()

            if count > 0:
                for member_id in members:
                    if member_id == receipt_dto.user_id:
                        continue
                        
                    target_user = await self._user_repository.get_by_id(member_id)
                    if target_user and target_user.push_token:
                        send_push_notification(
                            token=target_user.push_token,
                            title=f"מלאי חדש ב{home_name}! 🛒",
                            message=f"{scanner_name} הוסיף {count} מוצרים חדשים.",
                            data={"action": "receipt_added", "home_id": str(receipt_dto.home_id)}
                        )
                app_logger.info(f"Receipt scan notifications sent to members of home {receipt_dto.home_id}")
                
        except Exception as e:
            app_logger.error(f"Failed to send receipt notifications: {e}")

        return count
        
    async def remove_item(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID) -> Optional[Product]:
        """
        Removes a specific item batch (line) from the product.
        If the product becomes empty, it deletes the product entity entirely.
        """
        app_logger.debug(f"Attempting to remove item {item_id} from product {product_id}")
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_id(product_id)
        
        if not product or product.home_id != home_id:
            app_logger.warning(f"Item removal failed: Product {product_id} not found or access denied for home {home_id}")
            raise ValueError("Product not found in this home")
        
        product.remove_item(item_id)
        
        if product.total_quantity > 0:
            await self._product_repository.update(product)
            app_logger.info(f"Removed item {item_id}. Product {product_id} updated with new total: {product.total_quantity}")
            return product
        else:
            await self._product_repository.delete(product_id)
            app_logger.info(f"Removed last item {item_id}. Product {product_id} deleted completely.")
            
            # Note: when implementing shopping list

            # try:
            #     home = await self._home_repository.get_by_id(home_id)
            #     if home and home.get_admin():
            #         admin_user = await self._user_repository.get_by_id(home.get_admin())
                    
            #         if admin_user and admin_user.push_token:
            #             product_name = product.nickname if product.nickname else product.original_name
                        
            #             send_push_notification(
            #                 token=admin_user.push_token,
            #                 title="מוצר אזל מהמלאי! ⚠️",
            #                 message=f"המוצר '{product_name}' נגמר. תרצה שנוסיף לרשימת הקניות?.",
            #                 data={"action": "out_of_stock", "home_id": str(home_id)}
            #             )
            # except Exception as e:
            #     app_logger.error(f"Failed to send out of stock notification: {e}")
            
            return None

    async def update_item_quantity(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_quantity: int) -> Optional[Product]:
        app_logger.debug(f"Attempting to update quantity of item {item_id} to {new_quantity}")
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            app_logger.warning(f"Quantity update failed: Product {product_id} not found in home {home_id}")
            raise ValueError("Product not found")

        product.update_item_quantity(item_id, new_quantity)
        
        if product.total_quantity > 0:
            await self._product_repository.update(product)
            app_logger.info(f"Quantity for item {item_id} updated to {new_quantity}")
            return product
        else:
            await self._product_repository.delete(product_id)
            app_logger.info(f"Quantity set to 0. Product {product_id} deleted completely.")
            
            # Note: when implementing shopping list

            # try:
            #     home = await self._home_repository.get_by_id(home_id)
            #     if home and home.get_admin():
            #         admin_user = await self._user_repository.get_by_id(home.get_admin())
                    
            #         if admin_user and admin_user.push_token:
            #             product_name = product.nickname if product.nickname else product.original_name
                        
            #             send_push_notification(
            #                 token=admin_user.push_token,
            #                 title="מוצר אזל מהמלאי! ⚠️",
            #                 message=f"המוצר '{product_name}' נגמר. תרצה שנוסיף לרשימת הקניות?.",
            #                 data={"action": "out_of_stock", "home_id": str(home_id)}
            #             )
            # except Exception as e:
            #     app_logger.error(f"Failed to send out of stock notification: {e}")
            
            
            return None

    async def update_item_date(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_date: Optional[date]) -> Product:
        app_logger.debug(f"Attempting to update expiration date of item {item_id} to {new_date}")
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            app_logger.warning(f"Date update failed: Product {product_id} not found in home {home_id}")
            raise ValueError("Product not found")

        product.update_item_date(item_id, new_date)
        await self._product_repository.update(product)
        
        app_logger.info(f"Expiration date for item {item_id} updated successfully")
        return product
    
    async def update_item_location(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_location: LocationType) -> Product:
        app_logger.debug(f"Attempting to move item {item_id} to {new_location}")
        await self._check_access(user_id, home_id)
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            app_logger.warning(f"Location update failed: Product {product_id} not found in home {home_id}")
            raise ValueError("Product not found")

        product.update_item_location(item_id, new_location)
        await self._product_repository.update(product)
        
        app_logger.info(f"Location for item {item_id} updated to {new_location}")
        return product
        
    async def update_nickname(self, user_id: UUID, home_id: UUID, product_id: UUID, new_nickname: str) -> Product:
        app_logger.debug(f"Attempting to update nickname for product {product_id}")
        await self._check_access(user_id, home_id)

        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            app_logger.warning(f"Nickname update failed: Product {product_id} not found in home {home_id}")
            raise ValueError("Product not found")

        product.set_nickname(new_nickname)
        await self._product_repository.update(product)
        
        app_logger.info(f"Nickname for product {product_id} updated to '{new_nickname}'")
        return product
    
    async def update_location(self, user_id: UUID, home_id: UUID, product_id: UUID, new_location: LocationType) -> Product:
        app_logger.debug(f"Attempting to update aggregate location for product {product_id}")
        await self._check_access(user_id, home_id)

        product = await self._product_repository.get_by_id(product_id)
        if not product or product.get_home_id() != home_id:
            app_logger.warning(f"Aggregate location update failed: Product {product_id} not found")
            raise ValueError("Product not found in this home")
            
        product.set_location(new_location)
        await self._product_repository.update(product)
        
        app_logger.info(f"Aggregate location for product {product_id} updated to {new_location}")
        return product


    # ==========================================
    # Read / Filter / Search Operations
    # ==========================================

    async def filter_by_location(self, user_id: UUID, home_id: UUID, location: LocationType) -> List[ProductDTO]:
        app_logger.debug(f"Filtering products by location: {location} for home {home_id}")
        await self._check_access(user_id, home_id)
        
        products = await self._product_repository.list_all_by_home(home_id)
        warning_days = 3 
        
        dtos = []
        for p in products:
            dto = self._create_filtered_dto(
                product=p, 
                warning_days=warning_days,
                filter_func=lambda item: item.location == location
            )
            if dto:
                dtos.append(dto)
                
        return dtos

    async def filter_by_expiration_type(self, user_id: UUID, home_id: UUID, filter_type: ExpirationType) -> List[ProductDTO]:
        app_logger.debug(f"Filtering products by expiration type: {filter_type} for home {home_id}")
        warning_days = await self._check_access(user_id, home_id)
        
        products = await self._product_repository.list_all_by_home(home_id)
        
        dtos = []
        for p in products:
            dto = self._create_filtered_dto(
                product=p,
                warning_days=warning_days, 
                filter_func=lambda item: item.get_status(warning_days) == filter_type
            )
            if dto:
                dtos.append(dto)
                
        return dtos

    def _create_filtered_dto(self, product: Product, warning_days: int, filter_func: Callable) -> Optional[ProductDTO]:
        filtered_items_dtos = []
        view_total_quantity = 0

        for item in product.items:
            if filter_func(item):
                status = item.get_status(warning_days)
                filtered_items_dtos.append(ProductItemDTO(
                    id=item.id,
                    quantity=item.quantity,
                    expiration_date=item.expiration_date,
                    location=item.location, 
                    status=status
                ))
                view_total_quantity += item.quantity

        if not filtered_items_dtos:
            return None

        filtered_items_dtos.sort(key=lambda x: x.expiration_date or date.max)

        return ProductDTO(
            id=product.id,
            home_id=product.home_id,
            original_name=product.original_name,
            nickname=product.nickname,
            barcode=product.barcode,
            total_quantity=view_total_quantity, 
            items=filtered_items_dtos
        )

    async def search_product(self, user_id: UUID, home_id: UUID, query: str) -> List[Product]:
        """Searches for products based on product name or nickname."""
        app_logger.debug(f"Searching local inventory for '{query}' in home {home_id}")
        await self._check_access(user_id, home_id)
        search_results = await self._product_repository.search_by_name(home_id, query)            
        return search_results

    async def search_product_by_name_external_db(self, user_id: UUID, home_id: UUID, query: str) -> List[CatalogItem]:
        app_logger.debug(f"Searching external catalog for '{query}'")
        await self._check_access(user_id, home_id)
        search_results = await self._catalog_provider.search_items_by_name(query)
        return search_results
    
    async def search_product_by_barcode_external_db(self, user_id: UUID, home_id: UUID, barcode: str) -> Optional[CatalogItem]:
        app_logger.debug(f"Searching external catalog by barcode: {barcode}")
        await self._check_access(user_id, home_id)
        item = await self._catalog_provider.get_item_by_barcode(barcode)
        return item
    
    async def get_home_products(self, user_id: UUID, home_id: UUID) -> List[Product]:
        """Retrieves all products in the home's inventory."""
        app_logger.debug(f"Retrieving all products for home {home_id}")
        await self._check_access(user_id, home_id)
        products = await self._product_repository.list_all_by_home(home_id)
        return products

    async def check_expirations_and_notify(self):
        """
        Daily cron job function (Scalable Batch Version): 
        Scans homes in batches, checks for expiring/expired items, 
        and sends push notifications.
        """
        app_logger.info("Starting daily expiration check (Batch Mode)...")
        
        batch_size = 100
        offset = 0
        total_processed = 0

        while True:
            try:
                homes_batch = await self._home_repository.get_homes_batch(limit=batch_size, offset=offset)
                
                if not homes_batch:
                    break 

                for home in homes_batch:
                    try:
                        warning_days = home.get_expiration_range()
                        products = await self._product_repository.list_all_by_home(home.get_id())
                        
                        expired_names = set()
                        expiring_names = set()

                        for product in products:
                            name = product.nickname if product.nickname else product.original_name
                            for item in product.items:
                                status = item.get_status(warning_days)
                                if status == ExpirationType.EXPIRED:
                                    expired_names.add(name)
                                elif status == ExpirationType.GOING_TO_EXPIRE:
                                    expiring_names.add(name)

                        if not expired_names and not expiring_names:
                            continue 

                        msg_parts = []
                        if expired_names:
                            msg_parts.append(f"❌ פג תוקף: {', '.join(expired_names)}")
                        if expiring_names:
                            msg_parts.append(f"⏳ יפוגו בקרוב: {', '.join(expiring_names)}")

                        message = "\n".join(msg_parts)
                        home_name = home.get_name()
                        title = f"עדכון מלאי: {home_name} 📅"

                        members = home.get_members()
                        for member_id in members:
                            user = await self._user_repository.get_by_id(member_id)
                            if user and user.push_token:
                                send_push_notification(
                                    token=user.push_token,
                                    title=title,
                                    message=message,
                                    data={"action": "expiration_alert", "home_id": str(home.get_id())}
                                )

                    except Exception as e:
                        app_logger.error(f"Error checking expirations for home {home.get_id()}: {e}")

                total_processed += len(homes_batch)
                offset += batch_size
                
                # Adding a short sleep to prevent overwhelming the database in case of large number of homes. 
                asyncio.sleep(0.1) 

            except Exception as e:
                app_logger.error(f"Fatal error fetching batch at offset {offset}: {e}")
                break # עוצרים את הלולאה במקרה של קריסת DB כדי לא להיתקע לנצח

        app_logger.info(f"Finished daily expiration check. Processed {total_processed} homes total.")
    
    async def _check_access(self, user_id: UUID, home_id: UUID) -> int:
        """Helper to verify user exists, logged in, and member of the home"""
        home = await self._home_repository.get_by_id(home_id)
        if not home:
            app_logger.warning(f"Access check failed: Home {home_id} does not exist")
            raise ValueError("Home retrieval failed.")
        if not home.is_member(user_id):
            app_logger.warning(f"Access check failed: User {user_id} is not a member of home {home_id}")
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