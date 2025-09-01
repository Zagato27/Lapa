"""
Pydantic-схемы для аутентификации.

Используются в `app.api.v1.auth`.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr
from .user import UserProfile


class LoginRequest(BaseModel):
    """Запрос на вход"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Ответ с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    """Ответ на вход/регистрацию с токенами и профилем пользователя"""
    user: UserProfile
    tokens: TokenResponse


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Запрос на выход"""
    refresh_token: str
