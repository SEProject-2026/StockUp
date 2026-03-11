from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.repositories.i_product_repository import IProductRepository
from src.domain.smart_home.product import Product, ProductItem
from src.domain.smart_home.enums import LocationType
from src.infrastructure.db.models import ProductModel, ProductItemModel

class DbProductRepository(IProductRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, product: Product) -> None:
        """Standard save for single product additions - Always commits."""
        self._perform_upsert_logic(product)
        self.db.commit()

    async def save_all(self, products: List[Product]) -> None:
        """Bulk save for receipts - Commits once at the end."""
        for product in products:
            self._perform_upsert_logic(product)
        self.db.commit()

    def _perform_upsert_logic(self, product: Product) -> None:
        """Internal helper to handle the mapping logic without commit."""
        db_product = self.db.query(ProductModel).filter(ProductModel.id == str(product.id)).first()

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
                db_item.location = domain_item.location.name if domain_item.location else "OTHER"
                
                
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
                    location=domain_item.location.name if domain_item.location else "OTHER"
                )
                self.db.add(new_db_item)

        for leftover_item in existing_items.values():
            self.db.delete(leftover_item)

        self.db.flush()

        # db_product.items = []
        # db_product.items = [
        #     ProductItemModel(
        #         id=str(item.id),
        #         product_id=str(product.id),
        #         quantity=item.quantity,
        #         expiration_date=item.expiration_date,
        #         location=item.location.name if item.location else "OTHER"
        #     ) for item in product.items
        # ]
        # # Flush ensures the SQL is sent to the DB buffer
        # self.db.flush()

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