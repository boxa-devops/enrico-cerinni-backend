from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, select
from typing import List, Optional, Tuple
from decimal import Decimal
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.category import Category
from app.models.brand import Brand
from app.models.season import Season
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductFilter,
)
from app.utils.helpers import generate_sku, paginate_query, calculate_pagination_info
from fastapi import HTTPException, status


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        # Generate SKU if not provided
        if not product_data.sku:
            product_data.sku = generate_sku()

        # Check if SKU already exists
        existing_product = (
            self.db.query(Product).filter(Product.sku == product_data.sku).first()
        )
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this SKU already exists",
            )

        # Validate category if provided
        if product_data.category_id:
            category = (
                self.db.query(Category)
                .filter(Category.id == product_data.category_id)
                .first()
            )
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found"
                )

        # Validate brand if provided
        if product_data.brand_id:
            brand = (
                self.db.query(Brand).filter(Brand.id == product_data.brand_id).first()
            )
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Brand not found"
                )

        # Validate season if provided
        if product_data.season_id:
            season = (
                self.db.query(Season)
                .filter(Season.id == product_data.season_id)
                .first()
            )
            if not season:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Season not found"
                )

        db_product = Product(**product_data.dict())
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_products(self, filters: ProductFilter) -> Tuple[List[Product], dict]:
        query = self.db.query(Product).options(joinedload(Product.variants))

        if filters.name:
            query = query.filter(Product.name.ilike(f"%{filters.name}%"))

        if filters.brand_id:
            query = query.filter(Product.brand_id == filters.brand_id)

        if filters.season_id:
            query = query.filter(Product.season_id == filters.season_id)

        if filters.category_id:
            query = query.filter(Product.category_id == filters.category_id)

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term),
                    ProductVariant.sku.ilike(search_term)
                )
            )

        # Apply pagination
        total = query.count()
        paginated_query = paginate_query(query, filters.page, filters.size)
        products = paginated_query.all()
        
        pagination_info = calculate_pagination_info(total, filters.page, filters.size)
        return products, pagination_info

    def update_product(
        self, product_id: int, product_data: ProductUpdate
    ) -> Optional[Product]:
        """Update a product."""
        product = self.get_product(product_id)
        if not product:
            return None

        # Validate category if provided
        if product_data.category_id:
            category = (
                self.db.query(Category)
                .filter(Category.id == product_data.category_id)
                .first()
            )
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found"
                )

        # Validate brand if provided
        if product_data.brand_id:
            brand = (
                self.db.query(Brand).filter(Brand.id == product_data.brand_id).first()
            )
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Brand not found"
                )

        # Validate season if provided
        if product_data.season_id:
            season = (
                self.db.query(Season)
                .filter(Season.id == product_data.season_id)
                .first()
            )
            if not season:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Season not found"
                )

        # Update fields
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_product(self, product_id: int) -> bool:
        """Delete a product."""
        product = self.get_product(product_id)
        if not product:
            return False

        self.db.delete(product)
        self.db.commit()
        return True

    def search_products(
        self, search_term: str, page: int = 1, size: int = 10
    ) -> Tuple[List[Product], dict]:
        """Search products by name, brand, or SKU."""
        query = self.db.query(Product).filter(
            or_(
                Product.name.ilike(f"%{search_term}%"),
                Product.sku.ilike(f"%{search_term}%"),
            )
        )

        total = query.count()
        query = paginate_query(query, page, size)
        products = query.all()

        # Load variants for each product with relationships
        for product in products:
            # Ensure variants are loaded with their relationships
            if hasattr(product, 'variants'):
                # Force load the variants with their color and size relationships
                for variant in product.variants:
                    # Access the relationships to ensure they're loaded
                    _ = variant.color
                    _ = variant.size
            else:
                product.variants = []

        pagination = calculate_pagination_info(total, page, size)
        return products, pagination

    def get_product_by_sku(self, sku: str):
        """Get product by SKU."""
        product_variant = self.db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
        if product_variant:
            return product_variant
        return None
    
    def get_product_by_variant_sku(self, sku: str):
        """Get full product with all variants by variant SKU."""
        # First find the variant by SKU
        product_variant = self.db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
        if not product_variant:
            return None
            
        # Then get the full product with all variants
        product = (
            self.db.query(Product)
            .options(
                joinedload(Product.variants).joinedload(ProductVariant.color),
                joinedload(Product.variants).joinedload(ProductVariant.size),
                joinedload(Product.brand),
                joinedload(Product.season),
                joinedload(Product.category)
            )
            .filter(Product.id == product_variant.product_id)
            .first()
        )
        
        return product