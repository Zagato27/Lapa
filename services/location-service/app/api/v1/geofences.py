"""
API роуты для управления геофенсингом
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.location import (
    GeofenceCreate,
    GeofenceUpdate,
    GeofenceResponse
)
from app.services.geofence_service import GeofenceService

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

    # Здесь должна быть валидация токена через API Gateway
    # Пока что просто возвращаем данные из request
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("", response_model=GeofenceResponse, summary="Создание геофенса")
async def create_geofence(
    geofence_data: GeofenceCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание геофенса для заказа"""
    try:
        # Проверка прав доступа к заказу
        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == geofence_data.order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        geofence = await GeofenceService.create_geofence(db, geofence_data, current_user["user_id"])

        return GeofenceService.geofence_to_response(geofence)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating geofence: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания геофенса")


@router.get("/orders/{order_id}", summary="Получение геофенсов заказа")
async def get_order_geofences(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение геофенсов для заказа"""
    try:
        # Проверка прав доступа к заказу
        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        geofences = await GeofenceService.get_order_geofences(db, order_id, current_user["user_id"])

        return {
            "order_id": order_id,
            "geofences": [GeofenceService.geofence_to_response(gf) for gf in geofences],
            "total": len(geofences)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting geofences for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения геофенсов")


@router.get("/{geofence_id}", response_model=GeofenceResponse, summary="Получение геофенса по ID")
async def get_geofence(
    geofence_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение геофенса по ID"""
    try:
        geofence = await GeofenceService.get_geofence_by_id(db, geofence_id, current_user["user_id"])

        if not geofence:
            raise HTTPException(status_code=404, detail="Геофенс не найден")

        return GeofenceService.geofence_to_response(geofence)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting geofence {geofence_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения геофенса")


@router.put("/{geofence_id}", response_model=GeofenceResponse, summary="Обновление геофенса")
async def update_geofence(
    geofence_id: str,
    geofence_data: GeofenceUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление геофенса"""
    try:
        geofence = await GeofenceService.update_geofence(db, geofence_id, current_user["user_id"], geofence_data)

        if not geofence:
            raise HTTPException(status_code=404, detail="Геофенс не найден")

        return GeofenceService.geofence_to_response(geofence)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating geofence {geofence_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления геофенса")


@router.delete("/{geofence_id}", summary="Удаление геофенса")
async def delete_geofence(
    geofence_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление геофенса"""
    try:
        success = await GeofenceService.delete_geofence(db, geofence_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Геофенс не найден")

        return {"message": "Геофенс успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting geofence {geofence_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления геофенса")


@router.put("/{geofence_id}/toggle", summary="Включение/отключение геофенса")
async def toggle_geofence(
    geofence_id: str,
    is_active: bool = Query(..., description="Включить или отключить геофенс"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Включение или отключение геофенса"""
    try:
        success = await GeofenceService.toggle_geofence(db, geofence_id, current_user["user_id"], is_active)

        if not success:
            raise HTTPException(status_code=404, detail="Геофенс не найден")

        return {
            "message": f"Геофенс {'включен' if is_active else 'отключен'}",
            "geofence_id": geofence_id,
            "is_active": is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling geofence {geofence_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка переключения геофенса")


@router.get("/{geofence_id}/statistics", summary="Получение статистики геофенса")
async def get_geofence_statistics(
    geofence_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики геофенса"""
    try:
        statistics = await GeofenceService.get_geofence_statistics(db, geofence_id, current_user["user_id"])

        if not statistics:
            raise HTTPException(status_code=404, detail="Геофенс не найден")

        return statistics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting geofence statistics {geofence_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики геофенса")


@router.get("/point/geofences", summary="Поиск геофенсов по точке")
async def find_geofences_by_point(
    latitude: float = Query(..., description="Широта точки"),
    longitude: float = Query(..., description="Долгота точки"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Поиск геофенсов, содержащих указанную точку"""
    try:
        geofences = await GeofenceService.find_geofences_containing_point(db, latitude, longitude)

        # Фильтрация по правам доступа пользователя
        accessible_geofences = []
        for gf in geofences:
            # Проверка доступа через заказ
            from app.models.order import Order
            order_query = db.execute(
                select(Order).where(
                    Order.id == gf.order_id,
                    (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
                )
            )
            order_result = await order_query
            order = order_result.scalar_one_or_none()

            if order:
                accessible_geofences.append(GeofenceService.geofence_to_response(gf))

        return {
            "point": {"latitude": latitude, "longitude": longitude},
            "geofences": accessible_geofences,
            "total": len(accessible_geofences)
        }

    except Exception as e:
        logger.error(f"Error finding geofences by point ({latitude}, {longitude}): {e}")
        raise HTTPException(status_code=500, detail="Ошибка поиска геофенсов")
