from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from src.domain.receipt.receipt import ReceiptDTO

class IReceiptRepository(ABC):
    @abstractmethod
    async def save(self, receipt: ReceiptDTO) -> None:
        """Saves a receipt record to the database."""
        pass

    @abstractmethod
    async def get_by_home(self, home_id: UUID, limit: int = 50, since: Optional[datetime] = None) -> List[ReceiptDTO]:
        """Gets recent receipt records for a home, optionally filtered by date."""
        pass
