from typing import Optional
from uuid import UUID
from domain.user import User
from repositories.user_repository import IUserRepository


class InMemoryUserRepository(IUserRepository):
    def __init__(self):
        self.users = {}

    async def save(self, user: User) -> None:
        self.users[user.id] = user

    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.users.get(user_id, None)