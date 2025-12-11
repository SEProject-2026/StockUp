from datetime import date
import pytest
from uuid import UUID

from domain.smart_home.enums import LocationType
from domain.smart_home.home import Home
from domain.smart_home.product import Product
from domain.domain_services.domain_exception import UserMustBeMemberException, ProductNotFoundException

user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
home_id = UUID("223e4567-e89b-12d3-a456-426614174000")
product_id = UUID("d23e4567-e89b-12d3-a456-426614174000")

def test_home_initialization():
    """
    Test that a new Home entity is created with correct default values.
    """
    # Arrange + Act
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")

    # Assert

    assert home.get_id() == home_id
    assert home.get_name() == "My Home"
    assert home.get_join_code() == "JOIN123"
    assert home.is_member(user_id)
    assert home.is_admin(user_id)
    assert home.get_join_requests() == {}
    assert home.get_inventory() == {}

def test_set_name():
    """
    Test that the name of the Home can be updated.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="Old Name", join_code="JOIN123")

    # Act
    home.set_name("New Name")

    # Assert
    assert home.get_name() == "New Name"


def test_add_join_request():
    """
    Test that a join request can be added successfully.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    requester_id = UUID("423e4567-e89b-12d3-a456-426614174000")

    # Act
    home.add_join_request(requester_id)

    # Assert
    assert home.has_request_from(requester_id) is True

def test_add_existing_join_request_raises():
    """
    Test that adding an existing join request raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    requester_id = UUID("523e4567-e89b-12d3-a456-426614174000")
    home.add_join_request(requester_id)

    # Act / Assert
    with pytest.raises(ValueError) as exc_info:
        home.add_join_request(requester_id)
    
    assert str(exc_info.value) == "User has already requested to join."

def test_remove_join_request():
    """
    Test that a join request can be removed successfully.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    requester_id = UUID("623e4567-e89b-12d3-a456-426614174000")
    home.add_join_request(requester_id)

    # Act
    home.remove_join_request(requester_id)

    # Assert
    assert home.has_request_from(requester_id) is False

def test_remove_nonexistent_join_request_raises():
    """
    Test that removing a non-existent join request raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    requester_id = UUID("723e4567-e89b-12d3-a456-426614174000")

    # Act / Assert
    with pytest.raises(ValueError) as exc_info:
        home.remove_join_request(requester_id)
    
    assert str(exc_info.value) == "No such join request found."

def test_add_member():
    """
    Test that a member can be added successfully.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    new_member_id = UUID("823e4567-e89b-12d3-a456-426614174000")

    # Act
    home.add_member(new_member_id)

    # Assert
    assert home.is_member(new_member_id) is True

def test_add_existing_member_raises():
    """
    Test that adding an existing member raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    existing_member_id = UUID("923e4567-e89b-12d3-a456-426614174000")
    home.add_member(existing_member_id)

    # Act / Assert
    with pytest.raises(ValueError) as exc_info:
        home.add_member(existing_member_id)
    
    assert str(exc_info.value) == "User is already a member of the home."

def test_remove_member():
    """
    Test that a member can be removed successfully.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    member_id = UUID("a23e4567-e89b-12d3-a456-426614174000")
    home.add_member(member_id)

    # Act
    home.remove_member(member_id)

    # Assert
    assert home.is_member(member_id) is False

def test_remove_nonexistent_member_raises():
    """
    Test that removing a non-existent member raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    non_member_id = UUID("b23e4567-e89b-12d3-a456-426614174000")

    # Act / Assert
    with pytest.raises(UserMustBeMemberException) as exc_info:
        home.remove_member(non_member_id)

def test_assign_admin():
    """
    Test that assigning admin to a member works correctly.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    new_admin_id = UUID("c23e4567-e89b-12d3-a456-426614174000")
    home.add_member(new_admin_id)

    # Act
    home.assign_admin(new_admin_id)

    # Assert
    assert home.is_admin(new_admin_id) is True

def test_assign_admin_non_member_raises():
    """
    Test that assigning admin to a non-member raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    non_member_id = UUID("323e4567-e89b-12d3-a456-426614174000")

    # Act / Assert
    with pytest.raises(UserMustBeMemberException) as exc_info:
        home.assign_admin(non_member_id)
    
def test_add_to_inventory():
    """
    Test that a product can be added to the home's inventory.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Milk", quantity=5)

    # Act
    home.get_inventory()[product_id] = product

    # Assert
    assert product_id in home.get_inventory()
    assert home.get_inventory()[product_id].get_name() == "Milk"

