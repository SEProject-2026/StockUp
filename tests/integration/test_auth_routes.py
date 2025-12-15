import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.infrastructure.app_container import AppContainer

client = TestClient(app)

# Fixture to reset the database before each test
@pytest.fixture(autouse=True)
def reset_database():
    """
    Clears the in-memory database before every test to ensure a clean slate.
    """
    repo = AppContainer.get_user_repository()
    # Access the internal dictionary and clear it
    repo._users = {} 
    yield

# --- Registration Tests ---

def test_register_success():
    """
    Test that registering a new user works correctly.
    """
    response = client.post("/auth/register", json={
        "email": "new@test.com",
        "password": "Password123!",
        "name": "New User"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "new@test.com"

def test_register_duplicate_email():
    """
    Test that registering with an existing email raises an error (400).
    """
    # 1. First registration - Using a valid password
    client.post("/auth/register", json={
        "email": "dup@test.com", "password": "Password123!", "name": "1"
    })
    
    # 2. Second registration (should fail)
    response = client.post("/auth/register", json={
        "email": "dup@test.com", "password": "Password123!", "name": "2"
    })
    
    assert response.status_code == 400
    assert "already exists" in response.text

# --- Login Tests ---

def test_login_success():
    """
    Test that valid login credentials return an access token.
    """
    # Register first
    client.post("/auth/register", json={
        "email": "login@test.com", "password": "SecretPassword123!", "name": "Login User"
    })
    
    # Login
    response = client.post("/auth/login", json={
        "email": "login@test.com", "password": "SecretPassword123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert len(data["access_token"]) > 20

def test_login_wrong_password():
    """
    Test that login fails when the password is incorrect.
    """
    client.post("/auth/register", json={
        "email": "wrong@test.com", "password": "CorrectPass123!", "name": "User"
    })
    
    response = client.post("/auth/login", json={
        "email": "wrong@test.com", "password": "WRONG_PASS"
    })
    
    assert response.status_code == 401

# --- Security & Protected Routes Tests ---

def test_update_name_without_token():
    """
    Test that attempting to update the name without a token is blocked.
    """
    response = client.put("/auth/update_name", json={"name": "Hacker Name"})
    assert response.status_code == 401

def test_update_name_flow_success():
    """
    Full flow test: Register -> Login -> Update Name with Token.
    """
    email = "flow@test.com"
    pwd = "Password123!" # Valid password length
    
    # 1. Register
    client.post("/auth/register", json={"email": email, "password": pwd, "name": "Old Name"})
    
    # 2. Login
    login_res = client.post("/auth/login", json={"email": email, "password": pwd})
    assert login_res.status_code == 200
    
    token = login_res.json()["access_token"]
    
    # 3. Update Name (With Token)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put("/auth/update_name", json={"name": "New Cool Name"}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Cool Name"

def test_change_password_flow():
    """
    Test flow: Register -> Security Check -> Login -> Change Password -> Verify Login
    """
    email = "changepass@test.com"
    old_pass = "OldPassword123!"
    new_pass = "NewPassword456!"
    
    # 1. Register the user first
    client.post("/auth/register", json={"email": email, "password": old_pass, "name": "User"})

    # 2. Security Check: Attempt to change password WITHOUT a token
    # This ensures the route is protected and cannot be accessed anonymously.
    security_check = client.put("/auth/password", json={
        "current_password": old_pass,
        "new_password": new_pass
    })
    assert security_check.status_code == 401 # Unauthorized

    # 3. Login to get a valid token
    login_res = client.post("/auth/login", json={"email": email, "password": old_pass})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 4. Change Password (Success scenario with token)
    change_res = client.put("/auth/password", json={
        "current_password": old_pass,
        "new_password": new_pass
    }, headers=headers)
    
    assert change_res.status_code == 200
    
    # 5. Verify: Login with OLD password should FAIL (401)
    fail_login = client.post("/auth/login", json={"email": email, "password": old_pass})
    assert fail_login.status_code == 401
    
    # 6. Verify: Login with NEW password should SUCCEED (200)
    success_login = client.post("/auth/login", json={"email": email, "password": new_pass})
    assert success_login.status_code == 200