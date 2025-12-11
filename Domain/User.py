from uuid import UUID, uuid4
from typing import Optional

class User:
    def __init__(self, email: str, name: str, hashed_password: str, id: Optional[UUID] = None):
        self.id = id if id else uuid4()
        self.email = email
        self.name = name
        self.hashed_password = hashed_password

    def update_name(self, new_name: str):
        if not new_name:
            raise ValueError("Name cannot be empty")
        self.name = new_name
    
    def change_password(self, new_hashed_password: str):
        self.hashed_password = new_hashed_password