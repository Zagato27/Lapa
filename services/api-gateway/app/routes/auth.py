"""
Роуты аутентификации для API Gateway
"""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr

from app.services.discovery import ServiceDiscovery


router = APIRouter()
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Модель запроса на вход"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Модель запроса на регистрацию"""
    email: EmailStr
    password: str
    phone: str
    first_name: str
    last_name: str
    role: str = "client"  # client или walker


class RefreshTokenRequest(BaseModel):
    """Модель запроса на обновление токена"""
    refresh_token: str


async def get_service_discovery() -> ServiceDiscovery:
    """Зависимость для получения Service Discovery"""
    # В реальном приложении это будет внедрено через DI
    return ServiceDiscovery()


@router.post("/register", summary="Регистрация пользователя")
async def register(
    request: RegisterRequest,
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Регистрация нового пользователя"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/auth/register",
            method="POST",
            data=request.dict()
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка регистрации")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.post("/login", summary="Вход в систему")
async def login(
    request: LoginRequest,
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Аутентификация пользователя"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/auth/login",
            method="POST",
            data=request.dict()
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка входа")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.post("/refresh", summary="Обновление токена")
async def refresh_token(
    request: RefreshTokenRequest,
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Обновление access token с помощью refresh token"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/auth/refresh",
            method="POST",
            data=request.dict()
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка обновления токена")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.post("/logout", summary="Выход из системы")
async def logout(
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Выход из системы и отзыв токенов"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/auth/logout",
            method="POST",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка выхода")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")
