from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload, contains_eager
from src.repositories.i_product_repository import IProductRepository
from src.domain.product.product import Product, ProductItem
from src.domain.enums import ExpirationType, LocationType
from src.infrastructure.db.models import ProductModel, ProductItemModel

class DbProductRepository(IProductRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, product: Product) -> None:
        """Standard save for single product additions - Always commits."""
        await self._perform_upsert_logic(product)
        await self.db.commit()

    async def save_all(self, products: List[Product]) -> None:
        """Bulk save for receipts - Commits once at the end."""
        for product in products:
            await self._perform_upsert_logic(product)
        await self.db.commit()

    async def _perform_upsert_logic(self, product: Product) -> None:
        """Internal helper to handle the mapping logic without commit."""
        result = await self.db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.items))
            .where(ProductModel.id == str(product.id))
        )
        db_product = result.scalars().first()

        if not db_product:
            db_product = ProductModel(
                id=str(product.id),
                home_id=str(product.home_id),
                original_name=product.original_name,
                nickname=product.nickname,
                barcode=product.barcode
            )
            self.db.add(db_product)
        else:
            db_product.original_name = product.original_name
            db_product.nickname = product.nickname
            db_product.barcode = product.barcode
        
        existing_items = {item.id: item for item in db_product.items} if db_product.items else {}

        for domain_item in product.items:
            domain_item_id_str = str(domain_item.id)
            
            if domain_item_id_str in existing_items:
                db_item = existing_items[domain_item_id_str]
                
                db_item.expiration_date = domain_item.expiration_date
                db_item.location = domain_item.location.value if domain_item.location else LocationType.OTHER.value
                
                
                quantity_diff = domain_item.quantity - db_item.quantity 
                if quantity_diff != 0:
                    db_item.quantity = ProductItemModel.quantity + quantity_diff

                del existing_items[domain_item_id_str]
                
            else:
                new_db_item = ProductItemModel(
                    id=domain_item_id_str,
                    product_id=str(product.id),
                    quantity=domain_item.quantity,
                    expiration_date=domain_item.expiration_date,
                    location=domain_item.location.value if domain_item.location else LocationType.OTHER.value
                )
                self.db.add(new_db_item)

        for leftover_item in existing_items.values():
            await self.db.delete(leftover_item)

        await self.db.flush()

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        result = await self.db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.items))
            .where(ProductModel.id == str(product_id))
        )
        db_product = result.scalars().first()
        
        if not db_product:
            return None
            
        return self._to_domain(db_product)

    async def list_all_by_home(self, home_id: UUID) -> List[Product]:
        result = await self.db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.items))
            .where(ProductModel.home_id == str(home_id))
        )
        db_products = result.scalars().unique().all()
        return [self._to_domain(p) for p in db_products]

    async def search_by_name(self, home_id: UUID, query: str) -> List[Product]:
        search_pattern = f"%{query}%"
        result = await self.db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.items))
            .where(ProductModel.home_id == str(home_id))
            .where(
                (ProductModel.original_name.ilike(search_pattern)) | 
                (ProductModel.nickname.ilike(search_pattern))
            )
        )
        db_products = result.scalars().unique().all()
        return [self._to_domain(p) for p in db_products]

    async def update(self, product: Product) -> None:
        # Save handles both insert and update
        await self.save(product)

    async def delete(self, product_id: UUID) -> None:
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == str(product_id))
        )
        db_product = result.scalars().first()
        if db_product:
            await self.db.delete(db_product)
            await self.db.commit()

    async def get_by_original_name(self, home_id: UUID, name: str) -> Optional[Product]:
        result = await self.db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.items))
            .where(ProductModel.home_id == str(home_id))
            .where(ProductModel.original_name == name)
        )
        db_product = result.scalars().first()
        if not db_product:
            return None
        return self._to_domain(db_product)

    async def get_by_location(self, home_id: UUID, location: str) -> List[Product]:
        """
        Complex Query: Find products that have AT LEAST one item in the given location.
        """
        result = await self.db.execute(
            select(ProductModel)
            .join(ProductItemModel) # Join to filter by item location
            .where(ProductModel.home_id == str(home_id))
            .where(ProductItemModel.location == location)
            .options(selectinload(ProductModel.items)) # Eager load all items (even not matching ones)
        )
        db_products = result.scalars().unique().all()
        return [self._to_domain(p) for p in db_products]

    # --- Mapper ---

    def _to_domain(self, db_model: ProductModel) -> Product:
        # 1. Create the Aggregate Root
        product = Product(
            id=UUID(db_model.id),
            home_id=UUID(db_model.home_id),
            original_name=db_model.original_name,
            barcode=db_model.barcode,
            nickname=db_model.nickname
        )
        
        # 2. Reconstitute Items
        # We manually add them to the protected list _items to bypass business logic in add_item
        # (Since we are just loading state from DB, not adding new items)
        restored_items = []
        for db_item in db_model.items:
            loc_str = db_item.location if db_item.location else LocationType.OTHER.value
            
            domain_item = ProductItem(
                id=UUID(db_item.id),
                quantity=db_item.quantity,
                expiration_date=db_item.expiration_date,
                location=LocationType(loc_str)
            )
            restored_items.append(domain_item)
            
        product._items = restored_items
        
        return product
    
    async def filter_products(
        self, 
        home_id: UUID, 
        query_text: Optional[str] = None, 
        location: Optional[str] = None, 
        expiration_type: Optional[ExpirationType] = None,
        warning_days: int = 0
    ) -> List[Product]:
        
        stmt = (
            select(ProductModel)
            .join(ProductModel.items)
            .where(ProductModel.home_id == str(home_id))
        )

        if query_text and len(query_text) >= 2:
            stmt = stmt.where(
                or_(
                    ProductModel.original_name.ilike(f"%{query_text}%"),
                    ProductModel.nickname.ilike(f"%{query_text}%")
                )
            )

        if location:
            stmt = stmt.where(ProductItemModel.location == location)

        if expiration_type:
            today = date.today()
            
            if expiration_type == ExpirationType.EXPIRED:
                stmt = stmt.where(ProductItemModel.expiration_date < today)
                
            elif expiration_type == ExpirationType.GOING_TO_EXPIRE:
                warning_date = today + timedelta(days=warning_days)
                stmt = stmt.where(
                    and_(
                        ProductItemModel.expiration_date >= today,
                        ProductItemModel.expiration_date <= warning_date
                    )
                )

        stmt = stmt.options(contains_eager(ProductModel.items))

        result = await self.db.execute(stmt)
        db_products = result.scalars().unique().all()
        
        return [self._to_domain(p) for p in db_products]