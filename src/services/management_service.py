from uuid import UUID
from typing import List
from repositories.i_home_repository import IHomeRepository
from domain.smart_home.home import Home
from response import Response


class ManagementService:

    def __init__(self, home_repository: IHomeRepository):
            self._home_repository = home_repository


    def get_home_repository(self) -> IHomeRepository:
            return self._home_repository

    # ==========================================
    # 1. Home Management (House & Members)
    # ==========================================

    async def create_home(self, user_id: UUID, home_name: str) -> Response:
        """Creates a new home and sets the creator as ADMIN."""
        if not user_id or not home_name or home_name.strip() == "":
            return Response(isOk = False, error_message = "User ID and Home Name are required.")
        # Validation of home_name can be added with home repository checks
        try:
            home: Home = await self._home_repository.get_by_name(home_name)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while checking home name uniqueness.")
        
        if home is not None:
            return Response(isOk = False, error_message = "Home with the same name already exists.")
        
        # Create Home instance
        try:
            new_home: Home = Home(user_id=user_id, name=home_name)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while creating the home.")

        # Save to repository
        try:
            await self._home_repository.save(new_home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while saving the home.")
        data = new_home.get_home_details(user_id)
        data["message"] = "Home created successfully."
        return Response(
            isOk = True,
            data = data
        )

    async def view_home_code(self, user_id: UUID, home_id: UUID) -> Response:
        """Retrieves the home join code (Admin only)."""
        if not user_id or not home_id:
            return Response(isOk = False, error_message = "User ID and Home ID are required.")
        # Check if home exists
        try:
            home: Home = await self._home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            join_code = home.view_home_code(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while viewing the home code.")
        
        return Response(
            isOk = True,
            data = {
                "home id": str(home_id),
                "join code": join_code
            }
        )

    async def join_home(self, user_id: UUID, home_code: str) -> Response:
        """
        User requests to join a home using a code.
        Creates a 'join request' waiting for approval.
        """
        if not user_id or not home_code:
            return Response(isOk = False, error_message = "User ID and Home Code are required.")
        # Check if home exists
        try:
            home: Home = await self._home_repository.get_by_join_code(home_code)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            home.add_join_request(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while joining the home.")
        
        try:
            await self._home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Join request sent successfully."})

    async def answer_join_request(self, home_id: UUID, head_user_id: UUID, user_id: UUID, approved: bool) -> Response:
        """Head of House approves or denies a join request."""
        # Authentication session should provide user_id
        if not user_id or not home_id or not head_user_id:
            return Response(isOk = False, error_message = "Users ID and Home ID are required.")        
        try:
            home: Home = await self._home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            home.answer_join_request(head_user_id, user_id, approved)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while answering the join request.")
        
        try:
            await self._home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Join request answered successfully."})

    async def remove_member(self, head_user_id: UUID, home_id: UUID, target_user_id: UUID) -> Response:
        """Head of House removes a member from the home."""
        if not head_user_id or not home_id or not target_user_id:
            return Response(isOk = False, error_message = "Users ID and Home ID are required.") 
        try:
            home: Home = await self._home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            home.remove_member(head_user_id, target_user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while removing the user.")
        
        try:
            await self._home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "User removed successfully."})

    async def switch_home(self, user_id: UUID, target_home_id: UUID) -> Response:
        """Switches user context to a different home (returns new home details)."""
        if not user_id or not target_home_id:
            return Response(isOk = False, error_message = "User ID and Home ID are required.") 
        try:
            target_home: Home = await self._home_repository.get_by_id(target_home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if target_home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            target_home.can_switch_home(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = str(e))
        
        return Response(
            isOk = True,
            data = {
                "home id": str(target_home.get_id()),
                "home name": target_home.get_name(),
                "message": "Switched home successfully."
            }
        )

    async def leave_home(self, user_id: UUID, home_id: UUID) -> Response:
        """User voluntarily leaves a home."""
        if not user_id or not home_id:
            return Response(isOk = False, error_message = "User ID and Home ID are required.") 
        try:
            home: Home = await self._home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            home.leave_home(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while leaving the home.")
        
        try:
            await self._home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Left home successfully."})

    async def switch_home_head(self, current_head_id: UUID, home_id: UUID, new_head_id: UUID) -> Response:
        """Transfers 'Head of House' role to another member."""
        if not current_head_id or not home_id or not new_head_id:
            return Response(isOk = False, error_message = "Users ID and Home ID are required.") 
        try:
            home: Home = await self._home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            home.assign_admin(current_head_id, new_head_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while switching home head.")
        
        try:
            await self._home_repository.update(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while updating the home.")
        
        return Response(isOk = True, data = {"message": "Home head switched successfully."})

    async def delete_home(self, head_user_id: UUID, home_id: UUID) -> Response:
        """Permanently deletes the home and all associated data (Admin only)."""
        if not head_user_id or not home_id:
            return Response(isOk = False, error_message = "User ID and Home ID are required.") 
        try:
            home: Home = await self._home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            home.can_delete_home(head_user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = str(e))
        
        try:
            await self._home_repository.delete(home)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while deleting the home.")
        
        return Response(isOk = True, data = {"message": "Home deleted successfully."})

    async def get_home_details(self, user_id: UUID, home_id: UUID) -> Response:
        """Retrieves home details including members and inventory summary."""
        if not user_id or not home_id:
            return Response(isOk = False, error_message = "User ID and Home ID are required.") 
        try:
            home: Home = await self._home_repository.get_by_id(home_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving the home.")
        
        if home is None:
            return Response(isOk = False, error_message = "Home not found.")
        
        try:
            home_details = home.get_home_details(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while getting home details.")
        
        return Response(isOk = True, data = home_details)
    
    async def get_all_homes_for_user(self, user_id: UUID) -> Response:
        """Retrieves a list of all homes the user is a member of."""
        if not user_id:
            return Response(isOk = False, error_message = "User ID is required.") 
        try:
            homes: List[Home] = await self._home_repository.get_homes_by_user_id(user_id)
        except Exception as e:
            print(e)
            return Response(isOk = False, error_message = "An internal error occurred while retrieving homes.")
        
        home_dict = {}
        for home in homes:
            home_dict[home.get_id()] = home.get_name()

        return Response(isOk = True, data = home_dict)