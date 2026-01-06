from sqlalchemy import Column, String, Integer, Date, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from src.infrastructure.db.database import Base
import enum


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
    

    products = relationship("ProductModel", back_populates="home", cascade="all, delete-orphan")


class ProductModel(Base):

    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    home_id = Column(String, ForeignKey("homes.id"))
    
    original_name = Column(String)
    nickname = Column(String, nullable=True)
    barcode = Column(String, nullable=True, index=True)
    location = Column(String) 
    
    quantity = Column(Integer, default=0) 


    home = relationship("HomeModel", back_populates="products")
    
    items = relationship("ProductItemModel", back_populates="product", cascade="all, delete-orphan")


class ProductItemModel(Base):
    __tablename__ = "product_items"

    id = Column(Integer, primary_key=True, autoincrement=True) 
    product_id = Column(String, ForeignKey("products.id"))
    
    expiration_date = Column(Date, nullable=True) 
    quantity = Column(Integer)
    expiration_type = Column(String) 

    product = relationship("ProductModel", back_populates="items")