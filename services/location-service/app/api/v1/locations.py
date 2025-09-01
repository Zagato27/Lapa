"""
API роуты для управления геолокацией
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.location import (
    LocationTrackCreate,
    LocationTrackResponse,
    LocationTracksResponse,
    LiveTrackingResponse
)
from app.services.location_service import LocationService

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


@router.post("", response_model=LocationTrackResponse, summary="Создание точки отслеживания")
async def create_location_track(
    track_data: LocationTrackCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание точки отслеживания геолокации"""
    try:
        # Проверка прав доступа к заказу
        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == track_data.order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        track = await LocationService.create_location_track(db, track_data)

        return LocationService.track_to_response(track)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating location track: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания точки отслеживания")


@router.get("/orders/{order_id}", response_model=LocationTracksResponse, summary="Получение точек отслеживания заказа")
async def get_order_location_tracks(
    order_id: str,
    track_type: str = Query(None, description="Тип точки отслеживания"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(50, description="Количество точек на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение точек отслеживания для заказа"""
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

        tracks_response = await LocationService.get_location_tracks(
            db, order_id, page, limit, track_type
        )

        return tracks_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location tracks for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения точек отслеживания")


@router.get("/orders/{order_id}/current", response_model=LocationTrackResponse, summary="Получение текущей локации")
async def get_current_location(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение текущей локации для заказа"""
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

        current_location = await LocationService.get_current_location(db, order_id)

        if not current_location:
            raise HTTPException(status_code=404, detail="Текущая локация не найдена")

        return LocationService.track_to_response(current_location)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current location for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения текущей локации")


@router.get("/orders/{order_id}/history", summary="Получение истории геолокации")
async def get_location_history(
    order_id: str,
    hours: int = Query(24, description="Количество часов истории"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение истории геолокации заказа"""
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

        history = await LocationService.get_location_history(db, order_id, hours)

        return {
            "order_id": order_id,
            "hours": hours,
            "total_points": len(history),
            "tracks": [LocationService.track_to_response(track) for track in history]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location history for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения истории геолокации")


@router.post("/emergency", summary="Отправка экстренной геолокации")
async def send_emergency_location(
    order_id: str,
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправка экстренной геолокации"""
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

        await LocationService.process_emergency_location(
            db, order_id, latitude, longitude, current_user["user_id"]
        )

        return {
            "message": "Экстренная геолокация отправлена",
            "order_id": order_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending emergency location for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки экстренной геолокации")


@router.get("/live/{order_id}", response_model=LiveTrackingResponse, summary="Получение данных реального времени")
async def get_live_tracking_data(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение данных реального времени для заказа"""
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

        # Получение текущей локации
        current_location = await LocationService.get_current_location(db, order_id)

        # Получение статуса трекинга
        from app.database.session import get_session
        redis_session = await get_session()
        tracking_status = await redis_session.get_tracking_status(order_id)

        # Получение геофенсинга
        from app.services.geofence_service import GeofenceService
        geofences = await GeofenceService.get_order_geofences(db, order_id, current_user["user_id"])

        # Получение предупреждений
        from app.models.location_alert import LocationAlert
        alerts_query = db.execute(
            select(LocationAlert).where(
                LocationAlert.order_id == order_id,
                LocationAlert.is_read == False
            ).order_by(LocationAlert.timestamp.desc()).limit(10)
        )
        alerts_result = await alerts_query
        alerts = alerts_result.scalars().all()

        return LiveTrackingResponse(
            order_id=order_id,
            current_location=LocationService.track_to_response(current_location) if current_location else None,
            route_progress={},  # Здесь можно добавить прогресс маршрута
            active_alerts=[alert.to_dict() for alert in alerts],
            geofence_status={},  # Здесь можно добавить статус геофенсинга
            is_tracking_active=tracking_status.get("is_active", False) if tracking_status else False,
            last_update=current_location.timestamp if current_location else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting live tracking data for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных реального времени")
