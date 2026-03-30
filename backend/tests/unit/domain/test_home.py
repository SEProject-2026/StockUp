import uuid
import pytest
from src.domain.home.home import Home

# --- Initialization & Basic Properties ---

def test_home_initialization_success(any_home, any_user):
    """Verify home is created with correct attributes via fixture."""
    # any_home is created with any_user as admin in conftest
    assert any_home.get_name() == "Test Home"
    assert any_home.is_admin(any_user.id) is True
    assert any_user.id in any_home.get_members()
    assert len(any_home.get_join_code()) == 8
    assert any_home.get_expiration_range() == 7

def test_home_creation_empty_name_fails(any_user):
    """Verify validation prevents empty home names by calling Home class directly."""
    with pytest.raises(ValueError, match="Home name cannot be empty"):
        Home(user_id=any_user.id, name="")
    with pytest.raises(ValueError, match="Home name cannot be empty"):
        Home(user_id=any_user.id, name="   ")

# --- Membership & Join Requests ---

def test_add_join_request_success(any_home):
    user_id = uuid.uuid4()
    any_home.add_join_request(user_id)
    assert any_home.has_request_from(user_id) is True

def test_add_join_request_duplicate_fails(any_home):
    user_id = uuid.uuid4()
    any_home.add_join_request(user_id)
    
    with pytest.raises(ValueError, match="already requested to join"):
        any_home.add_join_request(user_id)

def test_add_join_request_existing_member_fails(any_home, any_user):
    # any_user is already the admin/member
    with pytest.raises(ValueError, match="already a member"):
        any_home.add_join_request(any_user.id)

def test_answer_request_approve_success(any_home, any_user):
    new_user_id = uuid.uuid4()
    
    any_home.add_join_request(new_user_id)
    any_home.answer_join_request(head_user_id=any_user.id, user_id=new_user_id, approved=True)
    
    assert any_home.is_member(new_user_id) is True
    assert any_home.has_request_from(new_user_id) is False

def test_answer_request_deny_success(any_home, any_user):
    new_user_id = uuid.uuid4()
    
    any_home.add_join_request(new_user_id)
    any_home.answer_join_request(head_user_id=any_user.id, user_id=new_user_id, approved=False)
    
    assert any_home.is_member(new_user_id) is False
    assert any_home.has_request_from(new_user_id) is False

def test_answer_request_unauthorized_fails(any_home):
    stranger_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    
    any_home.add_join_request(candidate_id)
    with pytest.raises(PermissionError, match="Only admin can approve"):
        any_home.answer_join_request(head_user_id=stranger_id, user_id=candidate_id, approved=True)

# --- Admin Actions ---

def test_assign_admin_success(any_home, any_user):
    new_admin_id = uuid.uuid4()
    
    any_home.add_member(new_admin_id)
    any_home.assign_admin(head_user_id=any_user.id, user_id=new_admin_id)
    
    assert any_home.get_admin() == new_admin_id
    assert any_home.is_admin(new_admin_id) is True

def test_assign_admin_non_member_fails(any_home, any_user):
    stranger_id = uuid.uuid4()
    
    with pytest.raises(ValueError, match="User is not a member"):
        any_home.assign_admin(head_user_id=any_user.id, user_id=stranger_id)

def test_update_expiration_range_success(any_home, any_user):
    any_home.update_expiration_range(head_user_id=any_user.id, new_range=14)
    assert any_home.get_expiration_range() == 14

def test_update_expiration_range_invalid_value_fails(any_home, any_user):
    with pytest.raises(ValueError, match="positive integer"):
        any_home.update_expiration_range(head_user_id=any_user.id, new_range=0)

# --- Leaving & Removal ---

def test_leave_home_success(any_home):
    user_id = uuid.uuid4()
    any_home.add_member(user_id)
    
    any_home.leave_home(user_id)
    assert any_home.is_member(user_id) is False

def test_admin_cannot_leave_fails(any_home, any_user):
    with pytest.raises(PermissionError, match="Admin cannot leave"):
        any_home.leave_home(any_user.id)

def test_remove_member_by_admin_success(any_home, any_user):
    member_id = uuid.uuid4()
    any_home.add_member(member_id)
    
    any_home.remove_member(head_user_id=any_user.id, user_id=member_id)
    assert any_home.is_member(member_id) is False

# --- Data Visibility ---

def test_get_home_details_admin_vs_member(any_home, any_user):
    member_id = uuid.uuid4()
    any_home.add_member(member_id)
    
    # Admin sees join code
    admin_details = any_home.get_home_details(any_user.id)
    assert admin_details["join code"] != "Restricted"
    
    # Member sees Restricted
    member_details = any_home.get_home_details(member_id)
    assert member_details["join code"] == "Restricted"