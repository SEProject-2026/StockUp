from pydantic import BaseModel, ConfigDict
from typing import Optional, Any

class GeneralResponse(BaseModel):
    """
    Generic response wrapper for most API actions.
    """
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None 