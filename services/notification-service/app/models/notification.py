"""
Модель уведомлений.

Используется:
- `NotificationService` и `DeliveryService` для постановки в очередь и доставки
- Эндпоинты `app.api.v1.notifications`
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum

from .base import Base


class NotificationType(str, enum.Enum):
    """Типы уведомлений"""
    SYSTEM = "system"              # Системное уведомление
    ORDER = "order"                # Уведомление о заказе
    PAYMENT = "payment"            # Уведомление о платеже
    CHAT = "chat"                  # Уведомление из чата
    PROMOTION = "promotion"        # Рекламное уведомление
    SECURITY = "security"          # Уведомление безопасности
    SOCIAL = "social"              # Социальное уведомление
    MARKETING = "marketing"        # Маркетинговое уведомление


class NotificationPriority(str, enum.Enum):
    """Приоритеты уведомлений"""
    LOW = "low"                    # Низкий
    NORMAL = "normal"              # Обычный
    HIGH = "high"                  # Высокий
    URGENT = "urgent"              # Срочный


class NotificationStatus(str, enum.Enum):
    """Статусы уведомлений"""
    PENDING = "pending"            # Ожидает отправки
    QUEUED = "queued"              # В очереди
    SENDING = "sending"            # Отправляется
    SENT = "sent"                  # Отправлено
    DELIVERED = "delivered"        # Доставлено
    READ = "read"                  # Прочитано
    FAILED = "failed"              # Ошибка отправки
    CANCELLED = "cancelled"        # Отменено


class Notification(Base):
    """Модель уведомления"""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Тип и статус
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)

    # Содержимое
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)                        # Дополнительные данные

    # Связанные объекты
    order_id = Column(String, ForeignKey("orders.id"), nullable=True, index=True)
    chat_id = Column(String, ForeignKey("chats.id"), nullable=True, index=True)
    media_file_id = Column(String, ForeignKey("media_files.id"), nullable=True, index=True)

    # Каналы доставки
    send_push = Column(Boolean, default=True)
    send_email = Column(Boolean, default=False)
    send_sms = Column(Boolean, default=False)
    send_telegram = Column(Boolean, default=False)

    # Расписание
    scheduled_at = Column(DateTime, nullable=True)            # Запланированное время отправки
    expires_at = Column(DateTime, nullable=True)              # Время истечения

    # Шаблон
    template_id = Column(String, ForeignKey("notification_templates.id"), nullable=True)

    # Статистика
    sent_at = Column(DateTime, nullable=True)                 # Время отправки
    delivered_at = Column(DateTime, nullable=True)            # Время доставки
    read_at = Column(DateTime, nullable=True)                 # Время прочтения
    failed_at = Column(DateTime, nullable=True)               # Время ошибки

    # Метаданные доставки
    delivery_attempts = Column(Integer, default=0)            # Количество попыток доставки
    last_delivery_error = Column(Text, nullable=True)         # Последняя ошибка доставки

    # Персонализация
    language = Column(String, default="ru")                   # Язык уведомления
    personalization_data = Column(JSON, nullable=True)        # Данные для персонализации

    # Метаданные
    metadata = Column(JSON, nullable=True)                    # Дополнительные метаданные
    tags = Column(JSON, nullable=True)                        # Теги для категоризации

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type.value}, recipient={self.recipient_id}, status={self.status.value})>"

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли отправки"""
        return self.status == NotificationStatus.PENDING

    @property
    def is_queued(self) -> bool:
        """Проверка, в очереди ли"""
        return self.status == NotificationStatus.QUEUED

    @property
    def is_sending(self) -> bool:
        """Проверка, отправляется ли"""
        return self.status == NotificationStatus.SENDING

    @property
    def is_sent(self) -> bool:
        """Проверка, отправлено ли"""
        return self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ]

    @property
    def is_delivered(self) -> bool:
        """Проверка, доставлено ли"""
        return self.status in [NotificationStatus.DELIVERED, NotificationStatus.READ]

    @property
    def is_read(self) -> bool:
        """Проверка, прочитано ли"""
        return self.status == NotificationStatus.READ

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка"""
        return self.status == NotificationStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        """Проверка, отменено ли"""
        return self.status == NotificationStatus.CANCELLED

    @property
    def is_expired(self) -> bool:
        """Проверка, истекло ли время"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_scheduled(self) -> bool:
        """Проверка, запланировано ли"""
        return self.scheduled_at is not None

    @property
    def can_send_now(self) -> bool:
        """Проверка возможности отправки сейчас"""
        if self.is_expired or self.is_cancelled or self.is_failed:
            return False

        if self.is_scheduled and self.scheduled_at > datetime.utcnow():
            return False

        return self.is_pending or self.is_queued

    @property
    def delivery_channels(self) -> list[str]:
        """Получение списка каналов доставки"""
        channels = []
        if self.send_push:
            channels.append("push")
        if self.send_email:
            channels.append("email")
        if self.send_sms:
            channels.append("sms")
        if self.send_telegram:
            channels.append("telegram")
        return channels

    def mark_as_queued(self):
        """Отметить как поставленное в очередь"""
        self.status = NotificationStatus.QUEUED
        self.updated_at = datetime.utcnow()

    def mark_as_sending(self):
        """Отметить как отправляющееся"""
        self.status = NotificationStatus.SENDING
        self.updated_at = datetime.utcnow()

    def mark_as_sent(self, sent_at: Optional[datetime] = None):
        """Отметить как отправленное"""
        self.status = NotificationStatus.SENT
        self.sent_at = sent_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_delivered(self, delivered_at: Optional[datetime] = None):
        """Отметить как доставленное"""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = delivered_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_read(self, read_at: Optional[datetime] = None):
        """Отметить как прочитанное"""
        self.status = NotificationStatus.READ
        self.read_at = read_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, error: str, failed_at: Optional[datetime] = None):
        """Отметить как неудачное"""
        self.status = NotificationStatus.FAILED
        self.last_delivery_error = error
        self.failed_at = failed_at or datetime.utcnow()
        self.delivery_attempts += 1
        self.updated_at = datetime.utcnow()

    def mark_as_cancelled(self):
        """Отметить как отмененное"""
        self.status = NotificationStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def increment_delivery_attempt(self):
        """Увеличить счетчик попыток доставки"""
        self.delivery_attempts += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "notification_type": self.notification_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "order_id": self.order_id,
            "chat_id": self.chat_id,
            "media_file_id": self.media_file_id,
            "send_push": self.send_push,
            "send_email": self.send_email,
            "send_sms": self.send_sms,
            "send_telegram": self.send_telegram,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "template_id": self.template_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "delivery_attempts": self.delivery_attempts,
            "last_delivery_error": self.last_delivery_error,
            "language": self.language,
            "personalization_data": self.personalization_data,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_system_notification(
        recipient_id: str,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> 'Notification':
        """Создание системного уведомления"""
        notification = Notification(
            id=str(uuid.uuid4()),
            recipient_id=recipient_id,
            notification_type=NotificationType.SYSTEM,
            priority=priority,
            title=title,
            message=message,
            send_push=True,
            send_email=False,
            send_sms=False
        )
        return notification

    @staticmethod
    def create_order_notification(
        recipient_id: str,
        order_id: str,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.HIGH
    ) -> 'Notification':
        """Создание уведомления о заказе"""
        notification = Notification(
            id=str(uuid.uuid4()),
            recipient_id=recipient_id,
            notification_type=NotificationType.ORDER,
            priority=priority,
            title=title,
            message=message,
            order_id=order_id,
            send_push=True,
            send_email=True,
            send_sms=False
        )
        return notification

    @staticmethod
    def create_chat_notification(
        recipient_id: str,
        chat_id: str,
        title: str,
        message: str
    ) -> 'Notification':
        """Создание уведомления из чата"""
        notification = Notification(
            id=str(uuid.uuid4()),
            recipient_id=recipient_id,
            notification_type=NotificationType.CHAT,
            priority=NotificationPriority.NORMAL,
            title=title,
            message=message,
            chat_id=chat_id,
            send_push=True,
            send_email=False,
            send_sms=False
        )
        return notification