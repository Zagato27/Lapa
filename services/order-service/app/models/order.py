"""
Модель заказа.

Используется:
- В `app.services.order_service.OrderService` для CRUD-операций и бизнес-логики заказов
- В `app.services.matching_service.MatchingService` для поиска/подбора
- В REST-эндпоинтах `app.api.v1.orders` для сериализации ответа через Pydantic-схемы

Основные поля включают геопозицию (PostGIS `POINT`), финансовые параметры и статусы.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import enum

from .base import Base


class OrderStatus(str, enum.Enum):
    """Статусы заказа"""
    PENDING = "pending"          # Ожидает подтверждения выгульщика
    CONFIRMED = "confirmed"      # Подтвержден выгульщиком
    IN_PROGRESS = "in_progress"  # Выполняется
    COMPLETED = "completed"      # Завершен успешно
    CANCELLED = "cancelled"      # Отменен
    NO_WALKER = "no_walker"      # Не найден выгульщик


class OrderType(str, enum.Enum):
    """Типы заказов"""
    SINGLE_WALK = "single_walk"      # Разовый выгул
    REGULAR_WALK = "regular_walk"    # Регулярный выгул
    PET_SITTING = "pet_sitting"      # Передержка
    PET_BOARDING = "pet_boarding"    # Зоогостиница


class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    # Межсервисные связи храним как строки без жёстких FK
    client_id = Column(String, nullable=False, index=True)
    walker_id = Column(String, nullable=True, index=True)
    pet_id = Column(String, nullable=False, index=True)

    # Тип и статус заказа
    order_type = Column(Enum(OrderType), nullable=False, default=OrderType.SINGLE_WALK)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)

    # Временные данные
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)

    # Геолокация
    # Геометрия хранится в PostGIS с SRID=4326 (WGS84)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=True)

    # Финансовая информация
    walker_hourly_rate = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)  # Общая сумма
    platform_commission = Column(Float, nullable=False)  # Комиссия платформы
    walker_earnings = Column(Float, nullable=False)  # Заработок выгульщика

    # Дополнительная информация
    special_instructions = Column(Text, nullable=True)
    walker_notes = Column(Text, nullable=True)  # Заметки выгульщика

    # Рейтинг и отзыв
    client_rating = Column(Float, nullable=True)  # Оценка от клиента
    walker_rating = Column(Float, nullable=True)  # Оценка от выгульщика
    client_review = Column(Text, nullable=True)
    walker_review = Column(Text, nullable=True)

    # Системная информация
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    confirmed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Причины отмены
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by = Column(String, nullable=True)  # user_id того, кто отменил

    # Настройки уведомлений
    client_notified = Column(Boolean, default=False)
    walker_notified = Column(Boolean, default=False)
    review_reminder_sent = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Order(id={self.id}, client={self.client_id}, walker={self.walker_id}, status={self.status.value})>"

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли заказ подтверждения"""
        return self.status == OrderStatus.PENDING

    @property
    def is_confirmed(self) -> bool:
        """Проверка, подтвержден ли заказ"""
        return self.status == OrderStatus.CONFIRMED

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли заказ"""
        return self.status in [OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]

    @property
    def is_completed(self) -> bool:
        """Проверка, завершен ли заказ"""
        return self.status == OrderStatus.COMPLETED

    @property
    def is_cancelled(self) -> bool:
        """Проверка, отменен ли заказ"""
        return self.status == OrderStatus.CANCELLED

    @property
    def duration_hours(self) -> float:
        """Продолжительность заказа в часах"""
        return self.duration_minutes / 60

    @property
    def actual_duration_minutes(self) -> Optional[int]:
        """Фактическая продолжительность заказа в минутах"""
        if self.actual_start_time and self.actual_end_time:
            return int((self.actual_end_time - self.actual_start_time).total_seconds() / 60)
        return None

    @property
    def can_be_cancelled_by_client(self) -> bool:
        """Проверка, может ли клиент отменить заказ"""
        if self.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            return False

        # Нельзя отменить менее чем за час до начала
        if self.scheduled_at:
            time_until_start = (self.scheduled_at - datetime.utcnow()).total_seconds() / 3600
            return time_until_start > 1

        return True

    @property
    def can_be_cancelled_by_walker(self) -> bool:
        """Проверка, может ли выгульщик отменить заказ"""
        if self.status not in [OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]:
            return False

        # Нельзя отменить менее чем за 30 минут до начала
        if self.scheduled_at:
            time_until_start = (self.scheduled_at - datetime.utcnow()).total_seconds() / 3600
            return time_until_start > 0.5

        return True

    def confirm(self, walker_id: str):
        """Подтверждение заказа выгульщиком"""
        self.walker_id = walker_id
        self.status = OrderStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()

    def start_walk(self):
        """Начало прогулки"""
        self.status = OrderStatus.IN_PROGRESS
        self.actual_start_time = datetime.utcnow()

    def complete_walk(self):
        """Завершение прогулки"""
        self.status = OrderStatus.COMPLETED
        self.actual_end_time = datetime.utcnow()
        self.completed_at = datetime.utcnow()

    def cancel(self, cancelled_by: str, reason: Optional[str] = None):
        """Отмена заказа"""
        self.status = OrderStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by = cancelled_by
        if reason:
            self.cancellation_reason = reason

    def add_client_review(self, rating: float, review: Optional[str] = None):
        """Добавление отзыва от клиента"""
        self.client_rating = rating
        if review:
            self.client_review = review

    def add_walker_review(self, rating: float, review: Optional[str] = None):
        """Добавление отзыва от выгульщика"""
        self.walker_rating = rating
        if review:
            self.walker_review = review
