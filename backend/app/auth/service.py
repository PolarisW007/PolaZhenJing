"""
=============================================================================
Module: auth.service
Description: Core authentication business logic – registration, login,
             password hashing, and JWT token creation / verification.
             核心认证业务逻辑 - 注册、登录、密码哈希和JWT令牌创建/验证。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: bcrypt, python-jose, sqlalchemy
=============================================================================
"""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    BadRequestException,
    ConflictException,
    UnauthorizedException,
)
from app.common.models import User
from app.config import settings

# ── Password Hashing ─────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT Tokens ───────────────────────────────────────────────────────────
def create_access_token(user_id: uuid.UUID) -> str:
    """
    Create a short-lived JWT access token.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """
    Create a long-lived JWT refresh token.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises:
        UnauthorizedException: If the token is invalid or expired.

    Returns:
        Decoded payload dict with at least 'sub' and 'type' keys.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise UnauthorizedException(detail="Invalid or expired token")


# ── User Operations ──────────────────────────────────────────────────────
async def register_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    display_name: str | None = None,
) -> User:
    """
    Register a new user.

    Business rules:
        - Username and email must be unique (raises ConflictException).
        - Password is hashed before storage.

    Returns:
        Newly created User ORM instance.
    """
    # Check for existing user
    stmt = select(User).where(or_(User.username == username, User.email == email))
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise ConflictException(detail="Username or email already exists")

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        display_name=display_name,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User:
    """
    Authenticate a user by username/email and password.

    Raises:
        BadRequestException: If credentials are invalid.

    Returns:
        Authenticated User ORM instance.
    """
    stmt = select(User).where(
        or_(User.username == username, User.email == username)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.hashed_password):
        raise BadRequestException(detail="Invalid username or password")

    if not user.is_active:
        raise BadRequestException(detail="User account is deactivated")

    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    """
    Fetch a user by primary key.

    Raises:
        UnauthorizedException: If user not found.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedException(detail="User not found")
    return user
