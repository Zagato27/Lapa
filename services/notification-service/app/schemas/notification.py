"""
Pydantic-схемы (v2) для уведомлений.

Используются в эндпоинтах `app.api.v1.notifications` и сервисах уведомлений.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class NotificationType(str, enum.Enum):
    """Типы уведомлений"""
    SYSTEM = "system"
    ORDER = "order"
    PAYMENT = "payment"
    CHAT = "chat"
    PROMOTION = "promotion"
    SECURITY = "security"
    SOCIAL = "social"
    MARKETING = "marketing"


class NotificationPriority(str, enum.Enum):
    """Приоритеты уведомлений"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, enum.Enum):
    """Статусы уведомлений"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationCreate(BaseModel):
    """Создание уведомления"""
    recipient_id: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    order_id: Optional[str] = None
    chat_id: Optional[str] = None
    media_file_id: Optional[str] = None
    send_push: bool = True
    send_email: bool = False
    send_sms: bool = False
    send_telegram: bool = False
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    language: str = "ru"

    @field_validator('title')
    def validate_title(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('Title too long')
        return v

    @field_validator('message')
    def validate_message(cls, v: str) -> str:
        if len(v) > 2000:
            raise ValueError('Message too long')
        return v


class NotificationUpdate(BaseModel):
    """Обновление уведомления"""
    title: Optional[str] = None
    message: Optional[str] = None
    priority: Optional[NotificationPriority] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    """Ответ с данными уведомления"""
    id: str
    recipient_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    status: NotificationStatus
    title: str
    message: str
    data: Optional[Dict[str, Any]]
    order_id: Optional[str]
    chat_id: Optional[str]
    media_file_id: Optional[str]
    send_push: bool
    send_email: bool
    send_sms: bool
    send_telegram: bool
    scheduled_at: Optional[datetime]
    expires_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    failed_at: Optional[datetime]
    language: str
    created_at: datetime
    updated_at: datetime


class NotificationSendRequest(BaseModel):
    """Запрос на отправку уведомления"""
    recipient_id: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    channels: List[str] = ["push"]  # push, email, sms, telegram
    scheduled_at: Optional[datetime] = None
    template_id: Optional[str] = None
    language: str = "ru"


class NotificationBulkSendRequest(BaseModel):
    """Запрос на массовую отправку уведомлений"""
    recipient_ids: List[str]
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    channels: List[str] = ["push"]
    scheduled_at: Optional[datetime] = None
    template_id: Optional[str] = None
    language: str = "ru"

    @field_validator('recipient_ids')
    def validate_recipient_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError('At least one recipient required')
        if len(v) > 1000:
            raise ValueError('Too many recipients')
        return v


class NotificationListResponse(BaseModel):
    """Ответ со списком уведомлений"""
    notifications: List[NotificationResponse]
    total: int
    page: int
    limit: int
    pages: int


class NotificationMarkReadRequest(BaseModel):
    """Запрос на отметку уведомления как прочитанное"""
    notification_ids: List[str]


class NotificationDeleteRequest(BaseModel):
    """Запрос на удаление уведомления"""
    notification_ids: List[str]


class NotificationSearchRequest(BaseModel):
    """Запрос на поиск уведомлений"""
    query: str
    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    priority: Optional[NotificationPriority] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50


class NotificationStatisticsResponse(BaseModel):
    """Ответ со статистикой уведомлений"""
    total_notifications: int
    sent_today: int
    delivered_today: int
    read_today: int
    failed_today: int
    delivery_rate: float
    read_rate: float
    period_start: datetime
    period_end: datetime


class NotificationChannelStats(BaseModel):
    """Статистика по каналам"""
    channel: str
    sent: int
    delivered: int
    read: int
    failed: int
    delivery_rate: float
    read_rate: float


class NotificationTypeStats(BaseModel):
    """Статистика по типам"""
    notification_type: str
    sent: int
    delivered: int
    read: int
    failed: int
    delivery_rate: float
    read_rate: float