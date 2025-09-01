"""
Pydantic-схемы (v2) для способов оплаты.

Используются в эндпоинтах `app.api.v1.payment_methods` и сервисе `PaymentMethodService`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class PaymentMethodType(str, enum.Enum):
    """Типы способов оплаты"""
    BANK_CARD = "bank_card"
    ELECTRONIC_WALLET = "electronic_wallet"
    BANK_ACCOUNT = "bank_account"
    SBP = "sbp"
    CRYPTO = "crypto"


class PaymentMethodCreate(BaseModel):
    """Создание способа оплаты"""
    type: PaymentMethodType
    provider: str
    card_number: Optional[str] = None
    expiry_date: Optional[str] = None
    cvv: Optional[str] = None
    cardholder_name: Optional[str] = None
    wallet_id: Optional[str] = None
    wallet_type: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bic: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    is_default: bool = False

    @field_validator('card_number')
    def validate_card_number(cls, v: str, values):
        """Валидация номера карты"""
        if values.get('type') == PaymentMethodType.BANK_CARD and not v:
            raise ValueError('Card number is required for bank card')
        if v and not v.replace(' ', '').replace('-', '').isdigit():
            raise ValueError('Card number must contain only digits')
        return v

    @field_validator('expiry_date')
    def validate_expiry_date(cls, v: str, values):
        """Валидация срока действия карты"""
        if values.get('type') == PaymentMethodType.BANK_CARD and not v:
            raise ValueError('Expiry date is required for bank card')
        if v:
            try:
                # Ожидаем формат MM/YY или MMYY
                if '/' in v:
                    month, year = v.split('/')
                else:
                    month, year = v[:2], v[2:]
                month, year = int(month), int(year)

                if year < 100:
                    year += 2000

                from datetime import datetime
                expiry = datetime(year, month, 1)
                if expiry < datetime.now():
                    raise ValueError('Card has expired')

            except (ValueError, IndexError):
                raise ValueError('Invalid expiry date format (MM/YY or MMYY)')
        return v

    @field_validator('cvv')
    def validate_cvv(cls, v: str, values):
        """Валидация CVV"""
        if values.get('type') == PaymentMethodType.BANK_CARD and not v:
            raise ValueError('CVV is required for bank card')
        if v and not (v.isdigit() and len(v) in [3, 4]):
            raise ValueError('CVV must be 3 or 4 digits')
        return v


class PaymentMethodUpdate(BaseModel):
    """Обновление способа оплаты"""
    title: Optional[str] = None
    is_default: Optional[bool] = None
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None


class PaymentMethodResponse(BaseModel):
    """Ответ с данными способа оплаты"""
    id: str
    user_id: str
    type: PaymentMethodType
    provider: str
    name: Optional[str]
    title: Optional[str]
    masked_number: Optional[str]
    masked_email: Optional[str]
    is_active: bool
    is_default: bool
    is_verified: bool
    daily_limit: Optional[int]
    monthly_limit: Optional[int]
    total_payments: int
    total_amount: int
    last_used_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]

    # Вычисляемые поля
    is_expired: Optional[bool] = None
    is_bank_card: Optional[bool] = None
    is_wallet: Optional[bool] = None
    usage_rate: Optional[float] = None


class PaymentMethodsListResponse(BaseModel):
    """Ответ со списком способов оплаты"""
    payment_methods: List[PaymentMethodResponse]
    total: int
    default_method_id: Optional[str]


class PaymentMethodVerificationRequest(BaseModel):
    """Запрос на верификацию способа оплаты"""
    verification_code: str


class PaymentMethodVerificationResponse(BaseModel):
    """Ответ на верификацию способа оплаты"""
    is_verified: bool
    message: str
    verification_attempts_remaining: int


class PaymentMethodLimitUpdate(BaseModel):
    """Обновление лимитов способа оплаты"""
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None


class PaymentMethodStatistics(BaseModel):
    """Статистика способа оплаты"""
    payment_method_id: str
    total_payments: int
    total_amount: int
    successful_payments: int
    failed_payments: int
    average_amount: float
    last_payment_date: Optional[datetime]
    fraud_score: int
