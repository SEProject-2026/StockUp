from fastapi import APIRouter, Depends, HTTPException, status, Header
from uuid import UUID

from src.services.management_service import ManagementService
from src.api.schemas.management_schemas import CreateHomeRequest, HomeDTO
from src.api.schemas.common import GeneralResponse
from src.api.security import get_current_user_id
from src.infrastructure.app_container import AppContainer

router = APIRouter(prefix="/homes", tags=["Home Management"])

management_service = AppContainer.get_management_service()
@router.post("/create", response_model=GeneralResponse)
async def create_home(
    request: CreateHomeRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    try:
        new_home = await management_service.create_home(user_id=user_id, home_name=request.name)
        
        home_dto = HomeDTO.from_domain(new_home)
        
        return GeneralResponse(
            status="success",
            message="Home created successfully",
            data=home_dto
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.get("/my_homes", response_model=GeneralResponse)
async def get_my_homes(
    user_id: UUID = Depends(get_current_user_id),
    service: ManagementService = Depends(AppContainer.get_management_service)
):
    try:

        homes = await service.get_all_homes_for_user(user_id)
        
        homes_dtos = [HomeDTO.from_domain(home) for home in homes]
        
        return GeneralResponse(
            status="success",
            data=homes_dtos
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))