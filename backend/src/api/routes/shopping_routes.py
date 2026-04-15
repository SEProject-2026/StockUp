from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session

from src.infrastructure.db.database import get_db
from src.services.shopping_list_service import ShoppingListService
from src.services.recommendation_service import RecommendationService
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

from src.api.routes.translate_notifications import translate_error
from src.services.management_service import ManagementService

router = APIRouter(prefix="/shopping-lists", tags=["Shopping List"])

# --- Dependency Injection ---
def get_management_service(db: Session = Depends(get_db)) -> ManagementService:
    return AppContainer.get_management_service(db)

ManagementServiceDep = Annotated[ManagementService, Depends(get_management_service)]

def get_shopping_list_service(db: Session = Depends(get_db)) -> ShoppingListService:
    return AppContainer.get_shopping_list_service(db)

def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationService:
    return AppContainer.get_recommendation_service(db)

ShoppingServiceDep = Annotated[ShoppingListService, Depends(get_shopping_list_service)]
RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]

# --- Routes Implementation ---

@router.post("/", response_model=GeneralResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    request: CreateShoppingListRequest, 
    service: ShoppingServiceDep, 
    management_service: ManagementServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} creating list '{request.name}' for home {request.home_id}")
    try:
        # Check if user belongs to home before creating
        # We assume the service or a dedicated validator handles this check
        await management_service.get_home_details(user_id, request.home_id)

        new_list = await service.create_shopping_list(request.home_id, request.name)
        return GeneralResponse(
            status="success", 
            message="List created", 
            data=ShoppingListDTO.model_validate(new_list)
        )
    except (ValueError, PermissionError) as e:
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=translated_message)
    except Exception as e:
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=translated_message)


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
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)


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
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)

@router.get("/{list_id}/recommendations", response_model=GeneralResponse)
async def get_recommendations(
    list_id: UUID,
    shopping_service: ShoppingServiceDep,
    recommendation_service: RecommendationServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} requesting recommendations for list {list_id}")
    try:
        shopping_list = await shopping_service.get_shopping_list(list_id)
        current_items = [item.item_name for item in shopping_list.items] if shopping_list.items else []
        
        recommendations = await recommendation_service.get_recommendations(
            home_id=shopping_list.home_id,
            current_shopping_list_items=current_items,
            max_results=10
        )
        return GeneralResponse(status="success", data=recommendations)
    except ValueError as e:
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)

    
@router.delete("/{list_id}/items/{item_name}", response_model=GeneralResponse)
async def remove_item_from_list(
    list_id: UUID,
    item_name: str,
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Removes a specific item from the shopping list by its name.
    """
    app_logger.info(f"User {user_id} is removing item '{item_name}' from list {list_id}")
    try:
        updated_list = await service.remove_item_from_list(list_id, item_name)
        return GeneralResponse(
            status="success",
            message=f"Item '{item_name}' removed successfully",
            data=ShoppingListDTO.model_validate(updated_list)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to remove item '{item_name}' from list {list_id}: {str(e)}")
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)

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
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)


@router.post("/{list_id}/enter-mode", response_model=GeneralResponse)
async def enter_shopping_mode(
    list_id: UUID, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Activates shopping mode for the specified list.
    """
    app_logger.info(f"User {user_id} is entering shopping mode for list {list_id}")
    try:
        updated_list = await service.enter_shopping_mode(list_id)
        return GeneralResponse(
            status="success", 
            message="Shopping mode activated",
            data=ShoppingListDTO.model_validate(updated_list)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to enter shopping mode for list {list_id}: {str(e)}")
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)

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
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)


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
        translated_message = translate_error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=translated_message)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: UUID, 
    service: ShoppingServiceDep,
    user_id: UUID = Depends(get_current_user_id)
):
    app_logger.info(f"User {user_id} deleting list {list_id}")
    # Ensure authorization before deletion
    await service.delete_shopping_list(list_id)