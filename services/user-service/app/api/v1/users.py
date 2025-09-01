"""
API роуты для управления пользователями.

Содержит:
- Получение и обновление профиля текущего пользователя
- Верификация выгульщика
- Поиск выгульщиков рядом (проксируется API Gateway)
- Получение пользователя по ID и списка пользователей (для админов)
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    UserUpdate,
    UserResponse,
    NearbyWalkersResponse,
    WalkerVerificationRequest,
    WalkerVerificationResponse
)
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.walker_service import WalkerService

router = APIRouter()
security = HTTPBearer(auto_error=False)
auth_service = AuthService()

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя.

    В прод-окружении токены проверяются API Gateway, который прокладывает
    `request.state.user_id` и `request.state.user_role`. Здесь оставляем
    резервную валидацию на уровне сервиса, если gateway недоступен.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    # Резервная валидация JWT, если API Gateway не проставил user_id
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        try:
            payload = auth_service.verify_token(credentials.credentials)
            user_id = payload.get("user_id")
        except Exception:
            raise HTTPException(status_code=401, detail="Неверный токен")

    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user


@router.get("/profile", response_model=UserResponse, summary="Получение профиля пользователя")
async def get_user_profile(
    current_user = Depends(get_current_user)
):
    """Получение профиля текущего пользователя"""
    try:
        user_profile = UserService.user_to_profile(current_user)
        return UserResponse(user=user_profile)

    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения профиля")


@router.put("/profile", response_model=UserResponse, summary="Обновление профиля пользователя")
async def update_user_profile(
    profile_data: UserUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление профиля пользователя"""
    try:
        updated_user = await UserService.update_user(db, current_user.id, profile_data)

        if not updated_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        user_profile = UserService.user_to_profile(updated_user)
        return UserResponse(user=user_profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления профиля")


@router.post("/verify-walker", response_model=WalkerVerificationResponse, summary="Верификация выгульщика")
async def verify_walker(
    verification_data: WalkerVerificationRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Верификация документов выгульщика"""
    try:
        if current_user.role != "walker":
            raise HTTPException(
                status_code=403,
                detail="Только выгульщики могут проходить верификацию"
            )

        verification_response = await WalkerService.create_verification_request(
            db, current_user.id, verification_data
        )

        return verification_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating walker verification: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания заявки на верификацию")


@router.get("/walker/nearby", response_model=NearbyWalkersResponse, summary="Поиск выгульщиков рядом")
async def get_nearby_walkers(
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
    radius: float = Query(5000, description="Радиус поиска в метрах"),
    db: AsyncSession = Depends(get_db)
):
    """Поиск выгульщиков в заданном радиусе"""
    try:
        walkers_response = await UserService.get_nearby_walkers(
            db, latitude, longitude, radius
        )

        return walkers_response

    except Exception as e:
        logger.error(f"Error finding nearby walkers: {e}")
        raise HTTPException(status_code=500, detail="Ошибка поиска выгульщиков")


@router.get("/{user_id}", response_model=UserResponse, summary="Получение информации о пользователе")
async def get_user_by_id(
    user_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о конкретном пользователе"""
    try:
        user = await UserService.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Проверка прав доступа (пользователь может смотреть только свой профиль или профили выгульщиков)
        if (user_id != current_user.id and
            current_user.role != "admin" and
            user.role not in ["walker"]):
            raise HTTPException(status_code=403, detail="Нет прав доступа")

        user_profile = UserService.user_to_profile(user)
        return UserResponse(user=user_profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пользователя")


@router.get("/", summary="Получение списка пользователей")
async def get_users(
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество пользователей на странице"),
    role: Optional[str] = Query(None, description="Фильтр по роли"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка пользователей с пагинацией"""
    try:
        # Проверка прав администратора для просмотра всех пользователей
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Требуются права администратора")

        users_data = await UserService.get_users_list(db, page, limit, role)

        # Преобразование пользователей в профили
        users_profiles = []
        for user in users_data["users"]:
            users_profiles.append(UserService.user_to_profile(user))

        return {
            "users": users_profiles,
            "total": users_data["total"],
            "page": users_data["page"],
            "limit": users_data["limit"],
            "pages": users_data["pages"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка пользователей")
