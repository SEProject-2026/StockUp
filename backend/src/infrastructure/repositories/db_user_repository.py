from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.repositories.user_repository import IUserRepository
from src.domain.user.user import User
from src.infrastructure.db.models import UserModel

class DbUserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, user: User) -> User:
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == str(user.id))
        )
        db_user = result.scalars().first()
        
        if not db_user:
            db_user = UserModel(id=str(user.id))
            self.db.add(db_user)
        
        db_user.email = user.email
        db_user.name = user.name
        db_user.push_token = user.push_token
        await self.db.commit()
        return self._to_domain(db_user)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        db_user = result.scalars().first()
        if not db_user:
            return None
        return self._to_domain(db_user)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == str(user_id))
        )
        db_user = result.scalars().first()
        if not db_user:
            return None
        return self._to_domain(db_user)

    async def get_names_by_ids(self, user_ids: list[UUID]) -> dict[UUID, str]:
        result = await self.db.execute(
            select(UserModel).where(UserModel.id.in_([str(uid) for uid in user_ids]))
        )
        db_users = result.scalars().all()
        return {UUID(db_user.id): db_user.name for db_user in db_users}
    
    async def update_push_token(self, user_id: UUID, new_push_token: str) -> Optional[User]:
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == str(user_id))
        )
        db_user = result.scalars().first()
        if not db_user:
            return None
        db_user.push_token = new_push_token
        await self.db.commit()
        return self._to_domain(db_user)

    def _to_domain(self, db_user: UserModel) -> User:
        return User(
            id=UUID(db_user.id),
            email=db_user.email,
            name=db_user.name,
            push_token=db_user.push_token
        )