import pytest
import uuid
from unittest.mock import MagicMock

class TestManagementService:

    # ==========================================
    # 1. Home Creation & Initial Access
    # ==========================================

    @pytest.mark.asyncio
    async def test_create_home_success(self, mgmt_service, mock_home_repo, any_user):
        """Happy Path: Verify a new home is created and saved correctly with the creator as admin."""
        home = await mgmt_service.create_home(any_user.id, "Green House")
        
        assert home.get_name() == "Green House"
        assert home.is_admin(any_user.id)
        mock_home_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_view_home_code_success(self, mgmt_service, auth_setup, mock_security_check):
        """Happy Path: Admin can retrieve the home join code."""
        home, admin = auth_setup
        mock_security_check.return_value = home

        code = await mgmt_service.view_home_code(admin.id, home._id)
        
        assert len(code) == 8
        assert code == home.get_join_code()

    @pytest.mark.asyncio
    async def test_view_home_code_access_denied(self, mgmt_service, auth_setup, mock_security_check):
        """Security: Non-members are blocked from viewing the home join code."""
        home, _ = auth_setup
        mock_security_check.side_effect = ValueError("User is not a member")
        stranger_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="User is not a member"):
            await mgmt_service.view_home_code(stranger_id, home._id)

    # ==========================================
    # 2. Join Requests & Notifications
    # ==========================================

    @pytest.mark.asyncio
    async def test_join_home_success(self, mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications):
        """Happy Path: Join request is created and admin is notified."""
        home, admin = auth_setup
        mock_home_repo.get_by_join_code.return_value = home
        requester_id = uuid.uuid4()
        
        mock_user_repo.get_by_id.side_effect = [admin, MagicMock(name="Requester")]

        await mgmt_service.join_home(requester_id, home.get_join_code())

        assert home.has_request_from(requester_id)
        mock_notifications.assert_called_once()

    @pytest.mark.asyncio
    async def test_join_home_already_member_fails(self, mgmt_service, mock_home_repo, auth_setup):
        """Sad Path: Existing member cannot submit a join request."""
        home, admin = auth_setup
        mock_home_repo.get_by_join_code.return_value = home

        with pytest.raises(ValueError, match="already a member"):
            await mgmt_service.join_home(admin.id, home.get_join_code())

    @pytest.mark.asyncio
    async def test_join_home_invalid_code_fails(self, mgmt_service, mock_home_repo):
        """Sad Path: Error when using a non-existent join code."""
        mock_home_repo.get_by_join_code.return_value = None
        
        with pytest.raises(ValueError, match="Home not found"):
            await mgmt_service.join_home(uuid.uuid4(), "INVALID")

    @pytest.mark.asyncio
    async def test_join_home_notification_failure_is_graceful(self, mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications):
        """Coverage Fix: Verify join request completes even if notification service fails."""
        home, admin = auth_setup
        mock_home_repo.get_by_join_code.return_value = home
        mock_notifications.side_effect = Exception("FCM Service Down")

        await mgmt_service.join_home(uuid.uuid4(), home.get_join_code())
        mock_home_repo.update.assert_called()

    # ==========================================
    # 3. Answering Requests
    # ==========================================

    @pytest.mark.asyncio
    async def test_answer_join_request_approve(self, mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications, mock_security_check):
        """Happy Path: Admin approves request."""
        home, admin = auth_setup
        requester_id = uuid.uuid4()
        home.add_join_request(requester_id)
        mock_security_check.return_value = home
        mock_user_repo.get_by_id.return_value = MagicMock(push_token="token123")

        await mgmt_service.answer_join_request(home._id, admin.id, requester_id, approved=True)

        assert home.is_member(requester_id)
        assert not home.has_request_from(requester_id)
        mock_notifications.assert_called()

    @pytest.mark.asyncio
    async def test_answer_join_request_deny(self, mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications, mock_security_check):
        """Happy Path: Admin denies request."""
        home, admin = auth_setup
        requester_id = uuid.uuid4()
        home.add_join_request(requester_id)
        mock_security_check.return_value = home
        mock_user_repo.get_by_id.return_value = MagicMock(push_token="token123")

        await mgmt_service.answer_join_request(home._id, admin.id, requester_id, approved=False)

        assert not home.is_member(requester_id)
        assert not home.has_request_from(requester_id)
        mock_notifications.assert_called()

    @pytest.mark.asyncio
    async def test_answer_join_request_unauthorized_member_fails(self, mgmt_service, mock_home_repo, auth_setup):
        """Sad Path: A regular member cannot approve join requests."""
        home, admin = auth_setup
        regular_member_id = uuid.uuid4()
        requester_id = uuid.uuid4()
        
        home.add_member(regular_member_id) # Add a regular member
        home.add_join_request(requester_id)
        mock_home_repo.get_by_id.return_value = home

        # Expecting the Domain to raise a PermissionError (or ValueError depending on your Domain logic)
        with pytest.raises(Exception): 
            await mgmt_service.answer_join_request(home._id, regular_member_id, requester_id, approved=True)

    # ==========================================
    # 4. Member & Role Management
    # ==========================================

    @pytest.mark.asyncio
    async def test_switch_home_success(self, mgmt_service, auth_setup, mock_security_check):
        """Coverage Fix: Test switching context between homes."""
        home, admin = auth_setup
        mock_security_check.return_value = home
        
        result = await mgmt_service.switch_home(admin.id, home._id)
        assert result.get_id() == home.get_id()

    @pytest.mark.asyncio
    async def test_remove_member_success(self, mgmt_service, mock_home_repo, auth_setup, mock_security_check):
        """Happy Path: Admin can remove a member."""
        home, admin = auth_setup
        member_id = uuid.uuid4()
        home.add_member(member_id)
        mock_security_check.return_value = home

        await mgmt_service.remove_member(admin.id, home._id, member_id)

        assert not home.is_member(member_id)
        mock_home_repo.update.assert_called()

    @pytest.mark.asyncio
    async def test_remove_member_unauthorized(self, mgmt_service, auth_setup, mock_security_check):
        """Sad Path: Stranger attempts to remove a member."""
        home, _ = auth_setup
        member_id = uuid.uuid4()
        stranger_id = uuid.uuid4()
        home.add_member(member_id)
        mock_security_check.side_effect = ValueError("User is not a member")

        with pytest.raises(ValueError, match="User is not a member"):
            await mgmt_service.remove_member(stranger_id, home._id, member_id)

    @pytest.mark.asyncio
    async def test_switch_home_head_success(self, mgmt_service, mock_home_repo, auth_setup, mock_security_check):
        """Happy Path: Ownership transfer."""
        home, admin = auth_setup
        new_admin_id = uuid.uuid4()
        home.add_member(new_admin_id)
        mock_security_check.return_value = home

        await mgmt_service.switch_home_head(admin.id, home._id, new_admin_id)

        assert home.get_admin() == new_admin_id
        mock_home_repo.update.assert_called()

    @pytest.mark.asyncio
    async def test_leave_home_success(self, mgmt_service, mock_home_repo, auth_setup, mock_security_check):
        """Happy Path: Member leaves home."""
        home, admin = auth_setup
        member_id = uuid.uuid4()
        home.add_member(member_id)
        mock_security_check.return_value = home

        await mgmt_service.leave_home(member_id, home._id)

        assert not home.is_member(member_id)
        mock_home_repo.update.assert_called()

    @pytest.mark.asyncio
    async def test_leave_home_admin_fails(self, mgmt_service, mock_home_repo, auth_setup, mock_security_check):
        """Sad Path: Admin cannot leave without transfer."""
        home, admin = auth_setup
        mock_security_check.return_value = home

        with pytest.raises(PermissionError, match="Admin cannot leave"):
            await mgmt_service.leave_home(admin.id, home._id)

    # ==========================================
    # 5. Data Retrieval & Settings
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_home_details_success(self, mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_security_check):
        home, admin = auth_setup
        mock_security_check.return_value = home
        mock_user_repo.get_names_by_ids.return_value = {admin.id: "AdminName"}

        details = await mgmt_service.get_home_details(admin.id, home._id)

        assert details["member_names"][admin.id] == "AdminName"
        assert "join code" in details

    @pytest.mark.asyncio
    async def test_update_expiration_range_success(self, mgmt_service, mock_home_repo, auth_setup, mock_security_check):
        home, admin = auth_setup
        mock_security_check.return_value = home

        await mgmt_service.update_expiration_range(admin.id, home._id, 14)

        assert home.get_expiration_range() == 14
        mock_home_repo.update.assert_called()

    @pytest.mark.asyncio
    async def test_update_expiration_range_invalid(self, mgmt_service, mock_home_repo, auth_setup, mock_security_check):
        home, admin = auth_setup
        mock_security_check.return_value = home

        with pytest.raises(ValueError, match="positive integer"):
            await mgmt_service.update_expiration_range(admin.id, home._id, -5)

    # ==========================================
    # 6. Deletion
    # ==========================================

    @pytest.mark.asyncio
    async def test_delete_home_success(self, mgmt_service, mock_home_repo, auth_setup, mock_security_check):
        home, admin = auth_setup
        mock_security_check.return_value = home

        await mgmt_service.delete_home(admin.id, home._id)

        mock_home_repo.delete.assert_called_with(home._id)

    @pytest.mark.asyncio
    async def test_delete_home_unauthorized(self, mgmt_service, auth_setup, mock_security_check):
        home, _ = auth_setup
        stranger_id = uuid.uuid4()
        mock_security_check.side_effect = ValueError("User is not a member")

        with pytest.raises(ValueError, match="User is not a member"):
            await mgmt_service.delete_home(stranger_id, home._id)

    # ==========================================
    # 7. Missing Endpoint Coverage
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_all_homes_for_user_success(self, mgmt_service, mock_home_repo):
        """Happy Path: Retrieve all homes for a user."""
        user_id = uuid.uuid4()
        mock_home_repo.get_homes_by_user_id.return_value = [MagicMock(), MagicMock()]
        
        homes = await mgmt_service.get_all_homes_for_user(user_id)
        assert len(homes) == 2
        mock_home_repo.get_homes_by_user_id.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_all_homes_for_user_missing_id(self, mgmt_service):
        """Sad Path: Fails when user ID is None."""
        with pytest.raises(ValueError, match="User ID is required"):
            await mgmt_service.get_all_homes_for_user(None)

    @pytest.mark.asyncio
    async def test_get_join_requests_success(self, mgmt_service, mock_home_repo, mock_user_repo, auth_setup):
        """Happy Path: Head of house retrieves join requests names."""
        home, admin = auth_setup
        requester_id = uuid.uuid4()
        home.add_join_request(requester_id) # Add a request
        mock_home_repo.get_by_id.return_value = home
        mock_user_repo.get_names_by_ids.return_value = {requester_id: "New Guy"}

        requests = await mgmt_service.get_join_requests(admin.id, home._id)
        
        assert requests[requester_id] == "New Guy"
        mock_user_repo.get_names_by_ids.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_access_missing_ids_fails(self, mgmt_service):
        """Sad Path: Service rejects actions if user_id or home_id is missing."""
        with pytest.raises(ValueError, match="User ID and Home ID are required"):
            # Using view_home_code as a proxy to trigger _check_access
            await mgmt_service.view_home_code(None, uuid.uuid4())
            
        with pytest.raises(ValueError, match="User ID and Home ID are required"):
            await mgmt_service.view_home_code(uuid.uuid4(), None)

    @pytest.mark.asyncio
    async def test_check_access_home_not_found_fails(self, mgmt_service, mock_home_repo):
        """Sad Path: Service handles non-existent home gracefully."""
        mock_home_repo.get_by_id.return_value = None # Simulate DB not finding the home
        
        with pytest.raises(ValueError, match="Home retrieval failed"):
            await mgmt_service.view_home_code(uuid.uuid4(), uuid.uuid4())
    
