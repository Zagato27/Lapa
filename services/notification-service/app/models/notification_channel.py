"""
Модель каналов доставки уведомлений.

Используется `DeliveryService` для выбора канала и провайдера.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum

from .base import Base


class ChannelType(str, enum.Enum):
    """Типы каналов"""
    PUSH = "push"                  # Push-уведомления
    EMAIL = "email"                # Email
    SMS = "sms"                    # SMS
    TELEGRAM = "telegram"          # Telegram


class ChannelStatus(str, enum.Enum):
    """Статусы каналов"""
    ACTIVE = "active"              # Активный
    INACTIVE = "inactive"          # Неактивный
    MAINTENANCE = "maintenance"    # Техническое обслуживание
    DISABLED = "disabled"          # Отключен


class NotificationChannel(Base):
    """Модель канала доставки уведомлений"""
    __tablename__ = "notification_channels"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    channel_type = Column(Enum(ChannelType), nullable=False)

    # Статус и настройки
    status = Column(Enum(ChannelStatus), nullable=False, default=ChannelStatus.ACTIVE)
    is_default = Column(Boolean, default=False)                # Канал по умолчанию

    # Конфигурация провайдера
    provider_name = Column(String, nullable=True)              # Название провайдера
    provider_config = Column(JSON, nullable=True)              # Конфигурация провайдера

    # Ограничения
    rate_limit = Column(Integer, nullable=True)                # Лимит запросов в минуту
    max_batch_size = Column(Integer, default=100)              # Максимальный размер пакета

    # Стоимость
    cost_per_message = Column(Float, nullable=True)            # Стоимость за сообщение

    # Статистика
    total_sent = Column(Integer, default=0)                    # Всего отправлено
    total_delivered = Column(Integer, default=0)               # Всего доставлено
    total_failed = Column(Integer, default=0)                  # Всего неудачных
    success_rate = Column(Float, nullable=True)                # Процент успешности

    # Метаданные
    metadata = Column(JSON, nullable=True)                     # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<NotificationChannel(id={self.id}, name={self.name}, type={self.channel_type.value}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли канал"""
        return self.status == ChannelStatus.ACTIVE

    @property
    def delivery_rate(self) -> Optional[float]:
        """Расчет процента доставки"""
        if self.total_sent == 0:
            return None
        return (self.total_delivered / self.total_sent) * 100

    def increment_sent(self):
        """Увеличение счетчика отправленных"""
        self.total_sent += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_delivered(self):
        """Увеличение счетчика доставленных"""
        self.total_delivered += 1
        self.updated_at = datetime.utcnow()

    def increment_failed(self):
        """Увеличение счетчика неудачных"""
        self.total_failed += 1
        self.updated_at = datetime.utcnow()

    def update_success_rate(self):
        """Обновление процента успешности"""
        if self.total_sent > 0:
            self.success_rate = (self.total_delivered / self.total_sent) * 100
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "channel_type": self.channel_type.value,
            "status": self.status.value,
            "is_default": self.is_default,
            "provider_name": self.provider_name,
            "rate_limit": self.rate_limit,
            "max_batch_size": self.max_batch_size,
            "cost_per_message": self.cost_per_message,
            "total_sent": self.total_sent,
            "total_delivered": self.total_delivered,
            "total_failed": self.total_failed,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_push_channel(name: str, provider_config: dict) -> 'NotificationChannel':
        """Создание канала push-уведомлений"""
        channel = NotificationChannel(
            id=str(uuid.uuid4()),
            name=name,
            channel_type=ChannelType.PUSH,
            provider_config=provider_config
        )
        return channel

    @staticmethod
    def create_email_channel(name: str, provider_config: dict) -> 'NotificationChannel':
        """Создание канала email"""
        channel = NotificationChannel(
            id=str(uuid.uuid4()),
            name=name,
            channel_type=ChannelType.EMAIL,
            provider_config=provider_config
        )
        return channel

    @staticmethod
    def create_sms_channel(name: str, provider_config: dict) -> 'NotificationChannel':
        """Создание канала SMS"""
        channel = NotificationChannel(
            id=str(uuid.uuid4()),
            name=name,
            channel_type=ChannelType.SMS,
            provider_config=provider_config
        )
        return channel