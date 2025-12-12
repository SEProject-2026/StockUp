import pytest
from uuid import UUID, uuid4
from domain.smart_home.home import Home

# קבועים לשימוש בטסטים
USER_ID = uuid4()
HOME_ID = uuid4()

@pytest.fixture
def home():
    return Home(user_id=USER_ID, id=HOME_ID, name="My Home", join_code="JOIN123")

def test_home_initialization(home):
    assert home.get_id() == HOME_ID
    assert home.get_name() == "My Home"
    assert home.get_join_code() == "JOIN123"
    assert home.is_member(USER_ID)
    assert home.is_admin(USER_ID)
    assert home.get_join_requests() == {}

def test_add_join_request(home):
    requester_id = uuid4()
    home.add_join_request(requester_id)
    assert home.has_request_from(requester_id) is True

def test_add_existing_join_request_raises(home):
    requester_id = uuid4()
    home.add_join_request(requester_id)
    
    with pytest.raises(ValueError, match="User has already requested to join"):
        home.add_join_request(requester_id)

def test_remove_join_request(home):
    requester_id = uuid4()
    home.add_join_request(requester_id)
    home.remove_join_request(requester_id)
    assert home.has_request_from(requester_id) is False

def test_add_member(home):
    new_member_id = uuid4()
    home.add_member(new_member_id)
    assert home.is_member(new_member_id) is True

def test_remove_member(home):
    member_id = uuid4()
    home.add_member(member_id)
    home.remove_member(member_id)
    assert home.is_member(member_id) is False

def test_assign_admin(home):
    new_admin_id = uuid4()
    home.add_member(new_admin_id)
    home.assign_admin(new_admin_id)
    assert home.is_admin(new_admin_id) is True