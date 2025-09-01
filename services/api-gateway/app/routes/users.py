"""
Роуты пользователей для API Gateway
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from app.services.discovery import ServiceDiscovery


router = APIRouter()
security = HTTPBearer(auto_error=False)


class UserProfileUpdate(BaseModel):
    """Модель обновления профиля пользователя"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    hourly_rate: Optional[float] = None


class WalkerVerificationRequest(BaseModel):
    """Модель запроса на верификацию выгульщика"""
    passport_number: str
    passport_series: str
    passport_issued_by: str
    passport_issued_date: str
    passport_expiry_date: str
    experience_years: int
    services_offered: List[str]
    work_schedule: Dict


async def get_service_discovery() -> ServiceDiscovery:
    """Зависимость для получения Service Discovery"""
    return ServiceDiscovery()


async def get_current_user(request: Request) -> Dict:
    """Зависимость для получения текущего пользователя"""
    return {
        "user_id": request.state.user_id,
        "role": request.state.user_role
    }


@router.get("/profile", summary="Получение профиля пользователя")
async def get_user_profile(
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Получение профиля текущего пользователя"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/users/profile",
            method="GET",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка получения профиля")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.put("/profile", summary="Обновление профиля пользователя")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Обновление профиля пользователя"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/users/profile",
            method="PUT",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            data=profile_data.dict(exclude_unset=True)
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка обновления профиля")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.post("/verify-walker", summary="Верификация выгульщика")
async def verify_walker(
    verification_data: WalkerVerificationRequest,
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Верификация документов выгульщика"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/users/verify-documents",
            method="POST",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            data=verification_data.dict()
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка верификации")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.get("/walker/nearby", summary="Поиск выгульщиков рядом")
async def get_nearby_walkers(
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
    radius: float = Query(5000, description="Радиус поиска в метрах"),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Поиск выгульщиков в заданном радиусе"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/users/walker/nearby",
            method="GET",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius
            }
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка поиска выгульщиков")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.get("/{user_id}", summary="Получение информации о пользователе")
async def get_user_by_id(
    user_id: str,
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Получение информации о конкретном пользователе"""
    try:
        response = await service_discovery.proxy_request(
            service_name="user-service",
            path=f"/api/v1/users/{user_id}",
            method="GET",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Пользователь не найден")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.get("/", summary="Получение списка пользователей")
async def get_users(
    request: Request,
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество пользователей на странице"),
    role: Optional[str] = Query(None, description="Фильтр по роли"),
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    """Получение списка пользователей с пагинацией"""
    try:
        params = {"page": page, "limit": limit}
        if role:
            params["role"] = role

        response = await service_discovery.proxy_request(
            service_name="user-service",
            path="/api/v1/users",
            method="GET",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            params=params
        )

        if response["status_code"] >= 400:
            raise HTTPException(
                status_code=response["status_code"],
                detail=response["error"].get("detail", "Ошибка получения пользователей")
            )

        return response["data"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")
