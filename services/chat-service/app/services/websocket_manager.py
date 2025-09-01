"""
Менеджер WebSocket соединений для чата
"""

import logging
import json
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from app.config import settings
from app.database.session import get_session
from app.schemas.websocket import (
    WebSocketMessage,
    WebSocketResponse,
    TypingIndicator,
    PresenceUpdate,
    ChatMessageData,
    SystemMessageData,
    ParticipantUpdateData
)

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Менеджер WebSocket соединений для чата"""

    def __init__(self):
        # Словарь активных соединений: chat_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Словарь соединений с метаданными: websocket -> connection_info
        self.connection_info: Dict[WebSocket, Dict] = {}
        # Словарь пользователей: user_id -> set of WebSocket connections
        self.user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: str, user_id: str, user_type: str = "member"):
        """Подключение нового WebSocket соединения"""
        try:
            await websocket.accept()

            # Создание информации о соединении
            connection_info = {
                "chat_id": chat_id,
                "user_id": user_id,
                "user_type": user_type,
                "connected_at": datetime.utcnow(),
                "last_ping": datetime.utcnow()
            }

            # Добавление в активные соединения
            if chat_id not in self.active_connections:
                self.active_connections[chat_id] = set()

            self.active_connections[chat_id].add(websocket)
            self.connection_info[websocket] = connection_info

            # Добавление в соединения пользователя
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()

            self.user_connections[user_id].add(websocket)

            # Сохранение в Redis
            redis_session = await get_session()
            connection_id = f"{user_id}_{chat_id}_{datetime.utcnow().timestamp()}"
            await redis_session.store_websocket_connection(connection_id, user_id, chat_id)

            # Установка статуса присутствия
            await redis_session.set_user_presence(user_id, chat_id, "online")

            # Отправка приветственного сообщения
            await websocket.send_json(WebSocketResponse(
                type="connection_established",
                data={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "user_type": user_type,
                    "online_count": len(self.active_connections.get(chat_id, set())),
                    "timestamp": datetime.utcnow().isoformat()
                }
            ).dict())

            # Уведомление других участников о новом участнике
            await self.send_system_message(chat_id, {
                "type": "user_joined",
                "user_id": user_id,
                "user_type": user_type,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_websocket=websocket)

            logger.info(f"WebSocket connected: {user_type} {user_id} to chat {chat_id}")

        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            raise

    async def disconnect(self, websocket: WebSocket):
        """Отключение WebSocket соединения"""
        try:
            connection_info = self.connection_info.get(websocket)
            if connection_info:
                chat_id = connection_info["chat_id"]
                user_id = connection_info["user_id"]
                user_type = connection_info["user_type"]

                # Удаление из активных соединений
                if chat_id in self.active_connections:
                    self.active_connections[chat_id].discard(websocket)

                    # Удаление пустого множества
                    if not self.active_connections[chat_id]:
                        del self.active_connections[chat_id]

                # Удаление из соединений пользователя
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(websocket)

                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]

                # Удаление из Redis
                redis_session = await get_session()
                await redis_session.remove_websocket_connection(f"{user_id}_{chat_id}")

                # Установка статуса присутствия
                await redis_session.set_user_presence(user_id, chat_id, "offline")

                # Удаление из информации о соединениях
                del self.connection_info[websocket]

                # Уведомление других участников об уходе
                await self.send_system_message(chat_id, {
                    "type": "user_left",
                    "user_id": user_id,
                    "user_type": user_type,
                    "timestamp": datetime.utcnow().isoformat()
                })

                logger.info(f"WebSocket disconnected: {user_type} {user_id} from chat {chat_id}")

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
            self.user_connections.clear()

            logger.info("All WebSocket connections disconnected")

        except Exception as e:
            logger.error(f"Error disconnecting all WebSockets: {e}")

    async def send_chat_message(self, chat_id: str, message_data: Dict[str, Any], exclude_websocket: Optional[WebSocket] = None):
        """Отправка сообщения в чат"""
        try:
            if chat_id not in self.active_connections:
                return

            message = WebSocketMessage(
                type="chat_message",
                chat_id=chat_id,
                data=ChatMessageData(**message_data).dict(),
                timestamp=datetime.utcnow()
            )

            await self._send_to_chat(chat_id, message.dict(), exclude_websocket)

        except Exception as e:
            logger.error(f"Error sending chat message to {chat_id}: {e}")

    async def send_system_message(self, chat_id: str, message_data: Dict[str, Any], exclude_websocket: Optional[WebSocket] = None):
        """Отправка системного сообщения"""
        try:
            if chat_id not in self.active_connections:
                return

            message = WebSocketMessage(
                type="system_message",
                chat_id=chat_id,
                data=SystemMessageData(**message_data).dict(),
                timestamp=datetime.utcnow()
            )

            await self._send_to_chat(chat_id, message.dict(), exclude_websocket)

        except Exception as e:
            logger.error(f"Error sending system message to {chat_id}: {e}")

    async def send_typing_indicator(self, chat_id: str, user_id: str, is_typing: bool):
        """Отправка индикатора набора текста"""
        try:
            redis_session = await get_session()

            if is_typing:
                await redis_session.set_typing_indicator(user_id, chat_id, True)
            else:
                await redis_session.set_typing_indicator(user_id, chat_id, False)

            # Получение списка набирающих пользователей
            typing_users = await redis_session.get_typing_users(chat_id)

            message = WebSocketMessage(
                type="typing_indicator",
                chat_id=chat_id,
                data={"typing_users": typing_users},
                timestamp=datetime.utcnow()
            )

            await self._send_to_chat(chat_id, message.dict())

        except Exception as e:
            logger.error(f"Error sending typing indicator to {chat_id}: {e}")

    async def send_presence_update(self, chat_id: str, user_id: str, status: str):
        """Отправка обновления статуса присутствия"""
        try:
            message = WebSocketMessage(
                type="presence_update",
                chat_id=chat_id,
                data=PresenceUpdate(
                    user_id=user_id,
                    status=status,
                    last_seen=datetime.utcnow()
                ).dict(),
                timestamp=datetime.utcnow()
            )

            await self._send_to_chat(chat_id, message.dict())

        except Exception as e:
            logger.error(f"Error sending presence update to {chat_id}: {e}")

    async def send_participant_update(self, chat_id: str, update_data: Dict[str, Any]):
        """Отправка обновления информации об участнике"""
        try:
            message = WebSocketMessage(
                type="participant_update",
                chat_id=chat_id,
                data=ParticipantUpdateData(**update_data).dict(),
                timestamp=datetime.utcnow()
            )

            await self._send_to_chat(chat_id, message.dict())

        except Exception as e:
            logger.error(f"Error sending participant update to {chat_id}: {e}")

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Отправка сообщения конкретному пользователю"""
        try:
            if user_id not in self.user_connections:
                return

            message["timestamp"] = datetime.utcnow().isoformat()

            # Отправка всем соединениям пользователя
            disconnected = set()
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except (WebSocketDisconnect, Exception):
                    disconnected.add(websocket)

            # Удаление отключенных соединений
            for websocket in disconnected:
                await self.disconnect(websocket)

        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")

    async def _send_to_chat(self, chat_id: str, message: Dict[str, Any], exclude_websocket: Optional[WebSocket] = None):
        """Отправка сообщения всем участникам чата"""
        try:
            if chat_id not in self.active_connections:
                return

            # Отправка сообщения всем соединениям чата
            disconnected = set()
            for websocket in self.active_connections[chat_id]:
                if websocket == exclude_websocket:
                    continue

                try:
                    await websocket.send_json(message)
                except (WebSocketDisconnect, Exception):
                    disconnected.add(websocket)

            # Удаление отключенных соединений
            for websocket in disconnected:
                await self.disconnect(websocket)

            logger.debug(f"Message sent to chat {chat_id}: {message.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"Error sending message to chat {chat_id}: {e}")

    async def ping_connections(self):
        """Отправка пинга всем активным соединениям"""
        try:
            current_time = datetime.utcnow()
            ping_message = WebSocketMessage(
                type="ping",
                data={"timestamp": current_time.isoformat()},
                timestamp=current_time
            )

            disconnected = set()

            for chat_id, connections in self.active_connections.items():
                for websocket in connections:
                    try:
                        await websocket.send_json(ping_message.dict())
                        # Обновление времени последнего пинга
                        if websocket in self.connection_info:
                            self.connection_info[websocket]["last_ping"] = current_time
                    except (WebSocketDisconnect, Exception):
                        disconnected.add(websocket)

            # Удаление отключенных соединений
            for websocket in disconnected:
                await self.disconnect(websocket)

            logger.debug(f"Ping sent to {len(self.active_connections)} chats")

        except Exception as e:
            logger.error(f"Error sending ping: {e}")

    def get_connection_count(self, chat_id: Optional[str] = None) -> int:
        """Получение количества активных соединений"""
        try:
            if chat_id:
                return len(self.active_connections.get(chat_id, set()))
            else:
                return sum(len(connections) for connections in self.active_connections.values())

        except Exception as e:
            logger.error(f"Error getting connection count: {e}")
            return 0

    def get_chat_participants_online(self, chat_id: str) -> List[Dict[str, Any]]:
        """Получение списка онлайн участников чата"""
        try:
            if chat_id not in self.active_connections:
                return []

            participants = []
            for websocket in self.active_connections[chat_id]:
                connection_info = self.connection_info.get(websocket)
                if connection_info:
                    participants.append({
                        "user_id": connection_info["user_id"],
                        "user_type": connection_info["user_type"],
                        "connected_at": connection_info["connected_at"].isoformat()
                    })

            return participants

        except Exception as e:
            logger.error(f"Error getting online participants for chat {chat_id}: {e}")
            return []
