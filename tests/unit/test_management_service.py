import pytest
from uuid import UUID, uuid4
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.services.management_service import ManagementService
from src.infrastructure.repositories.in_memory_home_repository import InMemoryHomeRepository

@pytest.fixture
def user_repo():
    return InMemoryUserRepository()
@pytest.fixture
def home_repo():
    return InMemoryHomeRepository()

@pytest.fixture
def management_service(home_repo, user_repo):
    return ManagementService(home_repository=home_repo, user_repository=user_repo)

# ==========================================
# 1. Success Paths
# ==========================================

@pytest.mark.asyncio
async def test_create_home_success(management_service, home_repo):
    user_id = uuid4()
    home_name = "My Castle"
    home = await management_service.create_home(user_id, home_name)
    assert home is not None
    assert home.get_name() == home_name
    assert home.get_id() is not None
    saved_home = await home_repo.get_by_id(home.get_id())
    assert saved_home is not None
    assert saved_home.is_member(user_id) is True 

@pytest.mark.asyncio
async def test_join_home_flow(management_service, home_repo):
    admin_id = uuid4()
    admin_home = await management_service.create_home(admin_id, "Clubhouse")
    home_id = admin_home.get_id()
    home_code = await management_service.view_home_code(admin_id, home_id)
    user_b = uuid4()
    await management_service.join_home(user_b, home_code)
    home_after_request = await home_repo.get_by_id(home_id)
    assert home_after_request.has_request_from(user_b) is True
    await management_service.answer_join_request(home_id, admin_id, user_b, True)
    updated_home = await home_repo.get_by_id(home_id)
    assert updated_home.is_member(user_b) is True
    assert updated_home.has_request_from(user_b) is False

@pytest.mark.asyncio
async def test_remove_member_success(management_service, home_repo):
    admin_id = uuid4()
    member_id = uuid4()
    home = await management_service.create_home(admin_id, "Test Home")
    home_id = home.get_id()
    home.add_member(member_id)
    await home_repo.update(home)
    updated_home = await management_service.remove_member(admin_id, home_id, member_id)
    assert updated_home.is_member(member_id) is False
    saved_home = await home_repo.get_by_id(home_id)
    assert saved_home.is_member(member_id) is False

@pytest.mark.asyncio
async def test_leave_home_success(management_service, home_repo):
    admin_id = uuid4()
    member_id = uuid4()
    home = await management_service.create_home(admin_id, "Leavers Home")
    home_id = home.get_id()
    home.add_member(member_id)
    await home_repo.update(home)
    await management_service.leave_home(member_id, home_id)
    saved_home = await home_repo.get_by_id(home_id)
    assert saved_home.is_member(member_id) is False

# ==========================================
# 2. Failure Paths
# ==========================================

@pytest.mark.asyncio
async def test_admin_cannot_leave_home(management_service):
    # Arrange
    admin_id = uuid4()
    home = await management_service.create_home(admin_id, "Admin Home")
    home_id = home.get_id()

    # Act & Assert
    with pytest.raises(PermissionError, match="Admin cannot leave the home"):
        await management_service.leave_home(admin_id, home_id)

@pytest.mark.asyncio
async def test_non_member_cannot_get_details(management_service):
    # Arrange
    admin_id = uuid4()
    stranger_id = uuid4()
    home = await management_service.create_home(admin_id, "Private Home")
    home_id = home.get_id()

    # Act & Assert
    with pytest.raises(ValueError, match="User is not a member of the home"):
        await management_service.get_home_details(stranger_id, home_id)

@pytest.mark.asyncio
async def test_join_home_with_invalid_code(management_service):
    # Arrange
    user_id = uuid4()
    invalid_code = "INVALID1"

    # Act & Assert
    with pytest.raises(ValueError, match="Home not found"):
        await management_service.join_home(user_id, invalid_code)

