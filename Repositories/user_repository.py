from abc import ABC, abstractmethod
from typing import Optional, Dict
from uuid import UUID

class IUserRepository(ABC):
    """
    Interface for User data access.
    Supports operations required by ARD sections 2.2.1 (Register) and 2.2.2 (Login).
    """

    @abstractmethod
    async def create(self, user_data: Dict) -> Dict:
        """
        Save a new user to the storage.
        Should assign a new unique ID to the user.
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict]:
        """
        Find a user by their email address.
        Used for login authentication and duplicate checks.
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[Dict]:
        """
        Find a user by their unique UUID.
        """
        pass