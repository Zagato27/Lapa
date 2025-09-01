"""
Основной сервис для управления чатами
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
from app.models.chat import Chat, ChatType, ChatStatus
from app.models.chat_participant import ChatParticipant, ParticipantRole, ParticipantStatus
from app.models.chat_settings import ChatSettings
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatsListResponse,
    ChatParticipantAdd,
    ChatParticipantUpdate,
    ChatParticipantResponse
)

logger = logging.getLogger(__name__)


class ChatService:
    """Сервис для работы с чатами"""

    @staticmethod
    async def create_chat(db: AsyncSession, creator_id: str, chat_data: ChatCreate) -> Chat:
        """Создание чата"""
        try:
            chat_id = str(uuid.uuid4())

            # Создание чата
            chat = Chat(
                id=chat_id,
                order_id=chat_data.order_id,
                creator_id=creator_id,
                chat_type=chat_data.chat_type,
                title=chat_data.title,
                description=chat_data.description,
                is_private=chat_data.is_private,
                allow_guests=chat_data.allow_guests,
                max_participants=chat_data.max_participants
            )

            db.add(chat)

            # Создание создателя чата как владельца
            owner_participant = ChatParticipant.create_owner(chat_id, creator_id)
            db.add(owner_participant)

            # Добавление других участников, если указаны
            if chat_data.participant_ids:
                for participant_id in chat_data.participant_ids:
                    if participant_id != creator_id:  # Не добавляем создателя дважды
                        participant = ChatParticipant.create_member(chat_id, participant_id, creator_id)
                        db.add(participant)

            # Создание настроек чата по умолчанию
            chat_settings = ChatSettings.create_default_settings(chat_id)
            db.add(chat_settings)

            await db.commit()
            await db.refresh(chat)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_chat_cache(chat_id)
            await redis_session.invalidate_chat_participants_cache(chat_id)

            logger.info(f"Chat created: {chat.id} by user {creator_id}")
            return chat

        except Exception as e:
            logger.error(f"Chat creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_chat_by_id(db: AsyncSession, chat_id: str, user_id: str) -> Optional[Chat]:
        """Получение чата по ID с проверкой доступа"""
        try:
            # Проверка кэша
            redis_session = await get_session()
            cached_chat = await redis_session.get_cached_chat(chat_id)

            if cached_chat:
                chat = Chat(**cached_chat)
                # Проверка доступа к чату
                if await ChatService._user_has_access_to_chat(db, user_id, chat_id):
                    return chat

            # Получение из базы данных
            query = select(Chat).where(Chat.id == chat_id)
            result = await db.execute(query)
            chat = result.scalar_one_or_none()

            if chat and await ChatService._user_has_access_to_chat(db, user_id, chat_id):
                # Кэширование
                chat_data = ChatService.chat_to_dict(chat)
                await redis_session.cache_chat(chat_id, chat_data)
                return chat

            return None

        except Exception as e:
            logger.error(f"Error getting chat {chat_id}: {e}")
            return None

    @staticmethod
    async def get_user_chats(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        chat_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> ChatsListResponse:
        """Получение чатов пользователя"""
        try:
            offset = (page - 1) * limit

            # Получение ID чатов, где пользователь является участником
            participant_query = select(ChatParticipant.chat_id).where(
                ChatParticipant.user_id == user_id,
                ChatParticipant.status == ParticipantStatus.ACTIVE
            )

            # Получение чатов
            query = select(Chat).where(Chat.id.in_(participant_query))

            if chat_type:
                query = query.where(Chat.chat_type == chat_type)
            if status:
                query = query.where(Chat.status == status)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение чатов с пагинацией
            query = query.order_by(desc(Chat.last_message_at), desc(Chat.created_at)).offset(offset).limit(limit)
            result = await db.execute(query)
            chats = result.scalars().all()

            pages = (total + limit - 1) // limit

            return ChatsListResponse(
                chats=[ChatService.chat_to_response(chat, user_id) for chat in chats],
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error getting user chats for {user_id}: {e}")
            return ChatsListResponse(chats=[], total=0, page=page, limit=limit, pages=0)

    @staticmethod
    async def update_chat(
        db: AsyncSession,
        chat_id: str,
        user_id: str,
        chat_data: ChatUpdate
    ) -> Optional[Chat]:
        """Обновление чата"""
        try:
            chat = await ChatService.get_chat_by_id(db, chat_id, user_id)
            if not chat:
                return None

            # Проверка прав на обновление
            participant = await ChatService._get_chat_participant(db, chat_id, user_id)
            if not participant or not participant.is_admin:
                raise ValueError("Insufficient permissions to update chat")

            update_data = chat_data.dict(exclude_unset=True)

            if not update_data:
                return chat

            stmt = (
                update(Chat)
                .where(Chat.id == chat_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Получение обновленного чата
                updated_chat = await ChatService.get_chat_by_id(db, chat_id, user_id)

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_chat_cache(chat_id)

                return updated_chat

            return chat

        except Exception as e:
            logger.error(f"Chat update failed for {chat_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_chat(db: AsyncSession, chat_id: str, user_id: str) -> bool:
        """Удаление чата"""
        try:
            chat = await ChatService.get_chat_by_id(db, chat_id, user_id)
            if not chat:
                return False

            # Проверка прав на удаление
            participant = await ChatService._get_chat_participant(db, chat_id, user_id)
            if not participant or not participant.is_owner:
                raise ValueError("Only chat owner can delete the chat")

            chat.delete()
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_chat_cache(chat_id)
            await redis_session.invalidate_chat_participants_cache(chat_id)

            logger.info(f"Chat {chat_id} deleted by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Chat deletion failed for {chat_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def add_participant(
        db: AsyncSession,
        chat_id: str,
        user_id: str,
        participant_data: ChatParticipantAdd
    ) -> Optional[ChatParticipant]:
        """Добавление участника в чат"""
        try:
            chat = await ChatService.get_chat_by_id(db, chat_id, user_id)
            if not chat:
                return None

            # Проверка прав на добавление участников
            adder_participant = await ChatService._get_chat_participant(db, chat_id, user_id)
            if not adder_participant or not adder_participant.can_invite_users:
                raise ValueError("No permission to add participants")

            # Проверка, не является ли уже участником
            existing_participant = await ChatService._get_chat_participant(db, chat_id, participant_data.user_id)
            if existing_participant:
                if existing_participant.status == ParticipantStatus.ACTIVE:
                    raise ValueError("User is already a participant")
                else:
                    # Реактивация участника
                    existing_participant.status = ParticipantStatus.ACTIVE
                    existing_participant.joined_at = datetime.utcnow()
                    await db.commit()
                    return existing_participant

            # Проверка лимита участников
            if chat.max_participants:
                active_count = await ChatService._count_active_participants(db, chat_id)
                if active_count >= chat.max_participants:
                    raise ValueError("Maximum number of participants reached")

            # Создание нового участника
            participant = ChatParticipant(
                id=str(uuid.uuid4()),
                chat_id=chat_id,
                user_id=participant_data.user_id,
                role=participant_data.role,
                invited_by=user_id,
                invited_at=datetime.utcnow()
            )

            db.add(participant)
            await db.commit()
            await db.refresh(participant)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_chat_participants_cache(chat_id)

            logger.info(f"Participant {participant_data.user_id} added to chat {chat_id}")
            return participant

        except Exception as e:
            logger.error(f"Adding participant failed for chat {chat_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def remove_participant(
        db: AsyncSession,
        chat_id: str,
        user_id: str,
        participant_id: str
    ) -> bool:
        """Удаление участника из чата"""
        try:
            chat = await ChatService.get_chat_by_id(db, chat_id, user_id)
            if not chat:
                return False

            # Проверка прав на удаление участников
            remover_participant = await ChatService._get_chat_participant(db, chat_id, user_id)
            participant_to_remove = await ChatService._get_chat_participant(db, chat_id, participant_id)

            if not participant_to_remove:
                raise ValueError("Participant not found")

            # Проверка прав: владелец может удалять всех, админ - всех кроме владельца
            can_remove = (
                remover_participant.is_owner or
                (remover_participant.is_admin and not participant_to_remove.is_owner) or
                user_id == participant_id  # Пользователь может удалить себя
            )

            if not can_remove:
                raise ValueError("No permission to remove participant")

            participant_to_remove.leave_chat()
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_chat_participants_cache(chat_id)

            logger.info(f"Participant {participant_id} removed from chat {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Removing participant failed for chat {chat_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def update_participant(
        db: AsyncSession,
        chat_id: str,
        user_id: str,
        participant_id: str,
        participant_data: ChatParticipantUpdate
    ) -> Optional[ChatParticipant]:
        """Обновление участника чата"""
        try:
            chat = await ChatService.get_chat_by_id(db, chat_id, user_id)
            if not chat:
                return None

            # Проверка прав на обновление участников
            updater_participant = await ChatService._get_chat_participant(db, chat_id, user_id)
            participant_to_update = await ChatService._get_chat_participant(db, chat_id, participant_id)

            if not participant_to_update:
                raise ValueError("Participant not found")

            # Проверка прав: владелец может обновлять всех, админ - всех кроме владельца
            can_update = (
                updater_participant.is_owner or
                (updater_participant.is_admin and not participant_to_update.is_owner)
            )

            if not can_update:
                raise ValueError("No permission to update participant")

            update_data = participant_data.dict(exclude_unset=True)

            if not update_data:
                return participant_to_update

            stmt = (
                update(ChatParticipant)
                .where(ChatParticipant.id == participant_to_update.id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Получение обновленного участника
                updated_participant = await ChatService._get_chat_participant(db, chat_id, participant_id)

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_chat_participants_cache(chat_id)

                return updated_participant

            return participant_to_update

        except Exception as e:
            logger.error(f"Updating participant failed for chat {chat_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_chat_participants(
        db: AsyncSession,
        chat_id: str,
        user_id: str
    ) -> List[ChatParticipantResponse]:
        """Получение участников чата"""
        try:
            chat = await ChatService.get_chat_by_id(db, chat_id, user_id)
            if not chat:
                return []

            # Проверка кэша
            redis_session = await get_session()
            cached_participants = await redis_session.get_cached_chat_participants(chat_id)

            if cached_participants:
                return [ChatParticipantResponse(**p) for p in cached_participants]

            # Получение из базы данных
            query = select(ChatParticipant).where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.status == ParticipantStatus.ACTIVE
            ).order_by(ChatParticipant.role.desc(), ChatParticipant.joined_at)

            result = await db.execute(query)
            participants = result.scalars().all()

            # Кэширование
            participants_data = [ChatService.participant_to_dict(p) for p in participants]
            await redis_session.cache_chat_participants(chat_id, participants_data)

            return [ChatService.participant_to_response(p) for p in participants]

        except Exception as e:
            logger.error(f"Error getting chat participants for {chat_id}: {e}")
            return []

    @staticmethod
    async def _user_has_access_to_chat(db: AsyncSession, user_id: str, chat_id: str) -> bool:
        """Проверка доступа пользователя к чату"""
        try:
            participant = await ChatService._get_chat_participant(db, chat_id, user_id)
            return participant and participant.can_participate

        except Exception:
            return False

    @staticmethod
    async def _get_chat_participant(db: AsyncSession, chat_id: str, user_id: str) -> Optional[ChatParticipant]:
        """Получение участника чата"""
        try:
            query = select(ChatParticipant).where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id == user_id
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception:
            return None

    @staticmethod
    async def _count_active_participants(db: AsyncSession, chat_id: str) -> int:
        """Подсчет активных участников чата"""
        try:
            query = select(func.count()).where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.status == ParticipantStatus.ACTIVE
            )
            result = await db.execute(query)
            return result.scalar()

        except Exception:
            return 0

    @staticmethod
    def chat_to_response(chat: Chat, user_id: str) -> ChatResponse:
        """Преобразование модели Chat в схему ChatResponse"""
        return ChatResponse(
            id=chat.id,
            order_id=chat.order_id,
            creator_id=chat.creator_id,
            chat_type=chat.chat_type,
            status=chat.status,
            title=chat.title,
            description=chat.description,
            is_private=chat.is_private,
            is_encrypted=chat.is_encrypted,
            allow_guests=chat.allow_guests,
            allow_files=chat.allow_files,
            max_participants=chat.max_participants,
            total_messages=chat.total_messages,
            total_participants=chat.total_participants,
            last_message_at=chat.last_message_at,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            can_send_messages=chat.can_send_messages,
            is_active=chat.is_active,
            is_archived=chat.is_archived,
            participants_count=chat.total_participants
        )

    @staticmethod
    def chat_to_dict(chat: Chat) -> Dict[str, Any]:
        """Преобразование модели Chat в словарь для кэширования"""
        return {
            "id": chat.id,
            "order_id": chat.order_id,
            "creator_id": chat.creator_id,
            "chat_type": chat.chat_type.value,
            "status": chat.status.value,
            "title": chat.title,
            "description": chat.description,
            "is_private": chat.is_private,
            "is_encrypted": chat.is_encrypted,
            "allow_guests": chat.allow_guests,
            "allow_files": chat.allow_files,
            "max_participants": chat.max_participants,
            "total_messages": chat.total_messages,
            "total_participants": chat.total_participants,
            "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
            "created_at": chat.created_at.isoformat(),
            "updated_at": chat.updated_at.isoformat()
        }

    @staticmethod
    def participant_to_response(participant: ChatParticipant) -> ChatParticipantResponse:
        """Преобразование модели ChatParticipant в схему ChatParticipantResponse"""
        return ChatParticipantResponse(
            id=participant.id,
            chat_id=participant.chat_id,
            user_id=participant.user_id,
            role=participant.role,
            status=participant.status,
            can_send_messages=participant.can_send_messages,
            can_send_files=participant.can_send_files,
            can_invite_users=participant.can_invite_users,
            can_delete_messages=participant.can_delete_messages,
            can_pin_messages=participant.can_pin_messages,
            can_manage_participants=participant.can_manage_participants,
            notifications_enabled=participant.notifications_enabled,
            messages_sent=participant.messages_sent,
            last_seen_at=participant.last_seen_at,
            joined_at=participant.joined_at,
            muted_until=participant.muted_until,
            banned_until=participant.banned_until,
            invited_by=participant.invited_by,
            invited_at=participant.invited_at,
            nickname=participant.nickname,
            is_owner=participant.is_owner,
            is_admin=participant.is_admin,
            is_active=participant.is_active,
            is_banned=participant.is_banned,
            is_muted=participant.is_muted,
            can_participate=participant.can_participate
        )

    @staticmethod
    def participant_to_dict(participant: ChatParticipant) -> Dict[str, Any]:
        """Преобразование модели ChatParticipant в словарь для кэширования"""
        return {
            "id": participant.id,
            "chat_id": participant.chat_id,
            "user_id": participant.user_id,
            "role": participant.role.value,
            "status": participant.status.value,
            "can_send_messages": participant.can_send_messages,
            "can_send_files": participant.can_send_files,
            "can_invite_users": participant.can_invite_users,
            "can_delete_messages": participant.can_delete_messages,
            "can_pin_messages": participant.can_pin_messages,
            "can_manage_participants": participant.can_manage_participants,
            "notifications_enabled": participant.notifications_enabled,
            "messages_sent": participant.messages_sent,
            "last_seen_at": participant.last_seen_at.isoformat() if participant.last_seen_at else None,
            "joined_at": participant.joined_at.isoformat(),
            "muted_until": participant.muted_until.isoformat() if participant.muted_until else None,
            "banned_until": participant.banned_until.isoformat() if participant.banned_until else None,
            "invited_by": participant.invited_by,
            "invited_at": participant.invited_at.isoformat() if participant.invited_at else None,
            "nickname": participant.nickname,
            "created_at": participant.created_at.isoformat(),
            "updated_at": participant.updated_at.isoformat()
        }
