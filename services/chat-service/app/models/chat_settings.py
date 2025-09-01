"""
Модель настроек чатов.

Используется `ChatService` и роутами `app.api.v1.chats`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import uuid

from .base import Base


class ChatSettings(Base):
    """Модель настроек чата"""
    __tablename__ = "chat_settings"

    id = Column(String, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False, index=True, unique=True)

    # Основные настройки
    allow_guests = Column(Boolean, default=False)      # Разрешить гостей
    allow_files = Column(Boolean, default=True)        # Разрешить файлы
    allow_images = Column(Boolean, default=True)       # Разрешить изображения
    allow_videos = Column(Boolean, default=True)       # Разрешить видео
    allow_voice_messages = Column(Boolean, default=True)  # Разрешить голосовые сообщения

    # Модерация
    enable_moderation = Column(Boolean, default=True)  # Включить модерацию
    auto_moderation = Column(Boolean, default=False)   # Автоматическая модерация
    banned_words_filter = Column(Boolean, default=True)  # Фильтр запрещенных слов

    # Уведомления
    enable_push_notifications = Column(Boolean, default=True)  # Push-уведомления
    enable_email_notifications = Column(Boolean, default=False)  # Email-уведомления
    enable_sms_notifications = Column(Boolean, default=False)   # SMS-уведомления
    notification_sound = Column(Boolean, default=True)          # Звук уведомлений

    # Безопасность
    encryption_enabled = Column(Boolean, default=False)         # Шифрование
    self_destruct_messages = Column(Boolean, default=False)     # Самоуничтожение сообщений
    self_destruct_timer = Column(Integer, nullable=True)       # Таймер самоуничтожения (секунды)

    # Ограничения
    max_message_length = Column(Integer, default=2000)          # Максимальная длина сообщения
    max_file_size_mb = Column(Integer, default=10)              # Максимальный размер файла
    rate_limit_messages = Column(Integer, default=10)           # Лимит сообщений в минуту
    slow_mode_seconds = Column(Integer, default=0)              # Медленный режим (секунды)

    # Внешний вид
    theme = Column(String, default="light")                     # Тема оформления
    language = Column(String, default="ru")                     # Язык интерфейса

    # Интеграции
    webhook_enabled = Column(Boolean, default=False)            # Webhook уведомления
    webhook_url = Column(String, nullable=True)                 # URL для webhook
    bot_enabled = Column(Boolean, default=False)                # Включить ботов

    # Архивация
    auto_archive_days = Column(Integer, nullable=True)          # Автоархивация через N дней
    archive_inactive_chats = Column(Boolean, default=True)      # Архивация неактивных чатов

    # Логирование
    enable_logging = Column(Boolean, default=False)             # Включить логирование
    log_sensitive_actions = Column(Boolean, default=True)       # Логировать чувствительные действия

    # Дополнительные настройки
    custom_emoji_enabled = Column(Boolean, default=True)        # Пользовательские эмодзи
    message_reactions_enabled = Column(Boolean, default=True)   # Реакции на сообщения
    message_replies_enabled = Column(Boolean, default=True)     # Ответы на сообщения
    message_editing_enabled = Column(Boolean, default=True)     # Редактирование сообщений
    message_deletion_enabled = Column(Boolean, default=True)    # Удаление сообщений

    # Метаданные
    metadata = Column(JSON, nullable=True)                      # Дополнительные настройки

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ChatSettings(chat={self.chat_id})>"

    @property
    def has_rate_limit(self) -> bool:
        """Проверка наличия лимита сообщений"""
        return self.rate_limit_messages > 0

    @property
    def has_slow_mode(self) -> bool:
        """Проверка режима медленных сообщений"""
        return self.slow_mode_seconds > 0

    @property
    def has_auto_archive(self) -> bool:
        """Проверка автоархивации"""
        return self.auto_archive_days is not None and self.auto_archive_days > 0

    @property
    def is_secure(self) -> bool:
        """Проверка безопасности чата"""
        return self.encryption_enabled or self.self_destruct_messages

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "allow_guests": self.allow_guests,
            "allow_files": self.allow_files,
            "allow_images": self.allow_images,
            "allow_videos": self.allow_videos,
            "allow_voice_messages": self.allow_voice_messages,
            "enable_moderation": self.enable_moderation,
            "auto_moderation": self.auto_moderation,
            "banned_words_filter": self.banned_words_filter,
            "enable_push_notifications": self.enable_push_notifications,
            "enable_email_notifications": self.enable_email_notifications,
            "enable_sms_notifications": self.enable_sms_notifications,
            "notification_sound": self.notification_sound,
            "encryption_enabled": self.encryption_enabled,
            "self_destruct_messages": self.self_destruct_messages,
            "self_destruct_timer": self.self_destruct_timer,
            "max_message_length": self.max_message_length,
            "max_file_size_mb": self.max_file_size_mb,
            "rate_limit_messages": self.rate_limit_messages,
            "slow_mode_seconds": self.slow_mode_seconds,
            "theme": self.theme,
            "language": self.language,
            "webhook_enabled": self.webhook_enabled,
            "webhook_url": self.webhook_url,
            "bot_enabled": self.bot_enabled,
            "auto_archive_days": self.auto_archive_days,
            "archive_inactive_chats": self.archive_inactive_chats,
            "enable_logging": self.enable_logging,
            "log_sensitive_actions": self.log_sensitive_actions,
            "custom_emoji_enabled": self.custom_emoji_enabled,
            "message_reactions_enabled": self.message_reactions_enabled,
            "message_replies_enabled": self.message_replies_enabled,
            "message_editing_enabled": self.message_editing_enabled,
            "message_deletion_enabled": self.message_deletion_enabled,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_default_settings(chat_id: str) -> 'ChatSettings':
        """Создание настроек по умолчанию"""
        settings = ChatSettings(
            id=str(uuid.uuid4()),
            chat_id=chat_id
        )
        return settings
