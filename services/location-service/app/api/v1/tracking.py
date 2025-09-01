"""
API роуты для управления трекингом
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.location import (
    TrackingStartRequest,
    TrackingStopRequest,
    RouteOptimizationRequest,
    LocationSharingRequest,
    LocationSharingResponse
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


@router.post("/start", summary="Начало отслеживания")
async def start_tracking(
    request: TrackingStartRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Начало отслеживания геолокации для заказа"""
    try:
        # Проверка прав доступа к заказу
        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == request.order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        success = await LocationService.start_tracking(db, request, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно начать отслеживание")

        return {
            "message": "Отслеживание начато",
            "order_id": request.order_id,
            "geofencing_enabled": request.enable_geofencing,
            "route_optimization_enabled": request.enable_route_optimization,
            "emergency_detection_enabled": request.enable_emergency_detection
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting tracking for order {request.order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка начала отслеживания")


@router.post("/stop", summary="Остановка отслеживания")
async def stop_tracking(
    request: TrackingStopRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Остановка отслеживания геолокации для заказа"""
    try:
        # Проверка прав доступа к заказу
        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == request.order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        success = await LocationService.stop_tracking(db, request, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно остановить отслеживание")

        return {
            "message": "Отслеживание остановлено",
            "order_id": request.order_id,
            "route_saved": request.save_route
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping tracking for order {request.order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка остановки отслеживания")


@router.get("/status/{order_id}", summary="Получение статуса отслеживания")
async def get_tracking_status(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статуса отслеживания для заказа"""
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

        # Получение статуса из Redis
        from app.database.session import get_session
        redis_session = await get_session()
        tracking_status = await redis_session.get_tracking_status(order_id)

        if tracking_status:
            return {
                "order_id": order_id,
                "is_active": tracking_status.get("is_active", False),
                "started_at": tracking_status.get("started_at"),
                "user_id": tracking_status.get("user_id")
            }
        else:
            return {
                "order_id": order_id,
                "is_active": False,
                "message": "Отслеживание не активно"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracking status for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статуса отслеживания")


@router.post("/route/optimize", summary="Оптимизация маршрута")
async def optimize_route(
    request: RouteOptimizationRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Оптимизация маршрута для заказа"""
    try:
        # Проверка прав доступа к заказу
        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == request.order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        # Получение маршрута
        from app.models.route import Route
        route_query = db.execute(
            select(Route).where(Route.order_id == request.order_id)
        )
        route_result = await route_query
        route = route_result.scalar_one_or_none()

        if not route:
            raise HTTPException(status_code=404, detail="Маршрут не найден")

        # Оптимизация маршрута
        if request.optimization_type == "simplify":
            route.optimize_route()
        # Здесь можно добавить другие типы оптимизации

        # Сохранение изменений
        await db.commit()

        return {
            "message": "Маршрут оптимизирован",
            "order_id": request.order_id,
            "optimization_type": request.optimization_type,
            "is_optimized": route.is_optimized
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing route for order {request.order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка оптимизации маршрута")


@router.put("/sharing", response_model=LocationSharingResponse, summary="Управление геолокацией")
async def manage_location_sharing(
    request: LocationSharingRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Включение или отключение геолокации для заказа"""
    try:
        # Проверка прав доступа к заказу
        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == request.order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        # Получение текущей локации
        current_location = await LocationService.get_current_location(db, request.order_id)

        # Получение статуса трекинга
        from app.database.session import get_session
        redis_session = await get_session()
        tracking_status = await redis_session.get_tracking_status(request.order_id)

        if request.enabled:
            # Включение геолокации
            if not tracking_status or not tracking_status.get("is_active"):
                start_request = TrackingStartRequest(
                    order_id=request.order_id,
                    enable_geofencing=True,
                    enable_route_optimization=True,
                    enable_emergency_detection=True
                )
                await LocationService.start_tracking(db, start_request, current_user["user_id"])

            sharing_started_at = datetime.utcnow()
        else:
            # Отключение геолокации
            if tracking_status and tracking_status.get("is_active"):
                stop_request = TrackingStopRequest(
                    order_id=request.order_id,
                    save_route=True
                )
                await LocationService.stop_tracking(db, stop_request, current_user["user_id"])

            sharing_started_at = None

        return LocationSharingResponse(
            order_id=request.order_id,
            is_sharing_enabled=request.enabled,
            last_location=LocationService.track_to_response(current_location) if current_location else None,
            sharing_started_at=sharing_started_at,
            emergency_contacts_notified=request.share_with_emergency_contacts
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing location sharing for order {request.order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка управления геолокацией")
