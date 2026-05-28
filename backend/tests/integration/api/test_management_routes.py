import pytest
import asyncio
from uuid import uuid4
from src.infrastructure.db.models import HomeModel, UserModel
from tests.factories import create_user_entity, create_home_entity
from src.api.security import get_current_user_id
from src.main import app

class TestManagementAPIIntegration:

    # ==========================================
    # 1. Home Creation & Listing
    # ==========================================

    async def test_create_home_api_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        await db_session.commit()
        
        payload = {"name": "Mansion"}
        response = await client.post("/homes/create", json=payload)

        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Mansion"

    async def test_get_my_homes_api(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        create_home_entity(db=db_session, admin_user=user, name="Home 1")
        create_home_entity(db=db_session, admin_user=user, name="Home 2")
        await db_session.commit()

        response = await client.get("/homes/my_homes")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2

    # ==========================================
    # 2. Join Codes & Requests
    # ==========================================

    async def test_view_join_code_success(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user=user)
        await db_session.commit()

        response = await client.get(f"/homes/{home.id}/join_code")
        assert response.status_code == 200
        assert "join_code" in response.json()["data"]

    async def test_view_join_code_forbidden_for_non_members(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        other_user = create_user_entity(db=db_session)
        other_home = create_home_entity(db=db_session, admin_user=other_user)
        await db_session.commit()

        response = await client.get(f"/homes/{other_home.id}/join_code")
        assert response.status_code == 403

    async def test_join_home_with_code_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        other_user = create_user_entity(db=db_session)
        target_home = create_home_entity(db=db_session, admin_user=other_user)
        await db_session.commit()

        response = await client.post("/homes/join", json={"home_code": target_home.join_code})
        assert response.status_code == 200

    async def test_get_join_requests_success(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        applicant = create_user_entity(db=db_session, name="John Doe")
        home = create_home_entity(db=db_session, admin_user=user, requesting_users=[applicant])
        await db_session.commit()

        response = await client.get(f"/homes/{home.id}/join_requests")
        assert response.status_code == 200
        assert str(applicant.id) in response.json()["data"]

    async def test_get_join_requests_unauthorized_forbidden(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        other_owner = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=other_owner)
        await db_session.commit()

        response = await client.get(f"/homes/{home.id}/join_requests")
        assert response.status_code == 403

    async def test_answer_join_request_approve(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        applicant = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=user, requesting_users=[applicant])
        await db_session.commit()

        payload = {"user_id": str(applicant.id), "approved": True}
        response = await client.post(f"/homes/{home.id}/answer_request", json=payload)

        assert response.status_code == 200
        assert str(applicant.id) in response.json()["data"]["member_ids"]

    async def test_answer_request_by_non_admin_fails(self, client, auth_user, db_session):
        owner = create_user_entity(db=db_session)
        user = create_user_entity(db=db_session, user_id=auth_user)
        applicant = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=owner, requesting_users=[applicant])
        
        db_home = await db_session.get(HomeModel, str(home.id))
        db_auth_user = await db_session.get(UserModel, str(auth_user))
        db_home.users.append(db_auth_user)
        await db_session.commit()

        response = await client.post(f"/homes/{home.id}/answer_request", json={"user_id": str(applicant.id), "approved": True})
        assert response.status_code == 400

    # ==========================================
    # 3. Membership & Roles
    # ==========================================

    async def test_remove_member_success(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        member = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=user)
        
        db_home = await db_session.get(HomeModel, str(home.id))
        db_member = await db_session.get(UserModel, str(member.id))
        db_home.users.append(db_member)
        await db_session.commit()

        response = await client.delete(f"/homes/{home.id}/members/{member.id}")
        assert response.status_code == 200
        assert str(member.id) not in response.json()["data"]["member_ids"]

    async def test_remove_member_unauthorized_fails(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        owner = create_user_entity(db=db_session)
        victim = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=owner)
        
        db_home = await db_session.get(HomeModel, str(home.id))
        db_auth = await db_session.get(UserModel, str(auth_user))
        db_victim = await db_session.get(UserModel, str(victim.id))
        db_home.users.extend([db_auth, db_victim])
        await db_session.commit()

        response = await client.delete(f"/homes/{home.id}/members/{victim.id}")
        assert response.status_code == 400

    async def test_leave_home_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        owner = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=owner)
        
        db_home = await db_session.get(HomeModel, str(home.id))
        db_auth = await db_session.get(UserModel, str(auth_user))
        db_home.users.append(db_auth)
        await db_session.commit()

        response = await client.post(f"/homes/{home.id}/leave")
        assert response.status_code == 200

    async def test_admin_cannot_leave_home_fails(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user=user)
        await db_session.commit()

        response = await client.post(f"/homes/{home.id}/leave")
        assert response.status_code == 400

    async def test_switch_home_head_success(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        successor = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=user)
        
        db_home = await db_session.get(HomeModel, str(home.id))
        db_successor = await db_session.get(UserModel, str(successor.id))
        db_home.users.append(db_successor) 
        await db_session.commit()

        response = await client.put(f"/homes/{home.id}/switch_head", json={"new_head_id": str(successor.id)})
        assert response.status_code == 200

    async def test_switch_head_to_non_member_fails(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        stranger = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=user)
        await db_session.commit()

        response = await client.put(f"/homes/{home.id}/switch_head", json={"new_head_id": str(stranger.id)})
        assert response.status_code == 400

    # ==========================================
    # 4. Settings & Expiration
    # ==========================================

    async def test_update_expiration_range_success(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user=user)
        await db_session.commit()

        response = await client.patch(f"/homes/{home.id}/expiration_range", json={"new_range": 14})
        assert response.status_code == 200
        assert response.json()["data"]["expiration_range"] == 14

    async def test_update_expiration_range_invalid_value(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user=user)
        await db_session.commit()

        response = await client.patch(f"/homes/{home.id}/expiration_range", json={"new_range": -5})
        assert response.status_code in [400, 422]

    # ==========================================
    # 5. Deletion & Found Scenarios
    # ==========================================

    async def test_delete_home_success(self, client, auth_user, db_session):
        """
        Happy Path: Admin successfully deletes a home.
        Cites: ADD 7.1 (Testing Strategy).
        """
        # 1. Setup: Create user and home
        user = create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user=user)
        await db_session.commit()

        # 2. Action: Delete via API
        response = await client.delete(f"/homes/{home.id}")
        assert response.status_code == 200

        # 3. Verification: Ensure it's gone from DB
        from sqlalchemy import select
        # Use engine directly to avoid session connection issues after commit
        engine = db_session.bind
        async with engine.connect() as conn:
            result = await conn.execute(select(HomeModel).where(HomeModel.id == str(home.id)))
            deleted_home = result.scalars().first()
        
        assert deleted_home is None

    async def test_delete_home_unauthorized_fails(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        owner = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user=owner)
        
        db_home = await db_session.get(HomeModel, str(home.id))
        db_auth = await db_session.get(UserModel, str(auth_user))
        db_home.users.append(db_auth)
        await db_session.commit()

        response = await client.delete(f"/homes/{home.id}")
        assert response.status_code == 400

    async def test_get_home_details_not_found(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        await db_session.commit()
        response = await client.get(f"/homes/{uuid4()}/details")
        assert response.status_code == 404

    async def test_answer_request_for_non_existent_user(self, client, auth_user, db_session):
        user = create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user=user)
        await db_session.commit()

        response = await client.post(f"/homes/{home.id}/answer_request", json={"user_id": str(uuid4()), "approved": True})
        assert response.status_code == 400

    async def test_interact_with_non_existent_home(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        await db_session.commit()
        response = await client.get(f"/homes/{uuid4()}/join_code")
        assert response.status_code in [400, 403, 404]