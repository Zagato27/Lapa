"""
Менеджер WebSocket соединений для реального времени
"""

import logging
import json
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from app.config import settings
from app.database.session import get_session

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Менеджер WebSocket соединений"""

    def __init__(self):
        # Словарь активных соединений: order_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Словарь соединений с метаданными: websocket -> connection_info
        self.connection_info: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, order_id: str, user_id: str, user_type: str):
        """Подключение нового WebSocket соединения"""
        try:
            await websocket.accept()

            # Создание информации о соединении
            connection_info = {
                "order_id": order_id,
                "user_id": user_id,
                "user_type": user_type,  # 'client' или 'walker'
                "connected_at": datetime.utcnow(),
                "last_ping": datetime.utcnow()
            }

            # Добавление в активные соединения
            if order_id not in self.active_connections:
                self.active_connections[order_id] = set()

            self.active_connections[order_id].add(websocket)
            self.connection_info[websocket] = connection_info

            # Сохранение в Redis для отслеживания
            redis_session = await get_session()
            connection_id = f"{user_id}_{order_id}_{datetime.utcnow().timestamp()}"
            await redis_session.store_websocket_connection(order_id, user_id, connection_id)

            logger.info(f"WebSocket connected: {user_type} {user_id} for order {order_id}")

            # Отправка приветственного сообщения
            await websocket.send_json({
                "type": "connection_established",
                "data": {
                    "order_id": order_id,
                    "user_id": user_id,
                    "user_type": user_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            raise

    async def disconnect(self, websocket: WebSocket):
        """Отключение WebSocket соединения"""
        try:
            # Получение информации о соединении
            connection_info = self.connection_info.get(websocket)
            if connection_info:
                order_id = connection_info["order_id"]
                user_id = connection_info["user_id"]

                # Удаление из активных соединений
                if order_id in self.active_connections:
                    self.active_connections[order_id].discard(websocket)

                    # Удаление пустого множества
                    if not self.active_connections[order_id]:
                        del self.active_connections[order_id]

                # Удаление из Redis
                redis_session = await get_session()
                await redis_session.remove_websocket_connection(f"{user_id}_{order_id}")

                # Удаление из информации о соединениях
                del self.connection_info[websocket]

                logger.info(f"WebSocket disconnected: {connection_info['user_type']} {user_id} for order {order_id}")

        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")

    async def disconnect_all(self):
        """Отключение всех WebSocket соединений"""
        try:
            for connections in self.active_connections.values():
                for websocket in connections:
                    try:
                        await websocket.close()
                    except:
                        pass

            self.active_connections.clear()
            self.connection_info.clear()

            logger.info("All WebSocket connections disconnected")

        except Exception as e:
            logger.error(f"Error disconnecting all WebSockets: {e}")

    async def send_to_order(self, order_id: str, message: Dict, exclude_websocket: Optional[WebSocket] = None):
        """Отправка сообщения всем подключенным к заказу"""
        try:
            if order_id not in self.active_connections:
                return

            # Добавление временной метки
            message["timestamp"] = datetime.utcnow().isoformat()

            # Отправка сообщения всем соединениям заказа
            disconnected = set()
            for websocket in self.active_connections[order_id]:
                if websocket == exclude_websocket:
                    continue

                try:
                    await websocket.send_json(message)
                except (WebSocketDisconnect, Exception):
                    disconnected.add(websocket)

            # Удаление отключенных соединений
            for websocket in disconnected:
                await self.disconnect(websocket)

            logger.debug(f"Message sent to order {order_id}: {message.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"Error sending message to order {order_id}: {e}")

    async def send_to_user_type(self, order_id: str, user_type: str, message: Dict):
        """Отправка сообщения пользователям определенного типа"""
        try:
            if order_id not in self.active_connections:
                return

            # Добавление временной метки
            message["timestamp"] = datetime.utcnow().isoformat()

            # Отправка сообщения пользователям нужного типа
            disconnected = set()
            for websocket in self.active_connections[order_id]:
                connection_info = self.connection_info.get(websocket)
                if connection_info and connection_info["user_type"] == user_type:
                    try:
                        await websocket.send_json(message)
                    except (WebSocketDisconnect, Exception):
                        disconnected.add(websocket)

            # Удаление отключенных соединений
            for websocket in disconnected:
                await self.disconnect(websocket)

            logger.debug(f"Message sent to {user_type}s for order {order_id}: {message.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"Error sending message to user type {user_type}: {e}")

    async def send_location_update(self, order_id: str, location_data: Dict, user_type: Optional[str] = None):
        """Отправка обновления геолокации"""
        try:
            message = {
                "type": "location_update",
                "data": location_data
            }

            if user_type:
                await self.send_to_user_type(order_id, user_type, message)
            else:
                await self.send_to_order(order_id, message)

        except Exception as e:
            logger.error(f"Error sending location update for order {order_id}: {e}")

    async def send_geofence_alert(self, order_id: str, alert_data: Dict):
        """Отправка предупреждения геофенсинга"""
        try:
            message = {
                "type": "geofence_alert",
                "data": alert_data
            }

            await self.send_to_order(order_id, message)

        except Exception as e:
            logger.error(f"Error sending geofence alert for order {order_id}: {e}")

    async def send_tracking_status(self, order_id: str, status_data: Dict):
        """Отправка статуса отслеживания"""
        try:
            message = {
                "type": "tracking_status",
                "data": status_data
            }

            await self.send_to_order(order_id, message)

        except Exception as e:
            logger.error(f"Error sending tracking status for order {order_id}: {e}")

    async def send_emergency_alert(self, order_id: str, emergency_data: Dict):
        """Отправка экстренного предупреждения"""
        try:
            message = {
                "type": "emergency_alert",
                "data": emergency_data
            }

            await self.send_to_order(order_id, message)

        except Exception as e:
            logger.error(f"Error sending emergency alert for order {order_id}: {e}")

    async def ping_connections(self):
        """Отправка пинга всем активным соединениям"""
        try:
            current_time = datetime.utcnow()
            ping_message = {
                "type": "ping",
                "data": {"timestamp": current_time.isoformat()}
            }

            disconnected = set()

            for order_id, connections in self.active_connections.items():
                for websocket in connections:
                    try:
                        await websocket.send_json(ping_message)
                        # Обновление времени последнего пинга
                        if websocket in self.connection_info:
                            self.connection_info[websocket]["last_ping"] = current_time
                    except (WebSocketDisconnect, Exception):
                        disconnected.add(websocket)

            # Удаление отключенных соединений
            for websocket in disconnected:
                await self.disconnect(websocket)

            logger.debug(f"Ping sent to {len(self.active_connections)} orders")

        except Exception as e:
            logger.error(f"Error sending ping: {e}")

    def get_connection_count(self, order_id: Optional[str] = None) -> int:
        """Получение количества активных соединений"""
        try:
            if order_id:
                return len(self.active_connections.get(order_id, set()))
            else:
                return sum(len(connections) for connections in self.active_connections.values())

        except Exception as e:
            logger.error(f"Error getting connection count: {e}")
            return 0

    def get_order_connections(self, order_id: str) -> List[Dict]:
        """Получение информации о соединениях для заказа"""
        try:
            if order_id not in self.active_connections:
                return []

            connections_info = []
            for websocket in self.active_connections[order_id]:
                connection_info = self.connection_info.get(websocket)
                if connection_info:
                    connections_info.append({
                        "user_id": connection_info["user_id"],
                        "user_type": connection_info["user_type"],
                        "connected_at": connection_info["connected_at"].isoformat(),
                        "last_ping": connection_info["last_ping"].isoformat()
                    })

            return connections_info

        except Exception as e:
            logger.error(f"Error getting order connections for {order_id}: {e}")
            return []
