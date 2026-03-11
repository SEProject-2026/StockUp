from typing import List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Nickname(BaseModel):
    home_id: UUID
    name: str
    barcodes:List[str]