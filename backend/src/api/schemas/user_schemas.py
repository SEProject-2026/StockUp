from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID

class UserDTO(BaseModel):
    """
    Public representation of a User.
    Contains only safe fields.
    """
    id: UUID
    email: EmailStr
    name: str

    model_config = ConfigDict(from_attributes=True)

# class RegisterRequest(BaseModel):
#     email: EmailStr
#     name: str
#     password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
#     password_confirm: str = Field(..., min_length=8, description="Password confirmation must match the password")

class RegisterRequest(BaseModel):
    user_id: UUID
    email: EmailStr
    name: str
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateNameRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Name cannot be empty")

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class LoginResponse(BaseModel):
    status: str
    access_token: str
    token_type: str = "bearer"
    data: UserDTO