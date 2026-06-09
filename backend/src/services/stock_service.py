
import asyncio
import os
from uuid import UUID, uuid4
from typing import Any, Callable, List, Optional, Dict
from datetime import date

from src.repositories.i_receipt_scanner import IReceiptScanner
from src.api.schemas.product_schemas import ProductDTO, ProductItemDTO
from src.domain.product.product import Product
from src.repositories.i_product_repository import IProductRepository
from src.repositories.i_home_repository import IHomeRepository
from src.repositories.catalog_provider import ICatalogProvider
from src.repositories.catalog_provider import CatalogItem
from src.repositories.i_receipt_repository import IReceiptRepository
from src.domain.enums import ExpirationType, LocationType, UnitType
from src.infrastructure.scanner.receipt_scanner import ReceiptScanner
from src.domain.receipt.receipt import ReceiptItemDTO, ReceiptDTO
from src.infrastructure.logger import app_logger
from src.repositories.user_repository import IUserRepository
from src.services.notification_service import send_push_notification
from src.services.house_auth import require_house_access

class StockService:
 
    def __init__(self, home_repository: IHomeRepository, product_repository: IProductRepository,
                  catalog_provider: ICatalogProvider, user_repository: IUserRepository, receipt_scanner: IReceiptScanner, receipt_repository: IReceiptRepository):
        self._home_repository = home_repository
        self._product_repository = product_repository
        self._catalog_provider = catalog_provider
        self._user_repository = user_repository
        self._receipt_scanner = receipt_scanner
        self._receipt_repository = receipt_repository

    # ==========================================
    # 2. Stock Management (Inventory)
    # ==========================================

    @require_house_access
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
        
    
    @require_house_access
    async def scan_receipt(
        self,
        user_id: UUID,
        home_id: UUID,
        files_paths: List[str],  
    ) -> ReceiptDTO:
        app_logger.debug(f"Starting receipt scan for home {home_id} with {len(files_paths)} files")
        

        # 1. Validation Guards
        self._validate_file_paths(files_paths)
        valid_paths = [str(fp) for fp in files_paths if fp and os.path.exists(str(fp))]
        if not valid_paths:
            raise ValueError("No valid files found in files_paths")


        
        app_logger.debug("Parsing receipt files through ML scanner...")
        chain_name, scanned_items = self._receipt_scanner.parse_receipt(valid_paths)
        print(f"Scanned items: {scanned_items}")
        print(f"Chain name: {chain_name}")
        receipt_items_dto: list[ReceiptItemDTO] = []

        # Bulk fetch all catalog items in one single query to minimize database roundtrip latency
        barcodes = list(scanned_items.keys())
        catalog_items = await self._catalog_provider.get_items_by_barcodes(barcodes, chain_name)
        catalog_map = {ci.barcode: ci for ci in catalog_items}

        for barcode, (qty, unit_str) in scanned_items.items():
            unit = UnitType(unit_str) if unit_str in UnitType.__members__ else UnitType.UNIT
            ci = catalog_map.get(barcode)

            if ci:
                avg_unit_weight = 1
                if unit == UnitType.KG:
                    avg_unit_weight = ci.weight
                    new_qty = qty / avg_unit_weight if avg_unit_weight else 1
                else:
                    new_qty = qty
                
                final_qty = new_qty

                receipt_items_dto.append(
                    ReceiptItemDTO(
                        barcode=barcode,
                        name=ci.name,
                        quantity=final_qty,
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
                        quantity=qty if unit == UnitType.UNIT else 1,
                        unit=unit,
                    )
                )

        app_logger.info(f"Successfully scanned receipt from '{chain_name}' with {len(receipt_items_dto)} items")
        for item in receipt_items_dto:
            app_logger.debug(f"  Item: {item.name} (barcode: {item.barcode}, qty: {item.quantity})")
            
        return ReceiptDTO(
            id=uuid4(),
            home_id=home_id,
            user_id=user_id,
            chain=chain_name,
            items=receipt_items_dto,
        )

    async def _map_scanned_item_to_dto(self, barcode: str, raw_qty: float, unit_str: str, chain_name: str) -> ReceiptItemDTO:
        """Helper to handle the logic of single item mapping and quantity calculation."""
        unit = UnitType(unit_str) if unit_str in UnitType.__members__ else UnitType.UNIT
        ci = await self._catalog_provider.get_item_by_barcode(barcode, chain_name)

        if ci:
            # Calculation with Rounding fix
            avg_unit_weight = ci.weight if (unit == UnitType.KG and ci.weight) else 1
            calculated_qty = int(round(raw_qty / avg_unit_weight)) if unit == UnitType.KG else int(raw_qty)
            
            return ReceiptItemDTO(
                barcode=barcode,
                name=ci.name,
                quantity=max(1, calculated_qty), # Ensure at least 1
                unit=unit,
                location=ci.location,
                weight=raw_qty if unit == UnitType.KG else None,
            )
        
        # Fallback for Unknown Product
        return ReceiptItemDTO(
            name="Unknown Product",
            barcode=barcode,
            quantity=int(raw_qty) if unit == UnitType.UNIT else 1,
            unit=unit,
            weight=raw_qty if unit == UnitType.KG else None # Keep the raw weight even if unknown
        )

    def _validate_file_paths(self, paths: List[str]):
        """Internal guard for file path integrity."""
        if not isinstance(paths, list) or not paths:
            raise ValueError("files_paths must be a non-empty list of file paths")
        if not all(isinstance(fp, (str, os.PathLike)) for fp in paths):
            raise TypeError("files_paths must contain only path strings")

    @require_house_access
    async def validate_receipt(self, receipt_dto: ReceiptDTO) -> int:
        """
        Fast validation-only path — called during the HTTP request.
        Returns the count of valid (non-unknown) items.
        """
        app_logger.debug(f"Validating receipt for home {receipt_dto.home_id} with {len(receipt_dto.items)} items")
        
        count = sum(1 for item in receipt_dto.items if item.name != "Unknown Product")
        app_logger.info(f"Receipt validated: {count} known items for home {receipt_dto.home_id}")
        return count

    async def commit_receipt(self, receipt_dto: ReceiptDTO, count: int) -> None:
        """
        Heavy persistence path — called as a BackgroundTask after the response is sent.
        FastAPI keeps request-scoped dependencies alive through background tasks,
        so the service's injected repositories and DB session are still valid.
        """
        try:
            await self._commit_receipt_internal(receipt_dto, count)
        except Exception as e:
            app_logger.error(f"Background receipt commit failed for home {receipt_dto.home_id}: {e}")

    async def _commit_receipt_internal(self, receipt_dto: ReceiptDTO, count: int) -> None:
        """
        Internal commit logic — executes within a dedicated DB session.
        Tracks new vs existing products and new vs merged items to enable
        the optimized save_all_receipt bulk path.
        """
        app_logger.debug(f"Committing receipt for home {receipt_dto.home_id} ({count} items)")
        
        existing_products = await self._product_repository.list_all_by_home(receipt_dto.home_id)
        products_map = {p.original_name: p for p in existing_products}
        
        # Track which products existed before this receipt
        existing_product_ids = {p.id for p in existing_products}
        
        # Collect IDs of items that existed BEFORE we start adding receipt items.
        # Any item ID NOT in this set after processing was created by add_item().
        pre_existing_item_ids = set()
        for p in existing_products:
            for item in p.items:
                pre_existing_item_ids.add(item.id)
        
        catalog_updated = False
        
        for item in receipt_dto.items:
            if item.name == "Unknown Product":
                continue
            
            if item.unit == UnitType.KG and item.quantity > 0 and item.barcode:
                current_measured_avg = item.weight / item.quantity
                await self._catalog_provider.update_weighted_mem_only(
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
            
            # Inventory uses Integer quantity. We ensure at least 1 unit if it's a known product.
            inventory_qty = max(1, int(item.quantity))
            product.add_item(inventory_qty, item.location, item.expiration_date)

        # Separate new vs existing products for the optimized save path
        new_products = []
        updated_products = []
        for product in products_map.values():
            if product.id in existing_product_ids:
                # Only include if it was actually modified (it was in the receipt)
                if any(item.name == product.original_name for item in receipt_dto.items if item.name != "Unknown Product"):
                    updated_products.append(product)
            else:
                new_products.append(product)

        # Determine which item IDs are newly created (not pre-existing)
        new_item_ids = set()
        for product in new_products + updated_products:
            for item in product.items:
                if item.id not in pre_existing_item_ids:
                    new_item_ids.add(item.id)

        if new_products or updated_products:
            await self._product_repository.save_all_receipt(
                new_products=new_products,
                updated_products=updated_products,
                new_item_ids=new_item_ids,
            )
            app_logger.info(
                f"Receipt saved: {len(new_products)} new + {len(updated_products)} updated products for home {receipt_dto.home_id}"
            )
            
        # Save the receipt to the receipt repository to track what was bought together
        # We only save KNOWN products to avoid polluting recommendation data with "Unknown Product" placeholders
        known_items = [item for item in receipt_dto.items if item.name != "Unknown Product"]
        
        if known_items:
            app_logger.info(f"Persisting receipt history for house {receipt_dto.home_id} ({len(known_items)} items)")
            # Create a localized DTO for storage that only contains known items
            persistence_dto = ReceiptDTO(
                id=receipt_dto.id,
                home_id=receipt_dto.home_id,
                user_id=receipt_dto.user_id,
                chain=receipt_dto.chain,
                items=known_items
            )
            await self._receipt_repository.save(persistence_dto)
            app_logger.info(f"Successfully saved receipt record for home {receipt_dto.home_id}")
        
        if catalog_updated:
            await self._catalog_provider.persist()
            app_logger.debug("Catalog weights persisted successfully")

        # Send push notifications concurrently
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
        
    @require_house_access
    async def remove_item(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID) -> Optional[Product]:
        """
        Removes a specific item batch (line) from the product.
        If the product becomes empty, it deletes the product entity entirely.
        """
        app_logger.debug(f"Attempting to remove item {item_id} from product {product_id}")
        
        
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
            
            # Note: Optionally after reviewing user's feedback

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

    @require_house_access
    async def update_item_quantity(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_quantity: int) -> Optional[Product]:
        app_logger.debug(f"Attempting to update quantity of item {item_id} to {new_quantity}")
        
        
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
            
            # Note: Optionally after reviewing user's feedback

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

    @require_house_access
    async def update_item_date(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_date: Optional[date]) -> Product:
        app_logger.debug(f"Attempting to update expiration date of item {item_id} to {new_date}")
        
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            app_logger.warning(f"Date update failed: Product {product_id} not found in home {home_id}")
            raise ValueError("Product not found")

        product.update_item_date(item_id, new_date)
        await self._product_repository.update(product)
        
        app_logger.info(f"Expiration date for item {item_id} updated successfully")
        return product
    
    @require_house_access
    async def update_item_location(self, user_id: UUID, home_id: UUID, product_id: UUID, item_id: UUID, new_location: LocationType) -> Product:
        app_logger.debug(f"Attempting to move item {item_id} to {new_location}")
        
        
        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            app_logger.warning(f"Location update failed: Product {product_id} not found in home {home_id}")
            raise ValueError("Product not found")

        product.update_item_location(item_id, new_location)
        await self._product_repository.update(product)
        
        app_logger.info(f"Location for item {item_id} updated to {new_location}")
        return product
        
    @require_house_access
    async def update_nickname(self, user_id: UUID, home_id: UUID, product_id: UUID, new_nickname: str) -> Product:
        app_logger.debug(f"Attempting to update nickname for product {product_id}")
        

        product = await self._product_repository.get_by_id(product_id)
        if not product or product.home_id != home_id:
            app_logger.warning(f"Nickname update failed: Product {product_id} not found in home {home_id}")
            raise ValueError("Product not found")

        product.set_nickname(new_nickname)
        await self._product_repository.update(product)
        
        app_logger.info(f"Nickname for product {product_id} updated to '{new_nickname}'")
        return product
    


    # ==========================================
    # Read / Filter / Search Operations
    # ==========================================

    @require_house_access
    async def filter_products(self, user_id: UUID, home_id: UUID, query: Optional[str]=None, location: Optional[LocationType]=None, expiration_type: Optional[ExpirationType]=None, home=None) -> List[Product]:

        app_logger.debug(f"Starting filter_manager with location={location} and expiration_type={expiration_type} for home {home_id}")
        warning_days = home.get_expiration_range()

        products = await self._product_repository.filter_products(home_id, query_text=query, location=location, expiration_type=expiration_type, warning_days=warning_days)
        return products        

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

    @require_house_access
    async def search_product_by_name_external_db(self, user_id: UUID, home_id: UUID, query: str) -> List[CatalogItem]:
        app_logger.debug(f"Searching external catalog for '{query}'")
        
        search_results = await self._catalog_provider.search_items_by_name(query)
        return search_results
    
    @require_house_access
    async def search_product_by_barcode_external_db(self, user_id: UUID, home_id: UUID, barcode: str) -> Optional[CatalogItem]:
        app_logger.debug(f"Searching external catalog by barcode: {barcode}")
        
        item = await self._catalog_provider.get_item_by_barcode(barcode)
        return item
    
    @require_house_access
    async def get_home_products(self, user_id: UUID, home_id: UUID) -> List[Product]:
        """Retrieves all products in the home's inventory."""
        app_logger.debug(f"Retrieving all products for home {home_id}")
        
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
                await asyncio.sleep(0.1) 

            except Exception as e:
                app_logger.error(f"Fatal error fetching batch at offset {offset}: {e}")
                break # עוצרים את הלולאה במקרה של קריסת DB כדי לא להיתקע לנצח

        app_logger.info(f"Finished daily expiration check. Processed {total_processed} homes total.")
    
    