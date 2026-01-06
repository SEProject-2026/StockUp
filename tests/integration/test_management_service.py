# import pytest
# from uuid import UUID, uuid4
# from src.services.management_service import ManagementService
# from src.infrastructure.repositories.in_memory_home_repository import InMemoryHomeRepository
# from src.response import Response

# @pytest.fixture
# def management_service():
#     home_repo = InMemoryHomeRepository()
#     service = ManagementService(home_repository=home_repo)    
#     return service


# @pytest.mark.asyncio
# async def test_create_home_success(management_service):
#     # Arrange
#     user_id = uuid4()
#     home_name = "My Castle"

#     # Act
#     response = await management_service.create_home(user_id, home_name)

#     # Assert
#     assert response.isOk() is True
#     assert response.get_data()["name"] == home_name
#     assert "id" in response.get_data()
#     assert "join code" in response.get_data()

#     # Verify Persistence 
#     saved_home = await management_service.get_home_repository().get_by_name(home_name)
#     assert saved_home is not None
#     assert saved_home.get_admin() == user_id

# @pytest.mark.asyncio
# async def test_join_home_flow(management_service):
#     # 1. User A creates a home
#     admin_id = uuid4()
#     create_res = await management_service.create_home(admin_id, "Clubhouse")
#     home_code = create_res.get_data()["join code"]
#     home_id = UUID(create_res.get_data()["id"])

#     # 2. User B requests to join
#     user_b = uuid4()
#     join_res = await management_service.join_home(user_b, home_code)
#     assert join_res.isOk() is True

#     # 3. Verify request exists
#     home = await management_service.get_home_repository().get_by_id(home_id)
#     assert home.has_request_from(user_b) is True

#     # 4. Admin approves
#     approve_res = await management_service.answer_join_request(home_id, admin_id, user_b, True)
#     assert approve_res.isOk() is True

#     # 5. Verify User B is now a member
#     updated_home = await management_service.get_home_repository().get_by_id(home_id)
#     assert updated_home.is_member(user_b) is True
#     assert updated_home.has_request_from(user_b) is False

# @pytest.mark.asyncio
# async def test_remove_member_success(management_service):
#     # Arrange: Create home and add a second member directly
#     admin_id = uuid4()
#     member_id = uuid4()
    
#     create_res = await management_service.create_home(admin_id, "Test Home")
#     home_id = UUID(create_res.get_data()["id"])
    
#     home = await management_service.get_home_repository().get_by_id(home_id)
#     home.add_member(member_id)
#     await management_service.get_home_repository().update(home)

#     # Act: Admin removes member
#     res = await management_service.remove_member(admin_id, home_id, member_id)

#     # Assert
#     assert res.isOk() is True
#     updated_home = await management_service.get_home_repository().get_by_id(home_id)
#     assert updated_home.is_member(member_id) is False

# @pytest.mark.asyncio
# async def test_leave_home_success(management_service):
#     # Arrange
#     admin_id = uuid4()
#     member_id = uuid4()
    
#     create_res = await management_service.create_home(admin_id, "Leavers Home")
#     home_id = UUID(create_res.get_data()["id"])
    
#     home = await management_service.get_home_repository().get_by_id(home_id)
#     home.add_member(member_id)
#     await management_service.get_home_repository().update(home)

#     # Act
#     res = await management_service.leave_home(member_id, home_id)

#     # Assert
#     assert res.isOk() is True
#     updated_home = await management_service.get_home_repository().get_by_id(home_id)
#     assert updated_home.is_member(member_id) is False

# @pytest.mark.asyncio
# async def test_admin_cannot_leave_home(management_service):
#     # Arrange
#     admin_id = uuid4()
#     create_res = await management_service.create_home(admin_id, "Admin Home")
#     home_id = UUID(create_res.get_data()["id"])

#     # Act
#     res = await management_service.leave_home(admin_id, home_id)
#     # Assert (Failure expected)
#     assert res.isOk() is False
#     assert "An internal error occurred while leaving the home." in res.get_error_message()