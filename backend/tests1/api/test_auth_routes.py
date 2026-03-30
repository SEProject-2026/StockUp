import pytest
import uuid
from src.main import app
from src.api.security import get_current_user_id
from tests1.container import testing_container

# Fixed UUID for testing consistency
FAKE_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

def setup_function():
    """
    Clear database state before each test.
    """
    testing_container.reset_state()
    # Ensure overrides are cleared before starting
    app.dependency_overrides.clear()

async def mocked_get_current_user_id():
    """
    Dependency override to bypass Supabase JWT verification.
    Always returns the fixed FAKE_USER_ID.
    """
    return FAKE_USER_ID

def test_register_success():
    """
    Test successful user synchronization from Supabase to local DB.
    Input: user_id (UUID), email, name.
    Expect: 200 OK and matching user data.
    """
    new_uid = str(uuid.uuid4())
    payload = {
        "user_id": new_uid,
        "email": "new_user@test.com",
        "name": "Test User"
    }

    response = testing_container.client.post("/auth/register", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "new_user@test.com"
    assert data["data"]["id"] == new_uid

def test_register_duplicate_email():
    """
    Test that registering two different UIDs with the same email fails.
    Expect: 400 Bad Request.
    """
    email = "shared@test.com"
    
    # Register first user
    testing_container.client.post("/auth/register", json={
        "user_id": str(uuid.uuid4()), "email": email, "name": "User 1"
    })

    # Try to register second user with same email
    response = testing_container.client.post("/auth/register", json={
        "user_id": str(uuid.uuid4()), "email": email, "name": "User 2"
    })

    assert response.status_code == 400
    assert "already exists" in response.text.lower()

def test_update_name_unauthorized():
    """
    Test that the protected update_name route fails without an Authorization header.
    Expect: 401 Unauthorized.
    """
    # Note: Dependency override is NOT applied here to test the security gate
    response = testing_container.client.put("/auth/update_name", json={"name": "New Name"})
    assert response.status_code == 401

def test_update_name_success():
    """
    Test successful name update for an authenticated user.
    Uses dependency override to bypass JWT parsing.
    """
    # 1. Setup: Apply dependency override for this specific test
    app.dependency_overrides[get_current_user_id] = mocked_get_current_user_id

    try:
        # 2. Setup: Ensure the user exists in our local DB first
        testing_container.client.post("/auth/register", json={
            "user_id": str(FAKE_USER_ID),
            "email": "auth_user@test.com",
            "name": "Old Name"
        })

        # 3. Act: Update the name
        # We send a dummy Bearer token; the content doesn't matter because of the override
        headers = {"Authorization": "Bearer mocked_token"}
        response = testing_container.client.put(
            "/auth/update_name", 
            json={"name": "Updated Name"},
            headers=headers
        )

        # 4. Assert
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Name"

    finally:
        # Clean up override for subsequent tests
        app.dependency_overrides.clear()