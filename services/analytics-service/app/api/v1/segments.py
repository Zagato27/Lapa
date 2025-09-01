"""
API роуты для управления сегментами пользователей
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("", summary="Создание сегмента")
async def create_segment(
    segment_data: Dict,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание сегмента пользователей"""
    try:
        # Здесь должна быть логика создания сегмента
        return {"message": "Сегмент создан", "segment_id": "segment_123"}

    except Exception as e:
        logger.error(f"Error creating segment: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания сегмента")


@router.get("", summary="Получение списка сегментов")
async def get_segments(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка сегментов"""
    try:
        # Здесь должна быть логика получения сегментов
        segments = []
        return {"segments": segments, "total": len(segments)}

    except Exception as e:
        logger.error(f"Error getting segments list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка сегментов")


@router.get("/{segment_id}", summary="Получение сегмента")
async def get_segment(
    segment_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение сегмента по ID"""
    try:
        # Здесь должна быть логика получения сегмента
        segment = {}
        return segment

    except Exception as e:
        logger.error(f"Error getting segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения сегмента")


@router.get("/{segment_id}/users", summary="Пользователи сегмента")
async def get_segment_users(
    segment_id: str,
    limit: int = Query(100, description="Количество пользователей"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение пользователей сегмента"""
    try:
        # Здесь должна быть логика получения пользователей сегмента
        users = []
        return {"users": users, "total": len(users)}

    except Exception as e:
        logger.error(f"Error getting segment users {segment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пользователей сегмента")
