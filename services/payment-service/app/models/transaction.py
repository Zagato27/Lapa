"""
Модель транзакций.

Используется `PaymentService` и `WalletService` для аудита операций.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

from .base import Base


class TransactionType(str, enum.Enum):
    """Типы транзакций"""
    PAYMENT = "payment"              # Платеж
    REFUND = "refund"                # Возврат
    PAYOUT = "payout"                # Выплата
    TRANSFER = "transfer"            # Перевод
    DEPOSIT = "deposit"              # Пополнение
    WITHDRAWAL = "withdrawal"        # Снятие
    FEE = "fee"                     # Комиссия
    BONUS = "bonus"                  # Бонус
    ADJUSTMENT = "adjustment"        # Корректировка


class TransactionStatus(str, enum.Enum):
    """Статусы транзакций"""
    PENDING = "pending"          # Ожидает обработки
    PROCESSING = "processing"    # Обрабатывается
    COMPLETED = "completed"      # Завершена успешно
    FAILED = "failed"           # Ошибка
    CANCELLED = "cancelled"     # Отменена


class Transaction(Base):
    """Модель транзакции"""
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)

    # Связи
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True)
    payout_id = Column(String, ForeignKey("payouts.id"), nullable=True)
    order_id = Column(String, nullable=True)
    user_id = Column(String, nullable=False, index=True)
    recipient_id = Column(String, nullable=True)  # Получатель (для переводов)

    # Тип и статус
    transaction_type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)

    # Финансовая информация
    amount = Column(Float, nullable=False)              # Сумма транзакции
    currency = Column(String, nullable=False, default="RUB")
    fee = Column(Float, default=0)                      # Комиссия
    net_amount = Column(Float, nullable=False)          # Чистая сумма

    # Баланс до и после транзакции
    balance_before = Column(Float, nullable=False)      # Баланс до транзакции
    balance_after = Column(Float, nullable=False)       # Баланс после транзакции

    # Описание и метаданные
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime, nullable=True)

    # Системная информация
    is_test = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String, nullable=True)

    # Аудит
    created_by = Column(String, nullable=True)          # Кто создал транзакцию
    approved_by = Column(String, nullable=True)         # Кто одобрил (для крупных сумм)
    failure_reason = Column(Text, nullable=True)        # Причина неудачи

    def __repr__(self):
        return f"<Transaction(id={self.id}, user={self.user_id}, type={self.transaction_type.value}, amount={self.amount}, status={self.status.value})>"

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли транзакция обработки"""
        return self.status == TransactionStatus.PENDING

    @property
    def is_processing(self) -> bool:
        """Проверка, обрабатывается ли транзакция"""
        return self.status == TransactionStatus.PROCESSING

    @property
    def is_completed(self) -> bool:
        """Проверка, завершена ли транзакция"""
        return self.status == TransactionStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка"""
        return self.status == TransactionStatus.FAILED

    @property
    def balance_change(self) -> float:
        """Изменение баланса"""
        return self.balance_after - self.balance_before

    @property
    def is_debit(self) -> bool:
        """Проверка, является ли дебетовой транзакцией (уменьшение баланса)"""
        return self.balance_change < 0

    @property
    def is_credit(self) -> bool:
        """Проверка, является ли кредитовой транзакцией (увеличение баланса)"""
        return self.balance_change > 0

    def mark_as_processing(self):
        """Отметить как обрабатываемую"""
        self.status = TransactionStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_as_completed(self):
        """Отметить как завершенную"""
        self.status = TransactionStatus.COMPLETED
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, reason: Optional[str] = None):
        """Отметить как неудачную"""
        self.status = TransactionStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.utcnow()

    def mark_as_cancelled(self, reason: Optional[str] = None):
        """Отметить как отмененную"""
        self.status = TransactionStatus.CANCELLED
        if reason:
            self.failure_reason = reason
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "payout_id": self.payout_id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "recipient_id": self.recipient_id,
            "transaction_type": self.transaction_type.value,
            "status": self.status.value,
            "amount": self.amount,
            "currency": self.currency,
            "fee": self.fee,
            "net_amount": self.net_amount,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "is_test": self.is_test
        }
