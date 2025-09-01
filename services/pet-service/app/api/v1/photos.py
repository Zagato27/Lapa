"""
API роуты для управления фотографиями питомцев
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.pet import PetPhotoCreate, PetPhotoResponse
from app.services.photo_service import PhotoService
from app.services.auth_service import AuthService

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


@router.post("/upload", response_model=PetPhotoResponse, summary="Загрузка фотографии питомца")
async def upload_pet_photo(
    pet_id: str,
    file: UploadFile = File(...),
    description: str = None,
    photo_type: str = "general",
    tags: str = None,  # JSON string of tags
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка фотографии питомца"""
    try:
        # Валидация типа файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Файл должен быть изображением"
            )

        # Парсинг тегов
        tags_list = None
        if tags:
            try:
                import json
                tags_list = json.loads(tags)
            except:
                raise HTTPException(
                    status_code=400,
                    detail="Неверный формат тегов"
                )

        # Создание данных для фотографии
        photo_data = PetPhotoCreate(
            filename=file.filename,
            description=description,
            photo_type=photo_type,
            tags=tags_list
        )

        # Создание фотографии
        photo = await PhotoService.create_photo(
            db, pet_id, current_user["user_id"], file, photo_data
        )

        if not photo:
            raise HTTPException(
                status_code=400,
                detail="Ошибка создания фотографии. Возможно, превышен лимит фотографий или питомец не найден."
            )

        return PhotoService.photo_to_response(photo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo for pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки фотографии")


@router.get("", summary="Получение фотографий питомца")
async def get_pet_photos(
    pet_id: str,
    photo_type: str = Query(None, description="Тип фотографии (avatar, general, medical)"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество фотографий на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка фотографий питомца"""
    try:
        photos_data = await PhotoService.get_pet_photos(
            db, pet_id, current_user["user_id"], photo_type, page, limit
        )

        return photos_data

    except Exception as e:
        logger.error(f"Error getting photos for pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения фотографий")


@router.get("/{photo_id}", response_model=PetPhotoResponse, summary="Получение фотографии по ID")
async def get_pet_photo(
    pet_id: str,
    photo_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение конкретной фотографии питомца"""
    try:
        photo = await PhotoService._get_photo_by_id(db, photo_id)

        if not photo or photo.pet_id != pet_id:
            raise HTTPException(status_code=404, detail="Фотография не найдена")

        # Проверка доступа через питомца
        pet = await PhotoService._get_pet_by_id(db, photo.pet_id, current_user["user_id"])
        if not pet:
            raise HTTPException(status_code=404, detail="Доступ запрещен")

        return PhotoService.photo_to_response(photo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo {photo_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения фотографии")


@router.delete("/{photo_id}", summary="Удаление фотографии")
async def delete_pet_photo(
    pet_id: str,
    photo_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление фотографии питомца"""
    try:
        success = await PhotoService.delete_photo(db, photo_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Фотография не найдена")

        return {"message": "Фотография успешно удалена"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting photo {photo_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления фотографии")


@router.put("/{photo_id}/avatar", summary="Установка как аватара")
async def set_as_avatar(
    pet_id: str,
    photo_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Установка фотографии как аватара питомца"""
    try:
        success = await PhotoService.set_as_avatar(db, photo_id, current_user["user_id"])

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Фотография или питомец не найдены"
            )

        return {"message": "Аватар успешно установлен"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting photo as avatar {photo_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка установки аватара")