def test_remove_from_inventory():
    """
    Test that a product can be removed from the home's inventory.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Milk", quantity=2)
    home.add_to_inventory(product)

    # Act
    home.remove_from_inventory(product_id)

    # Assert
    assert product_id not in home.get_inventory()

def test_remove_nonexistent_product_raises():
    """
    Test that removing a non-existent product from inventory raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    nonexistent_product_id = UUID("e23e4567-e89b-12d3-a456-426614174000")

    # Act / Assert
    with pytest.raises(ProductNotFoundException) as exc_info:
        home.remove_from_inventory(nonexistent_product_id)
    
def test_update_product_quantity():
    """
    Test that the quantity of a product in inventory can be updated.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Milk", quantity=10)
    home.add_to_inventory(product)

    # Act
    home.update_product_quantity(product_id, 15)

    # Assert
    assert home.get_inventory()[product_id].get_quantity() == 15

def test_update_product_quantity_nonexistent_raises():
    """
    Test that updating the quantity of a non-existent product raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    nonexistent_product_id = UUID("f23e4567-e89b-12d3-a456-426614174000")

    # Act / Assert
    with pytest.raises(ProductNotFoundException) as exc_info:
        home.update_product_quantity(nonexistent_product_id, 5)
    
def test_update_expiration_date():
    """
    Test that the expiration date of a product in inventory can be updated.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Milk", quantity=3, expiration_date=date.today())
    home.add_to_inventory(product)
    new_date = date.today().replace(day=date.today().day + 1)

    # Act
    home.update_expiration_date(product_id, new_date)

    # Assert
    assert home.get_inventory()[product_id].get_expiration_date() == new_date

def test_update_expiration_date_nonexistent_raises():
    """
    Test that updating the expiration date of a non-existent product raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    nonexistent_product_id = UUID("g23e4567-e89b-12d3-a456-426614174000")
    new_date = date.today().replace(day=date.today().day + 1)

    # Act / Assert
    with pytest.raises(ProductNotFoundException) as exc_info:
        home.update_expiration_date(nonexistent_product_id, new_date)
    
def test_update_nickname():
    """
    Test that the nickname of a product in inventory can be updated.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Tomato Dip", quantity=4)
    home.add_to_inventory(product)

    # Act
    home.update_nickname(product_id, "Ketchup")

    # Assert
    assert home.get_inventory()[product_id].get_nickname() == "Ketchup"

def test_update_nickname_nonexistent_raises():
    """
    Test that updating the nickname of a non-existent product raises an exception.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    nonexistent_product_id = UUID("h23e4567-e89b-12d3-a456-426614174000")

    # Act / Assert
    with pytest.raises(ProductNotFoundException) as exc_info:
        home.update_nickname(nonexistent_product_id, "New Nickname")
    
def test_filter_by_expiration_type():
    """
    Test that products can be filtered by expiration type.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Milk", quantity=5)
    home.add_to_inventory(product)

    # Act
    filtered_products = home.filter_by_expiration_type(product.get_expiration_type())

    # Assert
    assert product_id in filtered_products

def test_filter_by_location():
    """
    Test that products can be filtered by location.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Milk", quantity=5, location=LocationType.FRIDGE)
    home.add_to_inventory(product)

    # Act
    filtered_products = home.filter_by_location(LocationType.FRIDGE)

    # Assert
    assert product_id in filtered_products

def test_search_product():
    """
    Test that products can be searched by name or nickname.
    """
    # Arrange
    home = Home(user_id=user_id, id=home_id, name="My Home", join_code="JOIN123")
    product = Product(barcode="1234567890123", id=product_id, name="Milk", nickname="Dairy Drink", quantity=5)
    another_product_id = UUID("i23e4567-e89b-12d3-a456-426614174000")
    another_product = Product(barcode="9876543210987", id=another_product_id, name="Meat", nickname="Protein", quantity=3)
    home.add_to_inventory(product)
    home.add_to_inventory(another_product)

    # Act
    found_products_by_initials = home.search_product("M")
    found_products_by_name = home.search_product("Milk")
    found_products_by_nickname = home.search_product("Dairy")

    # Assert
    assert product_id in found_products_by_initials and another_product_id in found_products_by_initials
    assert product_id in found_products_by_name
    assert product_id in found_products_by_nickname