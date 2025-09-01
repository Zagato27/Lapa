"""
Redis сессии для User Service
"""

import json
import logging
from typing import Optional, Dict, Any
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

    async def set_session(self, session_id: str, data: Dict[str, Any], expire: int = 3600):
        """Сохранение сессии"""
        try:
            await self.redis.setex(f"session:{session_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error setting session {session_id}: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение сессии"""
        try:
            data = await self.redis.get(f"session:{session_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def delete_session(self, session_id: str):
        """Удаление сессии"""
        try:
            await self.redis.delete(f"session:{session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def set_refresh_token(self, user_id: str, token: str, expire: int):
        """Сохранение refresh token"""
        try:
            await self.redis.setex(f"refresh_token:{user_id}", expire, token)
            return True
        except Exception as e:
            logger.error(f"Error setting refresh token for user {user_id}: {e}")
            return False

    async def get_refresh_token(self, user_id: str) -> Optional[str]:
        """Получение refresh token"""
        try:
            return await self.redis.get(f"refresh_token:{user_id}")
        except Exception as e:
            logger.error(f"Error getting refresh token for user {user_id}: {e}")
            return None

    async def delete_refresh_token(self, user_id: str):
        """Удаление refresh token"""
        try:
            await self.redis.delete(f"refresh_token:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting refresh token for user {user_id}: {e}")
            return False


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session
