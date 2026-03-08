from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Any, List

# --- Input Schemas ---

class CreateHomeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class JoinHomeRequest(BaseModel):
    home_code: str = Field(..., min_length=6, max_length=6)

class AnswerJoinRequest(BaseModel):
    user_id: UUID
    approved: bool

class UpdateHomeHeadRequest(BaseModel):
    new_head_id: UUID

class UpdateExpirationRangeRequest(BaseModel):
    new_range: int = Field(..., gt=0, le=30, description="Number of days for 'going to expire' warning")

# --- Output Schemas ---

class HomeDTO(BaseModel):
    id: UUID
    name: str
    admin_id: UUID
    member_ids: List[UUID]      
    join_requests: List[UUID]
    expiration_range: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, home: Any) -> "HomeDTO":
        return cls(
            id=home.get_id(),
            name=home.get_name(),
            admin_id=home.get_admin(),
            member_ids=list(home.get_members()),      
            join_requests=list(home.get_join_requests()), 
            expiration_range=home.get_expiration_range()
        )