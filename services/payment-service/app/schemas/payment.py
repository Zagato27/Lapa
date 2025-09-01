"""
Pydantic-схемы (v2) для платежей.

Используются в эндпоинтах `app.api.v1.payments` и сервисах `PaymentService`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class PaymentStatus(str, enum.Enum):
    """Статусы платежа"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentType(str, enum.Enum):
    """Типы платежей"""
    ORDER_PAYMENT = "order_payment"
    WALLET_TOPUP = "wallet_topup"
    SUBSCRIPTION = "subscription"
    DONATION = "donation"
    FINE = "fine"
    BONUS = "bonus"


class PaymentProvider(str, enum.Enum):
    """Платежные провайдеры"""
    STRIPE = "stripe"
    YOOKASSA = "yookassa"
    TINKOFF = "tinkoff"
    SBP = "sbp"
    WALLET = "wallet"
    CASH = "cash"


class PaymentCreate(BaseModel):
    """Создание платежа"""
    order_id: Optional[str] = None
    payment_type: PaymentType = PaymentType.ORDER_PAYMENT
    amount: float
    currency: str = "RUB"
    payment_method_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    return_url: Optional[str] = None  # URL для перенаправления после оплаты
    webhook_url: Optional[str] = None  # URL для webhook уведомлений

    @field_validator('amount')
    def validate_amount(cls, v: float) -> float:
        from app.config import settings
        if v < settings.min_payment_amount:
            raise ValueError(f'Amount must be at least {settings.min_payment_amount}')
        if v > settings.max_payment_amount:
            raise ValueError(f'Amount cannot exceed {settings.max_payment_amount}')
        return v

    @field_validator('currency')
    def validate_currency(cls, v: str) -> str:
        from app.config import settings
        if v not in settings.supported_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(settings.supported_currencies)}')
        return v


class PaymentUpdate(BaseModel):
    """Обновление платежа"""
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Ответ с данными платежа"""
    id: str
    order_id: Optional[str]
    user_id: str
    payment_type: PaymentType
    status: PaymentStatus
    provider: PaymentProvider
    amount: float
    currency: str
    platform_commission: float
    provider_commission: Optional[float]
    net_amount: float
    provider_payment_id: Optional[str]
    payment_method_id: Optional[str]
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    refunded_at: Optional[datetime]
    refund_amount: Optional[float]
    refund_reason: Optional[str]
    is_test: bool

    # Вычисляемые поля
    is_pending: Optional[bool] = None
    is_processing: Optional[bool] = None
    is_completed: Optional[bool] = None
    is_failed: Optional[bool] = None
    is_refunded: Optional[bool] = None
    can_be_refunded: Optional[bool] = None
    refundable_amount: Optional[float] = None


class PaymentsListResponse(BaseModel):
    """Ответ со списком платежей"""
    payments: List[PaymentResponse]
    total: int
    page: int
    limit: int
    pages: int


class PaymentRefundRequest(BaseModel):
    """Запрос на возврат платежа"""
    amount: float
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('amount')
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Refund amount must be positive')
        return v


class PaymentEstimateRequest(BaseModel):
    """Запрос на расчет стоимости платежа"""
    amount: float
    currency: str = "RUB"
    payment_method_id: Optional[str] = None


class PaymentEstimateResponse(BaseModel):
    """Ответ с расчетом стоимости платежа"""
    amount: float
    currency: str
    platform_commission: float
    provider_commission: Optional[float]
    total_amount: float
    net_amount: float
    payment_method_fee: Optional[float]
    estimated_processing_time: Optional[str]  # "instant", "1-3 minutes", etc.


class PaymentWebhookData(BaseModel):
    """Данные webhook от платежного провайдера"""
    provider: str
    provider_payment_id: str
    status: str
    amount: float
    currency: str
    metadata: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None


class PaymentConfirmationRequest(BaseModel):
    """Запрос на подтверждение платежа"""
    payment_id: str
    confirmation_code: Optional[str] = None  # Для 3DS или других методов подтверждения


class PaymentCancelRequest(BaseModel):
    """Запрос на отмену платежа"""
    reason: Optional[str] = None


class PaymentRetryRequest(BaseModel):
    """Запрос на повтор платежа"""
    payment_method_id: Optional[str] = None  # Новый способ оплаты


class PaymentStatisticsResponse(BaseModel):
    """Ответ со статистикой платежей"""
    total_payments: int
    total_amount: float
    successful_payments: int
    failed_payments: int
    refunded_amount: float
    average_payment_amount: float
    payments_by_status: Dict[str, int]
    payments_by_provider: Dict[str, int]
    payments_by_type: Dict[str, int]
    period_start: datetime
    period_end: datetime
