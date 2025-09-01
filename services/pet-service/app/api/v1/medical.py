"""
API роуты для управления медицинской информацией питомцев
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.pet import (
    PetMedicalCreate,
    PetMedicalUpdate,
    PetMedicalResponse
)
from app.services.medical_service import MedicalService
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


@router.post("", response_model=PetMedicalResponse, summary="Создание медицинской записи")
async def create_medical_record(
    pet_id: str,
    medical_data: PetMedicalCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание медицинской записи для питомца"""
    try:
        medical_record = await MedicalService.create_medical_record(
            db, pet_id, current_user["user_id"], medical_data
        )

        if not medical_record:
            raise HTTPException(
                status_code=404,
                detail="Питомец не найден или доступ запрещен"
            )

        return MedicalService.medical_to_response(medical_record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating medical record for pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания медицинской записи")


@router.get("", summary="Получение медицинских записей питомца")
async def get_medical_records(
    pet_id: str,
    record_type: str = Query(None, description="Тип записи (vaccination, medication, etc.)"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество записей на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение медицинских записей питомца"""
    try:
        records_data = await MedicalService.get_medical_records(
            db, pet_id, current_user["user_id"], record_type, page, limit
        )

        return records_data

    except Exception as e:
        logger.error(f"Error getting medical records for pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения медицинских записей")


@router.get("/{record_id}", response_model=PetMedicalResponse, summary="Получение медицинской записи по ID")
async def get_medical_record(
    pet_id: str,
    record_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение конкретной медицинской записи"""
    try:
        record = await MedicalService.get_medical_record_by_id(db, record_id, current_user["user_id"])

        if not record:
            raise HTTPException(status_code=404, detail="Медицинская запись не найдена")

        return MedicalService.medical_to_response(record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting medical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения медицинской записи")


@router.put("/{record_id}", response_model=PetMedicalResponse, summary="Обновление медицинской записи")
async def update_medical_record(
    pet_id: str,
    record_id: str,
    medical_data: PetMedicalUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление медицинской записи"""
    try:
        updated_record = await MedicalService.update_medical_record(
            db, record_id, current_user["user_id"], medical_data
        )

        if not updated_record:
            raise HTTPException(status_code=404, detail="Медицинская запись не найдена")

        return MedicalService.medical_to_response(updated_record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating medical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления медицинской записи")


@router.delete("/{record_id}", summary="Удаление медицинской записи")
async def delete_medical_record(
    pet_id: str,
    record_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление медицинской записи"""
    try:
        success = await MedicalService.delete_medical_record(db, record_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Медицинская запись не найдена")

        return {"message": "Медицинская запись успешно удалена"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting medical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления медицинской записи")


@router.get("/upcoming/events", summary="Получение предстоящих медицинских событий")
async def get_upcoming_events(
    days_ahead: int = Query(30, description="Количество дней для поиска предстоящих событий"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение предстоящих медицинских событий для всех питомцев пользователя"""
    try:
        events = await MedicalService.get_upcoming_events(db, current_user["user_id"], days_ahead)

        return {"events": events, "total": len(events)}

    except Exception as e:
        logger.error(f"Error getting upcoming events for user {current_user['user_id']}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения предстоящих событий")
