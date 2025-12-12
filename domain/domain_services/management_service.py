from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date
from domain.domain_services.domain_exception import UserMustBeMemberException
from domain.smart_home.home import Home
from domain.user import User

class ManagementService:

    def __init__(self):
        pass

    def create_new_home(self, home_name: str, user_id: UUID) -> Home:
        if not home_name or home_name.strip() == "":
            raise ValueError("Home name cannot be empty.")
        
        uuid: UUID = uuid4()
        join_code: str = uuid.hex[:6].upper()  # Simple join code generation
        # When creating a home, the creator is both member and admin, no need to assign separately
        return Home(user_id=user_id, id=uuid, name=home_name, join_code=join_code)
    
    def view_home_code(self, user_id: UUID, home: Home) -> str:
        # Only admin can view the join code
        if not home.is_admin(user_id):
            raise PermissionError("Only admin can view the home join code.")
        return home.get_join_code()
    
    def join_home(self, user_id: UUID, home: Home) -> None:
        # Check if user has already requested to join
        if home.has_request_from(user_id):
            raise ValueError("User has already requested to join this home.")
        
        # Add join request
        home.add_join_request(user_id)

    def answer_join_request(self, head_user_id: UUID, home: Home, request_user_id: UUID, approved: bool) -> None:
        # Only admin can approve/deny join requests
        if not home.is_admin(head_user_id):
            raise PermissionError("Only admin can approve or deny join requests.")
        
        if not home.has_request_from(request_user_id):
            raise ValueError("No such join request found.")
        
        if approved:
            home.add_member(request_user_id)
        
        # Remove the request after processing
        home.remove_join_request(request_user_id)

    def remove_member(self, admin_user_id: UUID, home: Home, member_user_id: UUID) -> None:
        # Only admin can remove members
        if not home.is_admin(admin_user_id):
            raise PermissionError("Only admin can remove members from the home.")
        
        if not home.is_member(member_user_id):
            raise ValueError("User is not a member of this home.")
        
        home.remove_member(member_user_id)

    def can_switch_home(self, user_id: UUID, home: Home) -> None:
        if not home.is_member(user_id):
            raise ValueError("User is not a member of this home.")
        
    def leave_home(self, user_id: UUID, home: Home) -> None:
        if home.is_admin(user_id):
            raise PermissionError("Admin cannot leave the home. Transfer admin rights before leaving.")
        if not home.is_member(user_id):
            raise ValueError("User is not a member of this home.")
        
        home.remove_member(user_id)

    def switch_home_head(self, current_admin_id: UUID, home: Home, new_admin_id: UUID) -> None:
        if not home.is_admin(current_admin_id):
            raise PermissionError("Only current admin can transfer admin rights.")
        
        if not home.is_member(new_admin_id):
            raise ValueError("New admin must be a member of the home.")
        
        home.assign_admin(new_admin_id)

    def can_delete_home(self, admin_user_id: UUID, home: Home) -> None:
        if not home.is_admin(admin_user_id):
            raise PermissionError("Only admin can delete the home.")
        
    def get_home_details(self, user_id: UUID, home: Home) -> Dict:
        if not home.is_member(user_id):
            raise PermissionError("User is not a member of this home.")
        
        details = {
            "id": str(home.get_id()),
            "name": home.get_name(),
            "join_code": home.get_join_code() if home.is_admin(user_id) else "Restricted",
            "members": [str(member) for member in home.get_members()],
            "admin": str(home.get_admin())
        }
        return details
    
    def verify_user_membership(self, user_id: UUID, home: Home) -> None:
        if not home.is_member(user_id):
            raise UserMustBeMemberException()