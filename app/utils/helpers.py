import uuid
import random
import string
from datetime import datetime
from typing import Optional
from decimal import Decimal


def generate_sku() -> str:
    """Generate a unique SKU for products."""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SKU-{timestamp}-{random_chars}"


def generate_receipt_number() -> str:
    """Generate a unique receipt number for sales."""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"RCP-{timestamp}-{random_chars}"


def calculate_total_price(
    unit_price: Decimal, quantity: int, discount: Decimal = Decimal("0")
) -> Decimal:
    """Calculate total price with discount."""
    subtotal = unit_price * quantity
    return subtotal - discount


def format_currency(amount: Decimal) -> str:
    """Format decimal as currency string."""
    return f"${amount:.2f}"


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def paginate_query(query, page: int, size: int):
    """Apply pagination to a SQLAlchemy query."""
    offset = (page - 1) * size
    return query.offset(offset).limit(size)


def calculate_pagination_info(total: int, page: int, size: int) -> dict:
    """Calculate pagination information."""
    pages = (total + size - 1) // size
    return {"page": page, "size": size, "total": total, "pages": pages}
