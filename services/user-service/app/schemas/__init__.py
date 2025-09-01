"""
Pydantic схемы для User Service
"""

from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    WalkerVerificationRequest,
    WalkerVerificationResponse
)
from .auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse
)

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "WalkerVerificationRequest",
    "WalkerVerificationResponse",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "TokenResponse"
]
