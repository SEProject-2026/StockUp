import uuid
from datetime import date, datetime
from typing import Optional, List
from src.domain.user.user import User
from src.domain.home.home import Home
from src.domain.product.product import Product, ProductItem
from src.domain.shopping_list.shopping_list import ShoppingList, ShoppingListItem
from src.domain.enums import LocationType

# --- Domain Factories ---

def create_user_entity(
    user_id: Optional[uuid.UUID] = None, 
    email: Optional[str] = None, 
    name: str = "Test User"
) -> User:
    return User(
        id=user_id or uuid.uuid4(),
        email=email or f"user_{uuid.uuid4().hex[:6]}@test.com",
        name=name,
        push_token="mock_token_123"
    )

def create_home_entity(
    admin_user_id: Optional[uuid.UUID] = None, 
    name: str = "Test Home"
) -> Home:
    return Home(
        user_id=admin_user_id or uuid.uuid4(),
        name=name
    )

def create_product_entity(
    home_id: Optional[uuid.UUID] = None,
    name: str = "Test Product",
    barcode: Optional[str] = None
) -> Product:
    return Product(
        id=uuid.uuid4(),
        home_id=home_id or uuid.uuid4(),
        original_name=name,
        barcode=barcode
    )

def create_shopping_list_entity(
    home_id: Optional[uuid.UUID] = None,
    name: str = "Weekly List",
    items: Optional[List[ShoppingListItem]] = None
) -> ShoppingList:
    return ShoppingList(
        home_id=home_id or uuid.uuid4(),
        name=name,
        items=items or [],
        updated_at=datetime.now()
    )

# --- API Payload Helpers (For Integration Tests) ---

def create_register_payload(**kwargs) -> dict:
    return {
        "user_id": str(kwargs.get("user_id", uuid.uuid4())),
        "email": kwargs.get("email", "factory@test.com"),
        "name": kwargs.get("name", "Factory User")
    }

def create_add_product_payload(**kwargs) -> dict:
    return {
        "name": kwargs.get("name", "Milk"),
        "quantity": kwargs.get("quantity", 1),
        "location": kwargs.get("location", "FRIDGE"),
        "expiration_date": kwargs.get("expiration_date", None)
    }