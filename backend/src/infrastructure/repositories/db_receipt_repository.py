from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from src.infrastructure.db.models import ReceiptRecordModel, ReceiptRecordItemModel
from src.repositories.i_receipt_repository import IReceiptRepository
from src.domain.receipt.receipt import ReceiptDTO, ReceiptItemDTO
from src.domain.enums import UnitType, LocationType

class DbReceiptRepository(IReceiptRepository):
    def __init__(self, db: Session):
        self._db = db

    async def save(self, receipt: ReceiptDTO) -> None:
        new_receipt = ReceiptRecordModel(
            id=str(receipt.id),
            home_id=str(receipt.home_id),
            user_id=str(receipt.user_id),
            chain=receipt.chain,
        )
        
        for item in receipt.items:
            new_item = ReceiptRecordItemModel(
                id=str(uuid4()),
                receipt_id=str(receipt.id),
                name=item.name,
                barcode=item.barcode,
                quantity=item.quantity 
            )
            new_receipt.items.append(new_item)

        self._db.add(new_receipt)
        self._db.commit()

    async def get_by_home(self, home_id: UUID, limit: int = 50, since: Optional[datetime] = None) -> List[ReceiptDTO]:
        query = self._db.query(ReceiptRecordModel).filter(ReceiptRecordModel.home_id == str(home_id))
        
        if since:
            query = query.filter(ReceiptRecordModel.created_at >= since)
            
        records = (
            query.order_by(ReceiptRecordModel.created_at.desc())
            .limit(limit)
            .all()
        )
        
        dtos = []
        for r in records:
            items = []
            for i in r.items:
                items.append(ReceiptItemDTO(
                    name=i.name,
                    barcode=i.barcode,
                    quantity=int(i.quantity) if int(i.quantity) == i.quantity else 1,
                    unit=UnitType.UNIT,
                    location=LocationType.OTHER,
                    weight=i.quantity
                ))
            dto = ReceiptDTO(
                id=UUID(r.id),
                home_id=UUID(r.home_id),
                user_id=UUID(r.user_id),
                chain=r.chain,
                items=items
            )
            dtos.append(dto)
            
        return dtos
