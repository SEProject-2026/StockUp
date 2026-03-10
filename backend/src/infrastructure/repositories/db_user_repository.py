from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from backend.src.repositories.user_repository import IUserRepository
from backend.src.domain.user import User
from backend.src.infrastructure.db.models import UserModel

class DbUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, user: User) -> User:
        db_user = self.db.query(UserModel).filter(UserModel.id == str(user.id)).first()
        
        if not db_user:
            db_user = UserModel(id=str(user.id))
            self.db.add(db_user)
        
        db_user.email = user.email
        db_user.name = user.name
        db_user.hashed_password = user.hashed_password
        
        self.db.commit()
        return self._to_domain(db_user)

    async def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not db_user:
            return None
        return self._to_domain(db_user)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.id == str(user_id)).first()
        if not db_user:
            return None
        return self._to_domain(db_user)
    async def get_names_by_ids(self, user_ids: list[UUID]) -> dict[UUID, str]:
        db_users = self.db.query(UserModel).filter(UserModel.id.in_([str(uid) for uid in user_ids])).all()
        return {UUID(db_user.id): db_user.name for db_user in db_users}

    def _to_domain(self, db_user: UserModel) -> User:
        return User(
            id=UUID(db_user.id),
            email=db_user.email,
            name=db_user.name,
            hashed_password=db_user.hashed_password
        )