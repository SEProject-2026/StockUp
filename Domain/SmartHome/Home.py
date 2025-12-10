from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date

class Home:

    def __init__(self, user_id: UUID, id: UUID, name: str, join_code: str):
        self._id: UUID = id
        self._name: str = name
        self._join_code: str = join_code
        self._members: List[UUID] = [user_id]  # List of user IDs
        self._admin: Optional[UUID] = user_id  # Admin user ID, assigned to creator by default
        self._join_requests: List[UUID] = []  # List of user IDs requesting to join

    def get_id(self) -> UUID:
        return self._id
    
    def get_name(self) -> str:
        return self._name
    
    def get_join_code(self) -> str:
        return self._join_code
    
    def get_members(self) -> List[UUID]:
        return self._members
    
    def get_admin(self) -> UUID:
        return self._admin
    
    def get_join_requests(self) -> List[UUID]:
        return self._join_requests
    
    def set_name(self, name: str) -> None:
        self._name = name

    def assign_admin(self, user_id: UUID) -> None:
        if not self.is_member(user_id):
            raise ValueError("User must be a member to be assigned as admin.")
        self._admin = user_id

    def is_admin(self, user_id: UUID) -> bool:
        return self._admin == user_id
    
    def has_request_from(self, user_id: UUID) -> bool:
        return user_id in self._join_requests
    
    def add_join_request(self, user_id: UUID) -> None:
        if user_id in self._join_requests:
            raise ValueError("User has already requested to join.")
        self._join_requests.append(user_id)

    def remove_join_request(self, user_id: UUID) -> None:
        if user_id in self._join_requests:
            self._join_requests.remove(user_id)
        else:
            raise ValueError("No such join request found.")
        
    def add_member(self, user_id: UUID) -> None:
        if user_id in self._members:
            raise ValueError("User is already a member of the home.")
        self._members.append(user_id)

    def is_member(self, user_id: UUID) -> bool:
        return user_id in self._members
    
    def remove_member(self, user_id: UUID) -> None:
        if user_id in self._members:
            self._members.remove(user_id)
        else:
            raise ValueError("User is not a member of this home.")