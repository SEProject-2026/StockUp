from typing import Annotated 
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session 

from src.domain.user.user import User
from src.infrastructure import app_container
from src.infrastructure.logger import app_logger
from pydantic import BaseModel
from src.infrastructure.db.database import get_db
from src.api.schemas.user_schemas import (

    UserDTO,
    RegisterRequest, 
    LoginRequest, 
    LoginResponse, 
    UpdateNameRequest, 
    ChangePasswordRequest
)
from src.api.schemas.common import GeneralResponse

from src.infrastructure.app_container import AppContainer
from src.api.security import get_current_user_id
from src.services.user_service import UserService 

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return AppContainer.get_user_service(db)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.post("/register", response_model=GeneralResponse)
async def register(
    request: RegisterRequest,
    user_service: UserServiceDep 
):
    """
    Register a new user.
    """
    app_logger.info(f"Registration request received for email: {request.email}")
    try:
        user = await user_service.register(
            email=request.email, 
            password=request.password, 
            confirm_password=request.password_confirm,
            name=request.name
        )
        
        return GeneralResponse(
            status="success", 
            message="User created successfully", 
            data=UserDTO.model_validate(user) 
        )
    
    except ValueError as e:
        app_logger.warning(f"Registration failed for email {request.email} - Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    user_service: UserServiceDep 
):
    """
    Login and retrieve an access token.
    """
    app_logger.info(f"Login request received for email: {request.email}")
    try:
        user_entity, token = await user_service.login(request.email, request.password)
        
        return LoginResponse(
            status="success",
            access_token=token,
            data=UserDTO.model_validate(user_entity)
        )
    
    except ValueError:
        app_logger.warning(f"Login failed: Invalid credentials for email {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )


@router.put("/update_name", response_model=GeneralResponse)
async def update_name(
    request: UpdateNameRequest,
    user_service: UserServiceDep, 
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Update the user's name (Protected Route).
    """
    app_logger.info(f"Name update request received from user {user_id}")
    try:
        updated_user = await user_service.update_name(user_id, request.name)
        
        return GeneralResponse(
            status="success", 
            message="Name updated successfully", 
            data=UserDTO.model_validate(updated_user)
        )
    except ValueError as e:
        app_logger.warning(f"Name update failed for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    

@router.put("/password", response_model=GeneralResponse)
async def change_password(
    request: ChangePasswordRequest,
    user_service: UserServiceDep, 
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Change the authenticated user's password.
    Protected Route.
    """
    app_logger.info(f"Password change request received from user {user_id}")
    try:
        await user_service.change_password(
            user_id=user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        return GeneralResponse(
            status="success", 
            message="Password changed successfully"
        )
        
    except ValueError as e:
        app_logger.warning(f"Password change failed for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
class PushTokenUpdateDTO(BaseModel):
    push_token: str


@router.patch("/me/push-token")
async def update_push_token(
    data: PushTokenUpdateDTO,
    user_service: UserServiceDep, 
    user_id: UUID = Depends(get_current_user_id)
):
    try:
        await user_service.update_push_token(user_id, data.push_token)
        return {"status": "success", "message": "Push token saved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))