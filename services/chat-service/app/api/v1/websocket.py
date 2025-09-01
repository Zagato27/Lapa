"""
API роуты для WebSocket соединений
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.websocket_manager import WebSocketManager
from app.services.message_service import MessageService
from app.schemas.websocket import WebSocketMessage, WebSocketResponse
from app.schemas.message import MessageCreate

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user_ws(token: str, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Валидация пользователя для WebSocket"""
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Токен не предоставлен")

        # Здесь должна быть валидация токена через API Gateway
        # Пока что просто возвращаем mock данные
        return {"user_id": "mock_user_id"}

    except Exception as e:
        logger.error(f"WebSocket user validation error: {e}")
        raise HTTPException(status_code=401, detail="Неверный токен")


@router.websocket("/chats/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: str,
    token: str = Query(..., description="JWT токен для аутентификации"),
    user_type: str = Query("member", description="Тип пользователя: member, guest"),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket соединение для чата"""
    try:
        # Получение менеджера WebSocket
        websocket_manager = WebSocketManager()

        # Валидация токена
        user_info = await get_current_user_ws(token, db)
        user_id = user_info["user_id"]

        # Подключение к WebSocket
        await websocket_manager.connect(websocket, chat_id, user_id, user_type)

        try:
            while True:
                # Получение сообщения от клиента
                data = await websocket.receive_json()
                message = WebSocketMessage(**data)

                if message.type == "chat_message":
                    # Обработка сообщения чата
                    await handle_chat_message(websocket_manager, chat_id, user_id, message, db)

                elif message.type == "typing_start":
                    # Начало набора текста
                    await websocket_manager.send_typing_indicator(chat_id, user_id, True)

                elif message.type == "typing_stop":
                    # Окончание набора текста
                    await websocket_manager.send_typing_indicator(chat_id, user_id, False)

                elif message.type == "ping":
                    # Ответ на пинг
                    await websocket.send_json(WebSocketResponse(
                        type="pong",
                        data={"timestamp": message.timestamp}
                    ).dict())

                else:
                    # Неизвестный тип сообщения
                    await websocket.send_json(WebSocketResponse(
                        type="error",
                        success=False,
                        error=f"Неизвестный тип сообщения: {message.type}"
                    ).dict())

        except Exception as e:
            logger.error(f"WebSocket error for chat {chat_id}: {e}")
        finally:
            # Отключение WebSocket
            await websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"WebSocket connection error for chat {chat_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Внутренняя ошибка сервера")
        except:
            pass


async def handle_chat_message(
    websocket_manager: WebSocketManager,
    chat_id: str,
    user_id: str,
    message: WebSocketMessage,
    db: AsyncSession
):
    """Обработка сообщения чата"""
    try:
        message_data = message.data

        # Создание объекта сообщения
        chat_message = MessageCreate(
            content=message_data.get("content"),
            message_type=message_data.get("message_type", "text"),
            reply_to_message_id=message_data.get("reply_to_message_id"),
            attachment_id=message_data.get("attachment_id")
        )

        # Сохранение сообщения в базу данных
        saved_message = await MessageService.create_message(db, chat_id, user_id, chat_message)

        # Отправка сообщения всем участникам чата
        await websocket_manager.send_chat_message(chat_id, {
            "id": saved_message.id,
            "chat_id": saved_message.chat_id,
            "sender_id": saved_message.sender_id,
            "content": saved_message.content,
            "message_type": saved_message.message_type.value,
            "attachment_id": saved_message.attachment_id,
            "created_at": saved_message.created_at.isoformat()
        })

    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        # Отправка ошибки отправителю
        await websocket_manager.send_to_user(user_id, {
            "type": "error",
            "message": "Ошибка отправки сообщения"
        })


@router.get("/chats/{chat_id}/online", summary="Получение онлайн участников")
async def get_online_participants(
    chat_id: str,
    request: Request = None
):
    """Получение списка онлайн участников чата"""
    try:
        websocket_manager: WebSocketManager = request.app.state.websocket_manager
        participants = websocket_manager.get_chat_participants_online(chat_id)

        return {
            "chat_id": chat_id,
            "online_participants": participants,
            "online_count": len(participants)
        }

    except Exception as e:
        logger.error(f"Error getting online participants for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения онлайн участников")


@router.get("/stats", summary="Статистика WebSocket")
async def get_websocket_stats(
    request: Request = None
):
    """Получение статистики WebSocket соединений"""
    try:
        websocket_manager: WebSocketManager = request.app.state.websocket_manager

        return {
            "total_connections": websocket_manager.get_connection_count(),
            "timestamp": message.timestamp
        }

    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")
