"""
Основной сервис для управления заказами.

Функциональность:
- Создание, обновление, изменение статуса заказов
- Добавление отзывов
- Получение списков и статистики с кэшированием через Redis

Используется в эндпоинтах `app.api.v1.orders`.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from geoalchemy2 import WKTElement

from app.config import settings
from app.database.session import get_session
from app.models.order import Order, OrderStatus, OrderType
from app.models.order_review import OrderReview
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderProfile,
    OrderReviewCreate,
    OrdersListResponse,
    OrderCancellationRequest
)

logger = logging.getLogger(__name__)


class OrderService:
    """Сервис для работы с заказами"""

    @staticmethod
    async def create_order(db: AsyncSession, client_id: str, order_data: OrderCreate) -> Order:
        """Создание нового заказа"""
        try:
            order_id = str(uuid.uuid4())

            # Расчет стоимости заказа
            from app.services.pricing_service import PricingService
            pricing_info = await PricingService.calculate_order_price(
                db, order_data.duration_minutes, order_data.latitude, order_data.longitude
            )

            # Создание геометрии для PostGIS
            location_geom = WKTElement(f'POINT({order_data.longitude} {order_data.latitude})', srid=4326)

            order = Order(
                id=order_id,
                client_id=client_id,
                pet_id=order_data.pet_id,
                order_type=order_data.order_type,
                status=OrderStatus.PENDING,
                scheduled_at=order_data.scheduled_at,
                duration_minutes=order_data.duration_minutes,
                location=location_geom,
                latitude=order_data.latitude,
                longitude=order_data.longitude,
                address=order_data.address,
                walker_hourly_rate=pricing_info["walker_rate"],
                total_amount=pricing_info["total_amount"],
                platform_commission=pricing_info["commission"],
                walker_earnings=pricing_info["walker_earnings"],
                special_instructions=order_data.special_instructions
            )

            db.add(order)
            await db.commit()
            await db.refresh(order)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_user_orders_cache(client_id)

            logger.info(f"Order created successfully: {order.id} for client {client_id}")
            return order

        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: str, user_id: Optional[str] = None) -> Optional[Order]:
        """Получение заказа по ID"""
        try:
            query = select(Order).where(Order.id == order_id)

            if user_id:
                query = query.where(
                    or_(Order.client_id == user_id, Order.walker_id == user_id)
                )

            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None

    @staticmethod
    async def update_order(db: AsyncSession, order_id: str, client_id: str, order_data: OrderUpdate) -> Optional[Order]:
        """Обновление заказа"""
        try:
            update_data = order_data.dict(exclude_unset=True)

            if not update_data:
                return await OrderService.get_order_by_id(db, order_id, client_id)

            # Проверка, что заказ можно обновлять
            order = await OrderService.get_order_by_id(db, order_id, client_id)
            if not order or order.client_id != client_id:
                return None

            if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
                raise ValueError("Нельзя обновлять заказ в текущем статусе")

            stmt = (
                update(Order)
                .where(Order.id == order_id, Order.client_id == client_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                return None

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_cache(order_id)
            await redis_session.invalidate_user_orders_cache(client_id)

            return await OrderService.get_order_by_id(db, order_id, client_id)

        except Exception as e:
            logger.error(f"Order update failed for {order_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def confirm_order(db: AsyncSession, order_id: str, walker_id: str) -> bool:
        """Подтверждение заказа выгульщиком"""
        try:
            # Получение заказа
            order = await OrderService.get_order_by_id(db, order_id)
            if not order or order.status != OrderStatus.PENDING:
                return False

            # Проверка, что заказ еще актуален
            if order.scheduled_at < datetime.utcnow():
                return False

            # Подтверждение заказа
            order.confirm(walker_id)
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_cache(order_id)
            await redis_session.invalidate_user_orders_cache(order.client_id)
            await redis_session.invalidate_user_orders_cache(walker_id)

            logger.info(f"Order {order_id} confirmed by walker {walker_id}")
            return True

        except Exception as e:
            logger.error(f"Order confirmation failed for {order_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def start_walk(db: AsyncSession, order_id: str, walker_id: str) -> bool:
        """Начало прогулки"""
        try:
            order = await OrderService.get_order_by_id(db, order_id)
            if not order or order.walker_id != walker_id or order.status != OrderStatus.CONFIRMED:
                return False

            # Проверка времени начала
            time_until_start = (order.scheduled_at - datetime.utcnow()).total_seconds() / 3600
            if abs(time_until_start) > 0.5:  # ±30 минут
                return False

            order.start_walk()
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_cache(order_id)

            logger.info(f"Walk started for order {order_id}")
            return True

        except Exception as e:
            logger.error(f"Walk start failed for {order_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def complete_walk(db: AsyncSession, order_id: str, walker_id: str) -> bool:
        """Завершение прогулки"""
        try:
            order = await OrderService.get_order_by_id(db, order_id)
            if not order or order.walker_id != walker_id or order.status != OrderStatus.IN_PROGRESS:
                return False

            order.complete_walk()
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_cache(order_id)
            await redis_session.invalidate_user_orders_cache(order.client_id)
            await redis_session.invalidate_user_orders_cache(walker_id)

            logger.info(f"Walk completed for order {order_id}")
            return True

        except Exception as e:
            logger.error(f"Walk completion failed for {order_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def cancel_order(
        db: AsyncSession,
        order_id: str,
        cancelled_by: str,
        cancellation_data: OrderCancellationRequest
    ) -> bool:
        """Отмена заказа"""
        try:
            order = await OrderService.get_order_by_id(db, order_id)
            if not order:
                return False

            # Проверка прав на отмену
            can_cancel = (
                (order.client_id == cancelled_by and order.can_be_cancelled_by_client) or
                (order.walker_id == cancelled_by and order.can_be_cancelled_by_walker)
            )

            if not can_cancel:
                return False

            order.cancel(cancelled_by, cancellation_data.reason)
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_cache(order_id)
            await redis_session.invalidate_user_orders_cache(order.client_id)
            if order.walker_id:
                await redis_session.invalidate_user_orders_cache(order.walker_id)

            logger.info(f"Order {order_id} cancelled by {cancelled_by}")
            return True

        except Exception as e:
            logger.error(f"Order cancellation failed for {order_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_user_orders(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        order_type: Optional[str] = None
    ) -> OrdersListResponse:
        """Получение списка заказов пользователя"""
        try:
            offset = (page - 1) * limit

            # Проверка кэша (составной ключ по параметрам запроса)
            redis_session = await get_session()
            cache_key = f"{user_id}:{page}:{limit}:{status or ''}:{order_type or ''}"
            cached_orders = await redis_session.get_cached_user_orders_by_key(cache_key)

            if cached_orders:
                # Примечание: здесь уже сериализованные словари Order
                return OrdersListResponse(
                    orders=[OrderProfile(**order) for order in cached_orders],
                    total=len(cached_orders),
                    page=page,
                    limit=limit,
                    pages=1
                )

            # Построение запроса
            query = select(Order).where(
                or_(Order.client_id == user_id, Order.walker_id == user_id)
            )

            if status:
                # Перевод строки в Enum при необходимости
                try:
                    from app.models.order import OrderStatus, OrderType
                    query = query.where(Order.status == OrderStatus(status))
                except Exception:
                    query = query.where(Order.status == status)
            if order_type:
                try:
                    from app.models.order import OrderType
                    query = query.where(Order.order_type == OrderType(order_type))
                except Exception:
                    query = query.where(Order.order_type == order_type)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение заказов с пагинацией
            query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
            result = await db.execute(query)
            orders = result.scalars().all()

            # Кэширование результатов
            if page == 1 and len(orders) < 50:
                orders_data = [OrderService.order_to_dict(order) for order in orders]
                await redis_session.cache_user_orders_by_key(cache_key, orders_data)

            pages = (total + limit - 1) // limit

            return OrdersListResponse(
                orders=[OrderService.order_to_profile(order) for order in orders],
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error getting user orders for {user_id}: {e}")
            return OrdersListResponse(orders=[], total=0, page=page, limit=limit, pages=0)

    @staticmethod
    async def add_order_review(
        db: AsyncSession,
        order_id: str,
        reviewer_id: str,
        review_data: OrderReviewCreate
    ) -> Optional[OrderReview]:
        """Добавление отзыва о заказе"""
        try:
            order = await OrderService.get_order_by_id(db, order_id)
            if not order or order.status != OrderStatus.COMPLETED:
                return None

            # Определение типа ревьюера и получателя
            if order.client_id == reviewer_id:
                reviewer_type = "client"
                reviewee_id = order.walker_id
                reviewee_type = "walker"
                # Добавление рейтинга в заказ
                order.client_rating = review_data.rating
                order.client_review = review_data.comment
            elif order.walker_id == reviewer_id:
                reviewer_type = "walker"
                reviewee_id = order.client_id
                reviewee_type = "client"
                # Добавление рейтинга в заказ
                order.walker_rating = review_data.rating
                order.walker_review = review_data.comment
            else:
                return None

            review_id = str(uuid.uuid4())

            review = OrderReview(
                id=review_id,
                order_id=order_id,
                reviewer_id=reviewer_id,
                reviewer_type=reviewer_type,
                reviewee_id=reviewee_id,
                reviewee_type=reviewee_type,
                rating=review_data.rating,
                title=review_data.title,
                comment=review_data.comment,
                punctuality_rating=review_data.punctuality_rating,
                communication_rating=review_data.communication_rating,
                pet_care_rating=review_data.pet_care_rating,
                overall_experience=review_data.overall_experience,
                is_anonymous=review_data.is_anonymous
            )

            db.add(review)
            await db.commit()
            await db.refresh(review)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_cache(order_id)

            logger.info(f"Review added for order {order_id} by {reviewer_id}")
            return review

        except Exception as e:
            logger.error(f"Review creation failed for order {order_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_pending_orders_for_walker(db: AsyncSession, walker_id: str) -> List[Order]:
        """Получение ожидающих заказов для выгульщика"""
        try:
            # Заказы в радиусе выгульщика, ожидающие подтверждения
            from app.services.matching_service import MatchingService
            return await MatchingService.find_pending_orders_for_walker(db, walker_id)

        except Exception as e:
            logger.error(f"Error getting pending orders for walker {walker_id}: {e}")
            return []

    @staticmethod
    async def get_orders_statistics(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Получение статистики заказов пользователя"""
        try:
            # Общее количество заказов
            total_orders = await db.execute(
                select(func.count()).where(
                    or_(Order.client_id == user_id, Order.walker_id == user_id)
                )
            )
            total_orders = total_orders.scalar()

            # Количество по статусам
            status_stats = await db.execute(
                select(Order.status, func.count()).where(
                    or_(Order.client_id == user_id, Order.walker_id == user_id)
                ).group_by(Order.status)
            )
            status_counts = dict(status_stats.fetchall())

            # Средний рейтинг
            avg_rating = await db.execute(
                select(func.avg(Order.client_rating)).where(
                    Order.walker_id == user_id, Order.client_rating.isnot(None)
                )
            )
            avg_rating = avg_rating.scalar()

            return {
                "total_orders": total_orders,
                "status_counts": status_counts,
                "average_rating": float(avg_rating) if avg_rating else 0.0
            }

        except Exception as e:
            logger.error(f"Error getting order statistics for {user_id}: {e}")
            return {"total_orders": 0, "status_counts": {}, "average_rating": 0.0}

    @staticmethod
    def order_to_profile(order: Order) -> OrderProfile:
        """Преобразование модели Order в схему OrderProfile"""
        return OrderProfile(
            id=order.id,
            client_id=order.client_id,
            walker_id=order.walker_id,
            pet_id=order.pet_id,
            order_type=order.order_type,
            status=order.status,
            scheduled_at=order.scheduled_at,
            duration_minutes=order.duration_minutes,
            actual_start_time=order.actual_start_time,
            actual_end_time=order.actual_end_time,
            latitude=order.latitude,
            longitude=order.longitude,
            address=order.address,
            walker_hourly_rate=order.walker_hourly_rate,
            total_amount=order.total_amount,
            platform_commission=order.platform_commission,
            walker_earnings=order.walker_earnings,
            special_instructions=order.special_instructions,
            walker_notes=order.walker_notes,
            client_rating=order.client_rating,
            walker_rating=order.walker_rating,
            client_review=order.client_review,
            walker_review=order.walker_review,
            created_at=order.created_at,
            updated_at=order.updated_at,
            confirmed_at=order.confirmed_at,
            completed_at=order.completed_at,
            cancelled_at=order.cancelled_at,
            cancellation_reason=order.cancellation_reason,
            cancelled_by=order.cancelled_by,
            duration_hours=order.duration_hours,
            actual_duration_minutes=order.actual_duration_minutes,
            can_be_cancelled_by_client=order.can_be_cancelled_by_client,
            can_be_cancelled_by_walker=order.can_be_cancelled_by_walker
        )

    @staticmethod
    def order_to_dict(order: Order) -> Dict[str, Any]:
        """Преобразование модели Order в словарь для кэширования"""
        return {
            "id": order.id,
            "client_id": order.client_id,
            "walker_id": order.walker_id,
            "pet_id": order.pet_id,
            "order_type": order.order_type.value,
            "status": order.status.value,
            "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
            "duration_minutes": order.duration_minutes,
            "actual_start_time": order.actual_start_time.isoformat() if order.actual_start_time else None,
            "actual_end_time": order.actual_end_time.isoformat() if order.actual_end_time else None,
            "latitude": order.latitude,
            "longitude": order.longitude,
            "address": order.address,
            "walker_hourly_rate": order.walker_hourly_rate,
            "total_amount": order.total_amount,
            "platform_commission": order.platform_commission,
            "walker_earnings": order.walker_earnings,
            "special_instructions": order.special_instructions,
            "walker_notes": order.walker_notes,
            "client_rating": order.client_rating,
            "walker_rating": order.walker_rating,
            "client_review": order.client_review,
            "walker_review": order.walker_review,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
            "completed_at": order.completed_at.isoformat() if order.completed_at else None,
            "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
            "cancellation_reason": order.cancellation_reason,
            "cancelled_by": order.cancelled_by
        }
