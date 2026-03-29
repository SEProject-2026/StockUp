from datetime import datetime
from typing import List, Optional
from uuid import UUID
from src.repositories.i_receipt_repository import IReceiptRepository
from src.domain.receipt.receipt import ReceiptDTO

class InMemoryReceiptRepository(IReceiptRepository):
    def __init__(self):
        self._receipts = []

    async def save(self, receipt: ReceiptDTO) -> None:
        self._receipts.append(receipt)

    async def get_by_home(self, home_id: UUID, limit: int = 50, since: Optional[datetime] = None) -> List[ReceiptDTO]:
        res = [r for r in self._receipts if r.home_id == home_id]
        # In a real In-Memory repo we'd check dates, 
        # but for these tests we'll just return all matching the home and limit.
        return list(reversed(res))[:limit]
