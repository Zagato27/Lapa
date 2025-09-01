"""
Модель платежей.

Используется:
- `PaymentService` для CRUD, обработки и возвратов
- Эндпоинты `app.api.v1.payments`
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

from .base import Base


class PaymentStatus(str, enum.Enum):
    """Статусы платежа"""
    PENDING = "pending"          # Ожидает оплаты
    PROCESSING = "processing"    # Обрабатывается
    COMPLETED = "completed"      # Завершен успешно
    FAILED = "failed"           # Ошибка оплаты
    CANCELLED = "cancelled"     # Отменен
    REFUNDED = "refunded"       # Возвращен
    PARTIALLY_REFUNDED = "partially_refunded"  # Частично возвращен


class PaymentType(str, enum.Enum):
    """Типы платежей"""
    ORDER_PAYMENT = "order_payment"      # Оплата заказа
    WALLET_TOPUP = "wallet_topup"        # Пополнение кошелька
    SUBSCRIPTION = "subscription"        # Подписка
    DONATION = "donation"               # Пожертвование
    FINE = "fine"                      # Штраф
    BONUS = "bonus"                    # Бонус


class PaymentProvider(str, enum.Enum):
    """Платежные провайдеры"""
    STRIPE = "stripe"
    YOOKASSA = "yookassa"
    TINKOFF = "tinkoff"
    SBP = "sbp"
    WALLET = "wallet"
    CASH = "cash"


class Payment(Base):
    """Модель платежа"""
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Тип и статус платежа
    payment_type = Column(Enum(PaymentType), nullable=False, default=PaymentType.ORDER_PAYMENT)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    provider = Column(Enum(PaymentProvider), nullable=False)

    # Финансовая информация
    amount = Column(Float, nullable=False)              # Сумма платежа
    currency = Column(String, nullable=False, default="RUB")
    platform_commission = Column(Float, nullable=False, default=0)  # Комиссия платформы
    provider_commission = Column(Float, nullable=True)  # Комиссия провайдера
    net_amount = Column(Float, nullable=False)          # Чистая сумма (без комиссий)

    # Данные платежного провайдера
    provider_payment_id = Column(String, nullable=True)    # ID платежа у провайдера
    provider_data = Column(JSON, nullable=True)           # Дополнительные данные провайдера

    # Способ оплаты
    payment_method_id = Column(String, ForeignKey("payment_methods.id"), nullable=True)

    # Описание и метаданные
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    # Возвраты
    refund_amount = Column(Float, nullable=True, default=0)
    refund_reason = Column(Text, nullable=True)

    # Системная информация
    is_test = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Webhook и уведомления
    webhook_received = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Payment(id={self.id}, user={self.user_id}, amount={self.amount}, status={self.status.value})>"

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли платеж оплаты"""
        return self.status == PaymentStatus.PENDING

    @property
    def is_processing(self) -> bool:
        """Проверка, обрабатывается ли платеж"""
        return self.status == PaymentStatus.PROCESSING

    @property
    def is_completed(self) -> bool:
        """Проверка, завершен ли платеж успешно"""
        return self.status == PaymentStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка оплаты"""
        return self.status == PaymentStatus.FAILED

    @property
    def is_refunded(self) -> bool:
        """Проверка, возвращен ли платеж"""
        return self.status in [PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED]

    @property
    def can_be_refunded(self) -> bool:
        """Проверка, можно ли вернуть платеж"""
        from app.config import settings
        from datetime import timedelta

        if not self.is_completed:
            return False

        # Проверка таймаута возврата
        if self.paid_at:
            refund_deadline = self.paid_at + timedelta(seconds=settings.payment_refund_timeout)
            return datetime.utcnow() <= refund_deadline

        return False

    @property
    def refundable_amount(self) -> float:
        """Сумма доступная для возврата"""
        if not self.can_be_refunded:
            return 0
        return self.net_amount - (self.refund_amount or 0)

    def mark_as_paid(self, provider_payment_id: Optional[str] = None):
        """Отметить платеж как оплаченный"""
        self.status = PaymentStatus.COMPLETED
        self.paid_at = datetime.utcnow()
        if provider_payment_id:
            self.provider_payment_id = provider_payment_id
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, reason: Optional[str] = None):
        """Отметить платеж как неудачный"""
        self.status = PaymentStatus.FAILED
        self.extra_metadata = self.extra_metadata or {}
        if reason:
            self.extra_metadata["failure_reason"] = reason
        self.updated_at = datetime.utcnow()

    def mark_as_cancelled(self, reason: Optional[str] = None):
        """Отметить платеж как отмененный"""
        self.status = PaymentStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.extra_metadata = self.extra_metadata or {}
            self.extra_metadata["cancellation_reason"] = reason
        self.updated_at = datetime.utcnow()

    def process_refund(self, amount: float, reason: Optional[str] = None):
        """Обработать возврат платежа"""
        if amount > self.refundable_amount:
            raise ValueError("Сумма возврата превышает доступную сумму")

        self.refund_amount = (self.refund_amount or 0) + amount

        if abs(self.refund_amount - self.net_amount) < 0.01:  # Полный возврат
            self.status = PaymentStatus.REFUNDED
            self.refunded_at = datetime.utcnow()
        else:
            self.status = PaymentStatus.PARTIALLY_REFUNDED

        if reason:
            self.refund_reason = reason

        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "payment_type": self.payment_type.value,
            "status": self.status.value,
            "provider": self.provider.value,
            "amount": self.amount,
            "currency": self.currency,
            "platform_commission": self.platform_commission,
            "net_amount": self.net_amount,
            "provider_payment_id": self.provider_payment_id,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "refund_amount": self.refund_amount,
            "is_test": self.is_test
        }
