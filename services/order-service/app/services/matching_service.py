"""
Сервис для сопоставления заказов и выгульщиков.

Назначение:
- Поиск ближайших выгульщиков (через БД user-service или кэш API Gateway)
- Оценка стоимости вместе с PricingService
- Подбор лучшего выгульщика для конкретного заказа

Важные примечания:
- Избегаем небезопасных SQL строк; используем параметризацию
- Кэшируем результаты поиска по округлённым координатам
"""

import logging
import math
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from geoalchemy2 import WKTElement

from app.config import settings
from app.database.session import get_session
from app.models.order import Order, OrderStatus
from app.schemas.order import NearbyWalker, OrderEstimateResponse

logger = logging.getLogger(__name__)


class MatchingService:
    """Сервис для сопоставления заказов и выгульщиков"""

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Расчет расстояния между двумя точками по формуле гаверсинуса (в километрах)"""
        R = 6371.0  # Радиус Земли в километрах

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    async def find_nearby_walkers(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = None,
        limit: int = None
    ) -> List[NearbyWalker]:
        """Поиск выгульщиков рядом с указанной точкой"""
        try:
            if radius_km is None:
                radius_km = settings.default_search_radius / 1000  # перевод в километры
            if limit is None:
                limit = 10

            # Проверка кэша
            redis_session = await get_session()
            # Ключ кэша по округлённым координатам (2 знака после запятой ~1.1 км)
            location_key = f"{latitude:.2f}:{longitude:.2f}:{radius_km or 0}:{limit or 0}"
            cached_walkers = await redis_session.get_cached_nearby_walkers(location_key)

            if cached_walkers:
                return [NearbyWalker(**walker) for walker in cached_walkers]

            # SQL запрос для поиска выгульщиков в радиусе
            # Параметризованный запрос через text() для PostGIS функций
            walkers_query = text(
                """
                SELECT
                    u.id, u.first_name, u.last_name, u.avatar_url, u.rating,
                    u.total_orders, u.completed_orders, u.latitude, u.longitude,
                    u.hourly_rate, u.services_offered, u.bio,
                    ST_Distance(u.location, ST_GeogFromText(:walker_point)) as distance_meters,
                    EXTRACT(EPOCH FROM (NOW() - u.last_login_at))/60 as minutes_since_last_login
                FROM users u
                WHERE
                    u.role = 'walker'
                    AND u.is_active = true
                    AND u.is_walker_verified = true
                    AND u.location IS NOT NULL
                    AND u.rating >= :min_rating
                    AND ST_DWithin(
                        u.location::geography,
                        ST_GeogFromText(:walker_point),
                        :radius_meters
                    )
                ORDER BY distance_meters
                LIMIT :limit
                """
            )

            walker_point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
            result = await db.execute(
                walkers_query,
                {
                    "walker_point": walker_point_wkt,
                    "min_rating": settings.min_rating_for_orders,
                    "radius_meters": (radius_km * 1000),
                    "limit": limit,
                },
            )

            rows = result.fetchall()
            walkers = []

            for row in rows:
                # Расчет примерного времени прибытия (предполагаем скорость 5 км/ч пешком)
                walking_speed_kmh = 5
                distance_km = row.distance_meters / 1000
                estimated_arrival_minutes = int((distance_km / walking_speed_kmh) * 60)

                walker = NearbyWalker(
                    id=row.id,
                    first_name=row.first_name,
                    last_name=row.last_name,
                    avatar_url=row.avatar_url,
                    rating=row.rating,
                    total_orders=row.total_orders,
                    completed_orders=row.completed_orders,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    distance=row.distance_meters,
                    hourly_rate=row.hourly_rate,
                    services_offered=row.services_offered,
                    bio=row.bio,
                    estimated_arrival_minutes=estimated_arrival_minutes
                )
                walkers.append(walker)

            # Кэширование результатов
            walkers_data = [walker.dict() for walker in walkers]
            await redis_session.cache_nearby_walkers(location_key, walkers_data)

            return walkers

        except Exception as e:
            logger.error(f"Error finding nearby walkers: {e}")
            return []

    @staticmethod
    async def find_pending_orders_for_walker(db: AsyncSession, walker_id: str) -> List[Order]:
        """Поиск ожидающих заказов для выгульщика"""
        try:
            # Получение информации о выгульщике
            # Получение геопозиции выгульщика (параметризовано)
            walker_point_query = text(
                "SELECT ST_AsText(location) FROM users WHERE id = :walker_id AND role = 'walker' AND is_active = true"
            )
            walker_result = await db.execute(walker_point_query, {"walker_id": walker_id})
            walker_location = walker_result.scalar()

            if not walker_location:
                return []

            # Поиск заказов в радиусе выгульщика
            orders_query = text(
                """
                SELECT o.* FROM orders o
                WHERE
                    o.status = 'pending'
                    AND o.scheduled_at > NOW()
                    AND o.scheduled_at <= NOW() + INTERVAL '2 hours'
                    AND ST_DWithin(
                        o.location::geography,
                        ST_GeogFromText(:walker_point),
                        :radius_meters
                    )
                ORDER BY o.scheduled_at, ST_Distance(o.location, ST_GeogFromText(:walker_point))
                LIMIT 10
                """
            )

            result = await db.execute(
                orders_query,
                {
                    "walker_point": f"SRID=4326;{walker_location}",
                    "radius_meters": settings.default_search_radius,
                },
            )

            orders = []
            orders = [Order(**dict(row)) for row in result.mappings()]

            return orders

        except Exception as e:
            logger.error(f"Error finding pending orders for walker {walker_id}: {e}")
            return []

    @staticmethod
    async def calculate_order_estimate(
        db: AsyncSession,
        pet_id: str,
        latitude: float,
        longitude: float,
        duration_minutes: int
    ) -> OrderEstimateResponse:
        """Расчет стоимости заказа и поиск доступных выгульщиков"""
        try:
            from app.services.pricing_service import PricingService

            # Расчет стоимости
            pricing_info = await PricingService.calculate_order_price(
                db, duration_minutes, latitude, longitude
            )

            # Поиск выгульщиков рядом
            nearby_walkers = await MatchingService.find_nearby_walkers(
                db, latitude, longitude, limit=5
            )

            return OrderEstimateResponse(
                estimated_cost=pricing_info["total_amount"],
                platform_commission=pricing_info["commission"],
                walker_earnings=pricing_info["walker_earnings"],
                available_walkers=nearby_walkers,
                estimated_duration=duration_minutes
            )

        except Exception as e:
            logger.error(f"Error calculating order estimate: {e}")
            # Возвращаем пустой результат в случае ошибки
            return OrderEstimateResponse(
                estimated_cost=0.0,
                platform_commission=0.0,
                walker_earnings=0.0,
                available_walkers=[],
                estimated_duration=duration_minutes
            )

    @staticmethod
    async def match_order_to_walker(db: AsyncSession, order: Order) -> Optional[str]:
        """Автоматическое сопоставление заказа выгульщику"""
        try:
            # Поиск подходящих выгульщиков
            nearby_walkers = await MatchingService.find_nearby_walkers(
                db,
                order.latitude,
                order.longitude,
                limit=5
            )

            if not nearby_walkers:
                return None

            # Выбор лучшего выгульщика (по рейтингу и расстоянию)
            best_walker = max(nearby_walkers, key=lambda w:
                (w.rating * 0.7) + ((10000 - w.distance) / 10000 * 0.3)  # 70% рейтинг, 30% расстояние
            )

            return best_walker.id

        except Exception as e:
            logger.error(f"Error matching order {order.id} to walker: {e}")
            return None

    @staticmethod
    async def check_walker_availability(
        db: AsyncSession,
        walker_id: str,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> bool:
        """Проверка доступности выгульщика на указанное время"""
        try:
            # Проверка количества заказов в день
            start_of_day = scheduled_at.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            daily_orders_count = await db.execute(
                select(func.count()).where(
                    and_(
                        Order.walker_id == walker_id,
                        Order.scheduled_at >= start_of_day,
                        Order.scheduled_at < end_of_day,
                        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED])
                    )
                )
            )

            if daily_orders_count.scalar() >= settings.max_orders_per_day:
                return False

            # Проверка пересечения времени с существующими заказами
            order_end_time = scheduled_at + timedelta(minutes=duration_minutes)

            overlapping_orders = await db.execute(
                select(func.count()).where(
                    and_(
                        Order.walker_id == walker_id,
                        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]),
                        or_(
                            and_(
                                Order.scheduled_at <= scheduled_at,
                                func.dateadd(Order.scheduled_at, text(f"interval '{Order.duration_minutes} minutes'")) > scheduled_at
                            ),
                            and_(
                                Order.scheduled_at < order_end_time,
                                func.dateadd(Order.scheduled_at, text(f"interval '{Order.duration_minutes} minutes'")) >= order_end_time
                            ),
                            and_(
                                Order.scheduled_at >= scheduled_at,
                                func.dateadd(Order.scheduled_at, text(f"interval '{Order.duration_minutes} minutes'")) <= order_end_time
                            )
                        )
                    )
                )
            )

            return overlapping_orders.scalar() == 0

        except Exception as e:
            logger.error(f"Error checking walker availability {walker_id}: {e}")
            return False

    @staticmethod
    async def get_walker_schedule(db: AsyncSession, walker_id: str, date: datetime) -> Dict[str, Any]:
        """Получение расписания выгульщика на указанную дату"""
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            # Получение заказов на день
            orders_query = select(Order).where(
                and_(
                    Order.walker_id == walker_id,
                    Order.scheduled_at >= start_of_day,
                    Order.scheduled_at < end_of_day,
                    Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED])
                )
            ).order_by(Order.scheduled_at)

            result = await db.execute(orders_query)
            orders = result.scalars().all()

            # Формирование расписания
            schedule = {
                "date": date.date().isoformat(),
                "walker_id": walker_id,
                "orders": [],
                "available_slots": []
            }

            for order in orders:
                order_info = {
                    "order_id": order.id,
                    "start_time": order.scheduled_at.isoformat(),
                    "end_time": (order.scheduled_at + timedelta(minutes=order.duration_minutes)).isoformat(),
                    "client_id": order.client_id,
                    "pet_id": order.pet_id,
                    "status": order.status.value
                }
                schedule["orders"].append(order_info)

            return schedule

        except Exception as e:
            logger.error(f"Error getting walker schedule {walker_id}: {e}")
            return {
                "date": date.date().isoformat(),
                "walker_id": walker_id,
                "orders": [],
                "available_slots": []
            }
