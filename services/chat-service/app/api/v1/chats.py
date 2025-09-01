"""
API роуты для управления чатами
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatsListResponse,
    ChatParticipantAdd,
    ChatParticipantUpdate,
    ChatParticipantResponse
)
from app.services.chat_service import ChatService

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


@router.post("", response_model=ChatResponse, summary="Создание чата")
async def create_chat(
    chat_data: ChatCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового чата"""
    try:
        chat = await ChatService.create_chat(db, current_user["user_id"], chat_data)

        return ChatService.chat_to_response(chat, current_user["user_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания чата")


@router.get("", response_model=ChatsListResponse, summary="Получение списка чатов")
async def get_chats(
    chat_type: str = Query(None, description="Фильтр по типу чата"),
    status: str = Query(None, description="Фильтр по статусу чата"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество чатов на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка чатов пользователя"""
    try:
        chats_response = await ChatService.get_user_chats(
            db, current_user["user_id"], page, limit, chat_type, status
        )

        return chats_response

    except Exception as e:
        logger.error(f"Error getting chats list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка чатов")


@router.get("/{chat_id}", response_model=ChatResponse, summary="Получение чата по ID")
async def get_chat(
    chat_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о конкретном чате"""
    try:
        chat = await ChatService.get_chat_by_id(db, chat_id, current_user["user_id"])

        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        return ChatService.chat_to_response(chat, current_user["user_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения чата")


@router.put("/{chat_id}", response_model=ChatResponse, summary="Обновление чата")
async def update_chat(
    chat_id: str,
    chat_data: ChatUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление информации о чате"""
    try:
        chat = await ChatService.update_chat(db, chat_id, current_user["user_id"], chat_data)

        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        return ChatService.chat_to_response(chat, current_user["user_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления чата")


@router.delete("/{chat_id}", summary="Удаление чата")
async def delete_chat(
    chat_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление чата"""
    try:
        success = await ChatService.delete_chat(db, chat_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Чат не найден")

        return {"message": "Чат успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления чата")


@router.put("/{chat_id}/archive", summary="Архивация чата")
async def archive_chat(
    chat_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Архивация чата"""
    try:
        chat = await ChatService.get_chat_by_id(db, chat_id, current_user["user_id"])
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        if not chat.can_send_messages:
            raise HTTPException(status_code=400, detail="Чат уже архивирован")

        chat.archive()
        await db.commit()

        return {"message": "Чат успешно архивирован"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка архивации чата")


@router.put("/{chat_id}/freeze", summary="Заморозка чата")
async def freeze_chat(
    chat_id: str,
    reason: str = Query(..., description="Причина заморозки"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Заморозка чата"""
    try:
        chat = await ChatService.get_chat_by_id(db, chat_id, current_user["user_id"])
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        if chat.is_frozen:
            raise HTTPException(status_code=400, detail="Чат уже заморожен")

        chat.freeze()
        await db.commit()

        return {"message": "Чат успешно заморожен", "reason": reason}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error freezing chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка заморозки чата")


@router.post("/{chat_id}/participants", response_model=ChatParticipantResponse, summary="Добавление участника")
async def add_participant(
    chat_id: str,
    participant_data: ChatParticipantAdd,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавление участника в чат"""
    try:
        participant = await ChatService.add_participant(db, chat_id, current_user["user_id"], participant_data)

        return ChatService.participant_to_response(participant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding participant to chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления участника")


@router.delete("/{chat_id}/participants/{participant_id}", summary="Удаление участника")
async def remove_participant(
    chat_id: str,
    participant_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление участника из чата"""
    try:
        success = await ChatService.remove_participant(db, chat_id, current_user["user_id"], participant_id)

        if not success:
            raise HTTPException(status_code=404, detail="Участник не найден")

        return {"message": "Участник успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing participant {participant_id} from chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления участника")


@router.put("/{chat_id}/participants/{participant_id}", response_model=ChatParticipantResponse, summary="Обновление участника")
async def update_participant(
    chat_id: str,
    participant_id: str,
    participant_data: ChatParticipantUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление роли и прав участника"""
    try:
        participant = await ChatService.update_participant(
            db, chat_id, current_user["user_id"], participant_id, participant_data
        )

        if not participant:
            raise HTTPException(status_code=404, detail="Участник не найден")

        return ChatService.participant_to_response(participant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating participant {participant_id} in chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления участника")


@router.get("/{chat_id}/participants", summary="Получение участников чата")
async def get_chat_participants(
    chat_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка участников чата"""
    try:
        participants = await ChatService.get_chat_participants(db, chat_id, current_user["user_id"])

        return {
            "participants": participants,
            "total": len(participants)
        }

    except Exception as e:
        logger.error(f"Error getting chat participants for {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения участников")
