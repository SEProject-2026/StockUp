from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date

class Home:

    def __init__(self, user_id: UUID, id: UUID, name: str, join_code: str):
        self.__id: UUID = id
        self.__name: str = name
        self.__join_code: str = join_code
        self.__members: List[UUID] = [user_id]  # List of user IDs
        self.__admin: Optional[UUID] = user_id  # Admin user ID, assigned to creator by default
        self.__join_requests: List[UUID] = []  # List of user IDs requesting to join

    def assign_admin(self, user_id: UUID) -> None:
        if user_id not in self.__members:
            raise ValueError("User must be a member to be assigned as admin.")
        self.__admin = user_id