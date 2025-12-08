from uuid import UUID, uuid4
from typing import Optional

class User:
    def __init__(self, email: str, name: str, hashed_password: str, id: Optional[UUID] = None):
        self.id = id if id else uuid4()
        self.email = email
        self.name = name
        self.hashed_password = hashed_password
        self.is_active = True