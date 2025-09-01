"""
Pydantic схемы для подписок на уведомления
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class NotificationSubscriptionCreate(BaseModel):
    """Создание подписки на уведомления"""
    user_id: str
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    telegram_enabled: bool = False
    system_notifications: bool = True
    order_notifications: bool = True
    payment_notifications: bool = True
    chat_notifications: bool = True
    promotion_notifications: bool = False
    security_notifications: bool = True
    social_notifications: bool = True
    marketing_notifications: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    timezone: str = "Europe/Moscow"
    frequency_limit: Optional[int] = None
    batch_notifications: bool = False
    batch_interval: int = 60
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    language: str = "ru"
    personalization_enabled: bool = True


class NotificationSubscriptionUpdate(BaseModel):
    """Обновление подписки на уведомления"""
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    system_notifications: Optional[bool] = None
    order_notifications: Optional[bool] = None
    payment_notifications: Optional[bool] = None
    chat_notifications: Optional[bool] = None
    promotion_notifications: Optional[bool] = None
    security_notifications: Optional[bool] = None
    social_notifications: Optional[bool] = None
    marketing_notifications: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None
    frequency_limit: Optional[int] = None
    batch_notifications: Optional[bool] = None
    batch_interval: Optional[int] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    language: Optional[str] = None
    personalization_enabled: Optional[bool] = None


class NotificationSubscriptionResponse(BaseModel):
    """Ответ с данными подписки"""
    id: str
    user_id: str
    push_enabled: bool
    email_enabled: bool
    sms_enabled: bool
    telegram_enabled: bool
    system_notifications: bool
    order_notifications: bool
    payment_notifications: bool
    chat_notifications: bool
    promotion_notifications: bool
    security_notifications: bool
    social_notifications: bool
    marketing_notifications: bool
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str
    timezone: str
    frequency_limit: Optional[int]
    batch_notifications: bool
    batch_interval: int
    email_address: Optional[str]
    phone_number: Optional[str]
    telegram_chat_id: Optional[str]
    language: str
    personalization_enabled: bool
    total_sent: int
    total_delivered: int
    created_at: datetime
    updated_at: datetime
    last_notification_at: Optional[datetime]


class SubscriptionPreferencesUpdate(BaseModel):
    """Обновление предпочтений подписки"""
    channels: Optional[Dict[str, bool]] = None  # {"push": true, "email": false}
    notification_types: Optional[Dict[str, bool]] = None  # {"system": true, "marketing": false}
    quiet_hours: Optional[Dict[str, Any]] = None  # {"enabled": true, "start": "22:00", "end": "08:00"}
    frequency: Optional[Dict[str, Any]] = None  # {"limit": 10, "batch": true, "interval": 60}


class SubscriptionTestRequest(BaseModel):
    """Запрос на тест уведомления"""
    channels: List[str] = ["push"]  # Каналы для тестирования
    test_message: str = "Это тестовое уведомление"


class SubscriptionStatisticsResponse(BaseModel):
    """Ответ со статистикой подписки"""
    user_id: str
    total_sent: int
    total_delivered: int
    delivery_rate: Optional[float]
    read_rate: Optional[float]
    click_rate: Optional[float]
    channels_stats: Dict[str, Dict[str, Any]]
    types_stats: Dict[str, Dict[str, Any]]
    period_start: datetime
    period_end: datetime


class SubscriptionBulkUpdateRequest(BaseModel):
    """Запрос на массовое обновление подписок"""
    user_ids: List[str]
    preferences: SubscriptionPreferencesUpdate


class SubscriptionExportRequest(BaseModel):
    """Запрос на экспорт подписок"""
    user_ids: Optional[List[str]] = None
    format: str = "csv"  # csv, json, xml


class SubscriptionImportRequest(BaseModel):
    """Запрос на импорт подписок"""
    data: List[Dict[str, Any]]
    update_existing: bool = False


class SubscriptionUnsubscribeRequest(BaseModel):
    """Запрос на отписку от уведомлений"""
    channels: Optional[List[str]] = None  # Если None - отписка от всех
    reason: Optional[str] = None


class SubscriptionResubscribeRequest(BaseModel):
    """Запрос на повторную подписку"""
    channels: List[str]


class SubscriptionListResponse(BaseModel):
    """Ответ со списком подписок"""
    subscriptions: List[NotificationSubscriptionResponse]
    total: int
    page: int
    limit: int
    pages: int


class SubscriptionSearchRequest(BaseModel):
    """Запрос на поиск подписок"""
    query: str
    channels_enabled: Optional[List[str]] = None
    types_enabled: Optional[List[str]] = None
    has_quiet_hours: Optional[bool] = None
    language: Optional[str] = None
    limit: int = 50
