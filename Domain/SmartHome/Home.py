from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date

class Home:

    def __init__(self, user_id: UUID, id: UUID, name: str, join_code: str):
        self.id: UUID = id
        self.name: str = name
        self.join_code: str = join_code
        self.members: List[UUID] = [user_id]  # List of user IDs
        self.admin: Optional[UUID] = user_id  # Admin user ID, assigned to creator by default

    def assign_admin(self, user_id: UUID) -> None:
        if user_id not in self.members:
            raise ValueError("User must be a member to be assigned as admin.")
        self.admin = user_id