from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date
from Domain.SmartHome.Home import Home
from Domain import User

class ManagementService:

    def __init__(self):
        pass

    def create_new_home(self, home_name: str, user_id: UUID) -> Home:
        uuid: UUID = uuid4()
        join_code: str = uuid.hex[:6].upper()  # Simple join code generation
        # When creating a home, the creator is both member and admin, no need to assign separately
        return Home(user_id=user_id, id=uuid, name=home_name, join_code=join_code)
    
    def view_home_code(self, user_id: UUID, home: Home) -> str:
        # Only admin can view the join code
        if home.__admin != user_id:
            raise PermissionError("Only admin can view the home join code.")
        return home.__join_code
    
    def join_home(self, user_id: UUID, home: Home) -> bool:
        # Check if user has already requested to join
        if user_id in home.__join_requests:
            raise ValueError("User has already requested to join this home.")
        
        # Add join request
        home.__join_requests.append(user_id)
        return True