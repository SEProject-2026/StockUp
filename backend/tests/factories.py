import uuid
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from src.domain.user.user import User
from src.domain.home.home import Home
from src.domain.product.product import Product, ProductItem
from src.domain.shopping_list.shopping_list import ShoppingList, ShoppingListItem
from src.domain.enums import LocationType

# --- Domain & Persistence Factories ---

from src.infrastructure.db.models import UserModel, HomeModel


def create_user_entity(db: Optional[Session] = None, **kwargs) -> User:
    user_id = kwargs.get("user_id", uuid.uuid4())
    email = kwargs.get("email", f"user_{uuid.uuid4().hex[:6]}@test.com")
    name = kwargs.get("name", "Test User")
    push_token = kwargs.get("push_token", "mock_token_123")

    if db:
        # Create SQLAlchemy Model for Integration Tests
        db_user = UserModel(
            id=str(user_id),
            email=email,
            name=name,
            push_token=push_token
        )
        db.add(db_user)
        db.flush()
        return db_user # SQLAlchemy models are data-compatible with Domain Entities in most flows

    # Return pure Domain Entity for Unit Tests
    return User(
        id=user_id,
        email=email,
        name=name,
        push_token=push_token
    )

def create_home_entity(db: Optional[Session] = None, **kwargs) -> Home:
    home_id = kwargs.get("home_id", uuid.uuid4())
    name = kwargs.get("name", "Test Home")
    admin_id = kwargs.get("admin_user_id", uuid.uuid4())
    join_code = kwargs.get("join_code", uuid.uuid4().hex[:8].upper())
    requesting_user_ids = kwargs.get("requesting_user_ids", [])

    if db:
        # Fetch the admin user using a string ID for Postgres compatibility
        admin_user = db.query(UserModel).filter(UserModel.id == str(admin_id)).first()
        
        db_home = HomeModel(
            id=str(home_id),
            name=name,
            admin_id=str(admin_id), 
            join_code=join_code,
            expiration_range=kwargs.get("expiration_range", 7)
        )
        
        # Link the admin to the membership association table
        if admin_user:
            db_home.users.append(admin_user)
            
        # Link applicants to the join requests association table
        for r_id in requesting_user_ids:
            r_user = db.query(UserModel).filter(UserModel.id == str(r_id)).first()
            if r_user:
                db_home.join_requests.append(r_user)

        db.add(db_home)
        db.flush()
        return db_home

    # Domain Home uses admin_id (mapped as user_id in the domain layer)
    return Home(user_id=admin_id, name=name)

def create_product_entity(
    db: Optional[Session] = None,
    home_id: Optional[uuid.UUID] = None,
    name: str = "Test Product",
    barcode: Optional[str] = None,
    add_item: bool = False
) -> Product:
    product = Product(
        id=uuid.uuid4(),
        home_id=home_id or uuid.uuid4(),
        original_name=name,
        barcode=barcode
    )
    if add_item:
        product.add_item(quantity=1, location=LocationType.FRIDGE)
        
    if db:
        db.add(product)
        db.flush()
    return product

def create_shopping_list_entity(
    db: Optional[Session] = None,
    home_id: Optional[uuid.UUID] = None,
    name: str = "Weekly List"
) -> ShoppingList:
    sl = ShoppingList(
        home_id=home_id or uuid.uuid4(),
        name=name,
        updated_at=datetime.now()
    )
    if db:
        db.add(sl)
        db.flush()
    return sl

# --- API Payload Helpers (For Integration Tests) ---

def create_register_payload(**kwargs) -> dict:
    return {
        "user_id": str(kwargs.get("user_id", uuid.uuid4())),
        "email": kwargs.get("email", f"api_{uuid.uuid4().hex[:4]}@test.com"),
        "name": kwargs.get("name", "API User")
    }

def create_add_product_payload(**kwargs) -> dict:
    return {
        "name": kwargs.get("name", "Milk"),
        "home_id": str(kwargs.get("home_id", uuid.uuid4())),
        "quantity": kwargs.get("quantity", 1),
        "location": kwargs.get("location", "FRIDGE"),
        "barcode": kwargs.get("barcode", None),
        "expiration_date": kwargs.get("expiration_date", None)
    }

def create_shopping_list_payload(**kwargs) -> dict:
    return {
        "name": kwargs.get("name", "Grocery List"),
        "home_id": str(kwargs.get("home_id", uuid.uuid4()))
    }