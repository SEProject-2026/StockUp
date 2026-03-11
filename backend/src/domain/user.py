from uuid import UUID, uuid4
from typing import Optional

class User:
    def __init__(self, email: str, name: str, hashed_password: str, id: Optional[UUID] = None, push_token: Optional[str] = None):
        self.id = id if id else uuid4()
        self.email = email
        self.name = name
        self.hashed_password = hashed_password
        self.push_token = push_token

    def update_name(self, new_name: str):
        self.name = new_name
    
    def change_password(self, new_hashed_password: str):
        self.hashed_password = new_hashed_password

    def update_push_token(self, new_push_token: str):
        self.push_token = new_push_token