import os
import logging
import pytest

# Disable loguru logs
os.environ["LOGURU_OFF"] = "true"
try:
    from loguru import logger
    logger.disable("src")
    logger.disable("tests")
except ImportError:
    pass

# Disable standard python logging for libraries/services during tests
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("uvicorn").setLevel(logging.ERROR)
logging.getLogger("fastapi").setLevel(logging.ERROR)

from tests.factories import (
    create_user_entity, 
    create_home_entity, 
    create_product_entity, 
    create_shopping_list_entity
)

@pytest.fixture
def any_user(request):
    """
    Creates a user. If 'db_session' fixture is available in the test 
    context, it persists the user to the DB.
    """
    db = request.node.get_fixture_value("db_session") if "db_session" in request.fixturenames else None
    return create_user_entity(db=db)

@pytest.fixture
def any_home(any_user, request):
    """
    Creates a home linked to any_user. Persists if db_session is present.
    """
    db = request.node.get_fixture_value("db_session") if "db_session" in request.fixturenames else None
    return create_home_entity(db=db, admin_user_id=any_user.id)

@pytest.fixture
def auth_setup(any_home, any_user):
    """Returns a tuple of (home, user) already linked."""
    return any_home, any_user

@pytest.fixture
def any_product(any_home, request):
    """
    Creates a product linked to any_home. Persists if db_session is present.
    """
    db = request.node.get_fixture_value("db_session") if "db_session" in request.fixturenames else None
    return create_product_entity(db=db, home_id=any_home._id)

@pytest.fixture
def any_shopping_list(any_home, request):
    """
    Provides a shopping list linked to any_home. Persists if db_session is present.
    """
    db = request.node.get_fixture_value("db_session") if "db_session" in request.fixturenames else None
    return create_shopping_list_entity(db=db, home_id=any_home._id)