from uuid import UUID, uuid4
from typing import Optional

class User:
    def __init__(
        self, 
        email: str, 
        name: str, 
        id: Optional[UUID] = None, 
        push_token: Optional[str] = None
    ):
        
        # We keep the uuid4() default only as a fallback.
        self.id = id if id else uuid4()
        self.email = email
        self._validate_name(name)
        self.name = name
        self.push_token = push_token

    def update_name(self, new_name: str):
        self._validate_name(new_name)
        self.name = new_name

    def _validate_name(self, name: str):
        """Internal domain validation rule."""
        if not name or not name.strip():
            raise ValueError("User name cannot be empty")

    def update_push_token(self, new_push_token: str):
        self.push_token = new_push_token