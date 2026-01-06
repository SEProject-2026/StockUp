from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
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

router = APIRouter(prefix="/auth", tags=["Authentication"])

user_service = AppContainer.get_user_service()

@router.post("/register", response_model=GeneralResponse)
async def register(request: RegisterRequest):
    """
    Register a new user.
    """
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
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login and retrieve an access token.
    """
    try:
        user_entity, token = await user_service.login(request.email, request.password)
        
        return LoginResponse(
            status="success",
            access_token=token,
            data=UserDTO.model_validate(user_entity)
        )
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )

@router.put("/update_name", response_model=GeneralResponse)
async def update_name(
    request: UpdateNameRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Update the user's name (Protected Route).
    """
    try:
        updated_user = await user_service.update_name(user_id, request.name)
        
        return GeneralResponse(
            status="success", 
            message="Name updated successfully", 
            data=UserDTO.model_validate(updated_user)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/password", response_model=GeneralResponse)
async def change_password(
    request: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Change the authenticated user's password.
    Protected Route.
    """
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
        # This catches "Incorrect current password" or other validation errors
        raise HTTPException(status_code=400, detail=str(e))