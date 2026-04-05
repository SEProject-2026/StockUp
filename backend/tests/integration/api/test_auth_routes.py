import pytest
from uuid import uuid4
from tests.factories import create_register_payload, create_user_entity

class TestAuthIntegration:

    # ==========================================
    # 1. Registration (POST /auth/register)
    # ==========================================

    def test_register_user_success(self, client, db_session):
        """Happy Path: Register a new user with valid data."""
        payload = create_register_payload(name="Integration User")

        response = client.post("/auth/register", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "Integration User"
        assert data["data"]["email"] == payload["email"]

    def test_register_duplicate_email_fails(self, client, db_session):
        """Sad Path: Block registration with an existing email."""
        email = "duplicate@test.com"
        create_user_entity(db=db_session, email=email)
        db_session.commit()

        payload = create_register_payload(email=email)
        response = client.post("/auth/register", json=payload)

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_register_invalid_email_fails(self, client):
        """Validation: Pydantic EmailStr catches malformed email."""
        payload = {
            "user_id": str(uuid4()),
            "email": "not-an-email",
            "name": "Bad Email"
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_email_normalization(self, client, db_session):
        """Edge Case: Email duplicate detection regardless of case/spaces."""
        email = "  CapsTest@Example.com  "
        payload = {
            "user_id": str(uuid4()),
            "email": email,
            "name": "Caps User"
        }
        client.post("/auth/register", json=payload)
        
        # Try duplicate with lowercase and no spaces
        payload_lower = payload.copy()
        payload_lower["email"] = "capstest@example.com"
        payload_lower["user_id"] = str(uuid4())
        
        response = client.post("/auth/register", json=payload_lower)
        assert response.status_code == 400

    # ==========================================
    # 2. Update Profile (PUT /auth/update_name)
    # ==========================================

    def test_update_name_success(self, client, auth_user, db_session):
        """Happy Path: Authenticated user updates their name in DB."""
        create_user_entity(db=db_session, user_id=auth_user, name="Old Name")
        db_session.commit()

        response = client.put("/auth/update_name", json={"name": "Updated Name"})

        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Name"

    def test_update_name_empty_fails(self, client, auth_user):
        """Validation: Catch empty name strings (422)."""
        response = client.put("/auth/update_name", json={"name": ""})
        assert response.status_code == 422

    def test_update_name_user_not_found(self, client, auth_user, db_session):
        """Sad Path: Auth ID exists but user not in DB."""
        # No user created in db_session
        response = client.put("/auth/update_name", json={"name": "New Name"})
        assert response.status_code == 400

    # ==========================================
    # 3. Push Token (PATCH /auth/me/push-token)
    # ==========================================

    def test_update_push_token_success(self, client, auth_user, db_session):
        """Happy Path: Save push token for authenticated user."""
        create_user_entity(db=db_session, user_id=auth_user)
        db_session.commit()

        response = client.patch("/auth/me/push-token", json={"push_token": "expo_123"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"