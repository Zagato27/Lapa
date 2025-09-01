"""
Работа с Redis для Order Service.

Назначение:
- Кэширование заказов и их списков
- Кэширование результатов геопоиска выгульщиков
- Флаги ожидающих подтверждения заказов

Используется сервисами: `OrderService`, `MatchingService`, `GatewayService` (через общее подключение).
"""

import json
import logging
from typing import Optional, Dict, Any, List
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisSession:
    """Сервис для работы с Redis.

    Экземпляр создаётся один на процесс и реиспользуется через `get_session`.
    Методы ориентированы на высокоуровневые операции, используемые сервисами.
    """

    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True
        )

    async def cache_order(self, order_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование заказа"""
        try:
            await self.redis.setex(f"order:{order_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching order {order_id}: {e}")
            return False

    async def get_cached_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного заказа"""
        try:
            data = await self.redis.get(f"order:{order_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached order {order_id}: {e}")
            return None

    async def invalidate_order_cache(self, order_id: str):
        """Удаление кэша заказа"""
        try:
            await self.redis.delete(f"order:{order_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating order cache {order_id}: {e}")
            return False

    async def cache_user_orders(self, user_id: str, orders_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование списка заказов пользователя (обобщённый ключ по user_id).

        Применимо, когда параметры фильтрации стандартные/по умолчанию.
        """
        try:
            await self.redis.setex(f"user_orders:{user_id}", expire, json.dumps(orders_data))
            return True
        except Exception as e:
            logger.error(f"Error caching user orders {user_id}: {e}")
            return False

    async def get_cached_user_orders(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированного списка заказов пользователя по user_id."""
        try:
            data = await self.redis.get(f"user_orders:{user_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached user orders {user_id}: {e}")
            return None

    async def invalidate_user_orders_cache(self, user_id: str):
        """Удаление кэша заказов пользователя.

        Удаляет как простой ключ `user_orders:{user_id}`, так и все составные ключи вида
        `user_orders:*{user_id}*` (для кэша со страницами/фильтрами).
        """
        try:
            # Базовый ключ
            await self.redis.delete(f"user_orders:{user_id}")

            # Составные ключи (через scan_iter для избежания блокировок)
            pattern = f"user_orders:*{user_id}*"
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error invalidating user orders cache {user_id}: {e}")
            return False

    async def cache_user_orders_by_key(self, key_suffix: str, orders_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование списка заказов пользователя по составному ключу (пагинация/фильтры)."""
        try:
            await self.redis.setex(f"user_orders:{key_suffix}", expire, json.dumps(orders_data))
            return True
        except Exception as e:
            logger.error(f"Error caching user orders by key {key_suffix}: {e}")
            return False

    async def get_cached_user_orders_by_key(self, key_suffix: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэша списка заказов по составному ключу (пагинация/фильтры)."""
        try:
            data = await self.redis.get(f"user_orders:{key_suffix}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached user orders by key {key_suffix}: {e}")
            return None

    async def set_pending_order(self, order_id: str, walker_id: str, expire: int = 300):
        """Установка ожидающего подтверждения заказа для выгульщика"""
        try:
            await self.redis.setex(f"pending_order:{walker_id}:{order_id}", expire, "1")
            return True
        except Exception as e:
            logger.error(f"Error setting pending order {order_id} for walker {walker_id}: {e}")
            return False

    async def check_pending_order(self, walker_id: str, order_id: str) -> bool:
        """Проверка ожидающего подтверждения заказа"""
        try:
            return await self.redis.exists(f"pending_order:{walker_id}:{order_id}")
        except Exception as e:
            logger.error(f"Error checking pending order {order_id} for walker {walker_id}: {e}")
            return False

    async def remove_pending_order(self, walker_id: str, order_id: str):
        """Удаление ожидающего подтверждения заказа"""
        try:
            await self.redis.delete(f"pending_order:{walker_id}:{order_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing pending order {order_id} for walker {walker_id}: {e}")
            return False

    async def cache_nearby_walkers(self, location_key: str, walkers_data: List[Dict[str, Any]], expire: int = 600):
        """Кэширование списка выгульщиков рядом по ключу местоположения."""
        try:
            await self.redis.setex(f"nearby_walkers:{location_key}", expire, json.dumps(walkers_data))
            return True
        except Exception as e:
            logger.error(f"Error caching nearby walkers for {location_key}: {e}")
            return False

    async def get_cached_nearby_walkers(self, location_key: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированного списка выгульщиков рядом по ключу местоположения."""
        try:
            data = await self.redis.get(f"nearby_walkers:{location_key}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached nearby walkers for {location_key}: {e}")
            return None


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session
