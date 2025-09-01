"""
Сервис для расчёта стоимости заказов.

Назначение:
- Расчёт базовой ставки по району на основе ставок выгульщиков
- Применение временных/дневных множителей
- Возврат детализированной разбивки для UI/аналитики
"""

import logging
from typing import Dict, Any
from datetime import datetime, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.services.matching_service import MatchingService

logger = logging.getLogger(__name__)


class PricingService:
    """Сервис для расчета стоимости заказов"""

    # Базовые ставки по времени суток
    TIME_MULTIPLIERS = {
        (time(6, 0), time(10, 0)): 1.2,    # Утро (высокий спрос)
        (time(10, 0), time(17, 0)): 1.0,    # День (базовая ставка)
        (time(17, 0), time(22, 0)): 1.3,    # Вечер (высокий спрос)
        (time(22, 0), time(6, 0)): 1.5,     # Ночь (максимальная ставка)
    }

    # Множители по дням недели
    DAY_MULTIPLIERS = {
        0: 1.1,  # Понедельник
        1: 1.0,  # Вторник
        2: 1.0,  # Среда
        3: 1.0,  # Четверг
        4: 1.2,  # Пятница
        5: 1.4,  # Суббота
        6: 1.3,  # Воскресенье
    }

    @staticmethod
    async def calculate_order_price(
        db: AsyncSession,
        duration_minutes: int,
        latitude: float,
        longitude: float,
        scheduled_at: datetime = None
    ) -> Dict[str, float]:
        """Расчет стоимости заказа"""
        try:
            # Базовая стоимость за час
            base_hourly_rate = await PricingService._get_base_hourly_rate(db, latitude, longitude)

            # Применение множителей
            multiplier = 1.0

            if scheduled_at:
                # Множитель по времени суток
                time_multiplier = PricingService._get_time_multiplier(scheduled_at.time())
                multiplier *= time_multiplier

                # Множитель по дню недели
                day_multiplier = PricingService.DAY_MULTIPLIERS.get(scheduled_at.weekday(), 1.0)
                multiplier *= day_multiplier

                # Множитель по сезону/погоде (можно добавить в будущем)
                # season_multiplier = PricingService._get_season_multiplier(scheduled_at)
                # multiplier *= season_multiplier

            # Расчет стоимости
            duration_hours = duration_minutes / 60
            walker_rate = base_hourly_rate * multiplier
            walker_earnings = walker_rate * duration_hours

            # Комиссия платформы
            commission = walker_earnings * settings.platform_commission

            # Итоговая стоимость
            total_amount = walker_earnings + commission

            return {
                "base_hourly_rate": base_hourly_rate,
                "walker_rate": walker_rate,
                "walker_earnings": walker_earnings,
                "commission": commission,
                "total_amount": total_amount,
                "multiplier": multiplier
            }

        except Exception as e:
            logger.error(f"Error calculating order price: {e}")
            # Возвращаем базовую стоимость в случае ошибки
            base_rate = settings.walker_hourly_rate_min
            duration_hours = duration_minutes / 60
            walker_earnings = base_rate * duration_hours
            commission = walker_earnings * settings.platform_commission
            total_amount = walker_earnings + commission

            return {
                "base_hourly_rate": base_rate,
                "walker_rate": base_rate,
                "walker_earnings": walker_earnings,
                "commission": commission,
                "total_amount": total_amount,
                "multiplier": 1.0
            }

    @staticmethod
    async def _get_base_hourly_rate(db: AsyncSession, latitude: float, longitude: float) -> float:
        """Получение базовой ставки в зависимости от района"""
        try:
            # Поиск средней ставки выгульщиков в районе
            nearby_walkers = await MatchingService.find_nearby_walkers(
                db, latitude, longitude, radius_km=5, limit=10
            )

            if nearby_walkers:
                # Расчет средней ставки с учетом рейтинга
                total_rate = 0.0
                total_weight = 0.0

                for walker in nearby_walkers:
                    if walker.hourly_rate:
                        # Вес по рейтингу (рейтинг влияет на стоимость)
                        weight = walker.rating if walker.rating > 0 else 3.0
                        total_rate += walker.hourly_rate * weight
                        total_weight += weight

                if total_weight > 0:
                    avg_rate = total_rate / total_weight
                    # Ограничение ставки в допустимых пределах
                    return max(settings.walker_hourly_rate_min,
                             min(settings.walker_hourly_rate_max, avg_rate))

            # Возвращаем минимальную ставку, если не найдено выгульщиков
            return settings.walker_hourly_rate_min

        except Exception as e:
            logger.error(f"Error getting base hourly rate: {e}")
            return settings.walker_hourly_rate_min

    @staticmethod
    def _get_time_multiplier(order_time: time) -> float:
        """Получение множителя по времени суток"""
        for (start_time, end_time), multiplier in PricingService.TIME_MULTIPLIERS.items():
            if start_time <= end_time:
                # Обычный случай (например, 10:00 - 17:00)
                if start_time <= order_time <= end_time:
                    return multiplier
            else:
                # Переход через полночь (например, 22:00 - 06:00)
                if order_time >= start_time or order_time <= end_time:
                    return multiplier

        return 1.0  # Базовый множитель

    @staticmethod
    def _get_season_multiplier(scheduled_at: datetime) -> float:
        """Получение множителя по сезону"""
        month = scheduled_at.month

        # Летние месяцы (высокий спрос)
        if month in [6, 7, 8]:
            return 1.2

        # Осенние и весенние месяцы (средний спрос)
        elif month in [3, 4, 5, 9, 10, 11]:
            return 1.0

        # Зимние месяцы (низкий спрос)
        else:
            return 0.9

    @staticmethod
    async def get_dynamic_pricing(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """Получение динамического ценообразования"""
        try:
            # Расчет базовой стоимости
            pricing_info = await PricingService.calculate_order_price(
                db, duration_minutes, latitude, longitude, scheduled_at
            )

            # Анализ спроса в районе
            demand_multiplier = await PricingService._calculate_demand_multiplier(
                db, latitude, longitude, scheduled_at
            )

            # Корректировка стоимости по спросу
            adjusted_rate = pricing_info["walker_rate"] * demand_multiplier
            adjusted_earnings = adjusted_rate * (duration_minutes / 60)
            adjusted_commission = adjusted_earnings * settings.platform_commission
            adjusted_total = adjusted_earnings + adjusted_commission

            return {
                "base_pricing": pricing_info,
                "demand_multiplier": demand_multiplier,
                "adjusted_rate": adjusted_rate,
                "adjusted_earnings": adjusted_earnings,
                "adjusted_commission": adjusted_commission,
                "adjusted_total": adjusted_total,
                "savings_percentage": ((pricing_info["total_amount"] - adjusted_total) / pricing_info["total_amount"]) * 100
            }

        except Exception as e:
            logger.error(f"Error calculating dynamic pricing: {e}")
            # Возвращаем базовую стоимость в случае ошибки
            pricing_info = await PricingService.calculate_order_price(
                db, duration_minutes, latitude, longitude, scheduled_at
            )
            return {
                "base_pricing": pricing_info,
                "demand_multiplier": 1.0,
                "adjusted_rate": pricing_info["walker_rate"],
                "adjusted_earnings": pricing_info["walker_earnings"],
                "adjusted_commission": pricing_info["commission"],
                "adjusted_total": pricing_info["total_amount"],
                "savings_percentage": 0.0
            }

    @staticmethod
    async def _calculate_demand_multiplier(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        scheduled_at: datetime
    ) -> float:
        """Расчет множителя спроса"""
        try:
            # Поиск заказов в районе за последние 24 часа
            from datetime import timedelta
            time_window = scheduled_at - timedelta(hours=24)

            # Подсчет заказов в районе
            orders_count = await db.execute(
                select(func.count()).select_from('orders').where(
                    and_(
                        func.ST_DWithin('location', f'ST_GeomFromText(\'POINT({longitude} {latitude})\', 4326)', 5000),
                        'created_at >= time_window',
                        'status IN (\'confirmed\', \'in_progress\', \'completed\')'
                    )
                )
            )

            recent_orders = orders_count.scalar()

            # Расчет множителя на основе спроса
            if recent_orders < 5:
                return 0.9  # Низкий спрос - скидка
            elif recent_orders < 15:
                return 1.0  # Нормальный спрос
            elif recent_orders < 25:
                return 1.1  # Высокий спрос
            else:
                return 1.2  # Очень высокий спрос

        except Exception as e:
            logger.error(f"Error calculating demand multiplier: {e}")
            return 1.0

    @staticmethod
    async def get_price_breakdown(
        db: AsyncSession,
        duration_minutes: int,
        latitude: float,
        longitude: float,
        scheduled_at: datetime = None
    ) -> Dict[str, Any]:
        """Получение детальной разбивки стоимости"""
        try:
            pricing_info = await PricingService.calculate_order_price(
                db, duration_minutes, latitude, longitude, scheduled_at
            )

            duration_hours = duration_minutes / 60

            breakdown = {
                "duration_hours": duration_hours,
                "base_hourly_rate": pricing_info["base_hourly_rate"],
                "applied_multipliers": {
                    "time_of_day": PricingService._get_time_multiplier(scheduled_at.time()) if scheduled_at else 1.0,
                    "day_of_week": PricingService.DAY_MULTIPLIERS.get(scheduled_at.weekday(), 1.0) if scheduled_at else 1.0,
                },
                "final_hourly_rate": pricing_info["walker_rate"],
                "walker_earnings": pricing_info["walker_earnings"],
                "platform_commission": pricing_info["commission"],
                "total_amount": pricing_info["total_amount"],
                "commission_percentage": settings.platform_commission * 100
            }

            return breakdown

        except Exception as e:
            logger.error(f"Error getting price breakdown: {e}")
            return {
                "duration_hours": duration_minutes / 60,
                "error": "Unable to calculate price breakdown"
            }
