from typing import List, Optional, Annotated
from uuid import UUID, uuid4
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status, Header, Query, File
from sqlalchemy.orm import Session

from src.domain.receipt import ReceiptDTO, ReceiptItemDTO
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
from src.domain.smart_home.enums import LocationType, ExpirationType
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
    try:
        app_logger.info(f"Attempting to add product for user {user_id} in home {home_id}")
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
        app_logger.info(f"Product '{request.name}' added successfully for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            message="Product added successfully",
            data=ProductDTO.from_domain(product)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to add product '{request.name}' for user {user_id} in home {home_id} - {str(e)}")
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
    try:
        app_logger.info(f"Attempting to update quantity for item {item_id} of product {product_id} for user {user_id} in home {home_id}")
        updated_product = await service.update_item_quantity(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id,
            new_quantity=request.new_quantity
        )
        
        if updated_product is None:
            app_logger.info(f"Product completely removed for user {user_id} in home {home_id}")
            return GeneralResponse(status="success", message="Product completely removed", data=None)

        app_logger.info(f"Quantity updated successfully for item {item_id} of product {product_id} for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to update quantity for item {item_id} of product {product_id} for user {user_id} in home {home_id} - {str(e)}")
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
    try:
        app_logger.info(f"Attempting to update expiration date for item {item_id} of product {product_id} for user {user_id} in home {home_id}")
        updated_product = await service.update_item_date(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id,
            new_date=request.new_date
        )
        app_logger.info(f"Expiration date updated successfully for item {item_id} of product {product_id} for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to update expiration date for item {item_id} of product {product_id} for user {user_id} in home {home_id} - {str(e)}")
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
    try:
        app_logger.info(f"Attempting to update location for item {item_id} of product {product_id} for user {user_id} in home {home_id}")
        updated_product = await service.update_item_location(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id,
            new_location=request.location
        )
        app_logger.info(f"Location updated successfully for item {item_id} of product {product_id} for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to update location for item {item_id} of product {product_id} for user {user_id} in home {home_id} - {str(e)}")
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
    try:
        app_logger.info(f"Attempting to update nickname for product {product_id} for user {user_id} in home {home_id}")
        updated_product = await service.update_nickname(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            new_nickname=request.nickname
        )
        app_logger.info(f"Nickname updated successfully for product {product_id} for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        app_logger.warning(f"Failed to update nickname for product {product_id} for user {user_id} in home {home_id} - {str(e)}")
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
    try:
        app_logger.info(f"Attempting to remove item {item_id} of product {product_id} for user {user_id} in home {home_id}")
        result = await service.remove_item(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            item_id=item_id
        )
        
        message = "Item removed" if result else "Product completely removed"
        data = ProductDTO.from_domain(result) if result else None
        app_logger.info(f"Item {item_id} of product {product_id} removed successfully for user {user_id} in home {home_id}")
        return GeneralResponse(status="success", message=message, data=data)
        
    except ValueError as e:
        app_logger.warning(f"Failed to remove item {item_id} of product {product_id} for user {user_id} in home {home_id} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Search & Filter Routes ---

@router.get("/filter/location", response_model=GeneralResponse)
async def filter_by_location(
    location: LocationType,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        app_logger.info(f"Attempting to filter products by location for user {user_id} in home {home_id}")
        # Service returns List[ProductDTO]
        results = await service.filter_by_location(user_id, home_id, location)
        app_logger.info(f"Filtered products by location successfully for user {user_id} in home {home_id}")
        return GeneralResponse(status="success", data=results)
    except ValueError as e:
        app_logger.warning(f"Failed to filter products by location for user {user_id} in home {home_id} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/filter/expiration", response_model=GeneralResponse)
async def filter_by_expiration(
    type: ExpirationType,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        app_logger.info(f"Attempting to filter products by expiration type for user {user_id} in home {home_id}")
        # Service returns List[ProductDTO]
        results = await service.filter_by_expiration_type(user_id, home_id, type)
        app_logger.info(f"Filtered products by expiration type successfully for user {user_id} in home {home_id}")
        return GeneralResponse(status="success", data=results)
    except ValueError as e:
        app_logger.warning(f"Failed to filter products by expiration type for user {user_id} in home {home_id} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/search", response_model=GeneralResponse)
async def search_products(
    query: str,
    service: StockServiceDep,
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        app_logger.info(f"Attempting to search products with query '{query}' for user {user_id} in home {home_id}")
        # Service returns List[Product], so we convert to DTOs
        results = await service.search_product(user_id, home_id, query)
        dtos = [ProductDTO.from_domain(p) for p in results]
        app_logger.info(f"Products searched successfully for user {user_id} in home {home_id}")
        return GeneralResponse(status="success", data=dtos)
    except ValueError as e:
        app_logger.warning(f"Failed to search products with query '{query}' for user {user_id} in home {home_id} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/all", response_model=GeneralResponse)
async def get_all_products(
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        app_logger.info(f"Attempting to retrieve all products for user {user_id} in home {home_id}")
        products = await service.get_home_products(user_id=user_id, home_id=home_id)
        
        products_dtos = [ProductDTO.from_domain(p) for p in products]
        app_logger.info(f"All products retrieved successfully for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            data=products_dtos
        )
    except ValueError as e:
        app_logger.warning(f"Failed to retrieve all products for user {user_id} in home {home_id} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/catalog/search", response_model=GeneralResponse)
async def search_global_catalog_by_name(
    service: StockServiceDep, # <--- Injected Service (Must come before Query with defaults)
    query: str = Query(..., min_length=2, description="Search term (e.g., 'Milk')"),
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):

    try:
        app_logger.info(f"Attempting to search global catalog with query '{query}' for user {user_id} in home {home_id}")
        results = await service.search_product_by_name_external_db(
            user_id=user_id, 
            home_id=home_id, 
            query=query
        )
        
        # Convert Pydantic models to dicts for the JSON response
        data = [item.model_dump() for item in results]
        app_logger.info(f"Global catalog search completed successfully with query '{query}' for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            message=f"Found {len(results)} items",
            data=data
        )
    except ValueError as e:
        app_logger.warning(f"Failed to search global catalog with query '{query}' for user {user_id} in home {home_id} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/catalog/barcode/{barcode}", response_model=GeneralResponse)
async def get_global_product_by_barcode(
    barcode: str,
    service: StockServiceDep, # <--- Injected Service (Must come before Query/Header/Depends)
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Lookup a specific product in the global master catalog by barcode.
    If 'chain' is provided, it tries to find the chain-specific version first.
    """
    try:
        app_logger.info(f"Attempting to search global catalog by barcode '{barcode}' for user {user_id} in home {home_id}")
        item = await service.search_product_by_barcode_external_db(
            user_id=user_id, 
            home_id=home_id, 
            barcode=barcode,
        )
        
        if not item:
            app_logger.info(f"No product found in global catalog with barcode '{barcode}' for user {user_id} in home {home_id}")
            return GeneralResponse(
                status="success", 
                message="Product not found in global catalog", 
                data=None
            )
        app_logger.info(f"Product found in global catalog with barcode '{barcode}' for user {user_id} in home {home_id}")
        return GeneralResponse(
            status="success",
            message="Product found",
            data=item.model_dump()
        )
    except ValueError as e:
        app_logger.warning(f"Failed to search global catalog by barcode '{barcode}' for user {user_id} in home {home_id} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.post("/scan", response_model=GeneralResponse)
async def scan_receipt(
    service: StockServiceDep,
    files: List[UploadFile] = File(...),  
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        app_logger.info(f"Attempting to scan receipt for user {user_id} in home {home_id} with {len(files)} files")
        import tempfile, shutil, os
        from typing import List

        tmp_paths: List[str] = []

        try:
            # 1) save each uploaded file to a temp path
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

            # 2) run scan on all files in ONE logical receipt
            result = await service.scan_receipt(
                user_id=user_id,
                home_id=home_id,
                files_paths=tmp_paths,
            )
            app_logger.info(f"Receipt scanned successfully for user {user_id} in home {home_id} with {len(tmp_paths)} files")
            return GeneralResponse(
                status="success",
                data=result.model_dump(),
            )

        finally:
            # 3) cleanup temp files
            for p in tmp_paths:
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                except Exception as e:
                    app_logger.warning(f"Cleanup error: {e}")

    except Exception as e:
        app_logger.error(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scanning failed: {str(e)}",
        )

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
    try:
        app_logger.info(f"Attempting to add receipt for user {user_id} in home {home_id} with {len(request.items)} items")
        # Assemble the internal ReceiptDTO from Request and Auth data
        receipt_dto = ReceiptDTO(
            id=uuid4(),
            home_id=home_id,
            user_id=user_id,
            chain=request.chain,
            items=[
                ReceiptItemDTO(
                    name=item.name,
                    quantity=item.quantity, # Receipt scanner returns floats
                    barcode=item.barcode,
                    expiration_date=item.expiration_date,
                    unit=item.unit,
                    location=item.location,
                    nickname=item.nickname,
                    weight=item.weight
                ) for item in request.items
            ]
        )
        

        # Process via service which delegates to add_product for upsert logic
        processed_count = await service.add_receipt(receipt_dto)
        app_logger.info(f"Successfully processed receipt for user {user_id} in home {home_id} - {processed_count} items added")
        return GeneralResponse(
            status="success",
            message=f"Successfully added {processed_count} items from receipt",
            data={"added_count": processed_count}
        )
        
    except ValueError as e:
        app_logger.warning(f"Invalid request data for user {user_id} in home {home_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        app_logger.error(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error occurred while processing the receipt: {str(e)}"
        )
