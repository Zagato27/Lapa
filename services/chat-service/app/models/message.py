"""
Модель сообщений.

Используется `ChatService` и WebSocket-менеджером для трансляции.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class MessageType(str, enum.Enum):
    """Типы сообщений"""
    TEXT = "text"                    # Текстовое сообщение
    IMAGE = "image"                  # Изображение
    VIDEO = "video"                  # Видео
    FILE = "file"                    # Файл
    SYSTEM = "system"                # Системное сообщение
    LOCATION = "location"            # Геолокация
    CONTACT = "contact"              # Контакт
    STICKER = "sticker"              # Стикер
    VOICE = "voice"                  # Голосовое сообщение


class MessageStatus(str, enum.Enum):
    """Статусы сообщений"""
    SENT = "sent"                    # Отправлено
    DELIVERED = "delivered"          # Доставлено
    READ = "read"                    # Прочитано
    DELETED = "deleted"              # Удалено
    EDITED = "edited"                # Отредактировано


class Message(Base):
    """Модель сообщения"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Тип и статус сообщения
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    status = Column(Enum(MessageStatus), nullable=False, default=MessageStatus.SENT)

    # Содержимое сообщения
    content = Column(Text, nullable=True)              # Текст сообщения
    metadata = Column(JSON, nullable=True)             # Дополнительные данные

    # Медиафайлы
    attachment_id = Column(String, ForeignKey("message_attachments.id"), nullable=True)

    # Системная информация
    reply_to_message_id = Column(String, ForeignKey("messages.id"), nullable=True)  # Ответ на сообщение
    thread_id = Column(String, nullable=True)        # ID треда (для групповых чатов)
    is_pinned = Column(Boolean, default=False)        # Закреплено ли сообщение
    is_edited = Column(Boolean, default=False)        # Отредактировано ли сообщение

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    edited_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Статусы доставки
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Message(id={self.id}, chat={self.chat_id}, sender={self.sender_id}, type={self.message_type.value})>"

    @property
    def is_text_message(self) -> bool:
        """Проверка, является ли текстовым сообщением"""
        return self.message_type == MessageType.TEXT

    @property
    def is_media_message(self) -> bool:
        """Проверка, является ли медиа-сообщением"""
        return self.message_type in [MessageType.IMAGE, MessageType.VIDEO, MessageType.FILE]

    @property
    def is_system_message(self) -> bool:
        """Проверка, является ли системным сообщением"""
        return self.message_type == MessageType.SYSTEM

    @property
    def is_deleted(self) -> bool:
        """Проверка, удалено ли сообщение"""
        return self.status == MessageStatus.DELETED

    @property
    def has_attachment(self) -> bool:
        """Проверка наличия вложения"""
        return self.attachment_id is not None

    @property
    def is_reply(self) -> bool:
        """Проверка, является ли ответом на другое сообщение"""
        return self.reply_to_message_id is not None

    def mark_as_delivered(self):
        """Отметить как доставленное"""
        if self.status == MessageStatus.SENT:
            self.status = MessageStatus.DELIVERED
            self.delivered_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def mark_as_read(self):
        """Отметить как прочитанное"""
        self.status = MessageStatus.READ
        self.read_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_deleted(self):
        """Отметить как удаленное"""
        self.status = MessageStatus.DELETED
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def edit_content(self, new_content: str):
        """Редактирование содержимого"""
        self.content = new_content
        self.is_edited = True
        self.status = MessageStatus.EDITED
        self.edited_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def pin_message(self):
        """Закрепление сообщения"""
        self.is_pinned = True
        self.updated_at = datetime.utcnow()

    def unpin_message(self):
        """Открепление сообщения"""
        self.is_pinned = False
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "sender_id": self.sender_id,
            "message_type": self.message_type.value,
            "status": self.status.value,
            "content": self.content,
            "metadata": self.metadata,
            "attachment_id": self.attachment_id,
            "reply_to_message_id": self.reply_to_message_id,
            "thread_id": self.thread_id,
            "is_pinned": self.is_pinned,
            "is_edited": self.is_edited,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }

    def to_public_dict(self) -> dict:
        """Преобразование в публичный словарь (без чувствительных данных)"""
        data = self.to_dict()
        # Здесь можно убрать чувствительные данные если нужно
        return data

    @staticmethod
    def create_system_message(chat_id: str, content: str, metadata: Optional[dict] = None) -> 'Message':
        """Создание системного сообщения"""
        message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_id="system",  # Системный отправитель
            message_type=MessageType.SYSTEM,
            content=content,
            metadata=metadata
        )
        return message

    @staticmethod
    def create_text_message(chat_id: str, sender_id: str, content: str,
                          reply_to: Optional[str] = None) -> 'Message':
        """Создание текстового сообщения"""
        message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_id=sender_id,
            message_type=MessageType.TEXT,
            content=content,
            reply_to_message_id=reply_to
        )
        return message

    @staticmethod
    def create_media_message(chat_id: str, sender_id: str, message_type: MessageType,
                           attachment_id: str, caption: Optional[str] = None) -> 'Message':
        """Создание медиа-сообщения"""
        message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_id=sender_id,
            message_type=message_type,
            content=caption,
            attachment_id=attachment_id
        )
        return message
