from typing import Annotated # <--- Added for cleaner dependency injection
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session # <--- Added to type-hint the DB session

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
# Assuming UserService is the class returned by get_user_service
from src.services.user_service import UserService 

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- CHANGED: Removed global 'user_service = ...' ---
# Global variables cannot hold a database session because the session must be 
# created and closed for *every* request individually.

# --- ADDED: Dependency Helper ---
# This function gets a fresh DB session from FastAPI and passes it to the Container.
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return AppContainer.get_user_service(db)

# --- ADDED: Type Alias ---
# This allows us to use 'UserServiceDep' in routes without writing 'Depends(...)' every time.
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.post("/register", response_model=GeneralResponse)
async def register(
    request: RegisterRequest,
    user_service: UserServiceDep # <--- CHANGED: Injected the service here
):
    """
    Register a new user.
    """
    try:
        # We use the injected 'user_service' instance
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
async def login(
    request: LoginRequest,
    user_service: UserServiceDep # <--- CHANGED: Injected the service here
):
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
    user_service: UserServiceDep, # <--- CHANGED: Injected the service here
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
        user_service: UserServiceDep, # <--- CHANGED: Injected the service here
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