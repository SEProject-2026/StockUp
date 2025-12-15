from uuid import UUID, uuid4
from typing import Dict, Set
from src.domain.domain_exception import UserMustBeMemberException



class Home:

    def __init__(self, user_id: UUID, name: str):
        self._id: UUID = uuid4()
        self._name: str = name
        self._join_code: str = self._id.hex[:6].upper()  # Simple join code generation
        self._members: Set[UUID] = set()  # Set of user IDs
        self._members.add(user_id)  # Creator is the first member
        self._admin: UUID = user_id  # Admin user ID, assigned to creator by default
        self._join_requests: Set[UUID] = set()  # Set of user IDs requesting to join

    def get_id(self) -> UUID:
        return self._id
    
    def get_name(self) -> str:
        return self._name
    
    def get_join_code(self) -> str:
        return self._join_code
    
    def get_members(self) -> Set[UUID]:
        return self._members
    
    def get_admin(self) -> UUID:
        return self._admin
    
    def get_join_requests(self) -> Set[UUID]:
        return self._join_requests
    
    def set_name(self, name: str) -> None:
        self._name = name

    def assign_admin(self, head_user_id: UUID, user_id: UUID) -> None:
        if not self.is_admin(head_user_id):
                raise PermissionError("Only current admin can transfer admin rights.")
        if not self.is_member(user_id):
            raise UserMustBeMemberException()
        self._admin = user_id

    def is_admin(self, user_id: UUID) -> bool:
        return self._admin == user_id
    
    def has_request_from(self, user_id: UUID) -> bool:
        return user_id in self._join_requests
    
    def add_join_request(self, user_id: UUID) -> None:
        if self.has_request_from(user_id):
            raise ValueError("User has already requested to join.")
        self._join_requests.add(user_id)

    def answer_join_request(self, head_user_id: UUID, user_id: UUID, approved: bool) -> None:
        if not self.is_admin(head_user_id):
            raise PermissionError("Only admin can approve or deny join requests.")
        
        if not self.has_request_from(user_id):
            raise ValueError("No such join request found.")
        
        if approved:
            self.add_member(user_id)
        
        self._join_requests.remove(user_id)
        
    def add_member(self, user_id: UUID) -> None:
        if self.is_member(user_id):
            raise ValueError("User is already a member of the home.")
        self._members.add(user_id)

    def is_member(self, user_id: UUID) -> bool:
        return user_id in self._members
    
    def remove_member(self, head_user_id: UUID, user_id: UUID) -> None:
        if not self.is_admin(head_user_id):
            raise PermissionError("Only admin can remove members from the home.")
        
        if self.is_member(user_id):
            self._members.remove(user_id)
        else:
            raise UserMustBeMemberException()
        
    def leave_home(self, user_id: UUID) -> None:
        if self.is_admin(user_id):
            raise PermissionError("Admin cannot leave the home. Transfer admin rights before leaving.")
        if not self.is_member(user_id):
            raise ValueError("User is not a member of this home.")
        
        self._members.remove(user_id)
        
    def view_home_code(self, user_id: UUID) -> str:
        if not self.is_admin(user_id):
            raise PermissionError("Only admin can view the home join code.")
        return self.get_join_code()
    
    def get_home_details(self, user_id: UUID) -> Dict:
        if not self.is_member(user_id):
            raise UserMustBeMemberException()
        
        details = {
            "id": str(self.get_id()),
            "name": self.get_name(),
            "join code": self.get_join_code() if self.is_admin(user_id) else "Restricted",
            "members": [str(member) for member in self._members],
            "admin": str(self.get_admin())
        }
        return details
    
    def can_switch_home(self, user_id: UUID) -> None:
        if not self.is_member(user_id):
            raise UserMustBeMemberException()
        
    def can_delete_home(self, head_user_id: UUID) -> None:
        if not self.is_admin(head_user_id):
            raise PermissionError("Only admin can delete the home.")