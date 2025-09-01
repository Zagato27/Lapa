"""
Трекер геолокации для фоновой обработки
"""

import asyncio
import logging
from datetime import datetime, timedelta

from app.config import settings
from app.database.session import get_session
from app.services.location_service import LocationService
from app.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class LocationTracker:
    """Трекер геолокации для фоновой обработки"""

    def __init__(self):
        self.running = False
        self.websocket_manager: Optional[WebSocketManager] = None

    async def start_tracking(self):
        """Запуск трекинга геолокации"""
        self.running = True
        logger.info("Location tracker started")

        try:
            while self.running:
                await self._process_tracking_cycle()
                await asyncio.sleep(settings.tracking_interval_seconds)

        except Exception as e:
            logger.error(f"Error in location tracking cycle: {e}")
        finally:
            logger.info("Location tracker stopped")

    async def stop_tracking(self):
        """Остановка трекинга геолокации"""
        self.running = False
        logger.info("Location tracker stopping...")

    async def _process_tracking_cycle(self):
        """Обработка одного цикла трекинга"""
        try:
            redis_session = await get_session()

            # Получение списка активных отслеживаний
            active_trackings = await redis_session._redis.scan_iter("tracking_active:*")

            for tracking_key in active_trackings:
                try:
                    order_id = tracking_key.decode().replace("tracking_active:", "")
                    tracking_info = await redis_session.get_tracking_status(order_id)

                    if tracking_info and tracking_info.get("is_active"):
                        await self._process_order_tracking(order_id, tracking_info)

                except Exception as e:
                    logger.error(f"Error processing tracking for {tracking_key}: {e}")

        except Exception as e:
            logger.error(f"Error in tracking cycle: {e}")

    async def _process_order_tracking(self, order_id: str, tracking_info: dict):
        """Обработка трекинга для конкретного заказа"""
        try:
            # Здесь можно добавить логику обработки данных геолокации
            # Например, проверку геофенсов, анализ маршрутов и т.д.

            # Проверка времени активности трекинга
            started_at = datetime.fromisoformat(tracking_info["started_at"])
            max_duration = timedelta(hours=settings.max_tracking_duration_hours)

            if datetime.utcnow() - started_at > max_duration:
                logger.warning(f"Tracking timeout for order {order_id}")
                await self._stop_order_tracking(order_id)
                return

            # Отправка статуса трекинга через WebSocket
            if self.websocket_manager:
                status_data = {
                    "order_id": order_id,
                    "is_active": True,
                    "started_at": tracking_info["started_at"],
                    "duration_seconds": (datetime.utcnow() - started_at).total_seconds()
                }

                await self.websocket_manager.send_tracking_status(order_id, status_data)

        except Exception as e:
            logger.error(f"Error processing order tracking {order_id}: {e}")

    async def _stop_order_tracking(self, order_id: str):
        """Остановка трекинга для заказа"""
        try:
            redis_session = await get_session()
            await redis_session.stop_tracking(order_id)

            # Отправка уведомления об остановке
            if self.websocket_manager:
                await self.websocket_manager.send_tracking_status(order_id, {
                    "order_id": order_id,
                    "is_active": False,
                    "stopped_at": datetime.utcnow().isoformat()
                })

            logger.info(f"Tracking stopped for order {order_id}")

        except Exception as e:
            logger.error(f"Error stopping tracking for order {order_id}: {e}")

    async def process_location_update(self, order_id: str, location_data: dict, user_id: str):
        """Обработка обновления геолокации"""
        try:
            # Проверка активности трекинга
            redis_session = await get_session()
            tracking_info = await redis_session.get_tracking_status(order_id)

            if not tracking_info or not tracking_info.get("is_active"):
                logger.debug(f"Tracking not active for order {order_id}")
                return

            # Создание точки отслеживания
            from app.database.connection import get_db
            from app.schemas.location import LocationTrackCreate

            track_data = LocationTrackCreate(
                order_id=order_id,
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                accuracy=location_data.get("accuracy"),
                altitude=location_data.get("altitude"),
                speed=location_data.get("speed"),
                heading=location_data.get("heading"),
                battery_level=location_data.get("battery_level"),
                network_type=location_data.get("network_type"),
                device_info=location_data.get("device_info")
            )

            # Сохранение в базу данных
            db = await get_db()
            await LocationService.create_location_track(db.__aenter__(), track_data)

            # Проверка геофенсинга
            geofence_check = await LocationService.check_geofence_violations(
                db.__aenter__(), order_id, location_data["latitude"], location_data["longitude"]
            )

            # Отправка обновления через WebSocket
            if self.websocket_manager:
                await self.websocket_manager.send_location_update(order_id, {
                    "latitude": location_data["latitude"],
                    "longitude": location_data["longitude"],
                    "accuracy": location_data.get("accuracy"),
                    "speed": location_data.get("speed"),
                    "geofence_status": {
                        "is_inside": geofence_check.is_inside_geofence,
                        "distance_to_geofence": geofence_check.distance_to_geofence
                    }
                })

            # Обработка предупреждений геофенсинга
            if geofence_check.alerts_triggered:
                for alert in geofence_check.alerts_triggered:
                    if self.websocket_manager:
                        await self.websocket_manager.send_geofence_alert(order_id, {
                            "alert_type": alert.alert_type,
                            "title": alert.title,
                            "message": alert.message,
                            "severity": alert.severity,
                            "latitude": location_data["latitude"],
                            "longitude": location_data["longitude"]
                        })

        except Exception as e:
            logger.error(f"Error processing location update for order {order_id}: {e}")

    async def process_emergency_location(self, order_id: str, location_data: dict, user_id: str):
        """Обработка экстренной геолокации"""
        try:
            from app.database.connection import get_db

            db = await get_db()
            await LocationService.process_emergency_location(
                db.__aenter__(), order_id,
                location_data["latitude"], location_data["longitude"],
                user_id
            )

            # Отправка экстренного предупреждения
            if self.websocket_manager:
                await self.websocket_manager.send_emergency_alert(order_id, {
                    "latitude": location_data["latitude"],
                    "longitude": location_data["longitude"],
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                })

            logger.warning(f"Emergency location processed for order {order_id}")

        except Exception as e:
            logger.error(f"Error processing emergency location for order {order_id}: {e}")

    def set_websocket_manager(self, websocket_manager: WebSocketManager):
        """Установка менеджера WebSocket"""
        self.websocket_manager = websocket_manager
