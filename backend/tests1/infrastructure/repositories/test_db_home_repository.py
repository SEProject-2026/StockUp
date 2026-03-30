import pytest
from uuid import uuid4
from tests1.container import testing_container
from src.domain.home.home import Home
from src.domain.user.user import User

# --- Helpers ---

async def create_test_user(email="admin@test.com", name="Admin"):
    """
    Helper to create a user in the DB, required for creating a Home (Foreign Key).
    """
    fake_uid = "550e8400-e29b-41d4-a716-446655440000"
    user = User(id=fake_uid, email=email, name=name)
    # We use the user repo directly to save the user
    await testing_container.user_repo.save(user)
    return user

# --- Tests ---

@pytest.mark.asyncio
async def test_save_and_get_home_by_id():
    """
    Verifies that a home can be saved and retrieved with all scalar fields.
    """
    repo = testing_container.home_repo
    
    # 1. Create a user to be the admin
    admin = await create_test_user()
    
    # 2. Create Home domain object
    home = Home(user_id=admin.id, name="My Sweet Home")
    
    # 3. Save
    await repo.save(home)
    
    # 4. Retrieve
    fetched_home = await repo.get_by_id(home.get_id())
    
    # 5. Assertions
    assert fetched_home is not None
    assert fetched_home.get_id() == home.get_id()
    assert fetched_home.get_name() == "My Sweet Home"
    assert fetched_home.get_admin() == admin.id
    assert fetched_home.get_join_code() is not None
    # Verify the admin is automatically added as a member
    assert fetched_home.is_member(admin.id) is True

@pytest.mark.asyncio
async def test_save_home_with_members():
    """
    Verifies that the Many-to-Many relationship with Users (members) is persisted.
    """
    repo = testing_container.home_repo
    
    # 1. Create Users
    admin = await create_test_user(email="admin@a.com", name="Admin")
    member1 = await create_test_user(email="mem1@a.com", name="Member 1")
    member2 = await create_test_user(email="mem2@a.com", name="Member 2")
    
    # 2. Create Home
    home = Home(user_id=admin.id, name="Shared House")
    
    # 3. Add members in Domain
    home.add_member(member1.id)
    home.add_member(member2.id)
    
    # 4. Save
    await repo.save(home)
    
    # 5. Fetch and Verify
    fetched_home = await repo.get_by_id(home.get_id())
    
    assert fetched_home.is_member(member1.id) is True
    assert fetched_home.is_member(member2.id) is True
    assert len(fetched_home.get_members()) == 3 # Admin + 2 members

@pytest.mark.asyncio
async def test_save_home_with_join_requests():
    """
    Verifies that Join Requests (Many-to-Many) are persisted.
    """
    repo = testing_container.home_repo
    admin = await create_test_user()
    requester = await create_test_user(email="req@test.com", name="Requester")
    
    home = Home(user_id=admin.id, name="Private Club")
    home.add_join_request(requester.id)
    
    await repo.save(home)
    
    fetched_home = await repo.get_by_id(home.get_id())
    assert fetched_home.has_request_from(requester.id) is True

@pytest.mark.asyncio
async def test_get_by_join_code():
    """
    Verifies retrieval by Join Code.
    """
    repo = testing_container.home_repo
    admin = await create_test_user()
    home = Home(user_id=admin.id, name="Code Home")
    
    await repo.save(home)
    code = home.get_join_code()
    
    fetched_home = await repo.get_by_join_code(code)
    
    assert fetched_home is not None
    assert fetched_home.get_id() == home.get_id()

@pytest.mark.asyncio
async def test_get_by_name():
    """
    Verifies retrieval by Home Name.
    """
    repo = testing_container.home_repo
    admin = await create_test_user()
    home = Home(user_id=admin.id, name="Unique Name Mansion")
    
    await repo.save(home)
    
    fetched_home = await repo.get_by_name("Unique Name Mansion")
    assert fetched_home is not None
    assert fetched_home.get_id() == home.get_id()

@pytest.mark.asyncio
async def test_update_home():
    """
    Verifies updating scalar fields (renaming).
    """
    repo = testing_container.home_repo
    admin = await create_test_user()
    home = Home(user_id=admin.id, name="Old Name")
    await repo.save(home)
    
    # Update in memory
    home._name = "New Name" # Accessing protected member for test setup, or use a domain method if available
    
    # Save update
    await repo.update(home)
    
    fetched_home = await repo.get_by_id(home.get_id())
    assert fetched_home.get_name() == "New Name"

@pytest.mark.asyncio
async def test_delete_home():
    """
    Verifies deletion of a home.
    """
    repo = testing_container.home_repo
    admin = await create_test_user()
    home = Home(user_id=admin.id, name="To Be Deleted")
    await repo.save(home)
    
    # Verify it exists
    assert await repo.get_by_id(home.get_id()) is not None
    
    # Delete
    await repo.delete(home.get_id())
    
    # Verify it is gone
    assert await repo.get_by_id(home.get_id()) is None

@pytest.mark.asyncio
async def test_get_homes_by_user_id():
    """
    Verifies fetching all homes a specific user belongs to.
    """
    repo = testing_container.home_repo
    
    # Create Users
    user_a = await create_test_user(email="userA@test.com", name="User A")
    user_b = await create_test_user(email="userB@test.com", name="User B")
    
    # 1. Home where User A is Admin
    home1 = Home(user_id=user_a.id, name="A's Home")
    await repo.save(home1)
    
    # 2. Home where User A is just a Member (B is Admin)
    home2 = Home(user_id=user_b.id, name="B's Home")
    home2.add_member(user_a.id)
    await repo.save(home2)
    
    # 3. Home where User A is NOT involved
    home3 = Home(user_id=user_b.id, name="B's Private")
    await repo.save(home3)
    
    # Act
    homes_for_a = await repo.get_homes_by_user_id(user_a.id)
    
    # Assert
    assert len(homes_for_a) == 2
    home_ids = [h.get_id() for h in homes_for_a]
    assert home1.get_id() in home_ids
    assert home2.get_id() in home_ids
    assert home3.get_id() not in home_ids