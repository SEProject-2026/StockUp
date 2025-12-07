from uuid import UUID
from typing import List, Optional, Dict
from datetime import date
from Domain.SmartHome.Home import Home
from Domain import User

class ManagementService:

    def __init__(self):
        pass

    def create_new_home(self, home_name: str) -> Home:
        uuid: UUID = UUID()
        join_code: str = uuid.hex[:6].upper()  # Simple join code generation
        # When creating a home, the creator is both member and admin, no need to assign separately
        return Home(id=uuid, name=home_name, join_code=join_code)