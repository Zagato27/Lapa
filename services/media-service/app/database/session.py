"""
Redis сессии для Media Service
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

    async def cache_media_file(self, file_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование медиафайла"""
        try:
            await self.redis.setex(f"media_file:{file_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching media file {file_id}: {e}")
            return False

    async def get_cached_media_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного медиафайла"""
        try:
            data = await self.redis.get(f"media_file:{file_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached media file {file_id}: {e}")
            return None

    async def invalidate_media_file_cache(self, file_id: str):
        """Удаление кэша медиафайла"""
        try:
            await self.redis.delete(f"media_file:{file_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating media file cache {file_id}: {e}")
            return False

    async def cache_album_files(self, album_id: str, files_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование файлов альбома"""
        try:
            await self.redis.setex(f"album_files:{album_id}", expire, json.dumps(files_data))
            return True
        except Exception as e:
            logger.error(f"Error caching album files {album_id}: {e}")
            return False

    async def get_cached_album_files(self, album_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированных файлов альбома"""
        try:
            data = await self.redis.get(f"album_files:{album_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached album files {album_id}: {e}")
            return None

    async def invalidate_album_files_cache(self, album_id: str):
        """Удаление кэша файлов альбома"""
        try:
            await self.redis.delete(f"album_files:{album_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating album files cache {album_id}: {e}")
            return False

    async def set_processing_status(self, file_id: str, status: Dict[str, Any], expire: int = 86400):
        """Установка статуса обработки файла"""
        try:
            await self.redis.setex(f"processing:{file_id}", expire, json.dumps(status))
            return True
        except Exception as e:
            logger.error(f"Error setting processing status {file_id}: {e}")
            return False

    async def get_processing_status(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса обработки файла"""
        try:
            data = await self.redis.get(f"processing:{file_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting processing status {file_id}: {e}")
            return None

    async def delete_processing_status(self, file_id: str):
        """Удаление статуса обработки файла"""
        try:
            await self.redis.delete(f"processing:{file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting processing status {file_id}: {e}")
            return False

    async def increment_storage_usage(self, user_id: str, size_bytes: int) -> int:
        """Увеличение использованного места для пользователя"""
        try:
            key = f"storage_usage:{user_id}"
            current = int(await self.redis.get(key) or "0")
            new_total = current + size_bytes
            await self.redis.set(key, str(new_total))
            return new_total
        except Exception as e:
            logger.error(f"Error incrementing storage usage {user_id}: {e}")
            return 0

    async def get_storage_usage(self, user_id: str) -> int:
        """Получение использованного места для пользователя"""
        try:
            key = f"storage_usage:{user_id}"
            data = await self.redis.get(key)
            return int(data) if data else 0
        except Exception as e:
            logger.error(f"Error getting storage usage {user_id}: {e}")
            return 0

    async def decrement_storage_usage(self, user_id: str, size_bytes: int) -> int:
        """Уменьшение использованного места для пользователя"""
        try:
            key = f"storage_usage:{user_id}"
            current = int(await self.redis.get(key) or "0")
            new_total = max(0, current - size_bytes)
            await self.redis.set(key, str(new_total))
            return new_total
        except Exception as e:
            logger.error(f"Error decrementing storage usage {user_id}: {e}")
            return 0

    async def check_rate_limit(self, user_id: str, action: str) -> bool:
        """Проверка лимита запросов для пользователя"""
        try:
            key = f"rate_limit:{action}:{user_id}"
            count = int(await self.redis.get(key) or "0")

            if action == "upload":
                limit = settings.uploads_per_hour
            else:
                limit = 100  # Общий лимит

            if count >= limit:
                return False

            await self.redis.incr(key)
            await self.redis.expire(key, 3600)  # Сброс каждый час
            return True

        except Exception as e:
            logger.error(f"Error checking rate limit {user_id}:{action}: {e}")
            return False

    async def cache_metadata(self, file_id: str, metadata: Dict[str, Any], expire: int = 3600):
        """Кэширование метаданных файла"""
        try:
            await self.redis.setex(f"metadata:{file_id}", expire, json.dumps(metadata))
            return True
        except Exception as e:
            logger.error(f"Error caching metadata {file_id}: {e}")
            return False

    async def get_cached_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированных метаданных файла"""
        try:
            data = await self.redis.get(f"metadata:{file_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached metadata {file_id}: {e}")
            return None

    async def invalidate_metadata_cache(self, file_id: str):
        """Удаление кэша метаданных файла"""
        try:
            await self.redis.delete(f"metadata:{file_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating metadata cache {file_id}: {e}")
            return False

    async def set_access_token(self, token: str, access_data: Dict[str, Any], expire: int = 86400):
        """Установка данных токена доступа"""
        try:
            await self.redis.setex(f"access_token:{token}", expire, json.dumps(access_data))
            return True
        except Exception as e:
            logger.error(f"Error setting access token {token}: {e}")
            return False

    async def get_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Получение данных токена доступа"""
        try:
            data = await self.redis.get(f"access_token:{token}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting access token {token}: {e}")
            return None

    async def delete_access_token(self, token: str):
        """Удаление токена доступа"""
        try:
            await self.redis.delete(f"access_token:{token}")
            return True
        except Exception as e:
            logger.error(f"Error deleting access token {token}: {e}")
            return False

    async def increment_view_count(self, file_id: str) -> int:
        """Увеличение счетчика просмотров файла"""
        try:
            key = f"view_count:{file_id}"
            count = await self.redis.incr(key)
            return count
        except Exception as e:
            logger.error(f"Error incrementing view count {file_id}: {e}")
            return 0

    async def increment_download_count(self, file_id: str) -> int:
        """Увеличение счетчика скачиваний файла"""
        try:
            key = f"download_count:{file_id}"
            count = await self.redis.incr(key)
            return count
        except Exception as e:
            logger.error(f"Error incrementing download count {file_id}: {e}")
            return 0

    async def get_view_count(self, file_id: str) -> int:
        """Получение счетчика просмотров файла"""
        try:
            key = f"view_count:{file_id}"
            count = await self.redis.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Error getting view count {file_id}: {e}")
            return 0

    async def get_download_count(self, file_id: str) -> int:
        """Получение счетчика скачиваний файла"""
        try:
            key = f"download_count:{file_id}"
            count = await self.redis.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Error getting download count {file_id}: {e}")
            return 0


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session
