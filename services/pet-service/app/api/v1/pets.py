"""
API роуты для управления питомцами
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.pet import (
    PetCreate,
    PetUpdate,
    PetResponse,
    PetsListResponse
)
from app.services.pet_service import PetService
from app.services.auth_service import AuthService
from app.database.session import get_session

router = APIRouter()
security = HTTPBearer(auto_error=False)
auth_service = AuthService()

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя"""
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

    return {"user_id": user_id}


@router.post("", response_model=PetResponse, summary="Создание питомца")
async def create_pet(
    pet_data: PetCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового питомца"""
    try:
        # Проверка лимита питомцев
        user_pets = await PetService.get_user_pets(db, current_user["user_id"], page=1, limit=100)
        if user_pets.total >= 10:  # Максимум 10 питомцев на пользователя
            raise HTTPException(
                status_code=400,
                detail="Превышен лимит количества питомцев (максимум 10)"
            )

        pet = await PetService.create_pet(db, current_user["user_id"], pet_data)

        return PetResponse(pet=PetService.pet_to_profile(pet))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating pet: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания питомца")


@router.get("", response_model=PetsListResponse, summary="Получение списка питомцев")
async def get_user_pets(
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество питомцев на странице"),
    refresh: bool = Query(False, description="Принудительно обновить кэш"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка питомцев пользователя"""
    try:
        if refresh:
            # Принудительная инвалидация кэша перед получением списка
            redis_session = await get_session()
            await redis_session.invalidate_user_pets_cache(current_user["user_id"])

        pets_response = await PetService.get_user_pets(db, current_user["user_id"], page, limit)

        return pets_response

    except Exception as e:
        logger.error(f"Error getting user pets: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка питомцев")


@router.get("/stats", summary="Получение статистики питомцев")
async def get_pet_stats(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики питомцев пользователя"""
    try:
        stats = await PetService.get_pet_stats(db, current_user["user_id"])

        return stats

    except Exception as e:
        logger.error(f"Error getting pet stats: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")


@router.get("/{pet_id}", response_model=PetResponse, summary="Получение питомца по ID")
async def get_pet(
    pet_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о конкретном питомце"""
    try:
        pet = await PetService.get_pet_by_id(db, pet_id, current_user["user_id"])

        if not pet:
            raise HTTPException(status_code=404, detail="Питомец не найден")

        return PetResponse(pet=PetService.pet_to_profile(pet))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения питомца")


@router.put("/{pet_id}", response_model=PetResponse, summary="Обновление питомца")
async def update_pet(
    pet_id: str,
    pet_data: PetUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление данных питомца"""
    try:
        pet = await PetService.update_pet(db, pet_id, current_user["user_id"], pet_data)

        if not pet:
            raise HTTPException(status_code=404, detail="Питомец не найден")

        return PetResponse(pet=PetService.pet_to_profile(pet))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления питомца")


@router.delete("/{pet_id}", summary="Удаление питомца")
async def delete_pet(
    pet_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление питомца (мягкое удаление)"""
    try:
        success = await PetService.delete_pet(db, pet_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Питомец не найден")

        return {"message": "Питомец успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления питомца")


@router.put("/{pet_id}/avatar/{photo_id}", summary="Установка аватара питомца")
async def set_pet_avatar(
    pet_id: str,
    photo_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Установка фотографии как аватара питомца"""
    try:
        success = await PetService.set_pet_avatar(db, pet_id, current_user["user_id"], photo_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Питомец или фотография не найдены"
            )

        return {"message": "Аватар успешно установлен"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting pet avatar {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка установки аватара")
