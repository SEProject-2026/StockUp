import uuid
import pytest
from src.domain.home.home import Home

class TestHomeDomain:

    # ==========================================
    # 1. Initialization & Creation
    # ==========================================
    
    def test_initialization_success(self, any_home, any_user):
        """Happy Path: Verify home is created with correct attributes via fixture."""
        assert any_home.get_name() == "Test Home"
        assert any_home.is_admin(any_user.id) is True
        assert any_user.id in any_home.get_members()
        assert len(any_home.get_join_code()) == 8
        assert any_home.get_expiration_range() == 7

    def test_creation_empty_name_fails(self, any_user):
        """Sad Path: Verify validation prevents empty home names."""
        with pytest.raises(ValueError, match="Home name cannot be empty"):
            Home(user_id=any_user.id, name="")
        with pytest.raises(ValueError, match="Home name cannot be empty"):
            Home(user_id=any_user.id, name="   ")

    # ==========================================
    # 2. Join Requests (add_join_request)
    # ==========================================

    def test_add_join_request_success(self, any_home):
        """Happy Path: Adding a valid join request."""
        user_id = uuid.uuid4()
        any_home.add_join_request(user_id)
        assert any_home.has_request_from(user_id) is True

    def test_add_join_request_duplicate_fails(self, any_home):
        """Sad Path: Cannot request to join twice."""
        user_id = uuid.uuid4()
        any_home.add_join_request(user_id)
        with pytest.raises(ValueError, match="already requested to join"):
            any_home.add_join_request(user_id)

    def test_add_join_request_existing_member_fails(self, any_home, any_user):
        """Sad Path: Current members cannot request to join."""
        with pytest.raises(ValueError, match="already a member"):
            any_home.add_join_request(any_user.id)

    # ==========================================
    # 3. Answering Requests (answer_join_request)
    # ==========================================

    def test_answer_request_approve_success(self, any_home, any_user):
        """Happy Path: Admin approves a candidate."""
        new_user_id = uuid.uuid4()
        any_home.add_join_request(new_user_id)
        any_home.answer_join_request(head_user_id=any_user.id, user_id=new_user_id, approved=True)
        
        assert any_home.is_member(new_user_id) is True
        assert any_home.has_request_from(new_user_id) is False

    def test_answer_request_deny_success(self, any_home, any_user):
        """Happy Path: Admin denies a candidate."""
        new_user_id = uuid.uuid4()
        any_home.add_join_request(new_user_id)
        any_home.answer_join_request(head_user_id=any_user.id, user_id=new_user_id, approved=False)
        
        assert any_home.is_member(new_user_id) is False
        assert any_home.has_request_from(new_user_id) is False

    def test_answer_request_unauthorized_fails(self, any_home):
        """Sad Path: Non-admin tries to approve a candidate."""
        stranger_id = uuid.uuid4()
        candidate_id = uuid.uuid4()
        any_home.add_join_request(candidate_id)
        with pytest.raises(PermissionError, match="Only admin can approve"):
            any_home.answer_join_request(head_user_id=stranger_id, user_id=candidate_id, approved=True)

    # ==========================================
    # 4. Admin Management (assign_admin)
    # ==========================================

    def test_assign_admin_success(self, any_home, any_user):
        """Happy Path: Admin transfers role to another member."""
        new_admin_id = uuid.uuid4()
        any_home.add_member(new_admin_id)
        any_home.assign_admin(head_user_id=any_user.id, user_id=new_admin_id)
        
        assert any_home.get_admin() == new_admin_id
        assert any_home.is_admin(new_admin_id) is True

    def test_assign_admin_non_member_fails(self, any_home, any_user):
        """Sad Path: Cannot make a stranger an admin."""
        stranger_id = uuid.uuid4()
        with pytest.raises(ValueError, match="User is not a member"):
            any_home.assign_admin(head_user_id=any_user.id, user_id=stranger_id)

    # ==========================================
    # 5. Settings (update_expiration_range)
    # ==========================================

    def test_update_expiration_range_success(self, any_home, any_user):
        """Happy Path: Admin updates the warning range."""
        any_home.update_expiration_range(head_user_id=any_user.id, new_range=14)
        assert any_home.get_expiration_range() == 14

    def test_update_expiration_range_invalid_value_fails(self, any_home, any_user):
        """Sad Path: Range must be a positive integer."""
        with pytest.raises(ValueError, match="positive integer"):
            any_home.update_expiration_range(head_user_id=any_user.id, new_range=0)

    # ==========================================
    # 6. Membership Changes (leave & remove)
    # ==========================================

    def test_leave_home_success(self, any_home):
        """Happy Path: Member leaves voluntarily."""
        user_id = uuid.uuid4()
        any_home.add_member(user_id)
        any_home.leave_home(user_id)
        assert any_home.is_member(user_id) is False

    def test_admin_cannot_leave_fails(self, any_home, any_user):
        """Sad Path: Admin must transfer role before leaving."""
        with pytest.raises(PermissionError, match="Admin cannot leave"):
            any_home.leave_home(any_user.id)

    def test_remove_member_by_admin_success(self, any_home, any_user):
        """Happy Path: Admin removes a member."""
        member_id = uuid.uuid4()
        any_home.add_member(member_id)
        any_home.remove_member(head_user_id=any_user.id, user_id=member_id)
        assert any_home.is_member(member_id) is False

    # ==========================================
    # 7. Data Access (get_home_details)
    # ==========================================

    def test_get_home_details_admin_vs_member(self, any_home, any_user):
        """Security: Admin sees join code, member sees 'Restricted'."""
        member_id = uuid.uuid4()
        any_home.add_member(member_id)
        
        # Admin view
        assert any_home.get_home_details(any_user.id)["join code"] != "Restricted"
        # Member view
        assert any_home.get_home_details(member_id)["join code"] == "Restricted"