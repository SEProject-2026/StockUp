from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional
from src.domain.home.home import Home

class IHomeRepository(ABC):

    @abstractmethod
    async def save(self, home: Home) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, home_id: UUID) -> Optional[Home]:
        pass

    @abstractmethod
    async def get_by_join_code(self, home_code: str) -> Optional[Home]:
        pass

    @abstractmethod
    async def get_by_name(self, home_name: str) -> Optional[Home]:
        pass

    @abstractmethod
    async def delete(self, home_id: UUID) -> None:
        pass

    @abstractmethod
    async def update(self, home: Home) -> None:
        pass

    @abstractmethod
    async def get_homes_by_user_id(self, user_id: UUID) -> List[Home]:
        pass