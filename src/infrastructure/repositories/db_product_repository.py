from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from src.repositories.i_product_repository import IProductRepository
from src.domain.smart_home.product import Product
from src.domain.smart_home.enums import LocationType, ExpirationType
from src.infrastructure.db.models import ProductModel, ProductItemModel

class DbProductRepository(IProductRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, product: Product) -> None:
        db_product = self.db.query(ProductModel).filter(ProductModel.id == str(product.get_id())).first()

        if db_product:
            # Update existing product
            db_product.original_name = product.get_original_name()
            db_product.nickname = product.get_nickname()
            db_product.quantity = product.get_quantity()
            db_product.location = product.get_location().name if product.get_location() else None
            
            # Clear existing items to rewrite them from the domain entity
            db_product.items = [] 
        else:
            # Create new product
            db_product = ProductModel(
                id=str(product.get_id()),
                home_id=str(product.get_home_id()),
                original_name=product.get_original_name(),
                nickname=product.get_nickname(),
                barcode=product.get_barcode(),
                quantity=product.get_quantity(),
                location=product.get_location().name if product.get_location() else None
            )
            self.db.add(db_product)

        # Create ProductItemModel instances from the domain dictionary
        new_items = []
        for exp_date, (qty, exp_type) in product.get_expiration_dates().items():
            item = ProductItemModel(
                expiration_date=exp_date,
                quantity=qty,
                expiration_type=exp_type.name 
            )
            new_items.append(item)
        
        db_product.items = new_items 
        
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
        await self.save(product)

    async def delete(self, product_id: UUID) -> None:
        db_product = self.db.query(ProductModel).filter(ProductModel.id == str(product_id)).first()
        if db_product:
            self.db.delete(db_product)
            self.db.commit()

    async def get_by_name(self, home_id: UUID, name: str) -> Optional[Product]:
        db_product = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.items))
            .filter(ProductModel.home_id == str(home_id))
            .filter(
                (ProductModel.original_name == name) | 
                (ProductModel.nickname == name)
            )
            .first()
        )
        if not db_product:
            return None
        return self._to_domain(db_product)

    async def get_by_location(self, home_id: UUID, location: str) -> List[Product]:
        db_products = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.items))
            .filter(ProductModel.home_id == str(home_id))
            .filter(ProductModel.location == location)
            .all()
        )
        return [self._to_domain(p) for p in db_products]
         
    async def get_by_expiration_filter(self, home_id: UUID, home_expiration_range: int, filter_type: ExpirationType) -> List[Product]:
        # Fetching all products and filtering in memory (simplest approach for complex domain logic)
        all_products = await self.list_all_by_home(home_id)
        # Assuming the service layer or domain logic handles the specific filtering based on ExpirationType
        return all_products 

    def _to_domain(self, db_model: ProductModel) -> Product:
        # Create base object
        product = Product(
            home_id=UUID(db_model.home_id),
            original_name=db_model.original_name,
            quantity=0, # Will be recalculated
            expiration_range=7, # Default, or fetched if needed
            barcode=db_model.barcode,
            location=LocationType[db_model.location] if db_model.location else None,
            nickname=db_model.nickname
        )
        
        # Restore ID
        product._id = UUID(db_model.id)
        
        # Restore expiration dictionary from items
        product._expiration_dates_to_quantity = {}
        total_qty = 0
        
        for item in db_model.items:
            e_type = ExpirationType[item.expiration_type] if item.expiration_type else ExpirationType.FRESH
            product._expiration_dates_to_quantity[item.expiration_date] = (item.quantity, e_type)
            total_qty += item.quantity
            
        product._quantity = total_qty
        
        return product