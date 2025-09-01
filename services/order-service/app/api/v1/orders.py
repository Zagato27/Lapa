"""
API роуты для управления заказами
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrdersListResponse,
    OrderCancellationRequest,
    OrderEstimateResponse,
    OrderReviewCreate,
    OrderReviewResponse
)
from app.services.order_service import OrderService
from app.services.matching_service import MatchingService
from app.services.pricing_service import PricingService

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


@router.post("", response_model=OrderResponse, summary="Создание заказа")
async def create_order(
    order_data: OrderCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового заказа"""
    try:
        order = await OrderService.create_order(db, current_user["user_id"], order_data)

        return OrderResponse(order=OrderService.order_to_profile(order))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания заказа")


@router.get("", response_model=OrdersListResponse, summary="Получение списка заказов")
async def get_user_orders(
    status: str = Query(None, description="Фильтр по статусу"),
    order_type: str = Query(None, description="Фильтр по типу заказа"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество заказов на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка заказов пользователя"""
    try:
        orders_response = await OrderService.get_user_orders(
            db, current_user["user_id"], page, limit, status, order_type
        )

        return orders_response

    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка заказов")


@router.get("/estimate", response_model=OrderEstimateResponse, summary="Расчет стоимости заказа")
async def estimate_order(
    pet_id: str,
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
    duration_minutes: int = Query(..., description="Продолжительность в минутах"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Расчет стоимости заказа и поиск доступных выгульщиков"""
    try:
        estimate = await MatchingService.calculate_order_estimate(
            db, pet_id, latitude, longitude, duration_minutes
        )

        return estimate

    except Exception as e:
        logger.error(f"Error estimating order: {e}")
        raise HTTPException(status_code=500, detail="Ошибка расчета стоимости")


@router.get("/{order_id}", response_model=OrderResponse, summary="Получение заказа по ID")
async def get_order(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о конкретном заказе"""
    try:
        order = await OrderService.get_order_by_id(db, order_id, current_user["user_id"])

        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        return OrderResponse(order=OrderService.order_to_profile(order))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения заказа")


@router.put("/{order_id}", response_model=OrderResponse, summary="Обновление заказа")
async def update_order(
    order_id: str,
    order_data: OrderUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление данных заказа"""
    try:
        order = await OrderService.update_order(db, order_id, current_user["user_id"], order_data)

        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        return OrderResponse(order=OrderService.order_to_profile(order))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления заказа")


@router.put("/{order_id}/confirm", response_model=OrderResponse, summary="Подтверждение заказа выгульщиком")
async def confirm_order(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подтверждение заказа выгульщиком"""
    try:
        success = await OrderService.confirm_order(db, order_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно подтвердить заказ")

        order = await OrderService.get_order_by_id(db, order_id)
        return OrderResponse(order=OrderService.order_to_profile(order))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подтверждения заказа")


@router.put("/{order_id}/start-walk", response_model=OrderResponse, summary="Начало прогулки")
async def start_walk(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Начало прогулки"""
    try:
        success = await OrderService.start_walk(db, order_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно начать прогулку")

        order = await OrderService.get_order_by_id(db, order_id)
        return OrderResponse(order=OrderService.order_to_profile(order))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting walk for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка начала прогулки")


@router.put("/{order_id}/complete-walk", response_model=OrderResponse, summary="Завершение прогулки")
async def complete_walk(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Завершение прогулки"""
    try:
        success = await OrderService.complete_walk(db, order_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно завершить прогулку")

        order = await OrderService.get_order_by_id(db, order_id)
        return OrderResponse(order=OrderService.order_to_profile(order))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing walk for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка завершения прогулки")


@router.put("/{order_id}/cancel", response_model=OrderResponse, summary="Отмена заказа")
async def cancel_order(
    order_id: str,
    cancellation_data: OrderCancellationRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отмена заказа"""
    try:
        success = await OrderService.cancel_order(
            db, order_id, current_user["user_id"], cancellation_data
        )

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно отменить заказ")

        order = await OrderService.get_order_by_id(db, order_id)
        return OrderResponse(order=OrderService.order_to_profile(order))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отмены заказа")


@router.post("/{order_id}/review", response_model=OrderReviewResponse, summary="Добавление отзыва о заказе")
async def add_order_review(
    order_id: str,
    review_data: OrderReviewCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавление отзыва о заказе"""
    try:
        review = await OrderService.add_order_review(
            db, order_id, current_user["user_id"], review_data
        )

        if not review:
            raise HTTPException(status_code=400, detail="Невозможно добавить отзыв")

        return review

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding review for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления отзыва")


@router.get("/walker/pending", summary="Получение ожидающих заказов для выгульщика")
async def get_pending_orders_for_walker(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение ожидающих заказов для выгульщика"""
    try:
        orders = await OrderService.get_pending_orders_for_walker(db, current_user["user_id"])

        return {
            "orders": [OrderService.order_to_profile(order) for order in orders],
            "total": len(orders)
        }

    except Exception as e:
        logger.error(f"Error getting pending orders for walker: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения ожидающих заказов")


@router.get("/statistics/summary", summary="Получение статистики заказов")
async def get_order_statistics(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики заказов пользователя"""
    try:
        stats = await OrderService.get_orders_statistics(db, current_user["user_id"])

        return stats

    except Exception as e:
        logger.error(f"Error getting order statistics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")


@router.get("/pricing/breakdown", summary="Получение разбивки стоимости")
async def get_price_breakdown(
    duration_minutes: int = Query(..., description="Продолжительность в минутах"),
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
    scheduled_at: str = Query(None, description="Время начала (ISO format)"),
    db: AsyncSession = Depends(get_db)
):
    """Получение детальной разбивки стоимости заказа"""
    try:
        from datetime import datetime
        scheduled_time = None
        if scheduled_at:
            scheduled_time = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))

        breakdown = await PricingService.get_price_breakdown(
            db, duration_minutes, latitude, longitude, scheduled_time
        )

        return breakdown

    except Exception as e:
        logger.error(f"Error getting price breakdown: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения разбивки стоимости")
