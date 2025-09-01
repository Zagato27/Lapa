"""
Redis сессии для Payment Service
"""

import json
import logging
from typing import Optional, Dict, Any, List
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisSession:
    """Сервис для работы с Redis"""

    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True
        )

    async def cache_payment(self, payment_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование платежа"""
        try:
            await self.redis.setex(f"payment:{payment_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching payment {payment_id}: {e}")
            return False

    async def get_cached_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного платежа"""
        try:
            data = await self.redis.get(f"payment:{payment_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached payment {payment_id}: {e}")
            return None

    async def invalidate_payment_cache(self, payment_id: str):
        """Удаление кэша платежа"""
        try:
            await self.redis.delete(f"payment:{payment_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating payment cache {payment_id}: {e}")
            return False

    async def cache_wallet(self, wallet_id: str, data: Dict[str, Any], expire: int = 1800):
        """Кэширование кошелька"""
        try:
            await self.redis.setex(f"wallet:{wallet_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching wallet {wallet_id}: {e}")
            return False

    async def get_cached_wallet(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного кошелька"""
        try:
            data = await self.redis.get(f"wallet:{wallet_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached wallet {wallet_id}: {e}")
            return None

    async def invalidate_wallet_cache(self, wallet_id: str):
        """Удаление кэша кошелька"""
        try:
            await self.redis.delete(f"wallet:{wallet_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating wallet cache {wallet_id}: {e}")
            return False

    async def set_payment_session(self, session_id: str, payment_data: Dict[str, Any], expire: int = 900):
        """Установка сессии платежа"""
        try:
            await self.redis.setex(f"payment_session:{session_id}", expire, json.dumps(payment_data))
            return True
        except Exception as e:
            logger.error(f"Error setting payment session {session_id}: {e}")
            return False

    async def get_payment_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение сессии платежа"""
        try:
            data = await self.redis.get(f"payment_session:{session_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting payment session {session_id}: {e}")
            return None

    async def delete_payment_session(self, session_id: str):
        """Удаление сессии платежа"""
        try:
            await self.redis.delete(f"payment_session:{session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting payment session {session_id}: {e}")
            return False

    async def cache_exchange_rate(self, currency_pair: str, rate: float, expire: int = 3600):
        """Кэширование курса валюты"""
        try:
            await self.redis.setex(f"exchange_rate:{currency_pair}", expire, str(rate))
            return True
        except Exception as e:
            logger.error(f"Error caching exchange rate {currency_pair}: {e}")
            return False

    async def get_cached_exchange_rate(self, currency_pair: str) -> Optional[float]:
        """Получение кэшированного курса валюты"""
        try:
            data = await self.redis.get(f"exchange_rate:{currency_pair}")
            if data:
                return float(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached exchange rate {currency_pair}: {e}")
            return None

    async def set_payment_lock(self, payment_id: str, expire: int = 300):
        """Установка блокировки платежа"""
        try:
            await self.redis.setex(f"payment_lock:{payment_id}", expire, "1")
            return True
        except Exception as e:
            logger.error(f"Error setting payment lock {payment_id}: {e}")
            return False

    async def check_payment_lock(self, payment_id: str) -> bool:
        """Проверка блокировки платежа"""
        try:
            return await self.redis.exists(f"payment_lock:{payment_id}")
        except Exception as e:
            logger.error(f"Error checking payment lock {payment_id}: {e}")
            return False

    async def release_payment_lock(self, payment_id: str):
        """Снятие блокировки платежа"""
        try:
            await self.redis.delete(f"payment_lock:{payment_id}")
            return True
        except Exception as e:
            logger.error(f"Error releasing payment lock {payment_id}: {e}")
            return False

    async def cache_payment_method(self, method_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование способа оплаты"""
        try:
            await self.redis.setex(f"payment_method:{method_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching payment method {method_id}: {e}")
            return False

    async def get_cached_payment_method(self, method_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного способа оплаты"""
        try:
            data = await self.redis.get(f"payment_method:{method_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached payment method {method_id}: {e}")
            return None

    async def increment_daily_limit(self, user_id: str, amount: float) -> float:
        """Увеличение дневного лимита пользователя"""
        try:
            key = f"daily_limit:{user_id}"
            current = float(await self.redis.get(key) or "0")
            new_total = current + amount
            await self.redis.setex(key, 86400, str(new_total))  # 24 часа
            return new_total
        except Exception as e:
            logger.error(f"Error incrementing daily limit for user {user_id}: {e}")
            return 0

    async def get_daily_limit(self, user_id: str) -> float:
        """Получение дневного лимита пользователя"""
        try:
            key = f"daily_limit:{user_id}"
            data = await self.redis.get(key)
            return float(data) if data else 0
        except Exception as e:
            logger.error(f"Error getting daily limit for user {user_id}: {e}")
            return 0

    async def store_webhook_data(self, webhook_id: str, data: Dict[str, Any], expire: int = 86400):
        """Сохранение данных webhook"""
        try:
            await self.redis.setex(f"webhook:{webhook_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error storing webhook data {webhook_id}: {e}")
            return False

    async def get_webhook_data(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Получение данных webhook"""
        try:
            data = await self.redis.get(f"webhook:{webhook_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting webhook data {webhook_id}: {e}")
            return None


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session
