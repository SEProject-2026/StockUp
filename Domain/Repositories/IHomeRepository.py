from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from Domain.SmartHome.Home import Home

class IHomeRepository(ABC):

    @abstractmethod
    async def save(self, home: Home) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, home_id: UUID) -> Optional[Home]:
        pass

    @abstractmethod
    async def get_by_code(self, home_code: str) -> Optional[Home]:
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