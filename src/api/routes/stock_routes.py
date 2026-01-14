from typing import List, Optional, Annotated
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Path, status, Header, Query
from sqlalchemy.orm import Session

from src.infrastructure.db.database import get_db
from src.services.stock_service import StockService
from src.api.schemas.product_schemas import (
    ProductDTO, 
    AddProductRequest, 
    UpdateProductQuantityRequest, 
    UpdateProductNicknameRequest,
    UpdateExpirationDateRequest
)
from src.api.schemas.common import GeneralResponse
from src.domain.smart_home.enums import LocationType, ExpirationType
from src.infrastructure.app_container import AppContainer
from src.api.security import get_current_user_id

router = APIRouter(prefix="/stock", tags=["Stock Management"])

# --- Dependency Injection Setup ---

def get_stock_service(db: Session = Depends(get_db)) -> StockService:
    return AppContainer.get_stock_service(db)

StockServiceDep = Annotated[StockService, Depends(get_stock_service)]


# --- Routes ---

@router.post("/add", response_model=GeneralResponse)
async def add_product(
    request: AddProductRequest,
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
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
        
        product_dto = ProductDTO.from_domain(product)
        
        return GeneralResponse(
            status="success",
            message="Product added successfully",
            data=product_dto
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/scan", response_model=GeneralResponse)
async def scan_receipt(
    file: UploadFile = File(...),
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        import tempfile, shutil, os

        suffix = os.path.splitext(file.filename or "")[1] or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        try:
            result = await stock_service.scan_receipt(
                user_id=user_id,
                home_id=home_id,
                file_path=tmp_path,    
            )

            return GeneralResponse(
                status="success",
                data=result.model_dump(),
            )

        finally:
            try:
                os.remove(tmp_path)
            except:
                pass

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scanning failed: {str(e)}",
        )

@router.patch("/{product_id}/quantity", response_model=GeneralResponse)
async def update_quantity(
    product_id: UUID,
    request: UpdateProductQuantityRequest,
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        updated_product = await service.update_date_quantity(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            date=request.expiration_date, 
            new_quantity=request.new_quantity
        )
        
        if updated_product is None:
             return GeneralResponse(status="success", message="Product removed (quantity 0)", data=None)

        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{product_id}/expiration", response_model=GeneralResponse)
async def update_expiration(
    product_id: UUID,
    request: UpdateExpirationDateRequest,
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),

):
    try:
        updated_product = await service.update_expiration_date(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            old_date=request.old_date,
            new_date=request.new_date
        )
        return GeneralResponse(
            status="success",
            data=ProductDTO.from_domain(updated_product)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{product_id}/nickname", response_model=GeneralResponse)
async def update_nickname(
    product_id: UUID,
    request: UpdateProductNicknameRequest,
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}", response_model=GeneralResponse)
async def remove_product(
    product_id: UUID,
    service: StockServiceDep, # <--- Injected Service (Must come before Query with defaults)
    expiration_date: Optional[date]= Query(None), 
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        result = await service.remove_product(
            user_id=user_id,
            home_id=home_id,
            product_id=product_id,
            date=expiration_date
        )
        
        message = "Product quantity reduced" if result else "Product completely removed"
        data = ProductDTO.from_domain(result) if result else None
        
        return GeneralResponse(status="success", message=message, data=data)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Search & Filter Routes (GET) ---

@router.get("/search", response_model=GeneralResponse)
async def search_products(
    query: str,
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        results = await service.search_product(user_id, home_id, query)
        dtos = [ProductDTO.from_domain(p) for p in results]
        
        return GeneralResponse(status="success", data=dtos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/filter/location", response_model=GeneralResponse)
async def filter_by_location(
    location: LocationType,
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        results = await service.filter_by_location(user_id, home_id, location)
        dtos = [ProductDTO.from_domain(p) for p in results]
        return GeneralResponse(status="success", data=dtos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/filter/expiration", response_model=GeneralResponse)
async def filter_by_expiration(
    type: ExpirationType,
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        results = await service.filter_by_expiration_type(user_id, home_id, type)
        return GeneralResponse(status="success", data=results)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/all", response_model=GeneralResponse)
async def get_all_products(
    service: StockServiceDep, # <--- Injected Service
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        products = await service.get_home_products(user_id=user_id, home_id=home_id)
        
        products_dtos = [ProductDTO.from_domain(p) for p in products]
        
        return GeneralResponse(
            status="success",
            data=products_dtos
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.get("/catalog/search", response_model=GeneralResponse)
async def search_global_catalog_by_name(
    service: StockServiceDep, # <--- Injected Service (Must come before Query with defaults)
    query: str = Query(..., min_length=2, description="Search term (e.g., 'Milk')"),
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Search for products in the global master catalog (CSV) by name.
    Useful for autocomplete suggestions when adding a new product.
    """
    try:
        results = await service.search_product_by_name_external_db(
            user_id=user_id, 
            home_id=home_id, 
            query=query
        )
        
        # Convert Pydantic models to dicts for the JSON response
        data = [item.model_dump() for item in results]
        
        return GeneralResponse(
            status="success",
            message=f"Found {len(results)} items",
            data=data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/catalog/barcode/{barcode}", response_model=GeneralResponse)
async def get_global_product_by_barcode(
    barcode: str,
    service: StockServiceDep, # <--- Injected Service (Must come before Query/Header/Depends)
    chain: Optional[str] = Query(None, description="Optional chain context (e.g., 'rami_levi')"),
    home_id: UUID = Header(..., alias="X-Home-ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Lookup a specific product in the global master catalog by barcode.
    If 'chain' is provided, it tries to find the chain-specific version first.
    """
    try:
        item = await service.search_product_by_barcode_external_db(
            user_id=user_id, 
            home_id=home_id, 
            barcode=barcode,
            chain_name=chain
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))