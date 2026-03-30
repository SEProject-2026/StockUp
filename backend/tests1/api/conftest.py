import pytest
import uuid
from src.main import app as fastapi_app
from src.api.security import get_current_user_id

# --- Mocks ---

class MockSupabaseAuthProvider:
    """
    A fake Auth Provider that ensures we never touch the real Supabase API
    during automated tests.
    """
    def verify_token(self, token: str):
        # We return None because the actual UID injection 
        # is handled by the dependency_override below.
        return None

# --- Fixtures ---

@pytest.fixture(scope="session")
def app():
    """
    Provides the FastAPI app instance.
    """
    return fastapi_app

@pytest.fixture
def client():
    """
    Returns the TestClient from the testing container.
    """
    from tests1.container import testing_container
    return testing_container.client

@pytest.fixture
def mock_auth(app):
    """
    The most important fixture. It bypasses the JWT check and 
    injects a specific User ID into the request.
    
    Usage in a test:
        def test_something(client, mock_auth):
            uid = uuid.uuid4()
            mock_auth(uid)
            client.get("/protected-route")
    """
    def _set_user(user_id: uuid.UUID):
        # This function replaces 'get_current_user_id' inside FastAPI
        async def mocked_dependency():
            return user_id
            
        app.dependency_overrides[get_current_user_id] = mocked_dependency
    
    yield _set_user
    
    # Cleanup: remove the override after the test finishes
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def force_mock_provider():
    """
    Ensures that the TestingContainer always uses the Mock provider
    instead of the real SupabaseAuthProvider.
    """
    from tests1.container import testing_container
    testing_container.auth_provider = MockSupabaseAuthProvider()