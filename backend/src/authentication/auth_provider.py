from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

class IAuthProvider(ABC):

    @abstractmethod
    def create_token(self, user_id: UUID) -> str:
        #generates a session token for the given user_id
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[UUID]:
        #verifies the token and returns the associated user_id if valid, else None
        pass