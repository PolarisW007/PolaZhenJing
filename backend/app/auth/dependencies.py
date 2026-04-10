"""
=============================================================================
Module: auth.dependencies
Description: FastAPI dependencies for extracting and validating the current
             authenticated user from the Authorization header.
             FastAPI依赖项 - 从Authorization头中提取和验证当前认证用户。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.auth.service
=============================================================================
"""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import decode_token, get_user_by_id
from app.common.exceptions import ForbiddenException, UnauthorizedException
from app.common.models import User
from app.database import get_db

# Bearer token extractor
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts the JWT from the Authorization header,
    validates it, and returns the corresponding User.

    Raises:
        UnauthorizedException: Missing or invalid token.
    """
    if credentials is None:
        raise UnauthorizedException(detail="Authorization header missing")

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise UnauthorizedException(detail="Invalid token type")

    user_id = uuid.UUID(payload["sub"])
    user = await get_user_by_id(db, user_id)

    if not user.is_active:
        raise UnauthorizedException(detail="User account is deactivated")

    return user


async def get_current_superuser(
    user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the current user has superuser privileges.

    Raises:
        ForbiddenException: If user is not a superuser.
    """
    if not user.is_superuser:
        raise ForbiddenException(detail="Superuser privileges required")
    return user
