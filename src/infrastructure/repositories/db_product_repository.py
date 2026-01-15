from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from src.repositories.i_product_repository import IProductRepository
from src.domain.smart_home.product import Product, ProductItem
from src.domain.smart_home.enums import LocationType
from src.infrastructure.db.models import ProductModel, ProductItemModel

class DbProductRepository(IProductRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, product: Product) -> None:
        """
        Saves or updates the Aggregate Root (Product) and its children (Items).
        """
        # 1. Check if product exists
        db_product = self.db.query(ProductModel).filter(ProductModel.id == str(product.id)).first()

        if not db_product:
            # CREATE
            db_product = ProductModel(
                id=str(product.id),
                home_id=str(product.home_id),
                original_name=product.original_name,
                nickname=product.nickname,
                barcode=product.barcode
                # Note: 'quantity' and 'location' are NOT stored on ProductModel anymore
            )
            self.db.add(db_product)
        else:
            # UPDATE (Fields on the Aggregate Root)
            db_product.original_name = product.original_name
            db_product.nickname = product.nickname
            db_product.barcode = product.barcode

        # 2. Handle Items (The Children)
        # Approach: Replace all items logic (Simpler for consistency)
        # In a highly optimized system, we would diff the lists, but for now replace is safe.
        
        # Clear existing DB items
        db_product.items = []
        
        # Convert Domain Items -> DB Models
        new_db_items = []
        for item in product.items:
            db_item = ProductItemModel(
                id=str(item.id),
                product_id=str(product.id),
                quantity=item.quantity,
                expiration_date=item.expiration_date,
                location=item.location.name if item.location else "OTHER"
            )
            new_db_items.append(db_item)
            
        db_product.items = new_db_items
        
        self.db.commit()

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        db_product = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.items))
            .filter(ProductModel.id == str(product_id))
            .first()
        )
        
        if not db_product:
            return None
            
        return self._to_domain(db_product)

    async def list_all_by_home(self, home_id: UUID) -> List[Product]:
        db_products = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.items))
            .filter(ProductModel.home_id == str(home_id))
            .all()
        )
        return [self._to_domain(p) for p in db_products]

    async def search_by_name(self, home_id: UUID, query: str) -> List[Product]:
        search_pattern = f"%{query}%"
        db_products = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.items))
            .filter(ProductModel.home_id == str(home_id))
            .filter(
                (ProductModel.original_name.ilike(search_pattern)) | 
                (ProductModel.nickname.ilike(search_pattern))
            )
            .all()
        )
        return [self._to_domain(p) for p in db_products]

    async def update(self, product: Product) -> None:
        # Save handles both insert and update
        await self.save(product)

    async def delete(self, product_id: UUID) -> None:
        db_product = self.db.query(ProductModel).filter(ProductModel.id == str(product_id)).first()
        if db_product:
            self.db.delete(db_product)
            self.db.commit()

    async def get_by_original_name(self, home_id: UUID, name: str) -> Optional[Product]:
        db_product = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.items))
            .filter(ProductModel.home_id == str(home_id))
            .filter(ProductModel.original_name == name)
            .first()
        )
        if not db_product:
            return None
        return self._to_domain(db_product)

    async def get_by_location(self, home_id: UUID, location: str) -> List[Product]:
        """
        Complex Query: Find products that have AT LEAST one item in the given location.
        """
        db_products = (
            self.db.query(ProductModel)
            .join(ProductItemModel) # Join to filter by item location
            .filter(ProductModel.home_id == str(home_id))
            .filter(ProductItemModel.location == location)
            .options(joinedload(ProductModel.items)) # Eager load all items (even not matching ones)
            .distinct()
            .all()
        )
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
            loc_enum = LocationType[db_item.location] if db_item.location else LocationType.OTHER
            
            domain_item = ProductItem(
                id=UUID(db_item.id),
                quantity=db_item.quantity,
                expiration_date=db_item.expiration_date,
                location=loc_enum
            )
            restored_items.append(domain_item)
            
        product._items = restored_items
        
        return product