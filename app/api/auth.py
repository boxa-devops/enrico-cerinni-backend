from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import UserLogin, UserRegister, UserResponse
from app.schemas.common import ResponseModel
from app.utils.auth import (
    get_user_from_refresh_token,
    create_access_token,
    create_refresh_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_token_from_cookie,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=ResponseModel)
async def login(
    user_data: UserLogin, response: Response, db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    try:
        tokens = auth_service.login_user(user_data)

        # Set authentication cookies (with environment-appropriate security settings)
        set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])

        # Get user data for response
        user = auth_service.get_user_by_email(user_data.email)

        return ResponseModel(
            success=True,
            data={
                "id": user.id,
                "email": user.email,
                "name": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role.value,
                "created_at": user.created_at.isoformat(),
            },
            message="Login successful",
        )
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.post("/register", response_model=ResponseModel)
async def register(
    user_data: UserRegister, response: Response, db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    try:
        user = auth_service.create_user(user_data)

        # Auto-login after registration
        login_data = UserLogin(email=user_data.email, password=user_data.password)
        tokens = auth_service.login_user(login_data)
        set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])

        return ResponseModel(
            success=True,
            data={
                "id": user.id,
                "email": user.email,
                "name": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role.value,
                "created_at": user.created_at.isoformat(),
            },
            message="User registered and logged in successfully",
        )
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.post("/refresh", response_model=ResponseModel)
async def refresh_token(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    # Get refresh token from cookie or request body
    refresh_token = get_token_from_cookie(request, "refresh_token")

    if not refresh_token:
        return ResponseModel(success=False, message="No refresh token found")

    payload = get_user_from_refresh_token(refresh_token)
    if not payload:
        return ResponseModel(success=False, message="Invalid refresh token")

    token_data = {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }

    access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    # Set new cookies
    set_auth_cookies(response, access_token, new_refresh_token)

    return ResponseModel(
        success=True,
        data={"token": new_refresh_token},
        message="Token refreshed successfully",
    )


@router.get("/validate", response_model=ResponseModel)
async def validate_token(current_user=Depends(get_current_user)):
    return ResponseModel(
        success=True,
        data={
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.username,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone": current_user.phone,
            "role": current_user.role.value,
            "created_at": current_user.created_at.isoformat(),
        },
        message="Token is valid",
    )


@router.post("/logout", response_model=ResponseModel)
async def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    auth_service = AuthService(db)
    try:
        auth_service.logout_user(current_user.id)
        # Clear cookies
        clear_auth_cookies(response)
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)
    return ResponseModel(success=True, message="Logout successful")
