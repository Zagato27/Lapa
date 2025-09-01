"""
Основной сервис для управления уведомлениями
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_session
from app.models.notification import Notification, NotificationType, NotificationPriority, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationResponse

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для работы с уведомлениями"""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        notification_data: NotificationCreate
    ) -> Notification:
        """Создание уведомления"""
        try:
            notification = Notification(
                id=str(uuid.uuid4()),
                recipient_id=notification_data.recipient_id,
                notification_type=notification_data.notification_type,
                priority=notification_data.priority,
                title=notification_data.title,
                message=notification_data.message,
                data=notification_data.data,
                send_push=notification_data.send_push,
                send_email=notification_data.send_email,
                send_sms=notification_data.send_sms,
                send_telegram=notification_data.send_telegram,
                language=notification_data.language
            )

            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            logger.info(f"Notification created: {notification.id}")
            return notification

        except Exception as e:
            logger.error(f"Notification creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    def notification_to_response(notification: Notification) -> NotificationResponse:
        """Преобразование модели в схему ответа"""
        return NotificationResponse(
            id=notification.id,
            recipient_id=notification.recipient_id,
            notification_type=notification.notification_type,
            priority=notification.priority,
            status=notification.status,
            title=notification.title,
            message=notification.message,
            data=notification.data,
            send_push=notification.send_push,
            send_email=notification.send_email,
            send_sms=notification.send_sms,
            send_telegram=notification.send_telegram,
            language=notification.language,
            created_at=notification.created_at,
            updated_at=notification.updated_at
        )
