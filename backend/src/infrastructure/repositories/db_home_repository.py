from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload, selectinload
from src.repositories.i_home_repository import IHomeRepository
from src.domain.smart_home.home import Home
from src.infrastructure.db.models import HomeModel, UserModel

class DbHomeRepository(IHomeRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, home: Home) -> None:
        db_home = self.db.query(HomeModel).filter(HomeModel.id == str(home.get_id())).first()
        
        if not db_home:
            db_home = HomeModel(id=str(home.get_id()))
            self.db.add(db_home)
        
        # Update scalar fields
        db_home.name = home.get_name()
        db_home.join_code = home.get_join_code()
        db_home.expiration_range = home.get_expiration_range()
        db_home.admin_id = str(home.get_admin())
        
        # Update members relationship
        # We fetch all user models corresponding to the UUIDs in the domain entity
        member_ids = [str(uid) for uid in home.get_members()]
        if member_ids:
            db_users = self.db.query(UserModel).filter(UserModel.id.in_(member_ids)).all()
            db_home.users = db_users

        # Update join requests relationship
        request_ids = [str(uid) for uid in home.get_join_requests()]
        if request_ids:
            db_requests = self.db.query(UserModel).filter(UserModel.id.in_(request_ids)).all()
            db_home.join_requests = db_requests
        else:
            db_home.join_requests = []

        self.db.commit()

    async def get_by_id(self, home_id: UUID) -> Optional[Home]:
        db_home = (
            self.db.query(HomeModel)
            .options(joinedload(HomeModel.users), joinedload(HomeModel.join_requests))
            .filter(HomeModel.id == str(home_id))
            .first()
        )
        if not db_home:
            return None
        return self._to_domain(db_home)

    async def get_by_join_code(self, home_code: str) -> Optional[Home]:
        db_home = (
            self.db.query(HomeModel)
            .options(joinedload(HomeModel.users))
            .filter(HomeModel.join_code == home_code)
            .first()
        )
        if not db_home:
            return None
        return self._to_domain(db_home)

    async def get_by_name(self, home_name: str) -> Optional[Home]:
        db_home = (
            self.db.query(HomeModel)
            .options(joinedload(HomeModel.users))
            .filter(HomeModel.name == home_name)
            .first()
        )
        if not db_home:
            return None
        return self._to_domain(db_home)

    async def delete(self, home_id: UUID) -> None:
        db_home = self.db.query(HomeModel).filter(HomeModel.id == str(home_id)).first()
        if db_home:
            self.db.delete(db_home)
            self.db.commit()

    async def update(self, home: Home) -> None:
        await self.save(home)

    async def get_homes_by_user_id(self, user_id: UUID) -> List[Home]:
        db_homes = (
            self.db.query(HomeModel)
            .join(HomeModel.users)
            .filter(UserModel.id == str(user_id))
            .options(joinedload(HomeModel.users))
            .all()
        )
        return [self._to_domain(h) for h in db_homes]

    def _to_domain(self, db_home: HomeModel) -> Home:
        # Determine admin ID safely
        admin_id = UUID(db_home.admin_id) if db_home.admin_id else UUID(db_home.users[0].id)
        
        # Instantiate Home (using admin as creator for initialization)
        home = Home(user_id=admin_id, name=db_home.name)
        
        # Override internal state with DB data
        home._id = UUID(db_home.id)
        home._join_code = db_home.join_code
        home._expiration_range = db_home.expiration_range
        home._admin = admin_id
        
        # Reconstruct sets
        home._members = {UUID(u.id) for u in db_home.users}
        home._join_requests = {UUID(u.id) for u in db_home.join_requests}
        
        return home
    
    async def get_homes_batch(self, limit: int = 100, offset: int = 0) -> List[Home]:
        db_homes = (
            self.db.query(HomeModel)
            .options(
                selectinload(HomeModel.users),
                selectinload(HomeModel.join_requests)
            )
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        domain_homes = []
        for db_home in db_homes:
            domain_homes.append(self._to_domain(db_home))
            
        return domain_homes