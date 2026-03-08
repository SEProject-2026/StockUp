from uuid import UUID
from typing import List
from src.repositories.i_home_repository import IHomeRepository
from src.domain.smart_home.home import Home


class ManagementService:

    def __init__(self, home_repository: IHomeRepository):
            self._home_repository = home_repository

    # ==========================================
    # 1. Home Management (House & Members)
    # ==========================================

    async def create_home(self, user_id: UUID, home_name: str) -> Home:
        """
        Creates a new home.
        """
        new_home = Home(user_id=user_id, name=home_name)

        await self._home_repository.save(new_home)
        
        return new_home

    async def view_home_code(self, user_id: UUID, home_id: UUID) -> str:
        """Retrieves the home join code (Admin only)."""
        home = await self._check_access(user_id, home_id)

        join_code = home.view_home_code(user_id)

        return join_code

    async def join_home(self, user_id: UUID, home_code: str) -> None:
        """
        User requests to join a home using a code.
        Creates a 'join request' waiting for approval.
        """
        home: Home = await self._home_repository.get_by_join_code(home_code)

        if home is None:
            raise ValueError("Home not found.")

        home.add_join_request(user_id)
        await self._home_repository.update(home)

    async def answer_join_request(self, home_id: UUID, head_user_id: UUID, user_id: UUID, approved: bool) -> Home:
        """Head of House approves or denies a join request."""
        home = await self._check_access(head_user_id, home_id)
        home.answer_join_request(head_user_id, user_id, approved)

        await self._home_repository.update(home)
        return home
    
    async def remove_member(self, head_user_id: UUID, home_id: UUID, target_user_id: UUID) -> Home:
        """Head of House removes a member from the home."""
        home = await self._check_access(head_user_id, home_id)
        home.remove_member(head_user_id, target_user_id)
        
        await self._home_repository.update(home)
        return home

    async def switch_home(self, user_id: UUID, target_home_id: UUID) -> Home:
        """Switches user context to a different home (returns new home details)."""
        target_home = await self._check_access(user_id, target_home_id)
        target_home.can_switch_home(user_id)
       
        return target_home

    async def leave_home(self, user_id: UUID, home_id: UUID) -> None:
        """User voluntarily leaves a home."""
        home = await self._check_access(user_id, home_id)
        home.leave_home(user_id)
        
        await self._home_repository.update(home)

    async def switch_home_head(self, current_head_id: UUID, home_id: UUID, new_head_id: UUID) -> Home:
        """Transfers 'Head of House' role to another member."""
        home = await self._check_access(current_head_id, home_id)
        home.assign_admin(current_head_id, new_head_id)
        
        await self._home_repository.update(home)
        return home
        
    async def delete_home(self, head_user_id: UUID, home_id: UUID) -> None:
        """Permanently deletes the home and all associated data (Admin only)."""
        home = await self._check_access(head_user_id, home_id)
        home.can_delete_home(head_user_id)

        # Note: When implementing the notification system, we should also trigger 
        # notifications to all members about the home deletion here.
        
        await self._home_repository.delete(home_id)
        
    async def get_home_details(self, user_id: UUID, home_id: UUID) -> dict:
        """Retrieves home details including members and inventory summary."""
        home = await self._check_access(user_id, home_id)
        home_details = home.get_home_details(user_id)
        return home_details
    
    async def get_all_homes_for_user(self, user_id: UUID) -> List[Home]:
        """Retrieves a list of all homes the user is a member of."""
        if not user_id:
            raise ValueError("User ID is required.")
        homes: List[Home] = await self._home_repository.get_homes_by_user_id(user_id)
        return homes
    
    async def _check_access(self, user_id: UUID, home_id: UUID) -> Home:
        """Helper to verify user exists, logged in, and member of the home"""
        if not user_id or not home_id:
            raise ValueError("User ID and Home ID are required.")
        home = await self._home_repository.get_by_id(home_id)
        if not home:
            raise ValueError("Home retrieval failed.")
        if not home.is_member(user_id):
            raise ValueError("User is not a member of the home")
        return home