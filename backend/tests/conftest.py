import pytest
from tests.factories import (
    create_user_entity, 
    create_home_entity, 
    create_product_entity, 
    create_shopping_list_entity
)

@pytest.fixture
def any_user():
    return create_user_entity()

@pytest.fixture
def any_home(any_user):
    # Automatically links the home to the admin user created above
    return create_home_entity(admin_user_id=any_user.id)

@pytest.fixture
def auth_setup(any_home, any_user):
    """Returns a tuple of (home, user) already linked."""
    return any_home, any_user

@pytest.fixture
def any_product(any_home):
    return create_product_entity(home_id=any_home._id)

@pytest.fixture
def empty_list(any_home):
    """Provides a fresh shopping list linked to a home."""
    return create_shopping_list_entity(home_id=any_home._id)