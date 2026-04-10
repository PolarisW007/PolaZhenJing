"""
=============================================================================
Module: auth.router
Description: Authentication API endpoints – register, login, refresh, me.
             认证API端点 - 注册、登录、刷新令牌、获取当前用户。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.auth.service, app.auth.dependencies
=============================================================================
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_id,
    register_user,
)
from app.common.exceptions import UnauthorizedException
from app.common.models import User
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.

    - **username**: 3-64 characters, must be unique
    - **email**: valid email, must be unique
    - **password**: 8-128 characters
    """
    user = await register_user(
        db,
        username=body.username,
        email=body.email,
        password=body.password,
        display_name=body.display_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate with username/email and password.

    Returns an access token (short-lived) and a refresh token (long-lived).
    """
    user = await authenticate_user(db, body.username, body.password)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    """
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise UnauthorizedException(detail="Invalid token type")

    import uuid
    user = await get_user_by_id(db, uuid.UUID(payload["sub"]))
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
