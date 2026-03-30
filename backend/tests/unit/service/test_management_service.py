import pytest
import uuid
from unittest.mock import MagicMock

# --- 1. Home Creation & Initial Access ---

@pytest.mark.asyncio
async def test_create_home_success(mgmt_service, mock_home_repo, any_user):
    """Verify a new home is created and saved correctly with the creator as admin."""
    home = await mgmt_service.create_home(any_user.id, "Green House")
    
    assert home.get_name() == "Green House"
    assert home.is_admin(any_user.id)
    mock_home_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_view_home_code_success(mgmt_service, mock_home_repo, auth_setup):
    """Verify admin can retrieve the home join code."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    code = await mgmt_service.view_home_code(admin.id, home._id)
    
    assert len(code) == 8
    assert code == home.get_join_code()

@pytest.mark.asyncio
async def test_view_home_code_access_denied(mgmt_service, mock_home_repo, auth_setup):
    """Verify non-members are blocked from viewing the home join code."""
    home, _ = auth_setup
    mock_home_repo.get_by_id.return_value = home
    stranger_id = uuid.uuid4()
    
    with pytest.raises(ValueError, match="User is not a member"):
        await mgmt_service.view_home_code(stranger_id, home._id)

# --- 2. Join Requests & Notifications ---

@pytest.mark.asyncio
async def test_join_home_success(mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications):
    """Verify join request is created and admin is notified."""
    home, admin = auth_setup
    mock_home_repo.get_by_join_code.return_value = home
    requester_id = uuid.uuid4()
    
    # Mock return values for admin (to get push token) and requester
    mock_user_repo.get_by_id.side_effect = [admin, MagicMock(name="Requester")]

    await mgmt_service.join_home(requester_id, home.get_join_code())

    assert home.has_request_from(requester_id)
    mock_notifications.assert_called_once()

@pytest.mark.asyncio
async def test_join_home_already_member_fails(mgmt_service, mock_home_repo, auth_setup):
    """Verify that an existing member cannot submit a join request."""
    home, admin = auth_setup
    mock_home_repo.get_by_join_code.return_value = home

    with pytest.raises(ValueError, match="already a member"):
        await mgmt_service.join_home(admin.id, home.get_join_code())

@pytest.mark.asyncio
async def test_join_home_invalid_code_fails(mgmt_service, mock_home_repo):
    """Verify error when using a non-existent join code."""
    mock_home_repo.get_by_join_code.return_value = None
    
    with pytest.raises(ValueError, match="Home not found"):
        await mgmt_service.join_home(uuid.uuid4(), "INVALID")

@pytest.mark.asyncio
async def test_join_home_notification_failure_is_graceful(mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications):
    """Verify join request completes even if the notification service fails."""
    home, admin = auth_setup
    mock_home_repo.get_by_join_code.return_value = home
    mock_notifications.side_effect = Exception("FCM Service Down")

    await mgmt_service.join_home(uuid.uuid4(), home.get_join_code())
    
    mock_home_repo.update.assert_called()

# --- 3. Answering Requests ---

@pytest.mark.asyncio
async def test_answer_join_request_approve(mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications):
    """Verify admin can approve a request, adding the user to members."""
    home, admin = auth_setup
    requester_id = uuid.uuid4()
    home.add_join_request(requester_id)
    mock_home_repo.get_by_id.return_value = home
    mock_user_repo.get_by_id.return_value = MagicMock(push_token="token123")

    await mgmt_service.answer_join_request(home._id, admin.id, requester_id, approved=True)

    assert home.is_member(requester_id)
    assert not home.has_request_from(requester_id)
    mock_notifications.assert_called()

@pytest.mark.asyncio
async def test_answer_join_request_deny(mgmt_service, mock_home_repo, mock_user_repo, auth_setup, mock_notifications):
    """Verify admin can deny a request, removing it without adding a member."""
    home, admin = auth_setup
    requester_id = uuid.uuid4()
    home.add_join_request(requester_id)
    mock_home_repo.get_by_id.return_value = home
    mock_user_repo.get_by_id.return_value = MagicMock(push_token="token123")

    await mgmt_service.answer_join_request(home._id, admin.id, requester_id, approved=False)

    assert not home.is_member(requester_id)
    assert not home.has_request_from(requester_id)
    mock_notifications.assert_called()

# --- 4. Member & Role Management ---

@pytest.mark.asyncio
async def test_remove_member_success(mgmt_service, mock_home_repo, auth_setup):
    """Verify admin can remove a member."""
    home, admin = auth_setup
    member_id = uuid.uuid4()
    home.add_member(member_id)
    mock_home_repo.get_by_id.return_value = home

    await mgmt_service.remove_member(admin.id, home._id, member_id)

    assert not home.is_member(member_id)
    mock_home_repo.update.assert_called()

@pytest.mark.asyncio
async def test_remove_member_unauthorized(mgmt_service, mock_home_repo, auth_setup):
    home, _ = auth_setup
    member_id = uuid.uuid4()
    stranger_id = uuid.uuid4()
    home.add_member(member_id)
    mock_home_repo.get_by_id.return_value = home

    # The service fails here because the stranger isn't even a member
    with pytest.raises(ValueError, match="User is not a member of the home"):
        await mgmt_service.remove_member(stranger_id, home._id, member_id)

@pytest.mark.asyncio
async def test_switch_home_head_success(mgmt_service, mock_home_repo, auth_setup):
    """Verify ownership transfer to another member."""
    home, admin = auth_setup
    new_admin_id = uuid.uuid4()
    home.add_member(new_admin_id)
    mock_home_repo.get_by_id.return_value = home

    await mgmt_service.switch_home_head(admin.id, home._id, new_admin_id)

    assert home.get_admin() == new_admin_id
    mock_home_repo.update.assert_called()

@pytest.mark.asyncio
async def test_leave_home_success(mgmt_service, mock_home_repo, auth_setup):
    """Verify a regular member can leave the home."""
    home, admin = auth_setup
    member_id = uuid.uuid4()
    home.add_member(member_id)
    mock_home_repo.get_by_id.return_value = home

    await mgmt_service.leave_home(member_id, home._id)

    assert not home.is_member(member_id)
    mock_home_repo.update.assert_called()

@pytest.mark.asyncio
async def test_leave_home_admin_fails(mgmt_service, mock_home_repo, auth_setup):
    """Verify admin cannot leave without transferring ownership."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    with pytest.raises(PermissionError, match="Admin cannot leave"):
        await mgmt_service.leave_home(admin.id, home._id)

