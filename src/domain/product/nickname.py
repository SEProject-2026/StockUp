from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Nickname(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    home_id: UUID
    name: str
    barcode: str
    chain: Optional[str] = None