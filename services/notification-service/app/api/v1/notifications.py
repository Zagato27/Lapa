"""
API роуты для управления уведомлениями
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notification import (
    NotificationSendRequest,
    NotificationResponse,
    NotificationListResponse
)
from app.services.notification_service import NotificationService

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

    # Здесь должна быть валидация токена через API Gateway
    # Пока что просто возвращаем данные из request
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("/send", response_model=NotificationResponse, summary="Отправка уведомления")
async def send_notification(
    request: NotificationSendRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправка уведомления"""
    try:
        notification = await NotificationService.send_notification(db, request)

        return NotificationService.notification_to_response(notification)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки уведомления")


@router.get("", response_model=NotificationListResponse, summary="Получение списка уведомлений")
async def get_notifications(
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество уведомлений на странице"),
    status: str = Query(None, description="Фильтр по статусу"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка уведомлений пользователя"""
    try:
        result = await NotificationService.get_user_notifications(
            db, current_user["user_id"], page, limit, status
        )

        return NotificationListResponse(
            notifications=result["notifications"],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"]
        )

    except Exception as e:
        logger.error(f"Error getting notifications list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка уведомлений")


@router.get("/{notification_id}", response_model=NotificationResponse, summary="Получение уведомления по ID")
async def get_notification(
    notification_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение уведомления по ID"""
    try:
        notification = await NotificationService.get_notification_by_id(db, notification_id, current_user["user_id"])

        if not notification:
            raise HTTPException(status_code=404, detail="Уведомление не найдено")

        return NotificationService.notification_to_response(notification)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения уведомления")


@router.put("/{notification_id}/read", summary="Отметить как прочитанное")
async def mark_as_read(
    notification_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить уведомление как прочитанное"""
    try:
        updated_count = await NotificationService.mark_notifications_read(db, [notification_id], current_user["user_id"])

        if updated_count == 0:
            raise HTTPException(status_code=404, detail="Уведомление не найдено")

        return {"message": "Уведомление отмечено как прочитанное"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отметки уведомления")


@router.put("/read", summary="Отметить все как прочитанные")
async def mark_all_read(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить все уведомления пользователя как прочитанные"""
    try:
        # Получение всех непрочитанных уведомлений
        result = await NotificationService.get_user_notifications(db, current_user["user_id"])
        notification_ids = [n.id for n in result["notifications"] if n.status in ["sent", "delivered"]]

        if not notification_ids:
            return {"message": "Нет непрочитанных уведомлений"}

        updated_count = await NotificationService.mark_notifications_read(db, notification_ids, current_user["user_id"])

        return {"message": f"Отмечено {updated_count} уведомлений как прочитанные"}

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отметки уведомлений")


@router.delete("/{notification_id}", summary="Удаление уведомления")
async def delete_notification(
    notification_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление уведомления"""
    try:
        deleted_count = await NotificationService.delete_notifications(db, [notification_id], current_user["user_id"])

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Уведомление не найдено")

        return {"message": "Уведомление успешно удалено"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления уведомления")


@router.delete("", summary="Удаление нескольких уведомлений")
async def delete_notifications(
    notification_ids: list[str] = Query(..., description="ID уведомлений для удаления"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление нескольких уведомлений"""
    try:
        deleted_count = await NotificationService.delete_notifications(db, notification_ids, current_user["user_id"])

        return {"message": f"Удалено {deleted_count} уведомлений"}

    except Exception as e:
        logger.error(f"Error deleting notifications: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления уведомлений")


@router.put("/{notification_id}/cancel", summary="Отмена уведомления")
async def cancel_notification(
    notification_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отмена отправки уведомления"""
    try:
        success = await NotificationService.cancel_notification(db, notification_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Уведомление не найдено")

        return {"message": "Уведомление успешно отменено"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отмены уведомления")


@router.get("/stats", summary="Статистика уведомлений")
async def get_notification_stats(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики уведомлений пользователя"""
    try:
        result = await NotificationService.get_user_notifications(db, current_user["user_id"])

        total = result["total"]
        notifications = result["notifications"]

        stats = {
            "total": total,
            "unread": len([n for n in notifications if n.status in ["sent", "delivered"]]),
            "read": len([n for n in notifications if n.status == "read"]),
            "by_type": {},
            "by_status": {}
        }

        # Статистика по типам
        for notification in notifications:
            n_type = notification.notification_type.value
            n_status = notification.status.value

            stats["by_type"][n_type] = stats["by_type"].get(n_type, 0) + 1
            stats["by_status"][n_status] = stats["by_status"].get(n_status, 0) + 1

        return stats

    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")