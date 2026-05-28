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
        assert any_home.get_id().hex[:8].upper() == any_home.get_join_code()
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

    def test_answer_request_non_existent_fails(self, any_home, any_user):
        """Sad Path: Admin tries to approve a non-existent request."""
        non_existent_id = uuid.uuid4()
        with pytest.raises(ValueError, match="No such join request found"):
            any_home.answer_join_request(head_user_id=any_user.id, user_id=non_existent_id, approved=True)

    def test_answer_request_already_member_fails(self, any_home, any_user):
        """Sad Path: Admin tries to approve a request from an existing member."""
        member_id = uuid.uuid4()
        any_home.add_join_request(member_id)
        any_home.add_member(member_id)
        with pytest.raises(ValueError, match="User is already a member"):
            any_home.answer_join_request(head_user_id=any_user.id, user_id=member_id, approved=True)

    def test_review_join_request_list_as_admin_success(self, any_home, any_user):
        """Security: Admin can see all pending join requests."""
        candidate_id = uuid.uuid4()
        any_home.add_join_request(candidate_id)
        
        requests = any_home.get_join_requests_names(any_user.id)
        assert candidate_id in requests
    
    def test_review_join_request_list_as_member_fails(self, any_home, any_user):
        """Security: Members cannot see pending join requests."""
        member_id = uuid.uuid4()
        any_home.add_member(member_id)
        
        with pytest.raises(PermissionError, match="Only admin can view join requests"):
            any_home.get_join_requests_names(member_id)

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

    def test_assign_admin_unauthorized_fails(self, any_home):
        """Sad Path: Non-admin tries to assign a new admin."""
        stranger_id = uuid.uuid4()
        new_admin_id = uuid.uuid4()
        any_home.add_member(new_admin_id)
        
        with pytest.raises(PermissionError, match="Only current admin can transfer admin rights"):
            any_home.assign_admin(head_user_id=stranger_id, user_id=new_admin_id)

    # ==========================================
    # 5. Settings (update_expiration_range)
    # ==========================================

    def test_update_expiration_range_success(self, any_home, any_user):
        """Happy Path: Admin updates the warning range."""
        any_home.update_expiration_range(head_user_id=any_user.id, new_range=14)
        assert any_home.get_expiration_range() == 14
    
    def test_update_expiration_range_unauthorized_fails(self, any_home):
        """Sad Path: Non-admin tries to update expiration range."""
        stranger_id = uuid.uuid4()
        with pytest.raises(PermissionError, match="Only admin can update expiration range"):
            any_home.update_expiration_range(head_user_id=stranger_id, new_range=14)

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
    
    def test_leave_non_member_fails(self, any_home):
        """Sad Path: Non-members cannot leave."""
        stranger_id = uuid.uuid4()
        with pytest.raises(ValueError, match="User is not a member"):
            any_home.leave_home(stranger_id)

    def test_remove_member_by_admin_success(self, any_home, any_user):
        """Happy Path: Admin removes a member."""
        member_id = uuid.uuid4()
        any_home.add_member(member_id)
        any_home.remove_member(head_user_id=any_user.id, user_id=member_id)
        assert any_home.is_member(member_id) is False

    def test_remove_member_by_non_admin_fails(self, any_home):
        """Sad Path: Only admin can remove members."""
        stranger_id = uuid.uuid4()
        member_id = uuid.uuid4()
        any_home.add_member(member_id)
        
        with pytest.raises(PermissionError, match="Only admin can remove members"):
            any_home.remove_member(head_user_id=stranger_id, user_id=member_id)

    def test_remove_non_existent_member_fails(self, any_home, any_user):
        """Sad Path: Admin tries to remove a user who isn't a member."""
        non_member_id = uuid.uuid4()
        with pytest.raises(ValueError, match="User is not a member"):
            any_home.remove_member(head_user_id=any_user.id, user_id=non_member_id)

    # ==========================================
    # 7. Data Access (get_home_details)
    # ==========================================

    def test_view_home_code_by_admin_success(self, any_home):
        """Happy Path: Admin can view the join code."""
        admin_id = any_home.get_admin()
        assert any_home.view_home_code(admin_id) == any_home.get_join_code()

    def test_view_home_code_by_member_fails(self, any_home):
        """Sad Path: Members cannot view the join code."""
        member_id = uuid.uuid4()
        any_home.add_member(member_id)
        
        with pytest.raises(PermissionError, match="Only admin can view"):
            any_home.view_home_code(member_id)

    def test_get_home_details_admin_vs_member_success(self, any_home, any_user):
        """Security: Admin sees join code, member sees 'Restricted'."""
        member_id = uuid.uuid4()
        any_home.add_member(member_id)
        
        # Admin view
        assert any_home.get_home_details(any_user.id)["join code"] != "Restricted"
        # Member view
        assert any_home.get_home_details(member_id)["join code"] == "Restricted"

    def test_get_home_details_non_member_fails(self, any_home):
        """Sad Path: Non-members cannot access home details."""
        stranger_id = uuid.uuid4()
        with pytest.raises(ValueError, match="User is not a member"):
            any_home.get_home_details(stranger_id)

    #============================================
    # 8. Additional Security Tests
    #============================================

    def test_can_switch_home_member_success(self, any_home, any_user):
        """Happy Path: Member can switch to another home."""
        new_home = Home(user_id=any_user.id, name="New Home")
        assert any_home.can_switch_home(any_user.id) is None
        assert new_home.can_switch_home(any_user.id) is None

    def test_can_switch_home_non_member_fails(self, any_home):
        """Sad Path: Non-members cannot switch homes."""
        stranger_id = uuid.uuid4()
        with pytest.raises(ValueError, match="User is not a member"):
            any_home.can_switch_home(stranger_id)

    def test_can_delete_home_admin_success(self, any_home):
        """Happy Path: Admin can delete the home."""
        assert any_home.can_delete_home(any_home.get_admin()) is None

    def test_can_delete_home_non_admin_fails(self, any_home):
        """Sad Path: Only admin can delete the home."""
        stranger_id = uuid.uuid4()
        with pytest.raises(PermissionError, match="Only admin can delete the home"):
            any_home.can_delete_home(stranger_id)