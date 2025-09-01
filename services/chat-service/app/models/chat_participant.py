"""
Модель участников чатов.

Используется `ChatService` и роутами `app.api.v1.chats`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class ParticipantRole(str, enum.Enum):
    """Роли участников"""
    OWNER = "owner"          # Владелец чата
    ADMIN = "admin"          # Администратор
    MODERATOR = "moderator"  # Модератор
    MEMBER = "member"        # Участник
    GUEST = "guest"          # Гость


class ParticipantStatus(str, enum.Enum):
    """Статусы участников"""
    ACTIVE = "active"        # Активный
    INVITED = "invited"      # Приглашен
    BANNED = "banned"        # Забанен
    LEFT = "left"           # Покинул
    MUTED = "muted"         # Заглушен


class ChatParticipant(Base):
    """Модель участника чата"""
    __tablename__ = "chat_participants"

    id = Column(String, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Роль и статус
    role = Column(Enum(ParticipantRole), nullable=False, default=ParticipantRole.MEMBER)
    status = Column(Enum(ParticipantStatus), nullable=False, default=ParticipantStatus.ACTIVE)

    # Права доступа
    can_send_messages = Column(Boolean, default=True)
    can_send_files = Column(Boolean, default=True)
    can_invite_users = Column(Boolean, default=False)
    can_delete_messages = Column(Boolean, default=False)
    can_pin_messages = Column(Boolean, default=False)
    can_manage_participants = Column(Boolean, default=False)

    # Настройки уведомлений
    notifications_enabled = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    preview_enabled = Column(Boolean, default=True)

    # Статистика
    messages_sent = Column(Integer, default=0)       # Количество отправленных сообщений
    last_seen_at = Column(DateTime, nullable=True)   # Последнее посещение
    joined_at = Column(DateTime, default=func.now()) # Дата присоединения

    # Ограничения
    muted_until = Column(DateTime, nullable=True)    # Дата окончания заглушения
    banned_until = Column(DateTime, nullable=True)   # Дата окончания бана

    # Приглашение
    invited_by = Column(String, ForeignKey("users.id"), nullable=True)  # Кто пригласил
    invited_at = Column(DateTime, nullable=True)     # Дата приглашения

    # Метаданные
    nickname = Column(String, nullable=True)         # Псевдоним в чате
    metadata = Column(JSON, nullable=True)           # Дополнительные данные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ChatParticipant(chat={self.chat_id}, user={self.user_id}, role={self.role.value}, status={self.status.value})>"

    @property
    def is_owner(self) -> bool:
        """Проверка, является ли владельцем чата"""
        return self.role == ParticipantRole.OWNER

    @property
    def is_admin(self) -> bool:
        """Проверка, является ли администратором"""
        return self.role in [ParticipantRole.OWNER, ParticipantRole.ADMIN]

    @property
    def is_moderator(self) -> bool:
        """Проверка, является ли модератором"""
        return self.role in [ParticipantRole.OWNER, ParticipantRole.ADMIN, ParticipantRole.MODERATOR]

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли участник"""
        return self.status == ParticipantStatus.ACTIVE

    @property
    def is_banned(self) -> bool:
        """Проверка, забанен ли участник"""
        return self.status == ParticipantStatus.BANNED

    @property
    def is_muted(self) -> bool:
        """Проверка, заглушен ли участник"""
        return self.status == ParticipantStatus.MUTED or (
            self.muted_until and datetime.utcnow() < self.muted_until
        )

    @property
    def can_participate(self) -> bool:
        """Проверка возможности участия в чате"""
        return (
            self.is_active and
            not self.is_banned and
            not (self.banned_until and datetime.utcnow() < self.banned_until)
        )

    @property
    def permissions(self) -> dict:
        """Получение прав доступа участника"""
        return {
            "can_send_messages": self.can_send_messages and not self.is_muted,
            "can_send_files": self.can_send_files,
            "can_invite_users": self.can_invite_users,
            "can_delete_messages": self.can_delete_messages,
            "can_pin_messages": self.can_pin_messages,
            "can_manage_participants": self.can_manage_participants
        }

    def promote_to_admin(self):
        """Повышение до администратора"""
        self.role = ParticipantRole.ADMIN
        self.can_invite_users = True
        self.can_delete_messages = True
        self.can_pin_messages = True
        self.can_manage_participants = True
        self.updated_at = datetime.utcnow()

    def demote_to_member(self):
        """Понижение до обычного участника"""
        self.role = ParticipantRole.MEMBER
        self.can_invite_users = False
        self.can_delete_messages = False
        self.can_pin_messages = False
        self.can_manage_participants = False
        self.updated_at = datetime.utcnow()

    def mute(self, duration_minutes: Optional[int] = None):
        """Заглушение участника"""
        self.status = ParticipantStatus.MUTED
        if duration_minutes:
            self.muted_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.updated_at = datetime.utcnow()

    def unmute(self):
        """Снятие заглушения"""
        self.status = ParticipantStatus.ACTIVE
        self.muted_until = None
        self.updated_at = datetime.utcnow()

    def ban(self, duration_minutes: Optional[int] = None, reason: Optional[str] = None):
        """Бан участника"""
        self.status = ParticipantStatus.BANNED
        if duration_minutes:
            self.banned_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        if reason:
            self.metadata = self.metadata or {}
            self.metadata["ban_reason"] = reason
        self.updated_at = datetime.utcnow()

    def unban(self):
        """Снятие бана"""
        self.status = ParticipantStatus.ACTIVE
        self.banned_until = None
        if self.metadata and "ban_reason" in self.metadata:
            del self.metadata["ban_reason"]
        self.updated_at = datetime.utcnow()

    def leave_chat(self):
        """Покидание чата"""
        self.status = ParticipantStatus.LEFT
        self.updated_at = datetime.utcnow()

    def update_last_seen(self):
        """Обновление времени последнего посещения"""
        self.last_seen_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_message_count(self):
        """Увеличение счетчика отправленных сообщений"""
        self.messages_sent += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "status": self.status.value,
            "can_send_messages": self.can_send_messages,
            "can_send_files": self.can_send_files,
            "can_invite_users": self.can_invite_users,
            "can_delete_messages": self.can_delete_messages,
            "can_pin_messages": self.can_pin_messages,
            "can_manage_participants": self.can_manage_participants,
            "notifications_enabled": self.notifications_enabled,
            "messages_sent": self.messages_sent,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "joined_at": self.joined_at.isoformat(),
            "nickname": self.nickname,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_owner(chat_id: str, user_id: str) -> 'ChatParticipant':
        """Создание владельца чата"""
        participant = ChatParticipant(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            user_id=user_id,
            role=ParticipantRole.OWNER,
            can_send_messages=True,
            can_send_files=True,
            can_invite_users=True,
            can_delete_messages=True,
            can_pin_messages=True,
            can_manage_participants=True
        )
        return participant

    @staticmethod
    def create_member(chat_id: str, user_id: str, invited_by: Optional[str] = None) -> 'ChatParticipant':
        """Создание обычного участника"""
        participant = ChatParticipant(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            user_id=user_id,
            role=ParticipantRole.MEMBER,
            invited_by=invited_by,
            invited_at=datetime.utcnow() if invited_by else None
        )
        return participant
