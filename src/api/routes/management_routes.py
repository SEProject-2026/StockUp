from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Header
from uuid import UUID
from sqlalchemy.orm import Session

from src.infrastructure.db.database import get_db
from src.services.management_service import ManagementService
from src.api.schemas.management_schemas import AnswerJoinRequest, CreateHomeRequest, HomeDTO, JoinHomeRequest, UpdateExpirationRangeRequest, UpdateHomeHeadRequest
from src.api.schemas.common import GeneralResponse
from src.api.security import get_current_user_id
from src.infrastructure.app_container import AppContainer
from src.infrastructure.logger import app_logger  # <--- Added logger import

router = APIRouter(prefix="/homes", tags=["Home Management"])

# --- Dependency Injection Setup ---

def get_management_service(db: Session = Depends(get_db)) -> ManagementService:
    return AppContainer.get_management_service(db)

ManagementServiceDep = Annotated[ManagementService, Depends(get_management_service)]


# --- Routes ---

@router.post("/create", response_model=GeneralResponse)
async def create_home(
    request: CreateHomeRequest,
    service: ManagementServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Create home request received from user {user_id}")
    try:
        new_home = await service.create_home(user_id=user_id, home_name=request.name)
        home_dto = HomeDTO.from_domain(new_home)
        
        return GeneralResponse(
            status="success",
            message="Home created successfully",
            data=home_dto
        )
    except ValueError as e:
        app_logger.warning(f"Failed to create home for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.get("/my_homes", response_model=GeneralResponse)
async def get_my_homes(
    service: ManagementServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Get my homes request received from user {user_id}")
    try:
        homes = await service.get_all_homes_for_user(user_id)
        homes_dtos = [HomeDTO.from_domain(home) for home in homes]
        
        return GeneralResponse(
            status="success",
            data=homes_dtos
        )
    except ValueError as e:
        app_logger.warning(f"Failed to get homes for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/{home_id}/join_code", response_model=GeneralResponse)
async def view_home_code(
    home_id: UUID,
    service: ManagementServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"View join code request received from user {user_id} for home {home_id}")
    try:
        code = await service.view_home_code(user_id, home_id)
        return GeneralResponse(status="success", data={"join_code": code})
    except (ValueError, PermissionError) as e:
        app_logger.warning(f"View join code failed for user {user_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/join", response_model=GeneralResponse)
async def join_home(
    request: JoinHomeRequest,
    service: ManagementServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Join home request received from user {user_id} with code '{request.home_code}'")
    try:
        await service.join_home(user_id, request.home_code)
        return GeneralResponse(status="success", message="Join request sent successfully")
    except ValueError as e:
        app_logger.warning(f"Join home failed for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{home_id}/answer_request", response_model=GeneralResponse)
async def answer_join_request(
    home_id: UUID,
    request: AnswerJoinRequest,
    service: ManagementServiceDep,
    head_user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Answer join request received from head user {head_user_id} for user {request.user_id} in home {home_id}")
    try:
        home = await service.answer_join_request(home_id, head_user_id, request.user_id, request.approved)
        return GeneralResponse(status="success", data=HomeDTO.from_domain(home))
    except (ValueError, PermissionError) as e:
        app_logger.warning(f"Answer join request failed for head user {head_user_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{home_id}/members/{target_user_id}", response_model=GeneralResponse)
async def remove_member(
    home_id: UUID,
    target_user_id: UUID,
    service: ManagementServiceDep,
    head_user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Remove member request received from head user {head_user_id} for target user {target_user_id} in home {home_id}")
    try:
        home = await service.remove_member(head_user_id, home_id, target_user_id)
        return GeneralResponse(status="success", data=HomeDTO.from_domain(home))
    except (ValueError, PermissionError) as e:
        app_logger.warning(f"Remove member failed for head user {head_user_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{home_id}/leave", response_model=GeneralResponse)
async def leave_home(
    home_id: UUID,
    service: ManagementServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Leave home request received from user {user_id} for home {home_id}")
    try:
        await service.leave_home(user_id, home_id)
        return GeneralResponse(status="success", message="Left home successfully")
    except (ValueError, PermissionError) as e:
        app_logger.warning(f"Leave home failed for user {user_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{home_id}/switch_head", response_model=GeneralResponse)
async def switch_home_head(
    home_id: UUID,
    request: UpdateHomeHeadRequest,
    service: ManagementServiceDep,
    current_head_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Switch home head request received from current head {current_head_id} in home {home_id}")
    try:
        home = await service.switch_home_head(current_head_id, home_id, request.new_head_id)
        return GeneralResponse(status="success", data=HomeDTO.from_domain(home))
    except (ValueError, PermissionError) as e:
        app_logger.warning(f"Switch home head failed for current head {current_head_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{home_id}", response_model=GeneralResponse)
async def delete_home(
    home_id: UUID,
    service: ManagementServiceDep,
    head_user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Delete home request received from head user {head_user_id} for home {home_id}")
    try:
        await service.delete_home(head_user_id, home_id)
        return GeneralResponse(status="success", message="Home deleted successfully")
    except (ValueError, PermissionError) as e:
        app_logger.warning(f"Delete home failed for head user {head_user_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{home_id}/details", response_model=GeneralResponse)
async def get_home_details(
    home_id: UUID,
    service: ManagementServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Get home details request received from user {user_id} for home {home_id}")
    try:
        details = await service.get_home_details(user_id, home_id)
        return GeneralResponse(status="success", data=details)
    except ValueError as e:
        app_logger.warning(f"Get home details failed for user {user_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    

@router.patch("/{home_id}/expiration_range", response_model=GeneralResponse)
async def update_expiration_range(
    home_id: UUID,
    request: UpdateExpirationRangeRequest,
    service: ManagementServiceDep,
    head_user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Update expiration range request received from head user {head_user_id} for home {home_id}")
    try:
        updated_home = await service.update_expiration_range(
            head_user_id=head_user_id, 
            home_id=home_id, 
            new_range=request.new_range
        )
        
        return GeneralResponse(
            status="success",
            message="Expiration range updated successfully",
            data=HomeDTO.from_domain(updated_home)
        )
    except PermissionError as e:
        app_logger.warning(f"Expiration range update forbidden for user {head_user_id} in home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        app_logger.warning(f"Expiration range update failed for home {home_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/{home_id}/join_requests", response_model=GeneralResponse)
async def get_join_requests(
    home_id: UUID,
    service: ManagementServiceDep,
    head_user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"Get join requests received from head user {head_user_id} for home {home_id}")
    try:
        # The service returns a dict mapping UUIDs to Names
        requests_data = await service.get_join_requests(head_user_id, home_id)
        
        return GeneralResponse(
            status="success",
            message="Join requests retrieved successfully",
            data=requests_data
        )
    except (ValueError, PermissionError) as e:
        app_logger.warning(f"Failed to get join requests for home {home_id} - Reason: {str(e)}")
        # If the user is not the head of the house, return 403 Forbidden
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))