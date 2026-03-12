from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session

from src.infrastructure.db.database import get_db
from src.services.shopping_list_service import ShoppingListService
from src.api.schemas.shopping_schemas import (
    ShoppingListDTO, 
    CreateShoppingListRequest, 
    AddItemRequest, 
    UpdateQuantityRequest,
    ExitModeRequest
)
from src.api.schemas.common import GeneralResponse
from src.api.security import get_current_user_id
from src.infrastructure.app_container import AppContainer
from src.infrastructure.logger import app_logger

router = APIRouter(prefix="/shopping-lists", tags=["Shopping List"])

# --- Dependency Injection ---

def get_shopping_list_service(db: Session = Depends(get_db)) -> ShoppingListService:
    return AppContainer.get_shopping_list_service(db)

ShoppingServiceDep = Annotated[ShoppingListService, Depends(get_shopping_list_service)]

# --- Routes Implementation ---

@router.post("/", response_model=GeneralResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    request: CreateShoppingListRequest, 
    service: ShoppingServiceDep, 
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} creating list '{request.name}' for home {request.home_id}")
    try:
        # Check if user belongs to home before creating
        # We assume the service or a dedicated validator handles this check
        new_list = await service.create_shopping_list(request.home_id, request.name)
        return GeneralResponse(
            status="success", 
            message="List created", 
            data=ShoppingListDTO.model_validate(new_list)
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/home/{home_id}", response_model=GeneralResponse)
async def get_home_lists(
    home_id: UUID, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} accessing lists for home {home_id}")
    # Authorization check should happen here or inside the service
    lists = await service.get_all_shopping_lists_by_home(home_id)
    return GeneralResponse(status="success", data=[ShoppingListDTO.model_validate(l) for l in lists])


@router.get("/{list_id}", response_model=GeneralResponse)
async def get_list(
    list_id: UUID, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    try:
        shopping_list = await service.get_shopping_list(list_id)
        # Verify user has access to the home associated with this list
        return GeneralResponse(status="success", data=ShoppingListDTO.model_validate(shopping_list))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{list_id}/items", response_model=GeneralResponse)
async def add_item(
    list_id: UUID, 
    request: AddItemRequest, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} adding item to list {list_id}")
    try:
        updated = await service.add_item_to_list(
            list_id, request.item_name, request.quantity, request.location
        )
        return GeneralResponse(status="success", data=ShoppingListDTO.model_validate(updated))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{list_id}/items/{item_name}/quantity", response_model=GeneralResponse)
async def update_quantity(
    list_id: UUID, 
    item_name: str, 
    request: UpdateQuantityRequest, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    try:
        updated = await service.update_item_quantity(list_id, item_name, request.new_quantity)
        return GeneralResponse(status="success", data=ShoppingListDTO.model_validate(updated))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{list_id}/items/{item_name}/check", response_model=GeneralResponse)
async def check_bought(
    list_id: UUID, 
    item_name: str, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    try:
        updated = await service.check_item_as_bought(list_id, item_name)
        return GeneralResponse(status="success", data=ShoppingListDTO.model_validate(updated))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{list_id}/exit-mode", response_model=GeneralResponse)
async def exit_mode(
    list_id: UUID, 
    request: ExitModeRequest, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} finishing shopping for list {list_id}")
    try:
        updated = await service.exit_shopping_mode(list_id, clear=request.clear)
        return GeneralResponse(status="success", data=ShoppingListDTO.model_validate(updated))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: UUID, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} deleting list {list_id}")
    # Ensure authorization before deletion
    await service.delete_shopping_list(list_id)