@pytest.mark.asyncio
async def test_non_admin_cannot_view_code(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    member_id = uuid4()
    home = await management_service.create_home(admin_id, "Secret Code Home")
    home_id = home.get_id()
    
    # Add member bypassing the service for test setup
    home.add_member(member_id)
    await home_repo.update(home)

    # Act & Assert
    with pytest.raises(PermissionError, match="Only admin can view the home join code"):
        await management_service.view_home_code(member_id, home_id)

@pytest.mark.asyncio
async def test_non_admin_cannot_remove_member(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    member_1_id = uuid4()
    member_2_id = uuid4()
    
    home = await management_service.create_home(admin_id, "Removal Home")
    home_id = home.get_id()
    home.add_member(member_1_id)
    home.add_member(member_2_id)
    await home_repo.update(home)

    # Act & Assert (Member 1 tries to remove Member 2)
    with pytest.raises(PermissionError, match="Only admin can remove members from the home"):
        await management_service.remove_member(member_1_id, home_id, member_2_id)

@pytest.mark.asyncio
async def test_user_cannot_request_join_twice(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    home = await management_service.create_home(admin_id, "Double Request Home")
    home_id = home.get_id()
    home_code = await management_service.view_home_code(admin_id, home_id)
    
    user_id = uuid4()
    
    # First request should succeed
    await management_service.join_home(user_id, home_code)
    
    # Act & Assert (Second request should fail)
    with pytest.raises(ValueError, match="User has already requested to join"):
        await management_service.join_home(user_id, home_code)


# ==========================================
# 3. Missing UAT Coverage (Switch, Delete, Transfer Admin)
# ==========================================

@pytest.mark.asyncio
async def test_switch_home_success(management_service, home_repo):
    # Arrange
    user_id = uuid4()
    home = await management_service.create_home(user_id, "Vacation Home")
    home_id = home.get_id()

    # Act: User switches context to this home
    switched_home = await management_service.switch_home(user_id, home_id)

    # Assert
    assert switched_home is not None
    assert switched_home.get_id() == home_id

@pytest.mark.asyncio
async def test_switch_home_unauthorized(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    stranger_id = uuid4()
    home = await management_service.create_home(admin_id, "Private Home")
    
    # Act & Assert: Stranger tries to switch to a home they aren't in
    with pytest.raises(ValueError, match="User is not a member of the home"):
        await management_service.switch_home(stranger_id, home.get_id())

@pytest.mark.asyncio
async def test_delete_home_success(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    home = await management_service.create_home(admin_id, "To Be Deleted")
    home_id = home.get_id()

    # Act
    await management_service.delete_home(admin_id, home_id)

    # Assert
    deleted_home = await home_repo.get_by_id(home_id)
    assert deleted_home is None 

@pytest.mark.asyncio
async def test_delete_home_unauthorized(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    member_id = uuid4()
    home = await management_service.create_home(admin_id, "Keep Me Home")
    home.add_member(member_id)
    await home_repo.update(home)

    # Act & Assert: Regular member tries to delete
    with pytest.raises(PermissionError, match="Only admin can delete the home"):
        await management_service.delete_home(member_id, home.get_id())

@pytest.mark.asyncio
async def test_transfer_admin_success(management_service, home_repo):
    # Arrange
    old_admin_id = uuid4()
    new_admin_id = uuid4()
    home = await management_service.create_home(old_admin_id, "Transfer Home")
    home_id = home.get_id()
    
    home.add_member(new_admin_id)
    await home_repo.update(home)

    # Act
    updated_home = await management_service.switch_home_head(old_admin_id, home_id, new_admin_id)

    # Assert
    assert updated_home.get_admin() == new_admin_id
    assert updated_home.is_admin(old_admin_id) is False

    with pytest.raises(PermissionError, match="Only admin can view the home join code"):
        await management_service.view_home_code(old_admin_id, home_id)

@pytest.mark.asyncio
async def test_transfer_admin_unauthorized(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    member_1_id = uuid4()
    member_2_id = uuid4()
    
    home = await management_service.create_home(admin_id, "Secure Home")
    home_id = home.get_id()
    home.add_member(member_1_id)
    home.add_member(member_2_id)
    await home_repo.update(home)

    # Act & Assert: Member tries to steal/transfer admin rights
    with pytest.raises(PermissionError, match="Only current admin can transfer admin rights"):
        await management_service.switch_home_head(member_1_id, home_id, member_2_id)

@pytest.mark.asyncio
async def test_transfer_admin_to_non_member(management_service, home_repo):
    # Arrange
    admin_id = uuid4()
    stranger_id = uuid4()
    home = await management_service.create_home(admin_id, "Isolated Home")

    # Act & Assert: Admin tries to give admin rights to someone not in the home
    with pytest.raises(ValueError, match="User is not a member of the home"):
        await management_service.switch_home_head(admin_id, home.get_id(), stranger_id)