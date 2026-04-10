"""
=============================================================================
Module: auth.schemas
Description: Pydantic schemas for authentication endpoints:
             register, login, token response, and user info.
             认证端点的Pydantic模式 - 注册、登录、令牌响应和用户信息。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pydantic
=============================================================================
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=128)


class LoginRequest(BaseModel):
    """Schema for user login (accepts username or email)."""
    username: str = Field(..., description="Username or email address")
    password: str


# ── Response Schemas ─────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request to refresh an access token."""
    refresh_token: str


class UserResponse(BaseModel):
    """Public user profile information."""
    id: uuid.UUID
    username: str
    email: str
    display_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}
