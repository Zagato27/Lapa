"""
Модель доставки уведомлений.

Используется `DeliveryService` для трекинга отправки/доставки по каналам.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum

from .base import Base


class DeliveryStatus(str, enum.Enum):
    """Статусы доставки"""
    PENDING = "pending"            # Ожидает отправки
    SENT = "sent"                  # Отправлено
    DELIVERED = "delivered"        # Доставлено
    READ = "read"                  # Прочитано
    CLICKED = "clicked"            # Кликнуто
    FAILED = "failed"              # Ошибка доставки
    BOUNCED = "bounced"            # Отклонено
    SPAM = "spam"                  # Помечено как спам


class DeliveryChannel(str, enum.Enum):
    """Каналы доставки"""
    PUSH = "push"                  # Push-уведомление
    EMAIL = "email"                # Email
    SMS = "sms"                    # SMS
    TELEGRAM = "telegram"          # Telegram


class NotificationDelivery(Base):
    """Модель доставки уведомления"""
    __tablename__ = "notification_deliveries"

    id = Column(String, primary_key=True, index=True)
    notification_id = Column(String, ForeignKey("notifications.id"), nullable=False, index=True)

    # Канал доставки
    channel = Column(Enum(DeliveryChannel), nullable=False)
    status = Column(Enum(DeliveryStatus), nullable=False, default=DeliveryStatus.PENDING)

    # Идентификаторы доставки
    external_id = Column(String, nullable=True)                # ID в внешней системе
    message_id = Column(String, nullable=True)                 # ID сообщения
    recipient_identifier = Column(String, nullable=True)       # Идентификатор получателя

    # Временные метки
    sent_at = Column(DateTime, nullable=True)                  # Время отправки
    delivered_at = Column(DateTime, nullable=True)             # Время доставки
    read_at = Column(DateTime, nullable=True)                  # Время прочтения
    clicked_at = Column(DateTime, nullable=True)               # Время клика
    failed_at = Column(DateTime, nullable=True)                # Время ошибки

    # Информация об ошибке
    error_code = Column(String, nullable=True)                 # Код ошибки
    error_message = Column(Text, nullable=True)                # Сообщение об ошибке
    retry_count = Column(Integer, default=0)                   # Количество попыток

    # Метаданные доставки
    provider_response = Column(JSON, nullable=True)            # Ответ провайдера
    delivery_metadata = Column(JSON, nullable=True)            # Метаданные доставки

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NotificationDelivery(id={self.id}, notification={self.notification_id}, channel={self.channel.value}, status={self.status.value})>"

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли отправки"""
        return self.status == DeliveryStatus.PENDING

    @property
    def is_sent(self) -> bool:
        """Проверка, отправлено ли"""
        return self.status in [DeliveryStatus.SENT, DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED]

    @property
    def is_delivered(self) -> bool:
        """Проверка, доставлено ли"""
        return self.status in [DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED]

    @property
    def is_read(self) -> bool:
        """Проверка, прочитано ли"""
        return self.status in [DeliveryStatus.READ, DeliveryStatus.CLICKED]

    @property
    def is_clicked(self) -> bool:
        """Проверка, кликнуто ли"""
        return self.status == DeliveryStatus.CLICKED

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка"""
        return self.status in [DeliveryStatus.FAILED, DeliveryStatus.BOUNCED, DeliveryStatus.SPAM]

    @property
    def delivery_time(self) -> Optional[float]:
        """Время доставки в секундах"""
        if self.sent_at and self.delivered_at:
            return (self.delivered_at - self.sent_at).total_seconds()
        return None

    @property
    def read_time(self) -> Optional[float]:
        """Время до прочтения в секундах"""
        if self.delivered_at and self.read_at:
            return (self.read_at - self.delivered_at).total_seconds()
        return None

    def mark_as_sent(self, external_id: Optional[str] = None, sent_at: Optional[datetime] = None):
        """Отметить как отправленное"""
        self.status = DeliveryStatus.SENT
        self.external_id = external_id
        self.sent_at = sent_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_delivered(self, delivered_at: Optional[datetime] = None):
        """Отметить как доставленное"""
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = delivered_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_read(self, read_at: Optional[datetime] = None):
        """Отметить как прочитанное"""
        self.status = DeliveryStatus.READ
        self.read_at = read_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_clicked(self, clicked_at: Optional[datetime] = None):
        """Отметить как кликнутое"""
        self.status = DeliveryStatus.CLICKED
        self.clicked_at = clicked_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, error_code: str, error_message: str, failed_at: Optional[datetime] = None):
        """Отметить как неудачное"""
        self.status = DeliveryStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.failed_at = failed_at or datetime.utcnow()
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def mark_as_bounced(self, error_message: Optional[str] = None):
        """Отметить как отклоненное"""
        self.status = DeliveryStatus.BOUNCED
        if error_message:
            self.error_message = error_message
        self.failed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_spam(self):
        """Отметить как спам"""
        self.status = DeliveryStatus.SPAM
        self.failed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_retry_count(self):
        """Увеличение счетчика попыток"""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "channel": self.channel.value,
            "status": self.status.value,
            "external_id": self.external_id,
            "message_id": self.message_id,
            "recipient_identifier": self.recipient_identifier,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "provider_response": self.provider_response,
            "delivery_metadata": self.delivery_metadata,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_delivery(
        notification_id: str,
        channel: DeliveryChannel,
        recipient_identifier: str
    ) -> 'NotificationDelivery':
        """Создание записи доставки"""
        delivery = NotificationDelivery(
            id=str(uuid.uuid4()),
            notification_id=notification_id,
            channel=channel,
            recipient_identifier=recipient_identifier
        )
        return delivery