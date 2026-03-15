from typing import List, Optional, Annotated
from uuid import UUID, uuid4
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status, Header, Query, File
from sqlalchemy.orm import Session

from src.domain.receipt.receipt import ReceiptDTO, ReceiptItemDTO
from src.infrastructure.db.database import get_db
from src.services.stock_service import StockService
from src.api.schemas.product_schemas import (
    AddReceiptRequest,
    ProductDTO, 
    AddProductRequest,
    UpdateItemLocationRequest, 
    UpdateItemQuantityRequest, 
    UpdateItemExpirationRequest,
    UpdateProductNicknameRequest
)
from src.api.schemas.common import GeneralResponse
from src.domain.enums import LocationType, ExpirationType
from src.infrastructure.app_container import AppContainer
from src.api.security import get_current_user_id
from src.infrastructure.logger import app_logger

router = APIRouter(prefix="/stock", tags=["Stock Management"])

# --- Dependency Injection ---
def get_stock_service(db: Session = Depends(get_db)) -> StockService:
    return AppContainer.get_stock_service(db)

StockServiceDep = Annotated[StockService, Depends(get_stock_service)]

# --- Routes ---

@router.post("/add", response_model=GeneralResponse)
async def add_product(
    request: AddProductRequest,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    app_logger.info(f"Add product request received from user {user_id} for home {home_id}")
    try:
        product = await service.add_product(
            name=request.name,
            user_id=user_id,
            home_id=home_id,
            quantity=request.quantity,
            barcode=request.barcode,
            expiration_date=request.expiration_date,
            location=request.location,
            nickname=request.nickname
        )
        return GeneralResponse(
            status="success",
            message="Product added successfully",
            data=ProductDTO.from_domain(product)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to add product for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{product_id}/items/{item_id}/quantity", response_model=GeneralResponse)
async def update_item_quantity(
    product_id: UUID,
    item_id: UUID,
    request: UpdateItemQuantityRequest,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Updates the quantity of a specific item batch."""
    app_logger.info(f"Quantity update request received for item {item_id} from user {user_id}")
    try:
        updated_product = await service.update_item_quantity(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id,
            new_quantity=request.new_quantity
        )
        
        if updated_product is None:
            return GeneralResponse(status="success", message="Product completely removed", data=None)

        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Quantity update failed for item {item_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{product_id}/items/{item_id}/expiration", response_model=GeneralResponse)
async def update_item_expiration(
    product_id: UUID,
    item_id: UUID,
    request: UpdateItemExpirationRequest,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Updates the expiration date of a specific item batch."""
    app_logger.info(f"Expiration update request received for item {item_id} from user {user_id}")
    try:
        updated_product = await service.update_item_date(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id,
            new_date=request.new_date
        )
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Expiration update failed for item {item_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{product_id}/items/{item_id}/location", response_model=GeneralResponse)
async def update_item_location(
    product_id: UUID,
    item_id: UUID,
    request: UpdateItemLocationRequest,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Moves an item to a new location."""
    app_logger.info(f"Location update request received for item {item_id} from user {user_id}")
    try:
        updated_product = await service.update_item_location(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id,
            new_location=request.location
        )
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Location update failed for item {item_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{product_id}/nickname", response_model=GeneralResponse)
async def update_nickname(
    product_id: UUID,
    request: UpdateProductNicknameRequest,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Updates the nickname of the Product aggregate."""
    app_logger.info(f"Nickname update request received for product {product_id} from user {user_id}")
    try:
        updated_product = await service.update_nickname(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            new_nickname=request.nickname
        )
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Nickname update failed for product {product_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}/items/{item_id}", response_model=GeneralResponse)
async def remove_item(
    product_id: UUID,
    item_id: UUID,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Removes a specific item. If it's the last item, the Product is deleted."""
    app_logger.info(f"Item removal request received for item {item_id} from user {user_id}")
    try:
        result = await service.remove_item(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id
        )
        
        message = "Item removed" if result else "Product completely removed"
        data = ProductDTO.from_domain(result) if result else None
        
        return GeneralResponse(status="success", message=message, data=data)
        
    except ValueError as e:
        app_logger.warning(f"Item removal failed for item {item_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Search & Filter Routes ---

@router.get("/filter/location", response_model=GeneralResponse)
async def filter_by_location(
    location: LocationType,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    app_logger.info(f"Filter by location ({location}) request received from user {user_id}")
    try:
        results = await service.filter_by_location(user_id, home_id, location)
        return GeneralResponse(status="success", data=results)
    except ValueError as e:
        app_logger.warning(f"Filter by location failed for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/filter/expiration", response_model=GeneralResponse)
async def filter_by_expiration(
    type: ExpirationType,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    app_logger.info(f"Filter by expiration ({type}) request received from user {user_id}")
    try:
        results = await service.filter_by_expiration_type(user_id, home_id, type)
        return GeneralResponse(status="success", data=results)
    except ValueError as e:
        app_logger.warning(f"Filter by expiration failed for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/search", response_model=GeneralResponse)
async def search_products(
    query: str,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    app_logger.info(f"Search products request received from user {user_id} with query '{query}'")
    try:
        results = await service.search_product(user_id, home_id, query)
        dtos = [ProductDTO.from_domain(p) for p in results]
        return GeneralResponse(status="success", data=dtos)
    except ValueError as e:
        app_logger.warning(f"Search products failed for query '{query}' - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/all", response_model=GeneralResponse)
async def get_all_products(
    service: StockServiceDep, 
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    app_logger.info(f"Get all products request received from user {user_id} for home {home_id}")
    try:
        products = await service.get_home_products(user_id=user_id, home_id=home_id)
        products_dtos = [ProductDTO.from_domain(p) for p in products]
        return GeneralResponse(
            status="success",
            data=products_dtos
        )
    except ValueError as e:
        app_logger.warning(f"Get all products failed for user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/catalog/search", response_model=GeneralResponse)
async def search_global_catalog_by_name(
    service: StockServiceDep, 
    query: str = Query(..., min_length=2, description="Search term (e.g., 'Milk')"),
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    app_logger.info(f"Global catalog search request from user {user_id} with query '{query}'")
    try:
        results = await service.search_product_by_name_external_db(
            user_id=user_id, 
            home_id=home_id, 
            query=query
        )
        data = [item.model_dump() for item in results]
        return GeneralResponse(
            status="success",
            message=f"Found {len(results)} items",
            data=data
        )
    except ValueError as e:
        app_logger.warning(f"Global catalog search failed for query '{query}' - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/catalog/barcode/{barcode}", response_model=GeneralResponse)
async def get_global_product_by_barcode(
    barcode: str,
    service: StockServiceDep, 
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Lookup a specific product in the global master catalog by barcode.
    """
    app_logger.info(f"Global catalog barcode lookup request from user {user_id} for barcode '{barcode}'")
    try:
        item = await service.search_product_by_barcode_external_db(
            user_id=user_id, 
            home_id=home_id, 
            barcode=barcode,
        )
        
        if not item:
            return GeneralResponse(
                status="success", 
                message="Product not found in global catalog", 
                data=None
            )
            
        return GeneralResponse(
            status="success",
            message="Product found",
            data=item.model_dump()
        )
    except ValueError as e:
        app_logger.warning(f"Barcode lookup failed for '{barcode}' - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.post("/scan", response_model=GeneralResponse)
async def scan_receipt(
    service: StockServiceDep,
    files: List[UploadFile] = File(...),  
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    app_logger.info(f"Receipt scan request received from user {user_id} with {len(files)} files")
    import tempfile, shutil, os

    tmp_paths: List[str] = []

    try:
        for f in files:
            suffix = os.path.splitext(f.filename or "")[1] or ".bin"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp_path = tmp.name
                shutil.copyfileobj(f.file, tmp)
            try:
                await f.close()
            except Exception:
                pass
            tmp_paths.append(tmp_path)

        result = await service.scan_receipt(
            user_id=user_id,
            home_id=home_id,
            files_paths=tmp_paths,
        )
        
        return GeneralResponse(
            status="success",
            data=result.model_dump(),
        )

    except Exception as e:
        # Unexpected server error during scanning process
        app_logger.error(f"Receipt scanning process failed critically - Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scanning failed: {str(e)}",
        )
    finally:
        for p in tmp_paths:
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception as e:
                # Warning is perfect here: Cleanup failed, but it doesn't break the user's flow
                app_logger.warning(f"Failed to clean up temporary file {p} - {e}")


@router.post("/add-receipt", response_model=GeneralResponse)
async def add_receipt(
    request: AddReceiptRequest,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Accepts confirmed receipt items from the client and adds them to inventory.
    """
    app_logger.info(f"Add receipt request received from user {user_id} with {len(request.items)} items")
    try:
        receipt_dto = ReceiptDTO(
            id=uuid4(),
            home_id=home_id,
            user_id=user_id,
            chain=request.chain,
            items=[
                ReceiptItemDTO(
                    name=item.name,
                    quantity=item.quantity, 
                    barcode=item.barcode,
                    expiration_date=item.expiration_date,
                    unit=item.unit,
                    location=item.location,
                    nickname=item.nickname,
                    weight=item.weight
                ) for item in request.items
            ]
        )
        
        processed_count = await service.add_receipt(receipt_dto)
        
        return GeneralResponse(
            status="success",
            message=f"Successfully added {processed_count} items from receipt",
            data={"added_count": processed_count}
        )
        
    except ValueError as e:
        app_logger.warning(f"Invalid receipt data submitted by user {user_id} - Reason: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        app_logger.error(f"Critical error while processing receipt for user {user_id} - Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error occurred while processing the receipt: {str(e)}"
        )