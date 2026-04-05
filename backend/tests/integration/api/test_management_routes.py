import pytest
from uuid import uuid4
from src.infrastructure.db.models import HomeModel, UserModel
from tests.factories import create_user_entity, create_home_entity
from src.api.security import get_current_user_id
from src.main import app

class TestManagementAPIIntegration:

    # ==========================================
    # 1. Home Creation & Listing
    # ==========================================

    def test_create_home_api_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        db_session.flush()

        payload = {"name": "Mansion"}
        response = client.post("/homes/create", json=payload)

        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Mansion"

    def test_get_my_homes_api(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        create_home_entity(db=db_session, admin_user_id=auth_user, name="Home 1")
        create_home_entity(db=db_session, admin_user_id=auth_user, name="Home 2")
        db_session.flush()

        response = client.get("/homes/my_homes")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2

    # ==========================================
    # 2. Join Codes & Requests
    # ==========================================

    def test_view_join_code_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        db_session.flush()

        response = client.get(f"/homes/{home.id}/join_code")
        assert response.status_code == 200
        assert "join_code" in response.json()["data"]

    def test_view_join_code_forbidden_for_non_members(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        other_user = create_user_entity(db=db_session)
        other_home = create_home_entity(db=db_session, admin_user_id=other_user.id)
        db_session.flush()

        response = client.get(f"/homes/{other_home.id}/join_code")
        assert response.status_code == 403

    def test_join_home_with_code_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        other_user = create_user_entity(db=db_session)
        target_home = create_home_entity(db=db_session, admin_user_id=other_user.id)
        db_session.flush()

        response = client.post("/homes/join", json={"home_code": target_home.join_code})
        assert response.status_code == 200

    def test_get_join_requests_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        applicant = create_user_entity(db=db_session, name="John Doe")
        home = create_home_entity(db=db_session, admin_user_id=auth_user, requesting_user_ids=[applicant.id])
        db_session.flush()

        response = client.get(f"/homes/{home.id}/join_requests")
        assert response.status_code == 200
        assert str(applicant.id) in response.json()["data"]

    def test_get_join_requests_unauthorized_forbidden(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        other_owner = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=other_owner.id)
        db_session.flush()

        response = client.get(f"/homes/{home.id}/join_requests")
        assert response.status_code == 403

    def test_answer_join_request_approve(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        applicant = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=auth_user, requesting_user_ids=[applicant.id])
        db_session.flush()

        payload = {"user_id": str(applicant.id), "approved": True}
        response = client.post(f"/homes/{home.id}/answer_request", json=payload)

        assert response.status_code == 200
        assert str(applicant.id) in response.json()["data"]["member_ids"]

    def test_answer_request_by_non_admin_fails(self, client, auth_user, db_session):
        owner = create_user_entity(db=db_session)
        create_user_entity(db=db_session, user_id=auth_user)
        applicant = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=owner.id, requesting_user_ids=[applicant.id])
        
        db_home = db_session.get(HomeModel, str(home.id))
        db_home.users.append(db_session.get(UserModel, str(auth_user)))
        db_session.flush()

        response = client.post(f"/homes/{home.id}/answer_request", json={"user_id": str(applicant.id), "approved": True})
        assert response.status_code == 400

    # ==========================================
    # 3. Membership & Roles
    # ==========================================

    def test_remove_member_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        member = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        
        db_home = db_session.get(HomeModel, str(home.id))
        db_home.users.append(db_session.get(UserModel, str(member.id)))
        db_session.flush()

        response = client.delete(f"/homes/{home.id}/members/{member.id}")
        assert response.status_code == 200
        assert str(member.id) not in response.json()["data"]["member_ids"]

    def test_remove_member_unauthorized_fails(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        owner = create_user_entity(db=db_session)
        victim = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=owner.id)
        
        db_home = db_session.get(HomeModel, str(home.id))
        db_home.users.extend([db_session.get(UserModel, str(auth_user)), db_session.get(UserModel, str(victim.id))])
        db_session.flush()

        response = client.delete(f"/homes/{home.id}/members/{victim.id}")
        assert response.status_code == 400

    def test_leave_home_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        owner = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=owner.id)
        
        db_home = db_session.get(HomeModel, str(home.id))
        db_home.users.append(db_session.get(UserModel, str(auth_user)))
        db_session.flush()

        response = client.post(f"/homes/{home.id}/leave")
        assert response.status_code == 200

    def test_admin_cannot_leave_home_fails(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        db_session.flush()

        response = client.post(f"/homes/{home.id}/leave")
        assert response.status_code == 400

    def test_switch_home_head_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        successor = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        
        db_home = db_session.get(HomeModel, str(home.id))
        db_home.users.append(db_session.get(UserModel, str(successor.id))) 
        db_session.flush()

        response = client.put(f"/homes/{home.id}/switch_head", json={"new_head_id": str(successor.id)})
        assert response.status_code == 200

    def test_switch_head_to_non_member_fails(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        stranger = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        db_session.flush()

        response = client.put(f"/homes/{home.id}/switch_head", json={"new_head_id": str(stranger.id)})
        assert response.status_code == 400

    # ==========================================
    # 4. Settings & Expiration
    # ==========================================

    def test_update_expiration_range_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        db_session.flush()

        response = client.patch(f"/homes/{home.id}/expiration_range", json={"new_range": 14})
        assert response.status_code == 200
        assert response.json()["data"]["expiration_range"] == 14

    def test_update_expiration_range_invalid_value(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        db_session.flush()

        response = client.patch(f"/homes/{home.id}/expiration_range", json={"new_range": -5})
        assert response.status_code in [400, 422]

    # ==========================================
    # 5. Deletion & Found Scenarios
    # ==========================================

    def test_delete_home_success(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        db_session.flush()

        response = client.delete(f"/homes/{home.id}")
        assert response.status_code == 200
        assert db_session.get(HomeModel, str(home.id)) is None

    def test_delete_home_unauthorized_fails(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        owner = create_user_entity(db=db_session)
        home = create_home_entity(db=db_session, admin_user_id=owner.id)
        
        db_home = db_session.get(HomeModel, str(home.id))
        db_home.users.append(db_session.get(UserModel, str(auth_user)))
        db_session.flush()

        response = client.delete(f"/homes/{home.id}")
        assert response.status_code == 400

    def test_get_home_details_not_found(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        db_session.flush()
        response = client.get(f"/homes/{uuid4()}/details")
        assert response.status_code == 404

    def test_answer_request_for_non_existent_user(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        home = create_home_entity(db=db_session, admin_user_id=auth_user)
        db_session.flush()

        response = client.post(f"/homes/{home.id}/answer_request", json={"user_id": str(uuid4()), "approved": True})
        assert response.status_code == 400

    def test_interact_with_non_existent_home(self, client, auth_user, db_session):
        create_user_entity(db=db_session, user_id=auth_user)
        db_session.flush()
        response = client.get(f"/homes/{uuid4()}/join_code")
        assert response.status_code in [400, 403, 404]