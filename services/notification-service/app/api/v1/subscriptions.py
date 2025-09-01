"""
API роуты для управления подписками на уведомления
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notification_subscription import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionUpdate,
    NotificationSubscriptionResponse
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("", response_model=NotificationSubscriptionResponse, summary="Создание подписки")
async def create_subscription(
    subscription_data: NotificationSubscriptionCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание подписки на уведомления"""
    try:
        subscription = await SubscriptionService.create_subscription(db, subscription_data)

        return NotificationSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            push_enabled=subscription.push_enabled,
            email_enabled=subscription.email_enabled,
            sms_enabled=subscription.sms_enabled,
            telegram_enabled=subscription.telegram_enabled,
            system_notifications=subscription.system_notifications,
            order_notifications=subscription.order_notifications,
            payment_notifications=subscription.payment_notifications,
            chat_notifications=subscription.chat_notifications,
            promotion_notifications=subscription.promotion_notifications,
            security_notifications=subscription.security_notifications,
            social_notifications=subscription.social_notifications,
            marketing_notifications=subscription.marketing_notifications,
            quiet_hours_enabled=subscription.quiet_hours_enabled,
            quiet_hours_start=subscription.quiet_hours_start,
            quiet_hours_end=subscription.quiet_hours_end,
            timezone=subscription.timezone,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания подписки")


@router.get("", response_model=NotificationSubscriptionResponse, summary="Получение подписки")
async def get_subscription(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение подписки пользователя"""
    try:
        subscription = await SubscriptionService.get_subscription_by_user_id(db, current_user["user_id"])

        if not subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")

        return NotificationSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            push_enabled=subscription.push_enabled,
            email_enabled=subscription.email_enabled,
            sms_enabled=subscription.sms_enabled,
            telegram_enabled=subscription.telegram_enabled,
            system_notifications=subscription.system_notifications,
            order_notifications=subscription.order_notifications,
            payment_notifications=subscription.payment_notifications,
            chat_notifications=subscription.chat_notifications,
            promotion_notifications=subscription.promotion_notifications,
            security_notifications=subscription.security_notifications,
            social_notifications=subscription.social_notifications,
            marketing_notifications=subscription.marketing_notifications,
            quiet_hours_enabled=subscription.quiet_hours_enabled,
            quiet_hours_start=subscription.quiet_hours_start,
            quiet_hours_end=subscription.quiet_hours_end,
            timezone=subscription.timezone,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения подписки")


@router.put("", response_model=NotificationSubscriptionResponse, summary="Обновление подписки")
async def update_subscription(
    subscription_data: NotificationSubscriptionUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление подписки пользователя"""
    try:
        subscription = await SubscriptionService.get_subscription_by_user_id(db, current_user["user_id"])

        if not subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")

        # Обновление полей
        update_data = subscription_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(subscription, field):
                setattr(subscription, field, value)

        await db.commit()
        await db.refresh(subscription)

        return NotificationSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            push_enabled=subscription.push_enabled,
            email_enabled=subscription.email_enabled,
            sms_enabled=subscription.sms_enabled,
            telegram_enabled=subscription.telegram_enabled,
            system_notifications=subscription.system_notifications,
            order_notifications=subscription.order_notifications,
            payment_notifications=subscription.payment_notifications,
            chat_notifications=subscription.chat_notifications,
            promotion_notifications=subscription.promotion_notifications,
            security_notifications=subscription.security_notifications,
            social_notifications=subscription.social_notifications,
            marketing_notifications=subscription.marketing_notifications,
            quiet_hours_enabled=subscription.quiet_hours_enabled,
            quiet_hours_start=subscription.quiet_hours_start,
            quiet_hours_end=subscription.quiet_hours_end,
            timezone=subscription.timezone,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления подписки")


@router.put("/enable/{channel}", summary="Включение канала")
async def enable_channel(
    channel: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Включение канала уведомлений"""
    try:
        subscription = await SubscriptionService.get_subscription_by_user_id(db, current_user["user_id"])

        if not subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")

        if hasattr(subscription, f"{channel}_enabled"):
            setattr(subscription, f"{channel}_enabled", True)
            await db.commit()

            return {"message": f"Канал {channel} включен"}

        raise HTTPException(status_code=400, detail="Неверный канал")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling channel {channel}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка включения канала")


@router.put("/disable/{channel}", summary="Отключение канала")
async def disable_channel(
    channel: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отключение канала уведомлений"""
    try:
        subscription = await SubscriptionService.get_subscription_by_user_id(db, current_user["user_id"])

        if not subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")

        if hasattr(subscription, f"{channel}_enabled"):
            setattr(subscription, f"{channel}_enabled", False)
            await db.commit()

            return {"message": f"Канал {channel} отключен"}

        raise HTTPException(status_code=400, detail="Неверный канал")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling channel {channel}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отключения канала")


@router.post("/test", summary="Тестовое уведомление")
async def send_test_notification(
    channels: list[str] = Query(["push"], description="Каналы для тестирования"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправка тестового уведомления"""
    try:
        # Создание тестового уведомления
        from app.services.notification_service import NotificationService
        from app.schemas.notification import NotificationSendRequest

        test_request = NotificationSendRequest(
            recipient_id=current_user["user_id"],
            notification_type="system",
            priority="normal",
            title="Тестовое уведомление",
            message="Это тестовое уведомление для проверки настроек",
            channels=channels
        )

        notification = await NotificationService.send_notification(db, test_request)

        return {
            "message": "Тестовое уведомление отправлено",
            "notification_id": notification.id
        }

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки тестового уведомления")