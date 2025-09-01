"""
Модели базы данных для Notification Service
"""

from .base import Base
from .notification import Notification
from .notification_template import NotificationTemplate
from .notification_channel import NotificationChannel
from .notification_subscription import NotificationSubscription
from .notification_delivery import NotificationDelivery
from .notification_campaign import NotificationCampaign

__all__ = [
    "Base",
    "Notification",
    "NotificationTemplate",
    "NotificationChannel",
    "NotificationSubscription",
    "NotificationDelivery",
    "NotificationCampaign"
]