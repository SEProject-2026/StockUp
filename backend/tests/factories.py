import uuid
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import select

# Domain & Infrastructure imports
from src.domain.user.user import User
from src.domain.home.home import Home
from src.domain.product.product import Product, ProductItem
from src.domain.shopping_list.shopping_list import ShoppingList, ShoppingListItem
from src.domain.enums import LocationType

# --- Domain & Persistence Factories ---

from src.infrastructure.db.models import UserModel, HomeModel


# ==========================================
# 1. Domain & Persistence Factories (Async)
# ==========================================

def create_user_entity(db=None, **kwargs):
    """
    Creates a User. Supports Async DB for integration tests 
    and Domain Entities for unit tests.
    """
    user_id = kwargs.get("user_id", uuid.uuid4())
    email = kwargs.get("email", f"user_{uuid.uuid4().hex[:6]}@test.com")
    name = kwargs.get("name", "Test User")
    push_token = kwargs.get("push_token", "mock_token_123")

    if db:
        db_user = UserModel(
            id=str(user_id),
            email=email,
            name=name,
            push_token=push_token
        )
        db.add(db_user)
        return db_user 

    return User(
        id=user_id,
        email=email,
        name=name,
        push_token=push_token
    )

def create_home_entity(db=None, admin_user=None, requesting_users=None, **kwargs):
    """
    Creates a Home with optional admin and join requests.
    """
    home_id = kwargs.get("home_id", uuid.uuid4())
    name = kwargs.get("name", "Test Home")
    admin_id = admin_user.id if admin_user else kwargs.get("admin_user_id", uuid.uuid4())
    join_code = kwargs.get("join_code", uuid.uuid4().hex[:8].upper())

    if db:
        db_home = HomeModel(
            id=str(home_id),
            name=name,
            admin_id=str(admin_id), 
            join_code=join_code,
            expiration_range=kwargs.get("expiration_range", 7)
        )
        
        if admin_user:
            db_home.users.append(admin_user)
            
        if requesting_users:
            for u in requesting_users:
                db_home.join_requests.append(u)
                
        db.add(db_home)
        return db_home

    return Home(user_id=admin_id, name=name)

def create_product_entity(
    db=None,
    home_id: Optional[uuid.UUID] = None,
    name: str = "Test Product",
    barcode: Optional[str] = None,
    add_item: bool = False
) -> Product:
    """
    Creates a Product. If db is provided, it handles async persistence.
    """
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
    return product

def create_shopping_list_entity(
    db=None,
    home_id: Optional[uuid.UUID] = None,
    name: str = "Weekly List"
) -> ShoppingList:
    """
    Creates a ShoppingList with async DB support.
    """
    sl = ShoppingList(
        home_id=home_id or uuid.uuid4(),
        name=name,
        updated_at=datetime.now()
    )
    if db:
        db.add(sl)
    return sl

# ==========================================
# 2. API Payload Helpers (Synchronous)
# ==========================================

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