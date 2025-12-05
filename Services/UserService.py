from uuid import UUID
from typing import List, Optional, Dict
from datetime import date

from Repositories.user_repository import IUserRepository

class UserService:
    """
    Manages user lifecycle and authentication (independent of specific homes).
    """
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    async def register(self, email: str, password: str, name: str) -> Dict:
        """
        Registers a new user to the system.
        Input: Registration details.
        Output: Created user object (or success message).
        """
        

    async def login(self, email: str, password: str) -> Dict:
        """
        Authenticates a user.
        Input: Email and password.
        Output: Access Token (JWT) and basic user info.
        """
        raise NotImplementedError("login not implemented yet")

    async def logout(self, user_id: UUID) -> bool:
        """
        Logs out the user (invalidates token if stateful, or client-side action).
        """
        raise NotImplementedError("logout not implemented yet")