"""
Модель кампаний рассылок уведомлений.

Используется сервисами кампаний и эндпоинтом `app.api.v1.campaigns`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum

from .base import Base


class CampaignType(str, enum.Enum):
    """Типы кампаний"""
    NEWSLETTER = "newsletter"        # Рассылка новостей
    PROMOTION = "promotion"          # Рекламная кампания
    SYSTEM = "system"                # Системная рассылка
    TRANSACTIONAL = "transactional"  # Транзакционные уведомления


class CampaignStatus(str, enum.Enum):
    """Статусы кампаний"""
    DRAFT = "draft"                  # Черновик
    SCHEDULED = "scheduled"          # Запланирована
    RUNNING = "running"              # Выполняется
    PAUSED = "paused"                # Приостановлена
    COMPLETED = "completed"          # Завершена
    CANCELLED = "cancelled"          # Отменена


class CampaignPriority(str, enum.Enum):
    """Приоритеты кампаний"""
    LOW = "low"                      # Низкий
    NORMAL = "normal"                # Обычный
    HIGH = "high"                    # Высокий
    URGENT = "urgent"                # Срочный


class NotificationCampaign(Base):
    """Модель кампании рассылки уведомлений"""
    __tablename__ = "notification_campaigns"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Тип и статус
    campaign_type = Column(Enum(CampaignType), nullable=False)
    status = Column(Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)
    priority = Column(Enum(CampaignPriority), nullable=False, default=CampaignPriority.NORMAL)

    # Содержимое
    subject = Column(String, nullable=True)                    # Тема (для email)
    content = Column(Text, nullable=False)                     # Содержимое
    html_content = Column(Text, nullable=True)                 # HTML содержимое

    # Каналы доставки
    send_push = Column(Boolean, default=False)
    send_email = Column(Boolean, default=True)
    send_sms = Column(Boolean, default=False)
    send_telegram = Column(Boolean, default=False)

    # Аудитория
    target_users = Column(JSON, nullable=True)                 # Список целевых пользователей
    target_segments = Column(JSON, nullable=True)              # Сегменты аудитории
    target_filters = Column(JSON, nullable=True)               # Фильтры аудитории

    # Расписание
    scheduled_at = Column(DateTime, nullable=True)             # Запланированное время
    started_at = Column(DateTime, nullable=True)               # Время начала
    completed_at = Column(DateTime, nullable=True)             # Время завершения

    # Шаблон
    template_id = Column(String, ForeignKey("notification_templates.id"), nullable=True)

    # Создал
    creator_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Статистика
    total_recipients = Column(Integer, default=0)               # Общее количество получателей
    sent_count = Column(Integer, default=0)                     # Отправлено
    delivered_count = Column(Integer, default=0)                # Доставлено
    read_count = Column(Integer, default=0)                     # Прочитано
    clicked_count = Column(Integer, default=0)                  # Кликнуто
    failed_count = Column(Integer, default=0)                   # Неудачных
    unsubscribed_count = Column(Integer, default=0)             # Отписавшихся

    # Настройки
    respect_preferences = Column(Boolean, default=True)         # Учитывать предпочтения пользователей
    respect_quiet_hours = Column(Boolean, default=True)         # Учитывать тихие часы
    enable_tracking = Column(Boolean, default=True)             # Включить отслеживание

    # Бюджет и стоимость
    budget_limit = Column(Float, nullable=True)                 # Лимит бюджета
    estimated_cost = Column(Float, nullable=True)               # Предполагаемая стоимость
    actual_cost = Column(Float, nullable=True)                  # Фактическая стоимость

    # Метаданные
    metadata = Column(JSON, nullable=True)                      # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NotificationCampaign(id={self.id}, name={self.name}, type={self.campaign_type.value}, status={self.status.value})>"

    @property
    def is_draft(self) -> bool:
        """Проверка, является ли черновиком"""
        return self.status == CampaignStatus.DRAFT

    @property
    def is_scheduled(self) -> bool:
        """Проверка, запланирована ли"""
        return self.status == CampaignStatus.SCHEDULED

    @property
    def is_running(self) -> bool:
        """Проверка, выполняется ли"""
        return self.status == CampaignStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Проверка, завершена ли"""
        return self.status == CampaignStatus.COMPLETED

    @property
    def delivery_rate(self) -> Optional[float]:
        """Расчет процента доставки"""
        if self.sent_count == 0:
            return None
        return (self.delivered_count / self.sent_count) * 100

    @property
    def open_rate(self) -> Optional[float]:
        """Расчет процента прочтения"""
        if self.delivered_count == 0:
            return None
        return (self.read_count / self.delivered_count) * 100

    @property
    def click_rate(self) -> Optional[float]:
        """Расчет процента кликов"""
        if self.delivered_count == 0:
            return None
        return (self.clicked_count / self.delivered_count) * 100

    @property
    def bounce_rate(self) -> Optional[float]:
        """Расчет процента отказов"""
        if self.sent_count == 0:
            return None
        return (self.failed_count / self.sent_count) * 100

    @property
    def channels(self) -> list[str]:
        """Получение списка каналов"""
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

    def start_campaign(self):
        """Запуск кампании"""
        self.status = CampaignStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete_campaign(self):
        """Завершение кампании"""
        self.status = CampaignStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def pause_campaign(self):
        """Приостановка кампании"""
        self.status = CampaignStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def cancel_campaign(self):
        """Отмена кампании"""
        self.status = CampaignStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def increment_sent(self):
        """Увеличение счетчика отправленных"""
        self.sent_count += 1
        self.updated_at = datetime.utcnow()

    def increment_delivered(self):
        """Увеличение счетчика доставленных"""
        self.delivered_count += 1
        self.updated_at = datetime.utcnow()

    def increment_read(self):
        """Увеличение счетчика прочитанных"""
        self.read_count += 1
        self.updated_at = datetime.utcnow()

    def increment_clicked(self):
        """Увеличение счетчика кликнутых"""
        self.clicked_count += 1
        self.updated_at = datetime.utcnow()

    def increment_failed(self):
        """Увеличение счетчика неудачных"""
        self.failed_count += 1
        self.updated_at = datetime.utcnow()

    def set_recipients_count(self, count: int):
        """Установка количества получателей"""
        self.total_recipients = count
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "campaign_type": self.campaign_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "subject": self.subject,
            "content": self.content,
            "send_push": self.send_push,
            "send_email": self.send_email,
            "send_sms": self.send_sms,
            "send_telegram": self.send_telegram,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "template_id": self.template_id,
            "creator_id": self.creator_id,
            "total_recipients": self.total_recipients,
            "sent_count": self.sent_count,
            "delivered_count": self.delivered_count,
            "read_count": self.read_count,
            "clicked_count": self.clicked_count,
            "failed_count": self.failed_count,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_newsletter_campaign(
        name: str,
        subject: str,
        content: str,
        creator_id: str
    ) -> 'NotificationCampaign':
        """Создание кампании рассылки новостей"""
        campaign = NotificationCampaign(
            id=str(uuid.uuid4()),
            name=name,
            campaign_type=CampaignType.NEWSLETTER,
            subject=subject,
            content=content,
            creator_id=creator_id,
            send_email=True
        )
        return campaign

    @staticmethod
    def create_promotion_campaign(
        name: str,
        subject: str,
        content: str,
        creator_id: str
    ) -> 'NotificationCampaign':
        """Создание рекламной кампании"""
        campaign = NotificationCampaign(
            id=str(uuid.uuid4()),
            name=name,
            campaign_type=CampaignType.PROMOTION,
            subject=subject,
            content=content,
            creator_id=creator_id,
            send_push=True,
            send_email=True
        )
        return campaign
