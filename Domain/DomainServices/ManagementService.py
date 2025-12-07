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