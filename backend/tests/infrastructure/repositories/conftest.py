import pytest
from tests.container import testing_container

@pytest.fixture(scope="module", autouse=True)
def setup_db_mode_for_module():
    """
    Runs once per test file (module) in this directory.
    Switches the container to DB mode before the file starts,
    and returns it to Memory mode when the file finishes.
    """
    testing_container.activate_db_mode()
    yield
    testing_container.activate_memory_mode()

@pytest.fixture(autouse=True)
def reset_db_state_per_test():
    """
    Runs automatically before EVERY test function in this directory.
    Ensures absolute test isolation by cleaning the database.
    """
    testing_container.reset_state()
    yield