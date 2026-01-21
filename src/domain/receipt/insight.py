from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Optional

class InsightType(Enum):
    CROSS_SELL = "cross_sell"           # "You usually buy Tomatoes with Cucumbers"
    BASE_MODE_UPDATE = "base_mode_update" # "You buy more Milk than defined in Base Mode"

class Insight(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    home_id: UUID
    insight_type: InsightType
    
    # The primary item this insight is about (the "Nickname")
    item_name: str 
    
    # Detailed message for the UI
    message: str
    
    # Optional metadata (e.g., the suggested new quantity for Base Mode)
    suggested_value: Optional[float] = None
    
    # Confidence level (0.0 to 1.0) - how sure is the engine?
    confidence_score: float = 1.0