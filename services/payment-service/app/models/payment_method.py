"""
Модель способов оплаты.

Используется `PaymentMethodService` и эндпоинтами `app.api.v1.payment_methods`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

from .base import Base


class PaymentMethodType(str, enum.Enum):
    """Типы способов оплаты"""
    BANK_CARD = "bank_card"              # Банковская карта
    ELECTRONIC_WALLET = "electronic_wallet"  # Электронный кошелек
    BANK_ACCOUNT = "bank_account"        # Банковский счет
    SBP = "sbp"                         # Система быстрых платежей
    CRYPTO = "crypto"                   # Криптовалюта


class PaymentMethod(Base):
    """Модель способа оплаты"""
    __tablename__ = "payment_methods"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Тип и провайдер
    type = Column(Enum(PaymentMethodType), nullable=False)
    provider = Column(String, nullable=False)  # stripe, yookassa, tinkoff, etc.

    # Название и описание
    name = Column(String, nullable=True)       # Название способа оплаты
    title = Column(String, nullable=True)      # Отображаемое название

    # Данные способа оплаты (зашифрованные)
    encrypted_data = Column(Text, nullable=True)   # Зашифрованные данные карты/кошелька
    provider_data = Column(JSON, nullable=True)    # Данные от провайдера

    # Маскированные данные для отображения
    masked_number = Column(String, nullable=True)  # **** **** **** 1234
    masked_email = Column(String, nullable=True)   # user@***.com

    # Статус
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)    # По умолчанию
    is_verified = Column(Boolean, default=False)   # Проверен

    # Ограничения
    daily_limit = Column(Integer, nullable=True)   # Дневной лимит в рублях
    monthly_limit = Column(Integer, nullable=True) # Месячный лимит в рублях

    # Статистика использования
    total_payments = Column(Integer, default=0)     # Общее количество платежей
    total_amount = Column(Integer, default=0)       # Общая сумма платежей
    last_used_at = Column(DateTime, nullable=True)  # Последнее использование

    # Безопасность
    verification_attempts = Column(Integer, default=0)
    last_verification_at = Column(DateTime, nullable=True)
    fraud_score = Column(Integer, default=0)        # Оценка мошенничества (0-100)

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)    # Срок действия (для карт)

    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, user={self.user_id}, type={self.type.value}, title={self.title})>"

    @property
    def is_expired(self) -> bool:
        """Проверка истечения срока действия"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_bank_card(self) -> bool:
        """Проверка, является ли банковской картой"""
        return self.type == PaymentMethodType.BANK_CARD

    @property
    def is_wallet(self) -> bool:
        """Проверка, является ли электронным кошельком"""
        return self.type == PaymentMethodType.ELECTRONIC_WALLET

    @property
    def usage_rate(self) -> float:
        """Частота использования (платежей в день)"""
        if not self.created_at or not self.last_used_at:
            return 0

        from datetime import timedelta
        days_active = (self.last_used_at - self.created_at).days
        if days_active <= 0:
            return 0

        return self.total_payments / days_active

    def record_payment(self, amount: int):
        """Запись платежа"""
        self.total_payments += 1
        self.total_amount += amount
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_default(self):
        """Отметить как способ оплаты по умолчанию"""
        self.is_default = True
        self.updated_at = datetime.utcnow()

    def mark_as_verified(self):
        """Отметить как проверенный"""
        self.is_verified = True
        self.last_verification_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_verification_attempts(self):
        """Увеличить счетчик попыток верификации"""
        self.verification_attempts += 1
        self.updated_at = datetime.utcnow()

    def reset_verification_attempts(self):
        """Сбросить счетчик попыток верификации"""
        self.verification_attempts = 0
        self.updated_at = datetime.utcnow()

    def update_fraud_score(self, score: int):
        """Обновить оценку мошенничества"""
        self.fraud_score = max(0, min(100, score))  # Ограничение 0-100
        self.updated_at = datetime.utcnow()

    def to_public_dict(self) -> dict:
        """Преобразование в публичный словарь (без чувствительных данных)"""
        return {
            "id": self.id,
            "type": self.type.value,
            "provider": self.provider,
            "name": self.name,
            "title": self.title,
            "masked_number": self.masked_number,
            "masked_email": self.masked_email,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "is_verified": self.is_verified,
            "total_payments": self.total_payments,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat()
        }

    def to_dict(self) -> dict:
        """Преобразование в полный словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "provider": self.provider,
            "name": self.name,
            "title": self.title,
            "masked_number": self.masked_number,
            "masked_email": self.masked_email,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "is_verified": self.is_verified,
            "daily_limit": self.daily_limit,
            "monthly_limit": self.monthly_limit,
            "total_payments": self.total_payments,
            "total_amount": self.total_amount,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "verification_attempts": self.verification_attempts,
            "fraud_score": self.fraud_score,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
