from typing import Dict, List, Optional
from uuid import UUID, uuid4
from Repositories.i_home_repository import IHomeRepository
from domain.smart_home.home import Home

class InMemoryHomeRepository(IHomeRepository):
    
    def __init__(self):
        self._storage: Dict[UUID, Home] = {}

    async def save(self, home: Home) -> None:
        self._storage[home.get_id()] = home

    async def get_by_id(self, home_id: UUID) -> Optional[Home]:
        return self._storage.get(home_id)

    async def get_by_join_code(self, code: str) -> Optional[Home]:
        for home in self._storage.values():
            if home.get_join_code() == code:
                return home
        return None

    async def get_by_name(self, home_name: str) -> Optional[Home]:
        for home in self._storage.values():
            if home.get_name() == home_name:
                return home
        return None
    
    async def update(self, home: Home) -> None:
        self._storage[home.get_id()] = home

    async def delete(self, home_id: UUID) -> None:
        if home_id in self._storage:
            del self._storage[home_id]

    async def get_homes_by_user_id(self, user_id: UUID) -> List[Home]:
        result = []
        for home in self._storage.values():
            if home.is_member(user_id):
                result.append(home)
        return result