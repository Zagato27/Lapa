"""
Сервис для управления подписками на уведомления
"""

import logging
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification_subscription import NotificationSubscription
from app.schemas.notification_subscription import NotificationSubscriptionCreate

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Сервис для работы с подписками на уведомления"""

    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        subscription_data: NotificationSubscriptionCreate
    ) -> NotificationSubscription:
        """Создание подписки"""
        try:
            subscription = NotificationSubscription(
                id=str(uuid.uuid4()),
                user_id=subscription_data.user_id,
                push_enabled=subscription_data.push_enabled,
                email_enabled=subscription_data.email_enabled,
                sms_enabled=subscription_data.sms_enabled,
                telegram_enabled=subscription_data.telegram_enabled,
                email_address=subscription_data.email_address,
                phone_number=subscription_data.phone_number,
                telegram_chat_id=subscription_data.telegram_chat_id,
                language=subscription_data.language
            )

            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)

            logger.info(f"Subscription created for user {subscription.user_id}")
            return subscription

        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_subscription_by_user_id(
        db: AsyncSession,
        user_id: str
    ) -> Optional[NotificationSubscription]:
        """Получение подписки по ID пользователя"""
        try:
            query = select(NotificationSubscription).where(NotificationSubscription.user_id == user_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting subscription for user {user_id}: {e}")
            return None
