"""
Redis сессии для Notification Service
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

    async def cache_template(self, template_id: str, template_data: Dict[str, Any], expire: int = 3600):
        """Кэширование шаблона"""
        try:
            await self.redis.setex(f"template:{template_id}", expire, json.dumps(template_data))
            return True
        except Exception as e:
            logger.error(f"Error caching template {template_id}: {e}")
            return False

    async def get_cached_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного шаблона"""
        try:
            data = await self.redis.get(f"template:{template_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached template {template_id}: {e}")
            return None

    async def invalidate_template_cache(self, template_id: str):
        """Удаление кэша шаблона"""
        try:
            await self.redis.delete(f"template:{template_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating template cache {template_id}: {e}")
            return False

    async def cache_subscription(self, user_id: str, subscription_data: Dict[str, Any], expire: int = 1800):
        """Кэширование подписки пользователя"""
        try:
            await self.redis.setex(f"subscription:{user_id}", expire, json.dumps(subscription_data))
            return True
        except Exception as e:
            logger.error(f"Error caching subscription {user_id}: {e}")
            return False

    async def get_cached_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированной подписки"""
        try:
            data = await self.redis.get(f"subscription:{user_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached subscription {user_id}: {e}")
            return None

    async def invalidate_subscription_cache(self, user_id: str):
        """Удаление кэша подписки"""
        try:
            await self.redis.delete(f"subscription:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating subscription cache {user_id}: {e}")
            return False

    async def queue_notification(self, notification_data: Dict[str, Any]) -> str:
        """Добавление уведомления в очередь"""
        try:
            queue_key = "notifications:queue"
            notification_id = notification_data.get("id")

            # Добавление в очередь с приоритетом
            priority = notification_data.get("priority", "normal")
            priority_scores = {"urgent": 4, "high": 3, "normal": 2, "low": 1}
            score = priority_scores.get(priority, 2)

            await self.redis.zadd(queue_key, {json.dumps(notification_data): score})
            return notification_id

        except Exception as e:
            logger.error(f"Error queuing notification: {e}")
            raise

    async def dequeue_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Извлечение уведомлений из очереди"""
        try:
            queue_key = "notifications:queue"

            # Получение уведомлений с наивысшим приоритетом
            notifications = await self.redis.zrevrange(queue_key, 0, limit - 1, withscores=True)

            result = []
            for notification_json, score in notifications:
                notification_data = json.loads(notification_json)
                result.append(notification_data)

                # Удаление из очереди
                await self.redis.zrem(queue_key, notification_json)

            return result

        except Exception as e:
            logger.error(f"Error dequeuing notifications: {e}")
            return []

    async def get_queue_length(self) -> int:
        """Получение длины очереди"""
        try:
            queue_key = "notifications:queue"
            return await self.redis.zcard(queue_key)
        except Exception as e:
            logger.error(f"Error getting queue length: {e}")
            return 0

    async def increment_user_notification_count(self, user_id: str, channel: str) -> int:
        """Увеличение счетчика уведомлений пользователя"""
        try:
            key = f"user_notifications:{user_id}:{channel}"
            count = await self.redis.incr(key)

            # Установка срока действия (24 часа)
            await self.redis.expire(key, 86400)
            return count

        except Exception as e:
            logger.error(f"Error incrementing user notification count {user_id}:{channel}: {e}")
            return 0

    async def check_rate_limit(self, user_id: str, channel: str) -> bool:
        """Проверка лимита уведомлений для пользователя"""
        try:
            count = await self.increment_user_notification_count(user_id, channel)
            limit = settings.max_notifications_per_hour // 24  # Примерно в час

            return count <= limit

        except Exception as e:
            logger.error(f"Error checking rate limit {user_id}:{channel}: {e}")
            return False

    async def set_delivery_status(self, delivery_id: str, status_data: Dict[str, Any], expire: int = 86400):
        """Установка статуса доставки"""
        try:
            await self.redis.setex(f"delivery:{delivery_id}", expire, json.dumps(status_data))
            return True
        except Exception as e:
            logger.error(f"Error setting delivery status {delivery_id}: {e}")
            return False

    async def get_delivery_status(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса доставки"""
        try:
            data = await self.redis.get(f"delivery:{delivery_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting delivery status {delivery_id}: {e}")
            return None

    async def increment_channel_stats(self, channel: str, metric: str) -> int:
        """Увеличение статистики канала"""
        try:
            key = f"channel_stats:{channel}:{metric}"
            count = await self.redis.incr(key)

            # Установка срока действия (7 дней)
            await self.redis.expire(key, 604800)
            return count

        except Exception as e:
            logger.error(f"Error incrementing channel stats {channel}:{metric}: {e}")
            return 0

    async def get_channel_stats(self, channel: str) -> Dict[str, int]:
        """Получение статистики канала"""
        try:
            keys = [
                f"channel_stats:{channel}:sent",
                f"channel_stats:{channel}:delivered",
                f"channel_stats:{channel}:read",
                f"channel_stats:{channel}:failed"
            ]

            values = await self.redis.mget(keys)
            stats = {}

            for i, key in enumerate(keys):
                metric = key.split(":")[-1]
                stats[metric] = int(values[i]) if values[i] else 0

            return stats

        except Exception as e:
            logger.error(f"Error getting channel stats {channel}: {e}")
            return {}

    async def cache_user_preferences(self, user_id: str, preferences: Dict[str, Any], expire: int = 1800):
        """Кэширование предпочтений пользователя"""
        try:
            await self.redis.setex(f"user_preferences:{user_id}", expire, json.dumps(preferences))
            return True
        except Exception as e:
            logger.error(f"Error caching user preferences {user_id}: {e}")
            return False

    async def get_cached_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированных предпочтений пользователя"""
        try:
            data = await self.redis.get(f"user_preferences:{user_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached user preferences {user_id}: {e}")
            return None

    async def store_campaign_recipients(self, campaign_id: str, recipients: List[str], expire: int = 86400):
        """Сохранение списка получателей кампании"""
        try:
            key = f"campaign_recipients:{campaign_id}"
            await self.redis.sadd(key, *recipients)
            await self.redis.expire(key, expire)
            return True
        except Exception as e:
            logger.error(f"Error storing campaign recipients {campaign_id}: {e}")
            return False

    async def get_campaign_recipients(self, campaign_id: str) -> List[str]:
        """Получение списка получателей кампании"""
        try:
            key = f"campaign_recipients:{campaign_id}"
            recipients = await self.redis.smembers(key)
            return list(recipients) if recipients else []
        except Exception as e:
            logger.error(f"Error getting campaign recipients {campaign_id}: {e}")
            return []

    async def increment_campaign_stats(self, campaign_id: str, metric: str) -> int:
        """Увеличение статистики кампании"""
        try:
            key = f"campaign_stats:{campaign_id}:{metric}"
            count = await self.redis.incr(key)
            return count
        except Exception as e:
            logger.error(f"Error incrementing campaign stats {campaign_id}:{metric}: {e}")
            return 0

    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, int]:
        """Получение статистики кампании"""
        try:
            keys = [
                f"campaign_stats:{campaign_id}:sent",
                f"campaign_stats:{campaign_id}:delivered",
                f"campaign_stats:{campaign_id}:read",
                f"campaign_stats:{campaign_id}:clicked",
                f"campaign_stats:{campaign_id}:failed"
            ]

            values = await self.redis.mget(keys)
            stats = {}

            for i, key in enumerate(keys):
                metric = key.split(":")[-1]
                stats[metric] = int(values[i]) if values[i] else 0

            return stats

        except Exception as e:
            logger.error(f"Error getting campaign stats {campaign_id}: {e}")
            return {}


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session