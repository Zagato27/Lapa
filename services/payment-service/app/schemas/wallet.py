"""
Pydantic-схемы (v2) для кошельков.

Используются в эндпоинтах `app.api.v1.wallets` и сервисе `WalletService`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator


class WalletResponse(BaseModel):
    """Ответ с данными кошелька"""
    id: str
    user_id: str
    balance: float
    currency: str
    bonus_balance: float
    referral_balance: float
    available_balance: float
    is_active: bool
    is_frozen: bool
    frozen_reason: Optional[str]
    min_balance: Optional[float]
    max_balance: Optional[float]
    daily_limit: Optional[float]
    monthly_limit: Optional[float]
    total_deposits: float
    total_withdrawals: float
    total_earnings: float
    auto_topup_enabled: bool
    auto_topup_amount: Optional[float]
    auto_topup_threshold: Optional[float]
    two_factor_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_operation_at: Optional[datetime]

    # Вычисляемые поля
    can_spend: Optional[bool] = None
    is_overdrawn: Optional[bool] = None
    is_at_limit: Optional[bool] = None


class WalletOperationRequest(BaseModel):
    """Запрос на операцию с кошельком"""
    amount: float
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('amount')
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class WalletDepositRequest(WalletOperationRequest):
    """Запрос на пополнение кошелька"""
    payment_method_id: Optional[str] = None


class WalletWithdrawRequest(WalletOperationRequest):
    """Запрос на снятие с кошелька"""
    pass


class WalletTransferRequest(BaseModel):
    """Запрос на перевод между кошельками"""
    recipient_id: str
    amount: float
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('amount')
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Transfer amount must be positive')
        return v


class WalletSettingsUpdate(BaseModel):
    """Обновление настроек кошелька"""
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    auto_topup_enabled: Optional[bool] = None
    auto_topup_amount: Optional[float] = None
    auto_topup_threshold: Optional[float] = None
    two_factor_enabled: Optional[bool] = None


class WalletTransaction(BaseModel):
    """Транзакция кошелька"""
    id: str
    transaction_type: str
    amount: float
    balance_before: float
    balance_after: float
    description: Optional[str]
    created_at: datetime


class WalletTransactionsResponse(BaseModel):
    """Ответ со списком транзакций кошелька"""
    transactions: List[WalletTransaction]
    total: int
    page: int
    limit: int
    pages: int


class WalletStatementRequest(BaseModel):
    """Запрос на выписку по кошельку"""
    start_date: datetime
    end_date: datetime
    transaction_types: Optional[List[str]] = None


class WalletStatementResponse(BaseModel):
    """Ответ с выпиской по кошельку"""
    wallet_id: str
    user_id: str
    period_start: datetime
    period_end: datetime
    opening_balance: float
    closing_balance: float
    total_credits: float
    total_debits: float
    transactions: List[WalletTransaction]
