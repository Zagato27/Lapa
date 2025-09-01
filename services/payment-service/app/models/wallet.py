"""
Модель кошельков пользователей.

Используется `WalletService` и эндпоинтами `app.api.v1.wallets`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class Wallet(Base):
    """Модель кошелька пользователя"""
    __tablename__ = "wallets"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True, unique=True)

    # Баланс
    balance = Column(Float, nullable=False, default=0)
    currency = Column(String, nullable=False, default="RUB")

    # Ограничения
    min_balance = Column(Float, nullable=True, default=0)      # Минимальный баланс
    max_balance = Column(Float, nullable=True)                # Максимальный баланс
    daily_limit = Column(Float, nullable=True)                # Дневной лимит операций
    monthly_limit = Column(Float, nullable=True)              # Месячный лимит операций

    # Статус
    is_active = Column(Boolean, default=True)
    is_frozen = Column(Boolean, default=False)                 # Заморожен ли кошелек
    frozen_reason = Column(Text, nullable=True)                # Причина заморозки

    # Статистика
    total_deposits = Column(Float, default=0)                  # Общая сумма пополнений
    total_withdrawals = Column(Float, default=0)               # Общая сумма снятий
    total_payments = Column(Float, default=0)                  # Общая сумма платежей
    total_earnings = Column(Float, default=0)                  # Общая сумма заработков

    # Бонусы и промокоды
    bonus_balance = Column(Float, default=0)                   # Бонусный баланс
    referral_balance = Column(Float, default=0)                # Реферальный баланс

    # Настройки
    auto_topup_enabled = Column(Boolean, default=False)        # Автопополнение
    auto_topup_amount = Column(Float, nullable=True)           # Сумма автопополнения
    auto_topup_threshold = Column(Float, nullable=True)        # Порог для автопополнения

    # Безопасность
    pin_code_hash = Column(String, nullable=True)              # PIN-код для операций
    two_factor_enabled = Column(Boolean, default=False)        # Двухфакторная аутентификация

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_operation_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Wallet(id={self.id}, user={self.user_id}, balance={self.balance})>"

    @property
    def available_balance(self) -> float:
        """Доступный баланс (основной + бонусный)"""
        return self.balance + self.bonus_balance

    @property
    def can_spend(self) -> bool:
        """Проверка возможности совершения расходов"""
        return (
            self.is_active and
            not self.is_frozen and
            self.balance >= 0
        )

    @property
    def is_overdrawn(self) -> bool:
        """Проверка перерасхода"""
        return self.balance < 0

    @property
    def is_at_limit(self) -> bool:
        """Проверка достижения лимита баланса"""
        if self.max_balance is not None:
            return self.balance >= self.max_balance
        return False

    def can_afford(self, amount: float) -> bool:
        """Проверка возможности оплаты указанной суммы"""
        return self.available_balance >= amount

    def deposit(self, amount: float, description: Optional[str] = None) -> bool:
        """Пополнение баланса"""
        if amount <= 0:
            return False

        if self.max_balance is not None and self.balance + amount > self.max_balance:
            return False

        self.balance += amount
        self.total_deposits += amount
        self.last_operation_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        return True

    def withdraw(self, amount: float, description: Optional[str] = None) -> bool:
        """Снятие средств"""
        if amount <= 0 or not self.can_spend():
            return False

        if not self.can_afford(amount):
            return False

        # Сначала снимаем с основного баланса
        if self.balance >= amount:
            self.balance -= amount
        else:
            # Снимаем с бонусного баланса
            remaining = amount - self.balance
            self.balance = 0
            self.bonus_balance -= remaining

        self.total_withdrawals += amount
        self.last_operation_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        return True

    def hold_amount(self, amount: float) -> bool:
        """Холдирование средств (резервирование)"""
        if amount <= 0 or not self.can_spend():
            return False

        if not self.can_afford(amount):
            return False

        # Создаем холдирование (можно реализовать через отдельную таблицу holds)
        # Пока просто уменьшаем доступный баланс
        return self.withdraw(amount, "Amount held for payment")

    def release_hold(self, amount: float) -> bool:
        """Снятие холдирования средств"""
        if amount <= 0:
            return False

        return self.deposit(amount, "Hold released")

    def add_earnings(self, amount: float, description: Optional[str] = None) -> bool:
        """Добавление заработка"""
        if amount <= 0:
            return False

        self.balance += amount
        self.total_earnings += amount
        self.last_operation_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        return True

    def freeze(self, reason: Optional[str] = None):
        """Заморозка кошелька"""
        self.is_frozen = True
        if reason:
            self.frozen_reason = reason
        self.updated_at = datetime.utcnow()

    def unfreeze(self):
        """Разморозка кошелька"""
        self.is_frozen = False
        self.frozen_reason = None
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": self.balance,
            "currency": self.currency,
            "bonus_balance": self.bonus_balance,
            "available_balance": self.available_balance,
            "is_active": self.is_active,
            "is_frozen": self.is_frozen,
            "frozen_reason": self.frozen_reason,
            "total_deposits": self.total_deposits,
            "total_withdrawals": self.total_withdrawals,
            "total_earnings": self.total_earnings,
            "created_at": self.created_at.isoformat(),
            "last_operation_at": self.last_operation_at.isoformat() if self.last_operation_at else None
        }
