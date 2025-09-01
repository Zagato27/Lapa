"""
Сервис для управления сообщениями
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_session
from app.models.message import Message, MessageType, MessageStatus
from app.models.message_attachment import MessageAttachment
from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant, ParticipantStatus
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessagesListResponse,
    MessageAttachmentCreate,
    MessageAttachmentResponse
)

logger = logging.getLogger(__name__)


class MessageService:
    """Сервис для работы с сообщениями"""

    @staticmethod
    async def create_message(
        db: AsyncSession,
        chat_id: str,
        sender_id: str,
        message_data: MessageCreate
    ) -> Message:
        """Создание сообщения"""
        try:
            # Проверка прав на отправку сообщений
            participant = await MessageService._get_chat_participant(db, chat_id, sender_id)
            if not participant or not participant.can_send_messages or participant.is_muted:
                raise ValueError("Cannot send messages")

            # Проверка rate limiting
            redis_session = await get_session()
            message_count = await redis_session.increment_message_rate_limit(sender_id, chat_id)

            if message_count > settings.max_messages_per_minute:
                raise ValueError("Message rate limit exceeded")

            message_id = str(uuid.uuid4())

            message = Message(
                id=message_id,
                chat_id=chat_id,
                sender_id=sender_id,
                message_type=message_data.message_type,
                content=message_data.content,
                reply_to_message_id=message_data.reply_to_message_id,
                attachment_id=message_data.attachment_id
            )

            db.add(message)

            # Обновление статистики чата
            chat = await MessageService._get_chat(db, chat_id)
            if chat:
                chat.update_last_message_time()
                chat.increment_message_count()

            # Обновление статистики участника
            participant.increment_message_count()

            await db.commit()
            await db.refresh(message)

            # Инвалидация кэша сообщений
            await redis_session.invalidate_messages_cache(chat_id)

            logger.info(f"Message created: {message.id} in chat {chat_id} by user {sender_id}")
            return message

        except Exception as e:
            logger.error(f"Message creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_message_by_id(
        db: AsyncSession,
        message_id: str,
        user_id: str
    ) -> Optional[Message]:
        """Получение сообщения по ID с проверкой доступа"""
        try:
            query = select(Message).where(
                Message.id == message_id,
                Message.status != MessageStatus.DELETED
            )
            result = await db.execute(query)
            message = result.scalar_one_or_none()

            if message:
                # Проверка доступа к чату
                chat = await MessageService._get_chat(db, message.chat_id)
                if chat and await MessageService._user_has_access_to_chat(db, user_id, message.chat_id):
                    return message

            return None

        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            return None

    @staticmethod
    async def get_chat_messages(
        db: AsyncSession,
        chat_id: str,
        user_id: str,
        page: int = 1,
        limit: int = 50,
        before_message_id: Optional[str] = None,
        after_message_id: Optional[str] = None
    ) -> MessagesListResponse:
        """Получение сообщений чата"""
        try:
            # Проверка доступа к чату
            if not await MessageService._user_has_access_to_chat(db, user_id, chat_id):
                return MessagesListResponse(messages=[], total=0, page=page, limit=limit, pages=0, has_more=False)

            offset = (page - 1) * limit

            # Проверка кэша для первой страницы
            redis_session = await get_session()
            if page == 1 and not before_message_id and not after_message_id:
                cached_messages = await redis_session.get_cached_messages(chat_id)
                if cached_messages:
                    return MessagesListResponse(
                        messages=[MessageService.message_to_response(Message(**m)) for m in cached_messages],
                        total=len(cached_messages),
                        page=page,
                        limit=limit,
                        pages=1,
                        has_more=False
                    )

            # Построение запроса
            query = select(Message).where(
                Message.chat_id == chat_id,
                Message.status != MessageStatus.DELETED
            )

            # Фильтры по диапазону сообщений
            if before_message_id:
                before_message = await MessageService.get_message_by_id(db, before_message_id, user_id)
                if before_message:
                    query = query.where(Message.created_at < before_message.created_at)
            elif after_message_id:
                after_message = await MessageService.get_message_by_id(db, after_message_id, user_id)
                if after_message:
                    query = query.where(Message.created_at > after_message.created_at)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение сообщений с пагинацией
            query = query.order_by(desc(Message.created_at)).offset(offset).limit(limit)
            result = await db.execute(query)
            messages = result.scalars().all()

            # Переворот для правильного порядка (от старых к новым)
            messages = list(reversed(messages))

            pages = (total + limit - 1) // limit
            has_more = page * limit < total

            # Кэширование первой страницы
            if page == 1 and not before_message_id and not after_message_id:
                messages_data = [MessageService.message_to_dict(msg) for msg in messages]
                await redis_session.cache_messages(chat_id, messages_data)

            return MessagesListResponse(
                messages=[MessageService.message_to_response(msg) for msg in messages],
                total=total,
                page=page,
                limit=limit,
                pages=pages,
                has_more=has_more
            )

        except Exception as e:
            logger.error(f"Error getting chat messages for {chat_id}: {e}")
            return MessagesListResponse(messages=[], total=0, page=page, limit=limit, pages=0, has_more=False)

    @staticmethod
    async def update_message(
        db: AsyncSession,
        message_id: str,
        user_id: str,
        message_data: MessageUpdate
    ) -> Optional[Message]:
        """Обновление сообщения"""
        try:
            message = await MessageService.get_message_by_id(db, message_id, user_id)
            if not message:
                return None

            # Проверка прав на редактирование
            if message.sender_id != user_id:
                raise ValueError("Cannot edit other user's messages")

            # Проверка возможности редактирования
            time_limit = datetime.utcnow() - timedelta(minutes=15)  # 15 минут на редактирование
            if message.created_at < time_limit:
                raise ValueError("Message can no longer be edited")

            message.edit_content(message_data.content)
            await db.commit()
            await db.refresh(message)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_messages_cache(message.chat_id)

            logger.info(f"Message {message_id} updated by user {user_id}")
            return message

        except Exception as e:
            logger.error(f"Message update failed for {message_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_message(
        db: AsyncSession,
        message_id: str,
        user_id: str,
        delete_for_all: bool = False
    ) -> bool:
        """Удаление сообщения"""
        try:
            message = await MessageService.get_message_by_id(db, message_id, user_id)
            if not message:
                return False

            # Проверка прав на удаление
            participant = await MessageService._get_chat_participant(db, message.chat_id, user_id)
            can_delete = (
                message.sender_id == user_id or  # Свой сообщение
                (participant and participant.can_delete_messages)  # Есть права модератора
            )

            if not can_delete:
                raise ValueError("Cannot delete this message")

            if delete_for_all and participant and participant.can_delete_messages:
                # Полное удаление для всех
                message.mark_as_deleted()
            else:
                # Удаление только для себя (мягкое удаление)
                # В реальности здесь нужно создать запись о скрытии для пользователя
                message.mark_as_deleted()

            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_messages_cache(message.chat_id)

            logger.info(f"Message {message_id} deleted by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Message deletion failed for {message_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def mark_messages_as_read(
        db: AsyncSession,
        chat_id: str,
        user_id: str,
        message_ids: Optional[List[str]] = None
    ) -> int:
        """Отметка сообщений как прочитанные"""
        try:
            # Проверка доступа к чату
            if not await MessageService._user_has_access_to_chat(db, user_id, chat_id):
                return 0

            # Построение запроса
            query = select(Message).where(
                Message.chat_id == chat_id,
                Message.sender_id != user_id,  # Не свои сообщения
                Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED])
            )

            if message_ids:
                query = query.where(Message.id.in_(message_ids))

            result = await db.execute(query)
            messages = result.scalars().all()

            updated_count = 0
            for message in messages:
                message.mark_as_read()
                updated_count += 1

            if updated_count > 0:
                await db.commit()

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_messages_cache(chat_id)

            logger.info(f"Marked {updated_count} messages as read in chat {chat_id} for user {user_id}")
            return updated_count

        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            await db.rollback()
            return 0

    @staticmethod
    async def create_attachment(
        db: AsyncSession,
        chat_id: str,
        uploader_id: str,
        attachment_data: MessageAttachmentCreate
    ) -> MessageAttachment:
        """Создание вложения к сообщению"""
        try:
            # Проверка прав на загрузку файлов
            participant = await MessageService._get_chat_participant(db, chat_id, uploader_id)
            if not participant or not participant.can_send_files:
                raise ValueError("Cannot upload files")

            # Проверка размера файла
            file_size = getattr(attachment_data.file, 'size', 0)
            if file_size > settings.max_file_size_mb * 1024 * 1024:
                raise ValueError("File size exceeds limit")

            attachment_id = str(uuid.uuid4())

            attachment = MessageAttachment(
                id=attachment_id,
                uploader_id=uploader_id,
                attachment_type=attachment_data.attachment_type,
                original_filename=getattr(attachment_data.file, 'filename', 'unknown'),
                file_size=file_size,
                caption=attachment_data.caption
            )

            db.add(attachment)
            await db.commit()
            await db.refresh(attachment)

            logger.info(f"Attachment created: {attachment.id} for chat {chat_id}")
            return attachment

        except Exception as e:
            logger.error(f"Attachment creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def search_messages(
        db: AsyncSession,
        chat_id: str,
        user_id: str,
        query: str,
        limit: int = 50
    ) -> List[Message]:
        """Поиск сообщений в чате"""
        try:
            # Проверка доступа к чату
            if not await MessageService._user_has_access_to_chat(db, user_id, chat_id):
                return []

            # Поиск по содержимому сообщений
            search_query = select(Message).where(
                Message.chat_id == chat_id,
                Message.content.ilike(f"%{query}%"),
                Message.status != MessageStatus.DELETED
            ).order_by(desc(Message.created_at)).limit(limit)

            result = await db.execute(search_query)
            messages = result.scalars().all()

            logger.info(f"Found {len(messages)} messages matching '{query}' in chat {chat_id}")
            return messages

        except Exception as e:
            logger.error(f"Error searching messages in chat {chat_id}: {e}")
            return []

    @staticmethod
    async def _user_has_access_to_chat(db: AsyncSession, user_id: str, chat_id: str) -> bool:
        """Проверка доступа пользователя к чату"""
        try:
            participant = await MessageService._get_chat_participant(db, chat_id, user_id)
            return participant and participant.can_participate

        except Exception:
            return False

    @staticmethod
    async def _get_chat_participant(db: AsyncSession, chat_id: str, user_id: str) -> Optional[ChatParticipant]:
        """Получение участника чата"""
        try:
            from app.models.chat_participant import ChatParticipant
            query = select(ChatParticipant).where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id == user_id
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception:
            return None

    @staticmethod
    async def _get_chat(db: AsyncSession, chat_id: str) -> Optional[Chat]:
        """Получение чата"""
        try:
            query = select(Chat).where(Chat.id == chat_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception:
            return None

    @staticmethod
    def message_to_response(message: Message) -> MessageResponse:
        """Преобразование модели Message в схему MessageResponse"""
        return MessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            sender_id=message.sender_id,
            message_type=message.message_type,
            status=message.status,
            content=message.content,
            metadata=message.metadata,
            attachment_id=message.attachment_id,
            reply_to_message_id=message.reply_to_message_id,
            thread_id=message.thread_id,
            is_pinned=message.is_pinned,
            is_edited=message.is_edited,
            created_at=message.created_at,
            updated_at=message.updated_at,
            edited_at=message.edited_at,
            delivered_at=message.delivered_at,
            read_at=message.read_at,
            is_text_message=message.is_text_message,
            is_media_message=message.is_media_message,
            is_system_message=message.is_system_message,
            is_deleted=message.is_deleted,
            has_attachment=message.has_attachment,
            is_reply=message.is_reply
        )

    @staticmethod
    def message_to_dict(message: Message) -> Dict[str, Any]:
        """Преобразование модели Message в словарь для кэширования"""
        return {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "message_type": message.message_type.value,
            "status": message.status.value,
            "content": message.content,
            "metadata": message.metadata,
            "attachment_id": message.attachment_id,
            "reply_to_message_id": message.reply_to_message_id,
            "thread_id": message.thread_id,
            "is_pinned": message.is_pinned,
            "is_edited": message.is_edited,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat(),
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
            "read_at": message.read_at.isoformat() if message.read_at else None
        }
