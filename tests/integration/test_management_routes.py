import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.infrastructure.app_container import AppContainer

client = TestClient(app)

# --- Fixtures ---

@pytest.fixture(autouse=True)
def reset_database():
    """
    Clears the in-memory repositories before every test.
    """
    # Clear Users
    user_repo = AppContainer.get_user_repository()
    if hasattr(user_repo, "_users"):
        user_repo._users = {}
        
    # Clear Homes
    home_repo = AppContainer.get_home_repository()
    if hasattr(home_repo, "_homes"):
        home_repo._homes = {}
        
    yield

# --- Helper Functions ---

def get_auth_token(client, email="home_admin@test.com"):
    """
    Registers and logs in a user, returning the JWT token and user ID.
    """
    password = "Password123!"
    # 1. Register
    client.post("/auth/register", json={"email": email, "password": password, "name": "Admin User"})
    
    # 2. Login
    login_res = client.post("/auth/login", json={"email": email, "password": password})
    data = login_res.json()
    return data["access_token"], data["data"]["id"]

# --- Tests ---

def test_create_home_success():
    """
    Test that a logged-in user can successfully create a home.
    """
    token, user_id = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"name": "My Dream House"}
    
    response = client.post("/homes/create", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    home_data = data["data"]
    
    # Check DTO mapping
    assert home_data["name"] == "My Dream House"
    assert home_data["admin_id"] == user_id
    assert user_id in home_data["member_ids"] # Creator should be a member
    assert "id" in home_data

def test_create_home_validation_error():
    """
    Test that creating a home with an empty name fails (Pydantic validation).
    """
    token, _ = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Empty name should trigger 422 Unprocessable Entity
    payload = {"name": ""}
    
    response = client.post("/homes/create", json=payload, headers=headers)
    
    assert response.status_code == 422

def test_create_home_unauthorized():
    """
    Test that creating a home without a token fails.
    """
    payload = {"name": "Hacker House"}
    
    # No headers provided
    response = client.post("/homes/create", json=payload)
    
    assert response.status_code == 401