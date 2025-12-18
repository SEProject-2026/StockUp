from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Any
from src.domain.smart_home.home import Home 

# --- Input ---
class CreateHomeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Home name cannot be empty")

# --- Output ---
class HomeDTO(BaseModel):
    id: UUID
    name: str
    admin_id: UUID
    member_ids: List[UUID]      
    join_requests: List[UUID]
    expiration_range: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, home: Home) -> "HomeDTO":
        """
        Helper to convert Domain Entity (with sets and private fields) 
        to Pydantic DTO (with lists).
        """
        return cls(
            id=home.get_id(),
            name=home.get_name(),
            admin_id=home.get_admin(),
            member_ids=list(home.get_members()),      
            join_requests=list(home.get_join_requests()), 
            expiration_range=home.get_expiration_range()
        )