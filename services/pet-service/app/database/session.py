"""
Redis сессии для Pet Service
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

    async def cache_pet_profile(self, pet_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование профиля питомца"""
        try:
            await self.redis.setex(f"pet_profile:{pet_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching pet profile {pet_id}: {e}")
            return False

    async def get_cached_pet_profile(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного профиля питомца"""
        try:
            data = await self.redis.get(f"pet_profile:{pet_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached pet profile {pet_id}: {e}")
            return None

    async def invalidate_pet_cache(self, pet_id: str):
        """Удаление кэша питомца"""
        try:
            await self.redis.delete(f"pet_profile:{pet_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating pet cache {pet_id}: {e}")
            return False

    async def cache_user_pets(self, user_id: str, pets_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование списка питомцев пользователя"""
        try:
            await self.redis.setex(f"user_pets:{user_id}", expire, json.dumps(pets_data))
            return True
        except Exception as e:
            logger.error(f"Error caching user pets {user_id}: {e}")
            return False

    async def get_cached_user_pets(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированного списка питомцев пользователя"""
        try:
            data = await self.redis.get(f"user_pets:{user_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached user pets {user_id}: {e}")
            return None

    async def invalidate_user_pets_cache(self, user_id: str):
        """Удаление кэша питомцев пользователя"""
        try:
            await self.redis.delete(f"user_pets:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating user pets cache {user_id}: {e}")
            return False


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session
