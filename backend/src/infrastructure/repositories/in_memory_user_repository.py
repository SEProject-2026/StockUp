from typing import Optional
from uuid import UUID
from src.domain.user.user import User
from src.repositories.user_repository import IUserRepository


class InMemoryUserRepository(IUserRepository):
    def __init__(self):
        self.users = {}

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.users.get(user_id, None)
    
    async def get_names_by_ids(self, user_ids: list[UUID]) -> dict[UUID, str]:
        return {user_id: self.users[user_id].name for user_id in user_ids if user_id in self.users}