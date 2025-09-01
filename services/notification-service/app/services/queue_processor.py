"""
Процессор очереди уведомлений
"""

import asyncio
import logging
from typing import List, Dict, Any

from app.database.session import get_session
from app.config import settings

logger = logging.getLogger(__name__)


class QueueProcessor:
    """Процессор для обработки очереди уведомлений"""

    def __init__(self):
        self.is_processing = False
        self.processing_interval = settings.queue_processing_interval

    async def start_processing(self):
        """Запуск обработки очереди"""
        try:
            self.is_processing = True
            logger.info("Starting notification queue processor")

            while self.is_processing:
                try:
                    await self._process_batch()
                    await asyncio.sleep(self.processing_interval)
                except Exception as e:
                    logger.error(f"Error in queue processing batch: {e}")
                    await asyncio.sleep(5)  # Пауза перед следующей попыткой

        except Exception as e:
            logger.error(f"Error starting queue processor: {e}")

    async def stop_processing(self):
        """Остановка обработки очереди"""
        try:
            self.is_processing = False
            logger.info("Stopping notification queue processor")

        except Exception as e:
            logger.error(f"Error stopping queue processor: {e}")

    async def _process_batch(self):
        """Обработка пакета уведомлений"""
        try:
            redis_session = await get_session()

            # Получение уведомлений из очереди
            notifications = await redis_session.dequeue_notifications(settings.queue_batch_size)

            if not notifications:
                return

            logger.info(f"Processing {len(notifications)} notifications")

            # Обработка каждого уведомления
            for notification_data in notifications:
                try:
                    await self._process_notification(notification_data)
                except Exception as e:
                    logger.error(f"Error processing notification {notification_data.get('id')}: {e}")

        except Exception as e:
            logger.error(f"Error processing notification batch: {e}")

    async def _process_notification(self, notification_data: Dict[str, Any]):
        """Обработка одного уведомления"""
        try:
            notification_id = notification_data.get("id")
            recipient_id = notification_data.get("recipient_id")
            channels = notification_data.get("channels", [])

            logger.debug(f"Processing notification {notification_id} for user {recipient_id}")

            # Здесь должна быть логика отправки уведомления через каждый канал
            for channel in channels:
                try:
                    await self._send_via_channel(notification_id, recipient_id, channel)
                except Exception as e:
                    logger.error(f"Error sending notification {notification_id} via {channel}: {e}")

        except Exception as e:
            logger.error(f"Error processing notification {notification_data.get('id')}: {e}")

    async def _send_via_channel(self, notification_id: str, recipient_id: str, channel: str):
        """Отправка уведомления через конкретный канал"""
        try:
            logger.debug(f"Sending notification {notification_id} to {recipient_id} via {channel}")

            # Здесь должна быть логика отправки через конкретный канал
            # (Firebase для push, SendGrid для email, Twilio для SMS и т.д.)

            # Имитация успешной отправки
            await asyncio.sleep(0.1)  # Имитация сетевой задержки

            logger.debug(f"Successfully sent notification {notification_id} via {channel}")

        except Exception as e:
            logger.error(f"Error sending via {channel}: {e}")
            raise
