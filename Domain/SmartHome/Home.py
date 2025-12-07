from uuid import UUID
from typing import List, Optional, Dict
from datetime import date

class Home:

    def __init__(self, id: UUID, name: str, join_code: str):
        self.id: UUID = id
        self.name: str = name
        self.join_code: str = join_code
        self.members: List[UUID] = [id]  # List of user IDs
        self.admin: Optional[UUID] = id  # Admin user ID, assigned to creator by default

    def assign_admin(self, user_id: UUID) -> None:
        if user_id not in self.members:
            raise ValueError("User must be a member to be assigned as admin.")
        self.admin = user_id