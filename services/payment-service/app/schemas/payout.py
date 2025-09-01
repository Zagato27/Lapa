"""
Pydantic-схемы (v2) для выплат.

Используются в эндпоинтах `app.api.v1.payouts` и сервисах выплат.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class PayoutStatus(str, enum.Enum):
    """Статусы выплат"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class PayoutMethod(str, enum.Enum):
    """Методы выплат"""
    BANK_CARD = "bank_card"
    BANK_ACCOUNT = "bank_account"
    ELECTRONIC_WALLET = "electronic_wallet"
    CASH = "cash"
    SBP = "sbp"


class PayoutCreate(BaseModel):
    """Создание выплаты"""
    amount: float
    currency: str = "RUB"
    method: PayoutMethod
    recipient_name: str
    recipient_data: Dict[str, Any]
    period_start: datetime
    period_end: datetime
    description: Optional[str] = None
    priority: str = "normal"

    @field_validator('amount')
    def validate_amount(cls, v: float) -> float:
        from app.config import settings
        if v < settings.min_payout_amount:
            raise ValueError(f'Amount must be at least {settings.min_payout_amount}')
        return v

    @field_validator('currency')
    def validate_currency(cls, v: str) -> str:
        from app.config import settings
        if v not in settings.supported_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(settings.supported_currencies)}')
        return v

    @field_validator('recipient_data')
    def validate_recipient_data(cls, v: Dict[str, Any], values):
        """Валидация данных получателя в зависимости от метода"""
        method = values.get('method')
        if not method:
            return v

        required_fields = {
            PayoutMethod.BANK_CARD: ['card_number', 'expiry_date', 'cvv'],
            PayoutMethod.BANK_ACCOUNT: ['account_number', 'bank_name', 'bic'],
            PayoutMethod.ELECTRONIC_WALLET: ['wallet_id', 'wallet_type'],
            PayoutMethod.SBP: ['phone_number'],
            PayoutMethod.CASH: []  # Для наличных дополнительных данных не требуется
        }

        missing_fields = [field for field in required_fields[method] if field not in v]

        if missing_fields:
            raise ValueError(f'Missing required fields for {method.value}: {", ".join(missing_fields)}')

        return v


class PayoutUpdate(BaseModel):
    """Обновление выплаты"""
    description: Optional[str] = None
    priority: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class PayoutResponse(BaseModel):
    """Ответ с данными выплаты"""
    id: str
    user_id: str
    amount: float
    currency: str
    platform_fee: float
    net_amount: float
    status: PayoutStatus
    method: PayoutMethod
    period_start: datetime
    period_end: datetime
    recipient_name: str
    order_ids: Optional[List[str]]
    provider_payout_id: Optional[str]
    processed_by: Optional[str]
    processed_at: Optional[datetime]
    failure_reason: Optional[str]
    is_test: bool
    priority: str
    created_at: datetime
    updated_at: datetime
    scheduled_at: Optional[datetime]

    # Вычисляемые поля
    is_pending: Optional[bool] = None
    is_processing: Optional[bool] = None
    is_completed: Optional[bool] = None
    is_failed: Optional[bool] = None
    period_days: Optional[int] = None


class PayoutsListResponse(BaseModel):
    """Ответ со списком выплат"""
    payouts: List[PayoutResponse]
    total: int
    page: int
    limit: int
    pages: int


class PayoutProcessRequest(BaseModel):
    """Запрос на обработку выплаты"""
    payout_ids: List[str]


class PayoutCancelRequest(BaseModel):
    """Запрос на отмену выплаты"""
    reason: Optional[str] = None


class PayoutRetryRequest(BaseModel):
    """Запрос на повтор выплаты"""
    recipient_data: Optional[Dict[str, Any]] = None  # Новые данные получателя


class PayoutScheduleRequest(BaseModel):
    """Запрос на создание расписания выплат"""
    user_id: str
    schedule_type: str  # 'weekly', 'monthly', 'quarterly'
    payout_method: PayoutMethod
    recipient_data: Dict[str, Any]
    is_active: bool = True


class PayoutScheduleResponse(BaseModel):
    """Ответ с расписанием выплат"""
    id: str
    user_id: str
    schedule_type: str
    payout_method: PayoutMethod
    recipient_data: Dict[str, Any]
    is_active: bool
    next_payout_date: Optional[datetime]
    created_at: datetime


class PayoutStatisticsResponse(BaseModel):
    """Ответ со статистикой выплат"""
    total_payouts: int
    total_amount: float
    successful_payouts: int
    failed_payouts: int
    average_payout_amount: float
    payouts_by_status: Dict[str, int]
    payouts_by_method: Dict[str, int]
    period_start: datetime
    period_end: datetime
