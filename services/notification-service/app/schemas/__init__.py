"""
Pydantic схемы для Notification Service
"""

from .notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationSendRequest,
    NotificationBulkSendRequest,
    NotificationListResponse
)
from .notification_template import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    TemplateRenderRequest,
    TemplateRenderResponse
)
from .notification_subscription import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionUpdate,
    NotificationSubscriptionResponse
)
from .notification_delivery import (
    NotificationDeliveryResponse,
    DeliveryStatusResponse
)
from .notification_campaign import (
    NotificationCampaignCreate,
    NotificationCampaignUpdate,
    NotificationCampaignResponse,
    CampaignRecipientAddRequest
)

__all__ = [
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    "NotificationSendRequest",
    "NotificationBulkSendRequest",
    "NotificationListResponse",
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    "TemplateRenderRequest",
    "TemplateRenderResponse",
    "NotificationSubscriptionCreate",
    "NotificationSubscriptionUpdate",
    "NotificationSubscriptionResponse",
    "NotificationDeliveryResponse",
    "DeliveryStatusResponse",
    "NotificationCampaignCreate",
    "NotificationCampaignUpdate",
    "NotificationCampaignResponse",
    "CampaignRecipientAddRequest"
]