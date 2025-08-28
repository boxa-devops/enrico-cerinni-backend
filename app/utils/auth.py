from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Response
from app.config import settings
from app.models.user import User, UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create an access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_refresh_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str, secret: str) -> Optional[dict]:
    """Verify a JWT token."""
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def get_current_user_payload(token: str) -> Optional[dict]:
    """Get current user from access token."""
    payload = verify_token(token, settings.jwt_secret)
    if payload and payload.get("type") == "access":
        return payload
    return None


def get_user_from_refresh_token(token: str) -> Optional[dict]:
    """Get user from refresh token."""
    payload = verify_token(token, settings.jwt_refresh_secret)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


# Cookie-based authentication functions
def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set authentication cookies with environment-appropriate security settings."""
    # Determine security settings based on environment
    secure = False  # Use HTTPS in production
    samesite = "strict" if settings.is_production else "lax"  # Stricter in production
    
    # Access token cookie (short-lived)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,  # Convert to seconds
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )

    # Refresh token cookie (long-lived)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,  # Convert to seconds
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies with environment-appropriate security settings."""
    # Use same security settings as when setting cookies for proper cleanup
    secure = settings.is_production
    samesite = None
    
    response.delete_cookie(
        key="access_token", 
        path="/",
        secure=secure,
        samesite=samesite
    )
    response.delete_cookie(
        key="refresh_token", 
        path="/",
        secure=secure,
        samesite=samesite
    )


def get_token_from_cookie(request, cookie_name: str) -> Optional[str]:
    """Get token from cookie with proper error handling."""
    try:
        # Handle different types of FastAPI request objects
        if hasattr(request, 'cookies') and request.cookies:
            token = request.cookies.get(cookie_name)
            if token:
                print(f"Found {cookie_name} in cookies: {token[:20]}...")
                return token
            else:
                print(f"No {cookie_name} found in cookies. Available cookies: {list(request.cookies.keys())}")
        else:
            print(f"No cookies found in request or request has no cookies attribute")
        return None
    except Exception as e:
        print(f"Error getting token from cookie {cookie_name}: {str(e)}")
        return None
