import pytest
from uuid import UUID, uuid4
from src.domain.home.home import Home


USER_ID = uuid4()

@pytest.fixture
def home():
    return Home(user_id=USER_ID, name="My Home")

def test_home_initialization(home):
    assert home.get_name() == "My Home"
    assert home.get_admin() == USER_ID
    assert home.is_member(USER_ID) is True

def test_add_join_request(home):
    requester_id = uuid4()
    home.add_join_request(requester_id)
    assert home.has_request_from(requester_id) is True

def test_add_existing_join_request_raises(home):
    requester_id = uuid4()
    home.add_join_request(requester_id)
    
    with pytest.raises(ValueError, match="User has already requested to join"):
        home.add_join_request(requester_id)

def test_add_member(home):
    new_member_id = uuid4()
    home.add_member(new_member_id)
    assert home.is_member(new_member_id) is True

def test_remove_member(home):
    member_id = uuid4()
    home.add_member(member_id)
    home.remove_member(USER_ID, member_id)
    assert home.is_member(member_id) is False

def test_assign_admin(home):
    new_admin_id = uuid4()
    home.add_member(new_admin_id)
    home.assign_admin(USER_ID, new_admin_id)
    assert home.is_admin(new_admin_id) is True

def test_assign_admin_unauthorized(home):
    intruder_id = uuid4()
    new_admin_id = uuid4()
    home.add_member(new_admin_id)
    
    with pytest.raises(PermissionError, match="Only current admin can transfer admin rights."):
        home.assign_admin(intruder_id, new_admin_id)

def test_assign_admin_to_non_member(home):
    stranger_id = uuid4()
    
    with pytest.raises(ValueError, match="User is not a member of the home."):
        home.assign_admin(USER_ID, stranger_id)

def test_answer_join_request_unauthorized(home):
    requester_id = uuid4()
    intruder_id = uuid4()
    home.add_join_request(requester_id)
    
    with pytest.raises(PermissionError, match="Only admin can approve or deny join requests."):
        home.answer_join_request(intruder_id, requester_id, True)

def test_answer_non_existent_join_request(home):
    ghost_user_id = uuid4()
    
    with pytest.raises(ValueError, match="No such join request found."):
        home.answer_join_request(USER_ID, ghost_user_id, True)

def test_remove_member_unauthorized(home):
    member_id = uuid4()
    intruder_id = uuid4()
    home.add_member(member_id)
    home.add_member(intruder_id)
    
    with pytest.raises(PermissionError, match="Only admin can remove members from the home."):
        home.remove_member(intruder_id, member_id)

def test_admin_cannot_leave_home(home):
    with pytest.raises(PermissionError, match="Admin cannot leave the home. Transfer admin rights before leaving."):
        home.leave_home(USER_ID)

def test_answer_join_request_deny(home):
    requester_id = uuid4()
    home.add_join_request(requester_id)
    
    home.answer_join_request(USER_ID, requester_id, False)
    
    assert home.is_member(requester_id) is False
    assert home.has_request_from(requester_id) is False

def test_add_existing_member_raises(home):
    member_id = uuid4()
    home.add_member(member_id)
    
    with pytest.raises(ValueError, match="User is already a member of the home."):
        home.add_member(member_id)

def test_get_home_details_admin_vs_member(home):
    member_id = uuid4()
    home.add_member(member_id)
    
    admin_details = home.get_home_details(USER_ID)
    member_details = home.get_home_details(member_id)
    
    assert admin_details["join code"] == home.get_join_code()
    assert member_details["join code"] == "Restricted"

def test_get_home_details_unauthorized(home):
    stranger_id = uuid4()
    
    with pytest.raises(ValueError, match="User is not a member of the home."):
        home.get_home_details(stranger_id)