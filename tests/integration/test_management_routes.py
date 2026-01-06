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
    client.post("/auth/register", json={"email": email, "password": password, "password_confirm": password, "name": "Admin User"})
    
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


def test_get_my_homes_success():
    """
    Test that a user can retrieve all homes they belong to.
    """
    token, user_id = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create two homes
    client.post("/homes/create", json={"name": "City Apt"}, headers=headers)
    client.post("/homes/create", json={"name": "Country House"}, headers=headers)
    
    # 2. Get list of homes
    response = client.get("/homes/my_homes", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    homes_list = data["data"]
    assert len(homes_list) == 2
    
    # Verify names exist in the list
    home_names = [h["name"] for h in homes_list]
    assert "City Apt" in home_names
    assert "Country House" in home_names
    
    # Verify structure (DTO)
    assert "id" in homes_list[0]
    assert "member_ids" in homes_list[0]

def test_get_my_homes_empty_list():
    """
    Test that a user with no homes gets an empty list (not an error).
    """
    # Create a fresh user
    token, _ = get_auth_token(client, email="homeless@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/homes/my_homes", headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_my_homes_isolation():
    """
    Test that User A cannot see User B's homes.
    """
    # User A setup
    token_a, _ = get_auth_token(client, email="userA@test.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    client.post("/homes/create", json={"name": "User A Home"}, headers=headers_a)
    
    # User B setup
    token_b, _ = get_auth_token(client, email="userB@test.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    client.post("/homes/create", json={"name": "User B Home"}, headers=headers_b)
    
    # User A requests their homes
    response = client.get("/homes/my_homes", headers=headers_a)
    
    homes_list = response.json()["data"]
    assert len(homes_list) == 1
    assert homes_list[0]["name"] == "User A Home"
    # Ensure User B's home is NOT present
    assert "User B Home" not in [h["name"] for h in homes_list]