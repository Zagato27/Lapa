"""
Модель чатов.

Используется сервисом `ChatService` и роутами `app.api.v1.chats`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class ChatType(str, enum.Enum):
    """Типы чатов"""
    ORDER = "order"          # Чат по заказу
    SUPPORT = "support"      # Поддержка
    GROUP = "group"          # Групповой чат
    PRIVATE = "private"      # Приватный чат


class ChatStatus(str, enum.Enum):
    """Статусы чатов"""
    ACTIVE = "active"        # Активный
    ARCHIVED = "archived"    # Архивный
    DELETED = "deleted"      # Удаленный
    FROZEN = "frozen"        # Замороженный


class Chat(Base):
    """Модель чата"""
    __tablename__ = "chats"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=True, index=True)
    creator_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Тип и статус чата
    chat_type = Column(Enum(ChatType), nullable=False)
    status = Column(Enum(ChatStatus), nullable=False, default=ChatStatus.ACTIVE)

    # Название и описание
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Настройки чата
    is_private = Column(Boolean, default=False)      # Приватный чат
    is_encrypted = Column(Boolean, default=False)    # Шифрованный чат
    allow_guests = Column(Boolean, default=False)    # Разрешить гостей
    allow_files = Column(Boolean, default=True)      # Разрешить файлы
    max_participants = Column(Integer, nullable=True)  # Максимум участников

    # Статистика
    total_messages = Column(Integer, default=0)      # Общее количество сообщений
    total_participants = Column(Integer, default=0)  # Общее количество участников
    last_message_at = Column(DateTime, nullable=True)  # Время последнего сообщения

    # Системная информация
    metadata = Column(JSON, nullable=True)           # Дополнительные данные
    settings = Column(JSON, nullable=True)           # Настройки чата

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Chat(id={self.id}, type={self.chat_type.value}, title={self.title}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли чат"""
        return self.status == ChatStatus.ACTIVE

    @property
    def is_archived(self) -> bool:
        """Проверка, архивный ли чат"""
        return self.status == ChatStatus.ARCHIVED

    @property
    def is_deleted(self) -> bool:
        """Проверка, удален ли чат"""
        return self.status == ChatStatus.DELETED

    @property
    def is_frozen(self) -> bool:
        """Проверка, заморожен ли чат"""
        return self.status == ChatStatus.FROZEN

    @property
    def can_send_messages(self) -> bool:
        """Проверка, можно ли отправлять сообщения в чат"""
        return self.is_active and not self.is_frozen

    @property
    def participants_count(self) -> int:
        """Количество участников (вычисляемое поле)"""
        # В реальности это должно быть вычислено через запрос к ChatParticipant
        return self.total_participants

    def archive(self):
        """Архивация чата"""
        self.status = ChatStatus.ARCHIVED
        self.archived_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def delete(self):
        """Удаление чата"""
        self.status = ChatStatus.DELETED
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def freeze(self):
        """Заморозка чата"""
        self.status = ChatStatus.FROZEN
        self.updated_at = datetime.utcnow()

    def unfreeze(self):
        """Разморозка чата"""
        if self.status == ChatStatus.FROZEN:
            self.status = ChatStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def update_last_message_time(self):
        """Обновление времени последнего сообщения"""
        self.last_message_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_message_count(self):
        """Увеличение счетчика сообщений"""
        self.total_messages += 1
        self.updated_at = datetime.utcnow()

    def add_participant(self):
        """Добавление участника"""
        self.total_participants += 1
        self.updated_at = datetime.utcnow()

    def remove_participant(self):
        """Удаление участника"""
        if self.total_participants > 0:
            self.total_participants -= 1
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "creator_id": self.creator_id,
            "chat_type": self.chat_type.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "is_private": self.is_private,
            "is_encrypted": self.is_encrypted,
            "allow_guests": self.allow_guests,
            "allow_files": self.allow_files,
            "max_participants": self.max_participants,
            "total_messages": self.total_messages,
            "total_participants": self.total_participants,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @staticmethod
    def create_order_chat(order_id: str, client_id: str, walker_id: str) -> 'Chat':
        """Создание чата для заказа"""
        chat = Chat(
            id=str(uuid.uuid4()),
            order_id=order_id,
            creator_id=client_id,
            chat_type=ChatType.ORDER,
            title=f"Заказ #{order_id}",
            description="Чат по заказу на выгул питомца",
            is_private=True,
            allow_guests=False,
            max_participants=2
        )
        return chat

    @staticmethod
    def create_support_chat(user_id: str, title: str = "Поддержка") -> 'Chat':
        """Создание чата поддержки"""
        chat = Chat(
            id=str(uuid.uuid4()),
            creator_id=user_id,
            chat_type=ChatType.SUPPORT,
            title=title,
            description="Чат с технической поддержкой",
            is_private=True,
            allow_guests=False,
            max_participants=2
        )
        return chat
