from typing import Annotated 
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

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

from src.api.routes.translate_notifications import translate_error

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
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
            user_id=request.user_id,
            name=request.name
        )
        
        return GeneralResponse(
            status="success", 
            message="User created successfully", 
            data=UserDTO.model_validate(user) 
        )
    
    except ValueError as e:
        app_logger.warning(f"Registration failed for email {request.email} - Reason: {str(e)}")
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=400, detail=translated_message)


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
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=400, detail=translated_message)


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
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=400, detail=translated_message)

@router.post("/logout", response_model=GeneralResponse)
async def logout(
    user_service: UserServiceDep, 
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Logout the user and clear their push token.
    Protected Route.
    """
    app_logger.info(f"Logout request received from user {user_id}")
    await user_service.logout(user_id)
    
    return GeneralResponse(
        status="success", 
        message="Logged out successfully"
    )