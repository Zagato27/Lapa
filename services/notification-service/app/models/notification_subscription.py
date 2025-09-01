"""
Модель подписок на уведомления.

Используется `SubscriptionService` и эндпоинтами `app.api.v1.subscriptions`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class NotificationSubscription(Base):
    """Модель подписки на уведомления"""
    __tablename__ = "notification_subscriptions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, unique=True)

    # Настройки каналов
    push_enabled = Column(Boolean, default=True)               # Push-уведомления
    email_enabled = Column(Boolean, default=True)              # Email уведомления
    sms_enabled = Column(Boolean, default=False)               # SMS уведомления
    telegram_enabled = Column(Boolean, default=False)          # Telegram уведомления

    # Настройки типов уведомлений
    system_notifications = Column(Boolean, default=True)       # Системные уведомления
    order_notifications = Column(Boolean, default=True)        # Уведомления о заказах
    payment_notifications = Column(Boolean, default=True)      # Уведомления о платежах
    chat_notifications = Column(Boolean, default=True)         # Уведомления из чата
    promotion_notifications = Column(Boolean, default=False)   # Рекламные уведомления
    security_notifications = Column(Boolean, default=True)     # Уведомления безопасности
    social_notifications = Column(Boolean, default=True)       # Социальные уведомления
    marketing_notifications = Column(Boolean, default=False)   # Маркетинговые уведомления

    # Настройки расписания
    quiet_hours_enabled = Column(Boolean, default=False)       # Тихие часы
    quiet_hours_start = Column(String, default="22:00")        # Начало тихих часов
    quiet_hours_end = Column(String, default="08:00")          # Конец тихих часов
    timezone = Column(String, default="Europe/Moscow")        # Часовой пояс

    # Контактная информация
    email_address = Column(String, nullable=True)              # Email для уведомлений
    phone_number = Column(String, nullable=True)               # Телефон для SMS
    telegram_chat_id = Column(String, nullable=True)           # Telegram chat ID

    # Токены устройств
    push_tokens = Column(JSON, nullable=True)                  # Токены push-уведомлений

    # Статистика
    total_sent = Column(Integer, default=0)                    # Всего отправлено
    total_delivered = Column(Integer, default=0)               # Всего доставлено

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NotificationSubscription(user={self.user_id}, push={self.push_enabled}, email={self.email_enabled})>"

    @property
    def is_subscribed(self) -> bool:
        """Проверка активной подписки"""
        return (
            self.push_enabled or
            self.email_enabled or
            self.sms_enabled or
            self.telegram_enabled
        )

    @property
    def enabled_channels(self) -> list[str]:
        """Получение списка включенных каналов"""
        channels = []
        if self.push_enabled:
            channels.append("push")
        if self.email_enabled:
            channels.append("email")
        if self.sms_enabled:
            channels.append("sms")
        if self.telegram_enabled:
            channels.append("telegram")
        return channels

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "push_enabled": self.push_enabled,
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "telegram_enabled": self.telegram_enabled,
            "system_notifications": self.system_notifications,
            "order_notifications": self.order_notifications,
            "payment_notifications": self.payment_notifications,
            "chat_notifications": self.chat_notifications,
            "promotion_notifications": self.promotion_notifications,
            "security_notifications": self.security_notifications,
            "social_notifications": self.social_notifications,
            "marketing_notifications": self.marketing_notifications,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_default_subscription(user_id: str) -> 'NotificationSubscription':
        """Создание подписки с настройками по умолчанию"""
        subscription = NotificationSubscription(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        return subscription