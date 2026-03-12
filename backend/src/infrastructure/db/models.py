from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String, Integer, Date, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from src.infrastructure.db.database import Base

# Association Tables (No changes)
user_home_association = Table(
    "user_home",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("home_id", String, ForeignKey("homes.id"), primary_key=True)
)

join_requests_association = Table(
    "home_join_requests",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("home_id", String, ForeignKey("homes.id"), primary_key=True)
)

# --- Users & Homes ---

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)

    homes = relationship("HomeModel", secondary=user_home_association, back_populates="users")
    requested_homes = relationship("HomeModel", secondary=join_requests_association, back_populates="join_requests")


class HomeModel(Base):
    __tablename__ = "homes"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    join_code = Column(String, index=True) 
    expiration_range = Column(Integer, default=7) 

    admin_id = Column(String, ForeignKey("users.id"))
    admin = relationship("UserModel")

    users = relationship("UserModel", secondary=user_home_association, back_populates="homes")
    join_requests = relationship("UserModel", secondary=join_requests_association, back_populates="requested_homes")
    
    # Cascade delete is important: If Home is deleted, delete all Products
    products = relationship("ProductModel", back_populates="home", cascade="all, delete-orphan")
    shopping_lists = relationship("ShoppingListModel", back_populates="home", cascade="all, delete-orphan")


# --- Products & Items (Refactored) ---

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    home_id = Column(String, ForeignKey("homes.id"))
    
    original_name = Column(String)
    nickname = Column(String, nullable=True)
    barcode = Column(String, nullable=True, index=True)

    home = relationship("HomeModel", back_populates="products")
    
    # Cascade is crucial here. Deleting a Product deletes all its Items.
    items = relationship("ProductItemModel", back_populates="product", cascade="all, delete-orphan")


class ProductItemModel(Base):
    __tablename__ = "product_items"

    id = Column(String, primary_key=True, index=True) 
    
    product_id = Column(String, ForeignKey("products.id"))
    
    expiration_date = Column(Date, nullable=True) 
    quantity = Column(Integer)
    
    location = Column(String, default="OTHER") 
    

    product = relationship("ProductModel", back_populates="items")



class CatalogItemModel(Base):
    __tablename__ = "catalog_items"

    barcode = Column("Barcode", String, primary_key=True)
    chain = Column("Chain", String, primary_key=True, default="GLOBAL")
    name = Column("ItemName", String, nullable=False)
    manufacturer = Column("ManufacturerName", String)
    unit_of_measure = Column("UnitOfMeasure", String)
    qty_in_package = Column("QtyInPackage", String)
    last_update = Column("LastUpdate", DateTime)
    location = Column("SuggestedStorageCategory", String, default="OTHER")
    avg_weight = Column("AverageWeight", Float, default=0.0)
    sample_size = Column("SampleSize", Integer, default=0)


class ShoppingListModel(Base):
    __tablename__ = "shopping_lists"

    # Unique identifier for each shopping list
    id = Column(String, primary_key=True, index=True)
    
    # Link to the home - allows multiple lists per home (One-to-Many)
    home_id = Column(String, ForeignKey("homes.id"), index=True, nullable=False)
    
    # Descriptive name of the list (e.g., "Weekly Groceries")
    name = Column(String, default="New Shopping List")
    
    # Flag to indicate if the user is currently at the store using this list
    is_active_shopping_mode = Column(Boolean, default=False)
    
    # List items stored as a JSON array of objects
    # Format: [{"item_name": str, "quantity": int, "is_bought": bool}]
    items = Column(JSON, default=list)

    # Automatically set on row creation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Automatically updated by the database on every row modification
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship back to the HomeModel
    home = relationship("HomeModel", back_populates="shopping_lists")