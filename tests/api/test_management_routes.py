from tests.container import testing_container

def setup_function():
    testing_container.reset_state()

def get_auth_token(email="home_admin@test.com"):
    password = "Password123!"
    testing_container.client.post("/auth/register", json={
        "email": email, 
        "password": password, 
        "password_confirm": password, 
        "name": "Admin User"
    })
    
    login_res = testing_container.client.post("/auth/login", json={
        "email": email, 
        "password": password
    })
    data = login_res.json()
    return data["access_token"], data["data"]["id"]

def test_create_home_success():
    token, user_id = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"name": "My Dream House"}
    
    response = testing_container.client.post("/homes/create", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    home_data = data["data"]
    
    assert home_data["name"] == "My Dream House"
    assert home_data["admin_id"] == user_id
    assert user_id in home_data["member_ids"]
    assert "id" in home_data

def test_create_home_validation_error():
    token, _ = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"name": ""}
    
    response = testing_container.client.post("/homes/create", json=payload, headers=headers)
    
    assert response.status_code == 422

def test_create_home_unauthorized():
    payload = {"name": "Hacker House"}
    
    response = testing_container.client.post("/homes/create", json=payload)
    
    assert response.status_code == 401

def test_get_my_homes_success():
    token, user_id = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    testing_container.client.post("/homes/create", json={"name": "City Apt"}, headers=headers)
    testing_container.client.post("/homes/create", json={"name": "Country House"}, headers=headers)
    
    response = testing_container.client.get("/homes/my_homes", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    homes_list = data["data"]
    assert len(homes_list) == 2
    
    home_names = [h["name"] for h in homes_list]
    assert "City Apt" in home_names
    assert "Country House" in home_names
    
    assert "id" in homes_list[0]
    assert "member_ids" in homes_list[0]

def test_get_my_homes_empty_list():
    token, _ = get_auth_token(email="homeless@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = testing_container.client.get("/homes/my_homes", headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_my_homes_isolation():
    token_a, _ = get_auth_token(email="userA@test.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    testing_container.client.post("/homes/create", json={"name": "User A Home"}, headers=headers_a)
    
    token_b, _ = get_auth_token(email="userB@test.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    testing_container.client.post("/homes/create", json={"name": "User B Home"}, headers=headers_b)
    
    response = testing_container.client.get("/homes/my_homes", headers=headers_a)
    
    homes_list = response.json()["data"]
    assert len(homes_list) == 1
    assert homes_list[0]["name"] == "User A Home"
    assert "User B Home" not in [h["name"] for h in homes_list]