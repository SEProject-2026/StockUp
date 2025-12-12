from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date

from domain.domain_services.domain_exception import DomainException, UserMustBeMemberException, ProductNotFoundException
from domain.smart_home.enums import ExpirationType, LocationType
from domain.smart_home.product import Product

class Home:

    def __init__(self, user_id: UUID, id: UUID, name: str, join_code: str):
        self._id: UUID = id
        self._name: str = name
        self._join_code: str = join_code
        self._members: Dict[UUID, None] = {user_id: None}  # Dictionary of user IDs
        self._admin: UUID = user_id  # Admin user ID, assigned to creator by default
        self._join_requests: Dict[UUID, None] = {}  # Dictionary of user IDs requesting to join

    def get_id(self) -> UUID:
        return self._id
    
    def get_name(self) -> str:
        return self._name
    
    def get_join_code(self) -> str:
        return self._join_code
    
    def get_members(self) -> Dict[UUID, None]:
        return self._members
    
    def get_admin(self) -> UUID:
        return self._admin
    
    def get_join_requests(self) -> Dict[UUID, None]:
        return self._join_requests
    
    def set_name(self, name: str) -> None:
        self._name = name

    def assign_admin(self, user_id: UUID) -> None:
        if not self.is_member(user_id):
            raise UserMustBeMemberException()
        self._admin = user_id

    def is_admin(self, user_id: UUID) -> bool:
        return self._admin == user_id
    
    def has_request_from(self, user_id: UUID) -> bool:
        return user_id in self._join_requests
    
    def add_join_request(self, user_id: UUID) -> None:
        if user_id in self._join_requests:
            raise ValueError("User has already requested to join.")
        self._join_requests[user_id] = None

    def remove_join_request(self, user_id: UUID) -> None:
        if user_id in self._join_requests:
            del self._join_requests[user_id]
        else:
            raise ValueError("No such join request found.")
        
    def add_member(self, user_id: UUID) -> None:
        if user_id in self._members:
            raise ValueError("User is already a member of the home.")
        self._members[user_id] = None

    def is_member(self, user_id: UUID) -> bool:
        return user_id in self._members
    
    def remove_member(self, user_id: UUID) -> None:
        if user_id in self._members:
            del self._members[user_id]
        else:
            raise UserMustBeMemberException()