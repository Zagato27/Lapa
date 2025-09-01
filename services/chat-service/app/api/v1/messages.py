"""
API роуты для управления сообщениями
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessagesListResponse
)
from app.services.message_service import MessageService

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    # Здесь должна быть валидация токена через API Gateway
    # Пока что просто возвращаем данные из request
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("", response_model=MessageResponse, summary="Отправка сообщения")
async def send_message(
    chat_id: str = Query(..., description="ID чата"),
    message_data: MessageCreate = None,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправка сообщения в чат"""
    try:
        message = await MessageService.create_message(db, chat_id, current_user["user_id"], message_data or MessageCreate())

        return MessageService.message_to_response(message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки сообщения")


@router.get("", response_model=MessagesListResponse, summary="Получение сообщений чата")
async def get_chat_messages(
    chat_id: str = Query(..., description="ID чата"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(50, description="Количество сообщений на странице"),
    before_message_id: str = Query(None, description="ID сообщения для загрузки предыдущих"),
    after_message_id: str = Query(None, description="ID сообщения для загрузки следующих"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение сообщений чата"""
    try:
        messages_response = await MessageService.get_chat_messages(
            db, chat_id, current_user["user_id"], page, limit, before_message_id, after_message_id
        )

        return messages_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения сообщений")


@router.get("/{message_id}", response_model=MessageResponse, summary="Получение сообщения по ID")
async def get_message(
    message_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение конкретного сообщения"""
    try:
        message = await MessageService.get_message_by_id(db, message_id, current_user["user_id"])

        if not message:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")

        return MessageService.message_to_response(message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения сообщения")


@router.put("/{message_id}", response_model=MessageResponse, summary="Редактирование сообщения")
async def edit_message(
    message_id: str,
    message_data: MessageUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Редактирование сообщения"""
    try:
        message = await MessageService.update_message(db, message_id, current_user["user_id"], message_data)

        if not message:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")

        return MessageService.message_to_response(message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка редактирования сообщения")


@router.delete("/{message_id}", summary="Удаление сообщения")
async def delete_message(
    message_id: str,
    delete_for_all: bool = Query(False, description="Удалить для всех участников"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление сообщения"""
    try:
        success = await MessageService.delete_message(db, message_id, current_user["user_id"], delete_for_all)

        if not success:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")

        return {"message": "Сообщение успешно удалено"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления сообщения")


@router.put("/{message_id}/read", summary="Отметить как прочитанное")
async def mark_message_read(
    message_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить сообщение как прочитанное"""
    try:
        # Получение чата из сообщения
        message = await MessageService.get_message_by_id(db, message_id, current_user["user_id"])
        if not message:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")

        # Отметка сообщения как прочитанного
        updated_count = await MessageService.mark_messages_as_read(db, message.chat_id, current_user["user_id"], [message_id])

        if updated_count == 0:
            raise HTTPException(status_code=400, detail="Невозможно отметить сообщение как прочитанное")

        return {"message": "Сообщение отмечено как прочитанное"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking message {message_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отметки сообщения как прочитанного")


@router.put("/chats/{chat_id}/read", summary="Отметить все сообщения чата как прочитанные")
async def mark_chat_messages_read(
    chat_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить все сообщения чата как прочитанные"""
    try:
        updated_count = await MessageService.mark_messages_as_read(db, chat_id, current_user["user_id"])

        return {
            "message": f"Отмечено {updated_count} сообщений как прочитанные",
            "updated_count": updated_count
        }

    except Exception as e:
        logger.error(f"Error marking chat {chat_id} messages as read: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отметки сообщений как прочитанные")


@router.get("/search", summary="Поиск сообщений")
async def search_messages(
    chat_id: str = Query(..., description="ID чата для поиска"),
    query: str = Query(..., description="Текст для поиска"),
    limit: int = Query(50, description="Максимальное количество результатов"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Поиск сообщений в чате"""
    try:
        messages = await MessageService.search_messages(db, chat_id, current_user["user_id"], query, limit)

        return {
            "messages": [MessageService.message_to_response(msg) for msg in messages],
            "total": len(messages),
            "query": query
        }

    except Exception as e:
        logger.error(f"Error searching messages in chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка поиска сообщений")