# --- 5. Data Retrieval & Settings ---

@pytest.mark.asyncio
async def test_get_home_details_success(mgmt_service, mock_home_repo, mock_user_repo, auth_setup):
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_user_repo.get_names_by_ids.return_value = {admin.id: "AdminName"}

    details = await mgmt_service.get_home_details(admin.id, home._id)

    assert details["member_names"][admin.id] == "AdminName"
    # Matches the actual dictionary key returned by the service
    assert "join code" in details

@pytest.mark.asyncio
async def test_update_expiration_range_success(mgmt_service, mock_home_repo, auth_setup):
    """Verify updating the home's expiration warning range."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    await mgmt_service.update_expiration_range(admin.id, home._id, 14)

    assert home.get_expiration_range() == 14
    mock_home_repo.update.assert_called()

@pytest.mark.asyncio
async def test_update_expiration_range_invalid(mgmt_service, mock_home_repo, auth_setup):
    """Verify that invalid range values are rejected."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    with pytest.raises(ValueError, match="positive integer"):
        await mgmt_service.update_expiration_range(admin.id, home._id, -5)

# --- 6. Deletion ---

@pytest.mark.asyncio
async def test_delete_home_success(mgmt_service, mock_home_repo, auth_setup):
    """Verify permanent home deletion by the admin."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    await mgmt_service.delete_home(admin.id, home._id)

    mock_home_repo.delete.assert_called_with(home._id)

@pytest.mark.asyncio
async def test_delete_home_unauthorized(mgmt_service, mock_home_repo, auth_setup):
    """Verify non-members are blocked from deleting a home."""
    home, _ = auth_setup
    stranger_id = uuid.uuid4()
    mock_home_repo.get_by_id.return_value = home

    with pytest.raises(ValueError, match="User is not a member of the home"):
        await mgmt_service.delete_home(stranger_id, home._id)