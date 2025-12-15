from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID
from typing import Optional, Dict, Union

# --------------------------------------
# 1. Shared Models
# --------------------------------------

class UserDTO(BaseModel):
    """
    Public representation of a User.
    Contains only safe fields (no passwords or internal flags).
    """
    id: UUID
    email: EmailStr
    name: str

    model_config = ConfigDict(from_attributes=True)

# --------------------------------------
# 2. Input Models (Requests)
# --------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateNameRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Name cannot be empty")

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

# --------------------------------------
# 3. Output Models (Responses)
# --------------------------------------

class LoginResponse(BaseModel):
    """
    Specific response for login actions.
    Must guarantee the presence of an access_token.
    """
    status: str
    access_token: str
    token_type: str = "bearer"
    data: UserDTO

class GeneralResponse(BaseModel):
    """
    Generic response wrapper for most API actions.
    'data' is optional and flexible.
    """
    status: str
    message: Optional[str] = None
    # Can contain a UserDTO, a Dictionary, or be None
    data: Optional[Union[UserDTO, Dict]] = None