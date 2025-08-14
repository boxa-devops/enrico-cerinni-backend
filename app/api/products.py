from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.product_service import ProductService
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductFilter,
    PaginatedProductResponse,
)
from app.schemas.product_variant import ProductVariantResponse
from app.schemas.common import ResponseModel, PaginatedResponse
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/barcode/{barcode}", response_model=ResponseModel)
async def scan_barcode(barcode: str, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    product = product_service.get_product_by_variant_sku(barcode)
    if not product:
        return ResponseModel(success=False, message="Product not found")
    
    # Prepare variants data
    variants_data = []
    if hasattr(product, 'variants') and product.variants:
        for variant in product.variants:
            variants_data.append({
                'id': variant.id,
                'product_id': variant.product_id,
                'color_id': variant.color_id,
                'size_id': variant.size_id,
                'sku': variant.sku,
                'price': float(variant.price),
                'cost_price': float(variant.cost_price) if variant.cost_price else None,
                'stock_quantity': variant.stock_quantity,
                'min_stock_level': variant.min_stock_level,
                'is_active': variant.is_active,
                'created_at': variant.created_at.isoformat() if variant.created_at else None,
                'updated_at': variant.updated_at.isoformat() if variant.updated_at else None,
                'color_name': variant.color.name if variant.color else None,
                'size_name': variant.size.name if variant.size else None,
                'color_hex': variant.color.hex_code if variant.color else None,
            })
    
    return ResponseModel(success=True, data=ProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        brand_id=product.brand_id,
        season_id=product.season_id,
        category_id=product.category_id,
        image_url=product.image_url,
        created_at=product.created_at.isoformat(),
        updated_at=product.updated_at.isoformat() if product.updated_at else None,
        brand_name=product.brand.name if product.brand else None,
        season_name=product.season.name if product.season else None,
        category_name=product.category.name if product.category else None,
        variants=variants_data,
    ))

@router.get("/", response_model=ResponseModel)
async def get_products(
    name: Optional[str] = Query(None, description="Filter by product name"),
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    season_id: Optional[int] = Query(None, description="Filter by season ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(
        None, description="Search by name, brand, or description"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = ProductFilter(
        name=name,
        brand_id=brand_id,
        season_id=season_id,
        category_id=category_id,
        search=search,
        page=page,
        size=size,
    )

    product_service = ProductService(db)
    products, pagination = product_service.get_products(filters)

    product_responses = []
    for product in products:
        # Prepare variants data
        variants_data = []
        if hasattr(product, 'variants') and product.variants:
            for variant in product.variants:
                variants_data.append({
                    'id': variant.id,
                    'product_id': variant.product_id,
                    'color_id': variant.color_id,
                    'size_id': variant.size_id,
                    'sku': variant.sku,
                    'price': float(variant.price),
                    'cost_price': float(variant.cost_price) if variant.cost_price else None,
                    'stock_quantity': variant.stock_quantity,
                    'min_stock_level': variant.min_stock_level,
                    'is_active': variant.is_active,
                    'created_at': variant.created_at.isoformat() if variant.created_at else None,
                    'updated_at': variant.updated_at.isoformat() if variant.updated_at else None,
                    'color_name': variant.color.name if variant.color else None,
                    'size_name': variant.size.name if variant.size else None,
                    'color_hex': variant.color.hex_code if variant.color else None,
                })

        product_responses.append(
            ProductResponse(
                id=product.id,
                sku=product.sku,
                name=product.name,
                description=product.description,
                brand_id=product.brand_id,
                season_id=product.season_id,
                category_id=product.category_id,
                image_url=product.image_url,
                created_at=product.created_at.isoformat(),
                updated_at=product.updated_at.isoformat()
                if product.updated_at
                else None,
                brand_name=product.brand.name if product.brand else None,
                season_name=product.season.name if product.season else None,
                category_name=product.category.name if product.category else None,
                variants=variants_data,
            )
        )

    return ResponseModel(
        success=True,
        data=PaginatedProductResponse(items=product_responses, pagination=pagination),
        message="Products retrieved successfully",
    )


@router.get("/{product_id}", response_model=ResponseModel)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific product by ID."""
    product_service = ProductService(db)
    product = product_service.get_product(product_id)

    if not product:
        return ResponseModel(success=False, message="Product not found")

    # Prepare variants data
    variants_data = []
    if hasattr(product, 'variants') and product.variants:
        for variant in product.variants:
            variants_data.append({
                'id': variant.id,
                'product_id': variant.product_id,
                'color_id': variant.color_id,
                'size_id': variant.size_id,
                'sku': variant.sku,
                'price': float(variant.price),
                'cost_price': float(variant.cost_price) if variant.cost_price else None,
                'stock_quantity': variant.stock_quantity,
                'min_stock_level': variant.min_stock_level,
                'is_active': variant.is_active,
                'created_at': variant.created_at.isoformat() if variant.created_at else None,
                'updated_at': variant.updated_at.isoformat() if variant.updated_at else None,
                'color_name': variant.color.name if variant.color else None,
                'size_name': variant.size.name if variant.size else None,
                'color_hex': variant.color.hex_code if variant.color else None,
            })

    return ResponseModel(
        success=True,
        data=ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            brand_id=product.brand_id,
            season_id=product.season_id,
            category_id=product.category_id,
            image_url=product.image_url,
            created_at=product.created_at.isoformat(),
            updated_at=product.updated_at.isoformat() if product.updated_at else None,
            brand_name=product.brand.name if product.brand else None,
            season_name=product.season.name if product.season else None,
            category_name=product.category.name if product.category else None,
            variants=variants_data,
        ),
        message="Product retrieved successfully",
    )


@router.post("/", response_model=ResponseModel)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new product."""
    product_service = ProductService(db)
    try:
        product = product_service.create_product(product_data)
        return ResponseModel(
            success=True,
            data=ProductResponse(
                id=product.id,
                sku=product.sku,
                name=product.name,
                description=product.description,
                brand_id=product.brand_id,
                season_id=product.season_id,
                category_id=product.category_id,
                image_url=product.image_url,
                created_at=product.created_at.isoformat(),
                updated_at=product.updated_at.isoformat()
                if product.updated_at
                else None,
                brand_name=product.brand.name if product.brand else None,
                season_name=product.season.name if product.season else None,
                category_name=product.category.name if product.category else None,
            ),
            message="Product created successfully",
        )
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.put("/{product_id}", response_model=ResponseModel)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a product."""
    product_service = ProductService(db)
    product = product_service.update_product(product_id, product_data)

    if not product:
        return ResponseModel(success=False, message="Product not found")

    return ResponseModel(
        success=True,
        data=ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            brand_id=product.brand_id,
            season_id=product.season_id,
            category_id=product.category_id,
            image_url=product.image_url,
            created_at=product.created_at.isoformat(),
            updated_at=product.updated_at.isoformat() if product.updated_at else None,
            brand_name=product.brand.name if product.brand else None,
            season_name=product.season.name if product.season else None,
            category_name=product.category.name if product.category else None,
        ),
        message="Product updated successfully",
    )


@router.delete("/{product_id}", response_model=ResponseModel)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product."""
    product_service = ProductService(db)
    success = product_service.delete_product(product_id)

    if not success:
        return ResponseModel(success=False, message="Product not found")

    return ResponseModel(success=True, message="Product deleted successfully")



