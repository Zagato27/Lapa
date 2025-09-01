"""
API роуты для аутентификации.

Включают регистрацию, вход, обновление токена и выход (отзыв refresh token).
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()
security = HTTPBearer(auto_error=False)
auth_service = AuthService()

logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, summary="Регистрация пользователя")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Регистрация нового пользователя"""
    try:
        # Проверка, существует ли пользователь с таким email
        existing_user = await UserService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким email уже существует"
            )

        # Создание пользователя
        user = await UserService.create_user(db, user_data)

        # Создание токенов
        access_token_data = {"user_id": user.id, "role": user.role}
        access_token = auth_service.create_access_token(access_token_data)

        refresh_token_data = {"user_id": user.id, "role": user.role}
        refresh_token = auth_service.create_refresh_token(refresh_token_data)

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600
        )

        user_profile = UserService.user_to_profile(user)

        return LoginResponse(user=user_profile, tokens=tokens)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")


@router.post("/login", response_model=LoginResponse, summary="Вход в систему")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Аутентификация пользователя"""
    try:
        user = await auth_service.authenticate_user(db, login_data.email, login_data.password)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Неверный email или пароль"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="Аккаунт заблокирован"
            )

        # Создание токенов
        access_token_data = {"user_id": user.id, "role": user.role}
        access_token = auth_service.create_access_token(access_token_data)

        refresh_token_data = {"user_id": user.id, "role": user.role}
        refresh_token = auth_service.create_refresh_token(refresh_token_data)

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600
        )

        user_profile = UserService.user_to_profile(user)

        return LoginResponse(user=user_profile, tokens=tokens)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {login_data.email}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка входа")


@router.post("/refresh", response_model=TokenResponse, summary="Обновление токена")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Обновление access token с помощью refresh token"""
    try:
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=3600
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления токена")


@router.post("/logout", summary="Выход из системы")
async def logout(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Выход из системы и отзыв refresh token"""
    try:
        # Проверка refresh token
        payload = auth_service.verify_token(refresh_data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Неверный тип токена")

        user_id = payload.get("user_id")

        # Отзыв refresh token
        await auth_service.revoke_refresh_token(user_id)

        return {"message": "Выход выполнен успешно"}

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка выхода")
