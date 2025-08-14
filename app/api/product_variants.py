from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import ProductVariant, Product, Color, Size
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
    ProductVariantBulkCreate,
    ProductVariantBulkUpdate,
)
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user
from app.models.user import User
from app.utils.helpers import generate_sku

router = APIRouter(prefix="/product-variants", tags=["product-variants"])


@router.get("/product/{product_id}", response_model=ResponseModel)
async def get_product_variants(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all variants for a specific product."""
    try:
        # Check if product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return ResponseModel(success=False, message="Product not found")

        variants = (
            db.query(ProductVariant).filter(ProductVariant.product_id == product_id).all()
        )

        # Add color and size names to response
        variant_responses = []
        for variant in variants:
            variant_data = {
                "id": variant.id,
                "product_id": variant.product_id,
                "color_id": variant.color_id,
                "size_id": variant.size_id,
                "sku": variant.sku,
                "price": float(variant.price),
                "cost_price": float(variant.cost_price) if variant.cost_price else None,
                "stock_quantity": variant.stock_quantity,
                "min_stock_level": variant.min_stock_level,
                "is_active": variant.is_active,
                "created_at": variant.created_at.isoformat() if variant.created_at else None,
                "updated_at": variant.updated_at.isoformat() if variant.updated_at else None,
                "color_name": variant.color.name if variant.color else None,
                "size_name": variant.size.name if variant.size else None,
                "color_hex": variant.color.hex_code if variant.color else None,
            }
            variant_responses.append(variant_data)

        return ResponseModel(
            success=True,
            data=variant_responses,
            message="Product variants retrieved successfully",
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch product variants: {str(e)}")


@router.post("/", response_model=ResponseModel)
async def create_product_variant(
    variant_data: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new product variant."""
    try:
        # Check if product exists
        product = db.query(Product).filter(Product.id == variant_data.product_id).first()
        if not product:
            return ResponseModel(success=False, message="Product not found")

        # Check if color exists
        color = db.query(Color).filter(Color.id == variant_data.color_id).first()
        if not color:
            return ResponseModel(success=False, message="Color not found")

        # Check if size exists
        size = db.query(Size).filter(Size.id == variant_data.size_id).first()
        if not size:
            return ResponseModel(success=False, message="Size not found")

        # Check if variant already exists
        existing_variant = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.product_id == variant_data.product_id,
                ProductVariant.color_id == variant_data.color_id,
                ProductVariant.size_id == variant_data.size_id,
            )
            .first()
        )
        if existing_variant:
            return ResponseModel(
                success=False, 
                message="Product variant with this color and size combination already exists"
            )

        # Generate SKU if not provided
        if not variant_data.sku:
            variant_data.sku = generate_sku()

        # Check if SKU already exists
        existing_sku = (
            db.query(ProductVariant).filter(ProductVariant.sku == variant_data.sku).first()
        )
        if existing_sku:
            return ResponseModel(
                success=False, 
                message="Product variant with this SKU already exists"
            )

        variant = ProductVariant(**variant_data.dict())
        db.add(variant)
        db.commit()
        db.refresh(variant)

        # Add color and size names to response
        variant_response = ProductVariantResponse.from_orm(variant)
        variant_response.color_name = variant.color.name if variant.color else None
        variant_response.size_name = variant.size.name if variant.size else None

        return ResponseModel(
            success=True,
            data=variant_response,
            message="Product variant created successfully",
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to create product variant: {str(e)}")


@router.post("/bulk", response_model=ResponseModel)
async def create_product_variants_bulk(
    bulk_data: ProductVariantBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create multiple product variants for a product."""
    try:
        # Check if product exists
        product = db.query(Product).filter(Product.id == bulk_data.product_id).first()
        if not product:
            return ResponseModel(success=False, message="Product not found")
        
        color_ids = [variant.color_id for variant in bulk_data.variants]
        size_ids = [variant.size_id for variant in bulk_data.variants]

        # Check if colors exist
        colors = db.query(Color).filter(Color.id.in_(color_ids)).all()
        if len(colors) != len(set(color_ids)):
            return ResponseModel(success=False, message="One or more colors not found")

        # Check if sizes exist
        sizes = db.query(Size).filter(Size.id.in_(size_ids)).all()
        if len(sizes) != len(set(size_ids)):
            return ResponseModel(success=False, message="One or more sizes not found")

        created_variants = []

        for variant_data in bulk_data.variants:
            # Check if variant already exists
            existing_variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.product_id == bulk_data.product_id,
                    ProductVariant.color_id == variant_data.color_id,
                    ProductVariant.size_id == variant_data.size_id,
                )
                .first()
            )

            if not existing_variant:
                # Generate unique SKU if not provided
                sku = variant_data.sku if variant_data.sku else generate_sku()
                while (
                    db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
                ):
                    sku = generate_sku()

                variant = ProductVariant(
                    product_id=bulk_data.product_id,
                    color_id=variant_data.color_id,
                    size_id=variant_data.size_id,
                    sku=sku,
                    price=variant_data.price,
                    cost_price=variant_data.cost_price,
                    stock_quantity=variant_data.stock_quantity,
                    min_stock_level=variant_data.min_stock_level,
                )
                db.add(variant)
                created_variants.append(variant)

        db.commit()

        # Refresh all created variants
        for variant in created_variants:
            db.refresh(variant)

        # Prepare response
        variant_responses = []
        for variant in created_variants:
            variant_data = {
                "id": variant.id,
                "product_id": variant.product_id,
                "color_id": variant.color_id,
                "size_id": variant.size_id,
                "sku": variant.sku,
                "price": float(variant.price),
                "cost_price": float(variant.cost_price) if variant.cost_price else None,
                "stock_quantity": variant.stock_quantity,
                "min_stock_level": variant.min_stock_level,
                "is_active": variant.is_active,
                "created_at": variant.created_at.isoformat() if variant.created_at else None,
                "updated_at": variant.updated_at.isoformat() if variant.updated_at else None,
                "color_name": variant.color.name if variant.color else None,
                "size_name": variant.size.name if variant.size else None,
            }
            variant_responses.append(variant_data)

        return ResponseModel(
            success=True,
            data=variant_responses,
            message=f"Created {len(created_variants)} product variants successfully",
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to create product variants: {str(e)}")


@router.put("/{variant_id}", response_model=ResponseModel)
async def update_product_variant(
    variant_id: int,
    variant_data: ProductVariantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a product variant."""
    try:
        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            return ResponseModel(success=False, message="Product variant not found")

        # Check if new color exists
        if variant_data.color_id:
            color = db.query(Color).filter(Color.id == variant_data.color_id).first()
            if not color:
                return ResponseModel(success=False, message="Color not found")

        # Check if new size exists
        if variant_data.size_id:
            size = db.query(Size).filter(Size.id == variant_data.size_id).first()
            if not size:
                return ResponseModel(success=False, message="Size not found")

        # Check if new combination already exists
        if variant_data.color_id or variant_data.size_id:
            new_color_id = variant_data.color_id or variant.color_id
            new_size_id = variant_data.size_id or variant.size_id

            existing_variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.product_id == variant.product_id,
                    ProductVariant.color_id == new_color_id,
                    ProductVariant.size_id == new_size_id,
                    ProductVariant.id != variant_id,
                )
                .first()
            )
            if existing_variant:
                return ResponseModel(
                    success=False,
                    message="Product variant with this color and size combination already exists"
                )

        # Check if new SKU already exists
        if variant_data.sku and variant_data.sku != variant.sku:
            existing_sku = (
                db.query(ProductVariant)
                .filter(ProductVariant.sku == variant_data.sku)
                .first()
            )
            if existing_sku:
                return ResponseModel(
                    success=False,
                    message="Product variant with this SKU already exists"
                )

        for field, value in variant_data.dict(exclude_unset=True).items():
            setattr(variant, field, value)

        db.commit()
        db.refresh(variant)

        # Add color and size names to response
        variant_response = ProductVariantResponse.from_orm(variant)
        variant_response.color_name = variant.color.name if variant.color else None
        variant_response.size_name = variant.size.name if variant.size else None

        return ResponseModel(
            success=True,
            data=variant_response,
            message="Product variant updated successfully",
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to update product variant: {str(e)}")


@router.delete("/{variant_id}", response_model=ResponseModel)
async def delete_product_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product variant."""
    try:
        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            return ResponseModel(success=False, message="Product variant not found")

        db.delete(variant)
        db.commit()

        return ResponseModel(success=True, message="Product variant deleted successfully")
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to delete product variant: {str(e)}")
