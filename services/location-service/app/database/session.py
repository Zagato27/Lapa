"""
Redis сессии для Location Service
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

    async def cache_location_track(self, track_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование точки отслеживания"""
        try:
            await self.redis.setex(f"location_track:{track_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching location track {track_id}: {e}")
            return False

    async def get_cached_location_track(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированной точки отслеживания"""
        try:
            data = await self.redis.get(f"location_track:{track_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached location track {track_id}: {e}")
            return None

    async def cache_order_locations(self, order_id: str, locations_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование локаций заказа"""
        try:
            await self.redis.setex(f"order_locations:{order_id}", expire, json.dumps(locations_data))
            return True
        except Exception as e:
            logger.error(f"Error caching order locations {order_id}: {e}")
            return False

    async def get_cached_order_locations(self, order_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированных локаций заказа"""
        try:
            data = await self.redis.get(f"order_locations:{order_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached order locations {order_id}: {e}")
            return None

    async def invalidate_order_locations_cache(self, order_id: str):
        """Удаление кэша локаций заказа"""
        try:
            await self.redis.delete(f"order_locations:{order_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating order locations cache {order_id}: {e}")
            return False

    async def set_tracking_active(self, order_id: str, user_id: str, expire: int = 43200):  # 12 часов
        """Установка активного отслеживания для заказа"""
        try:
            tracking_data = {
                "order_id": order_id,
                "user_id": user_id,
                "started_at": str(datetime.utcnow()),
                "is_active": True
            }
            await self.redis.setex(f"tracking_active:{order_id}", expire, json.dumps(tracking_data))
            return True
        except Exception as e:
            logger.error(f"Error setting tracking active for order {order_id}: {e}")
            return False

    async def get_tracking_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса отслеживания"""
        try:
            data = await self.redis.get(f"tracking_active:{order_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting tracking status for order {order_id}: {e}")
            return None

    async def stop_tracking(self, order_id: str):
        """Остановка отслеживания"""
        try:
            await self.redis.delete(f"tracking_active:{order_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping tracking for order {order_id}: {e}")
            return False

    async def cache_geofence(self, geofence_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование геофенса"""
        try:
            await self.redis.setex(f"geofence:{geofence_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching geofence {geofence_id}: {e}")
            return False

    async def get_cached_geofence(self, geofence_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного геофенса"""
        try:
            data = await self.redis.get(f"geofence:{geofence_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached geofence {geofence_id}: {e}")
            return None

    async def cache_order_geofences(self, order_id: str, geofences_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэширование геофенсов заказа"""
        try:
            await self.redis.setex(f"order_geofences:{order_id}", expire, json.dumps(geofences_data))
            return True
        except Exception as e:
            logger.error(f"Error caching order geofences {order_id}: {e}")
            return False

    async def get_cached_order_geofences(self, order_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение кэшированных геофенсов заказа"""
        try:
            data = await self.redis.get(f"order_geofences:{order_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached order geofences {order_id}: {e}")
            return None

    async def store_websocket_connection(self, order_id: str, user_id: str, connection_id: str):
        """Сохранение WebSocket соединения"""
        try:
            connection_data = {
                "order_id": order_id,
                "user_id": user_id,
                "connection_id": connection_id,
                "connected_at": str(datetime.utcnow())
            }
            await self.redis.setex(f"websocket:{connection_id}", 3600, json.dumps(connection_data))

            # Добавление в список соединений заказа
            connections_key = f"order_websockets:{order_id}"
            await self.redis.sadd(connections_key, connection_id)
            await self.redis.expire(connections_key, 3600)

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
                order_id = connection_info["order_id"]

                # Удаление из списка соединений заказа
                connections_key = f"order_websockets:{order_id}"
                await self.redis.srem(connections_key, connection_id)

            await self.redis.delete(f"websocket:{connection_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing websocket connection {connection_id}: {e}")
            return False

    async def get_order_websocket_connections(self, order_id: str) -> List[str]:
        """Получение списка WebSocket соединений заказа"""
        try:
            connections_key = f"order_websockets:{order_id}"
            connections = await self.redis.smembers(connections_key)
            return list(connections) if connections else []
        except Exception as e:
            logger.error(f"Error getting websocket connections for order {order_id}: {e}")
            return []

    async def cache_route(self, route_id: str, data: Dict[str, Any], expire: int = 3600):
        """Кэширование маршрута"""
        try:
            await self.redis.setex(f"route:{route_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching route {route_id}: {e}")
            return False

    async def get_cached_route(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированного маршрута"""
        try:
            data = await self.redis.get(f"route:{route_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached route {route_id}: {e}")
            return None

    async def store_location_alert(self, alert_id: str, data: Dict[str, Any], expire: int = 86400):  # 24 часа
        """Сохранение предупреждения о геолокации"""
        try:
            await self.redis.setex(f"location_alert:{alert_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error storing location alert {alert_id}: {e}")
            return False

    async def get_location_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Получение предупреждения о геолокации"""
        try:
            data = await self.redis.get(f"location_alert:{alert_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting location alert {alert_id}: {e}")
            return None


# Глобальный экземпляр Redis сессии
redis_session = RedisSession()


async def get_session() -> RedisSession:
    """Получение экземпляра Redis сессии"""
    return redis_session
