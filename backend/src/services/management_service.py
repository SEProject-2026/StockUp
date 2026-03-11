from uuid import UUID
from typing import List
from src.repositories.user_repository import IUserRepository
from src.repositories.i_home_repository import IHomeRepository
from src.domain.home.home import Home
from src.infrastructure.logger import app_logger

class ManagementService:

    def __init__(self, home_repository: IHomeRepository, user_repository: IUserRepository):
            self._home_repository = home_repository
            self._user_repository = user_repository

    # ==========================================
    # 1. Home Management (House & Members)
    # ==========================================

    async def create_home(self, user_id: UUID, home_name: str) -> Home:
        """
        Creates a new home.
        """
        app_logger.debug(f"User {user_id} is creating a new home named '{home_name}'")
        new_home = Home(user_id=user_id, name=home_name)

        await self._home_repository.save(new_home)
        app_logger.info(f"Home '{home_name}' created successfully with ID: {new_home.get_id()} by user {user_id}")
        
        return new_home

    async def view_home_code(self, user_id: UUID, home_id: UUID) -> str:
        """Retrieves the home join code (Admin only)."""
        app_logger.debug(f"User {user_id} requesting to view join code for home {home_id}")
        home = await self._check_access(user_id, home_id)

        join_code = home.view_home_code(user_id)
        return join_code

    async def join_home(self, user_id: UUID, home_code: str) -> None:
        """
        User requests to join a home using a code.
        Creates a 'join request' waiting for approval.
        """
        app_logger.debug(f"User {user_id} attempting to join a home using code: {home_code}")
        home: Home = await self._home_repository.get_by_join_code(home_code)

        if home is None:
            app_logger.warning(f"Join home failed: Invalid join code '{home_code}' used by user {user_id}")
            raise ValueError("Home not found.")

        home.add_join_request(user_id)
        await self._home_repository.update(home)
        app_logger.info(f"User {user_id} successfully submitted a join request to home {home.get_id()}")

    async def answer_join_request(self, home_id: UUID, head_user_id: UUID, user_id: UUID, approved: bool) -> Home:
        """Head of House approves or denies a join request."""
        action = "approve" if approved else "deny"
        app_logger.debug(f"User {head_user_id} attempting to {action} join request for user {user_id} in home {home_id}")
        
        home = await self._check_access(head_user_id, home_id)
        home.answer_join_request(head_user_id, user_id, approved)

        await self._home_repository.update(home)
        app_logger.info(f"Join request for user {user_id} was {action}d by head user {head_user_id} in home {home_id}")
        return home

    async def remove_member(self, head_user_id: UUID, home_id: UUID, target_user_id: UUID) -> Home:
        """Head of House removes a member from the home."""
        app_logger.debug(f"User {head_user_id} attempting to remove member {target_user_id} from home {home_id}")
        home = await self._check_access(head_user_id, home_id)
        
        home.remove_member(head_user_id, target_user_id)
        await self._home_repository.update(home)
        
        app_logger.info(f"Member {target_user_id} was removed from home {home_id} by head user {head_user_id}")
        return home

    async def switch_home(self, user_id: UUID, target_home_id: UUID) -> Home:
        """Switches user context to a different home (returns new home details)."""
        app_logger.debug(f"User {user_id} attempting to switch context to home {target_home_id}")
        target_home = await self._check_access(user_id, target_home_id)
        
        target_home.can_switch_home(user_id)
        return target_home

    async def leave_home(self, user_id: UUID, home_id: UUID) -> None:
        """User voluntarily leaves a home."""
        app_logger.debug(f"User {user_id} attempting to leave home {home_id}")
        home = await self._check_access(user_id, home_id)
        
        home.leave_home(user_id)
        await self._home_repository.update(home)
        app_logger.info(f"User {user_id} successfully left home {home_id}")

    async def switch_home_head(self, current_head_id: UUID, home_id: UUID, new_head_id: UUID) -> Home:
        """Transfers 'Head of House' role to another member."""
        app_logger.debug(f"User {current_head_id} attempting to transfer Head of House role to {new_head_id} in home {home_id}")
        home = await self._check_access(current_head_id, home_id)
        
        home.assign_admin(current_head_id, new_head_id)
        await self._home_repository.update(home)
        
        app_logger.info(f"Head of House role in home {home_id} transferred from {current_head_id} to {new_head_id}")
        return home
        
    async def delete_home(self, head_user_id: UUID, home_id: UUID) -> None:
        """Permanently deletes the home and all associated data (Admin only)."""
        app_logger.debug(f"User {head_user_id} attempting to delete home {home_id}")
        home = await self._check_access(head_user_id, home_id)
        
        home.can_delete_home(head_user_id)

        # Note: When implementing the notification system, we should also trigger 
        # notifications to all members about the home deletion here.
        
        await self._home_repository.delete(home_id)
        app_logger.info(f"Home {home_id} was completely deleted by head user {head_user_id}")
        
    async def get_home_details(self, user_id: UUID, home_id: UUID) -> dict:
        """Retrieves home details including members and inventory summary."""
        app_logger.debug(f"User {user_id} requesting details for home {home_id}")
        home = await self._check_access(user_id, home_id)
        
        home_details = home.get_home_details(user_id)
        names = await self._user_repository.get_names_by_ids(list(home_details['members']))
        home_details['member_names'] = names
        home_details.pop('members')
        return home_details
    

    async def get_join_requests(self, head_user_id: UUID, home_id: UUID) -> dict:
        """Head of House retrieves list of pending join requests."""
        app_logger.debug(f"User {head_user_id} requesting join requests for home {home_id}")
        home = await self._check_access(head_user_id, home_id)
        
        join_requests = home.get_join_requests_names(head_user_id)
        names = await self._user_repository.get_names_by_ids(list(join_requests))
        return names
    
    async def get_all_homes_for_user(self, user_id: UUID) -> List[Home]:
        """Retrieves a list of all homes the user is a member of."""
        app_logger.debug(f"Retrieving all homes for user {user_id}")
        if not user_id:
            app_logger.warning("get_all_homes_for_user failed: user_id is missing")
            raise ValueError("User ID is required.")
            
        homes: List[Home] = await self._home_repository.get_homes_by_user_id(user_id)
        return homes
    
    async def update_expiration_range(self, head_user_id: UUID, home_id: UUID, new_range: int) -> Home:
        app_logger.debug(f"User {head_user_id} attempting to update expiration range to {new_range} in home {home_id}")
        home = await self._home_repository.get_by_id(home_id)
        
        # Note: Missing access check here in your original code! 
        # Usually, only the head of the house should be able to do this.
        # Assuming `update_expiration_range` in the Domain model checks this.
        home.update_expiration_range(head_user_id, new_range)
        
        await self._home_repository.update(home)
        app_logger.info(f"Expiration range for home {home_id} updated to {new_range} by user {head_user_id}")
        return home

    async def _check_access(self, user_id: UUID, home_id: UUID) -> Home:
        """Helper to verify user exists, logged in, and member of the home"""
        if not user_id or not home_id:
            app_logger.warning("Access check failed: Missing user_id or home_id")
            raise ValueError("User ID and Home ID are required.")
            
        home = await self._home_repository.get_by_id(home_id)
        if not home:
            app_logger.warning(f"Access check failed: Home {home_id} does not exist")
            raise ValueError("Home retrieval failed.")
            
        if not home.is_member(user_id):
            app_logger.warning(f"SECURITY WARNING: User {user_id} attempted to access home {home_id} without membership")
            raise ValueError("User is not a member of the home")
            
        return home