from tests.container import testing_container

def setup_function():
    testing_container.reset_state()

def test_register_success():
    response = testing_container.client.post("/auth/register", json={
        "email": "new@test.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "name": "New User"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "new@test.com"

def test_register_duplicate_email():
    testing_container.client.post("/auth/register", json={
        "email": "dup@test.com", "password": "Password123!", "password_confirm": "Password123!", "name": "1"
    })
    
    response = testing_container.client.post("/auth/register", json={
        "email": "dup@test.com", "password": "Password123!", "password_confirm": "Password123!", "name": "2"
    })
    
    assert response.status_code == 400

def test_login_success():
    testing_container.client.post("/auth/register", json={
        "email": "login@test.com", "password": "SecretPassword123!", "password_confirm": "SecretPassword123!", "name": "Login User"
    })
    
    response = testing_container.client.post("/auth/login", json={
        "email": "login@test.com", "password": "SecretPassword123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert len(data["access_token"]) > 20

def test_login_wrong_password():
    testing_container.client.post("/auth/register", json={
        "email": "wrong@test.com", "password": "CorrectPass123!", "password_confirm": "CorrectPass123!", "name": "User"
    })
    
    response = testing_container.client.post("/auth/login", json={
        "email": "wrong@test.com", "password": "WRONG_PASS"
    })
    
    assert response.status_code == 401

def test_update_name_without_token():
    response = testing_container.client.put("/auth/update_name", json={"name": "Hacker Name"})
    assert response.status_code == 401

def test_update_name_flow_success():
    email = "flow@test.com"
    pwd = "Password123!" 
    
    testing_container.client.post("/auth/register", json={"email": email, "password": pwd, "password_confirm": pwd, "name": "Old Name"})
    
    login_res = testing_container.client.post("/auth/login", json={"email": email, "password": pwd})
    assert login_res.status_code == 200
    
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = testing_container.client.put("/auth/update_name", json={"name": "New Cool Name"}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Cool Name"

def test_change_password_flow():
    email = "changepass@test.com"
    old_pass = "OldPassword123!"
    new_pass = "NewPassword456!"
    
    testing_container.client.post("/auth/register", json={"email": email, "password": old_pass, "password_confirm": old_pass, "name": "User"})

    security_check = testing_container.client.put("/auth/password", json={
        "current_password": old_pass,
        "new_password": new_pass
    })
    assert security_check.status_code == 401 

    login_res = testing_container.client.post("/auth/login", json={"email": email, "password": old_pass})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    change_res = testing_container.client.put("/auth/password", json={
        "current_password": old_pass,
        "new_password": new_pass
    }, headers=headers)
    
    assert change_res.status_code == 200
    
    fail_login = testing_container.client.post("/auth/login", json={"email": email, "password": old_pass})
    assert fail_login.status_code == 401
    
    success_login = testing_container.client.post("/auth/login", json={"email": email, "password": new_pass})
    assert success_login.status_code == 200