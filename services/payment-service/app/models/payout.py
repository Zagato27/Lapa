"""
Модель выплат исполнителям.

Используется `PayoutService` и эндпоинтами `app.api.v1.payouts`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

from .base import Base


class PayoutStatus(str, enum.Enum):
    """Статусы выплат"""
    PENDING = "pending"          # Ожидает обработки
    PROCESSING = "processing"    # Обрабатывается
    COMPLETED = "completed"      # Завершена успешно
    FAILED = "failed"           # Ошибка выплаты
    CANCELLED = "cancelled"     # Отменена
    ON_HOLD = "on_hold"         # На удержании


class PayoutMethod(str, enum.Enum):
    """Методы выплат"""
    BANK_CARD = "bank_card"          # Банковская карта
    BANK_ACCOUNT = "bank_account"    # Банковский счет
    ELECTRONIC_WALLET = "electronic_wallet"  # Электронный кошелек
    CASH = "cash"                   # Наличные
    SBP = "sbp"                     # Система быстрых платежей


class Payout(Base):
    """Модель выплаты исполнителю"""
    __tablename__ = "payouts"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Финансовая информация
    amount = Column(Float, nullable=False)              # Сумма выплаты
    currency = Column(String, nullable=False, default="RUB")
    platform_fee = Column(Float, nullable=False, default=0)  # Комиссия платформы
    net_amount = Column(Float, nullable=False)          # Чистая сумма к выплате

    # Статус и метод
    status = Column(Enum(PayoutStatus), nullable=False, default=PayoutStatus.PENDING)
    method = Column(Enum(PayoutMethod), nullable=False)

    # Период выплат
    period_start = Column(DateTime, nullable=False)     # Начало периода
    period_end = Column(DateTime, nullable=False)       # Конец периода

    # Данные получателя
    recipient_name = Column(String, nullable=False)
    recipient_data = Column(JSON, nullable=False)       # Данные для выплаты (карта, счет и т.д.)

    # Связанные заказы
    order_ids = Column(JSON, nullable=True)             # Список ID заказов для этой выплаты

    # Данные платежного провайдера
    provider_payout_id = Column(String, nullable=True)  # ID выплаты у провайдера
    provider_data = Column(JSON, nullable=True)         # Дополнительные данные провайдера

    # Обработка
    processed_by = Column(String, nullable=True)        # Кто обработал выплату
    processed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)        # Причина неудачи

    # Системная информация
    is_test = Column(Boolean, default=False)
    priority = Column(String, default="normal")         # normal, high, urgent

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    scheduled_at = Column(DateTime, nullable=True)      # Запланированное время выплаты

    def __repr__(self):
        return f"<Payout(id={self.id}, user={self.user_id}, amount={self.amount}, status={self.status.value})>"

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли выплата обработки"""
        return self.status == PayoutStatus.PENDING

    @property
    def is_processing(self) -> bool:
        """Проверка, обрабатывается ли выплата"""
        return self.status == PayoutStatus.PROCESSING

    @property
    def is_completed(self) -> bool:
        """Проверка, завершена ли выплата"""
        return self.status == PayoutStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка выплаты"""
        return self.status == PayoutStatus.FAILED

    @property
    def period_days(self) -> int:
        """Количество дней в периоде выплаты"""
        from datetime import timedelta
        delta = self.period_end - self.period_start
        return delta.days

    def mark_as_processing(self):
        """Отметить как обрабатываемую"""
        self.status = PayoutStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_as_completed(self, provider_payout_id: Optional[str] = None):
        """Отметить как завершенную"""
        self.status = PayoutStatus.COMPLETED
        self.processed_at = datetime.utcnow()
        if provider_payout_id:
            self.provider_payout_id = provider_payout_id
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, reason: Optional[str] = None):
        """Отметить как неудачную"""
        self.status = PayoutStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.utcnow()

    def mark_as_cancelled(self, reason: Optional[str] = None):
        """Отметить как отмененную"""
        self.status = PayoutStatus.CANCELLED
        if reason:
            self.failure_reason = reason
        self.updated_at = datetime.utcnow()

    def put_on_hold(self, reason: Optional[str] = None):
        """Поставить на удержание"""
        self.status = PayoutStatus.ON_HOLD
        if reason:
            self.failure_reason = reason
        self.updated_at = datetime.utcnow()

    def release_from_hold(self):
        """Снять с удержания"""
        if self.status == PayoutStatus.ON_HOLD:
            self.status = PayoutStatus.PENDING
            self.failure_reason = None
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "method": self.method.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "recipient_name": self.recipient_name,
            "processed_by": self.processed_by,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None
        }
