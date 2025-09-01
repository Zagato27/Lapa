"""
Redis сессии для Chat Service
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

    async def cache_chat(self, chat_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование чата"""
        try:
            await self.redis.setex(f"chat:{chat_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching chat {chat_id}: {e}")
            return False

    async def get_cached_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного чата"""
        try:
            data = await self.redis.get(f"chat:{chat_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached chat {chat_id}: {e}")
            return None

    async def invalidate_chat_cache(self, chat_id: str):
        """Удаление кэша чата"""
        try:
            await self.redis.delete(f"chat:{chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating chat cache {chat_id}: {e}")
            return False

    async def cache_messages(self, chat_id: str, messages_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование сообщений чата"""
        try:
            await self.redis.setex(f"chat_messages:{chat_id}", expire, json.dumps(messages_data))
            return True
        except Exception as e:
            logger.error(f"Error caching messages for chat {chat_id}: {e}")
            return False

    async def get_cached_messages(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированных сообщений чата"""
        try:
            data = await self.redis.get(f"chat_messages:{chat_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached messages for chat {chat_id}: {e}")
            return None

    async def invalidate_messages_cache(self, chat_id: str):
        """Удаление кэша сообщений чата"""
        try:
            await self.redis.delete(f"chat_messages:{chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating messages cache for chat {chat_id}: {e}")
            return False

    async def store_websocket_connection(self, connection_id: str, user_id: str, chat_id: str):
        """Сохранение WebSocket соединения"""
        try:
            connection_data = {
                "connection_id": connection_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "connected_at": str(datetime.utcnow())
            }
            await self.redis.setex(f"websocket:{connection_id}", 3600, json.dumps(connection_data))

            # Добавление в список соединений чата
            connections_key = f"chat_websockets:{chat_id}"
            await self.redis.sadd(connections_key, connection_id)
            await self.redis.expire(connections_key, 3600)

            # Добавление в список соединений пользователя
            user_connections_key = f"user_websockets:{user_id}"
            await self.redis.sadd(user_connections_key, connection_id)
            await self.redis.expire(user_connections_key, 3600)

            return True
        except Exception as e:
            logger.error(f"Error storing websocket connection {connection_id}: {e}")
            return False

    async def remove_websocket_connection(self, connection_id: str):
        """Удаление WebSocket соединения"""
        try:
            # Получение данных соединения
            connection_data = await self.redis.get(f"websocket:{connection_id}")
            if connection_data:
                connection_info = json.loads(connection_data)
                chat_id = connection_info["chat_id"]
                user_id = connection_info["user_id"]

                # Удаление из списка соединений чата
                connections_key = f"chat_websockets:{chat_id}"
                await self.redis.srem(connections_key, connection_id)

                # Удаление из списка соединений пользователя
                user_connections_key = f"user_websockets:{user_id}"
                await self.redis.srem(user_connections_key, connection_id)

            await self.redis.delete(f"websocket:{connection_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing websocket connection {connection_id}: {e}")
            return False

    async def get_chat_websocket_connections(self, chat_id: str) -> List[str]:
        """Получение списка WebSocket соединений чата"""
        try:
            connections_key = f"chat_websockets:{chat_id}"
            connections = await self.redis.smembers(connections_key)
            return list(connections) if connections else []
        except Exception as e:
            logger.error(f"Error getting websocket connections for chat {chat_id}: {e}")
            return []

    async def get_user_websocket_connections(self, user_id: str) -> List[str]:
        """Получение списка WebSocket соединений пользователя"""
        try:
            user_connections_key = f"user_websockets:{user_id}"
            connections = await self.redis.smembers(user_connections_key)
            return list(connections) if connections else []
        except Exception as e:
            logger.error(f"Error getting websocket connections for user {user_id}: {e}")
            return []

    async def set_user_presence(self, user_id: str, chat_id: str, status: str, expire: int = 300):
        """Установка статуса присутствия пользователя"""
        try:
            presence_data = {
                "user_id": user_id,
                "chat_id": chat_id,
                "status": status,
                "last_seen": str(datetime.utcnow())
            }
            await self.redis.setex(f"presence:{user_id}:{chat_id}", expire, json.dumps(presence_data))
            return True
        except Exception as e:
            logger.error(f"Error setting user presence {user_id}:{chat_id}: {e}")
            return False

    async def get_user_presence(self, user_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса присутствия пользователя"""
        try:
            data = await self.redis.get(f"presence:{user_id}:{chat_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting user presence {user_id}:{chat_id}: {e}")
            return None

    async def set_typing_indicator(self, user_id: str, chat_id: str, is_typing: bool, expire: int = 10):
        """Установка индикатора набора текста"""
        try:
            if is_typing:
                typing_data = {
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "is_typing": True,
                    "timestamp": str(datetime.utcnow())
                }
                await self.redis.setex(f"typing:{user_id}:{chat_id}", expire, json.dumps(typing_data))
            else:
                await self.redis.delete(f"typing:{user_id}:{chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting typing indicator {user_id}:{chat_id}: {e}")
            return False

    async def get_typing_users(self, chat_id: str) -> List[Dict[str, Any]]:
        """Получение списка набирающих пользователей"""
        try:
            # Получение всех ключей с индикаторами набора для чата
            keys = await self.redis.keys(f"typing:*:{chat_id}")
            typing_users = []

            for key in keys:
                data = await self.redis.get(key)
                if data:
                    typing_users.append(json.loads(data))

            return typing_users
        except Exception as e:
            logger.error(f"Error getting typing users for chat {chat_id}: {e}")
            return []

    async def increment_message_rate_limit(self, user_id: str, chat_id: str) -> int:
        """Увеличение счетчика сообщений для rate limiting"""
        try:
            key = f"message_rate:{user_id}:{chat_id}"
            count = await self.redis.incr(key)
            await self.redis.expire(key, 60)  # Сброс каждую минуту
            return count
        except Exception as e:
            logger.error(f"Error incrementing message rate limit {user_id}:{chat_id}: {e}")
            return 0

    async def get_message_rate_limit(self, user_id: str, chat_id: str) -> int:
        """Получение счетчика сообщений для rate limiting"""
        try:
            key = f"message_rate:{user_id}:{chat_id}"
            count = await self.redis.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Error getting message rate limit {user_id}:{chat_id}: {e}")
            return 0

    async def cache_chat_participants(self, chat_id: str, participants_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование участников чата"""
        try:
            await self.redis.setex(f"chat_participants:{chat_id}", expire, json.dumps(participants_data))
            return True
        except Exception as e:
            logger.error(f"Error caching chat participants {chat_id}: {e}")
            return False

    async def get_cached_chat_participants(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированных участников чата"""
        try:
            data = await self.redis.get(f"chat_participants:{chat_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached chat participants {chat_id}: {e}")
            return None

    async def invalidate_chat_participants_cache(self, chat_id: str):
        """Удаление кэша участников чата"""
        try:
            await self.redis.delete(f"chat_participants:{chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating chat participants cache {chat_id}: {e}")
            return False

    async def store_push_notification(self, notification_id: str, data: Dict[str, Any], expire: int = 86400):
        """Сохранение push-уведомления"""
        try:
            await self.redis.setex(f"push_notification:{notification_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error storing push notification {notification_id}: {e}")
            return False

    async def get_push_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Получение push-уведомления"""
        try:
            data = await self.redis.get(f"push_notification:{notification_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting push notification {notification_id}: {e}")
            return None


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session
