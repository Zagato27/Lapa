"""
Pydantic-схемы (v2) для заказов.

Используются во входных/выходных данных эндпоинтов `app.api.v1.orders`,
а также как контракт между слоем сервисов и API.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class OrderStatus(str, enum.Enum):
    """Статусы заказа"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_WALKER = "no_walker"


class OrderType(str, enum.Enum):
    """Типы заказов"""
    SINGLE_WALK = "single_walk"
    REGULAR_WALK = "regular_walk"
    PET_SITTING = "pet_sitting"
    PET_BOARDING = "pet_boarding"


class OrderCreate(BaseModel):
    """Создание заказа"""
    pet_id: str
    order_type: OrderType = OrderType.SINGLE_WALK
    scheduled_at: datetime
    duration_minutes: int
    latitude: float
    longitude: float
    address: Optional[str] = None
    special_instructions: Optional[str] = None
    preferred_walker_id: Optional[str] = None  # Предпочитаемый выгульщик

    @field_validator('duration_minutes')
    def validate_duration(cls, v: int) -> int:
        if v < 30:
            raise ValueError('Duration must be at least 30 minutes')
        if v > 180:
            raise ValueError('Duration cannot exceed 180 minutes')
        return v

    @field_validator('scheduled_at')
    def validate_scheduled_time(cls, v: datetime) -> datetime:
        now = datetime.utcnow()
        if v <= now:
            raise ValueError('Scheduled time must be in the future')
        # Максимум 30 дней вперед
        max_date = now.replace(hour=23, minute=59, second=59)
        from datetime import timedelta
        if v > max_date + timedelta(days=30):
            raise ValueError('Cannot schedule more than 30 days in advance')
        return v


class OrderUpdate(BaseModel):
    """Обновление заказа"""
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    special_instructions: Optional[str] = None
    walker_notes: Optional[str] = None

    @field_validator('duration_minutes')
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 30:
                raise ValueError('Duration must be at least 30 minutes')
            if v > 180:
                raise ValueError('Duration cannot exceed 180 minutes')
        return v


class OrderProfile(BaseModel):
    """Профиль заказа"""
    id: str
    client_id: str
    walker_id: Optional[str]
    pet_id: str
    order_type: OrderType
    status: OrderStatus
    scheduled_at: datetime
    duration_minutes: int
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    latitude: float
    longitude: float
    address: Optional[str]
    walker_hourly_rate: float
    total_amount: float
    platform_commission: float
    walker_earnings: float
    special_instructions: Optional[str]
    walker_notes: Optional[str]
    client_rating: Optional[float]
    walker_rating: Optional[float]
    client_review: Optional[str]
    walker_review: Optional[str]
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    cancelled_by: Optional[str]

    # Вычисляемые поля
    duration_hours: Optional[float] = None
    actual_duration_minutes: Optional[int] = None
    can_be_cancelled_by_client: Optional[bool] = None
    can_be_cancelled_by_walker: Optional[bool] = None


class OrderResponse(BaseModel):
    """Ответ с данными заказа"""
    order: OrderProfile


class OrderReviewCreate(BaseModel):
    """Создание отзыва о заказе"""
    rating: float
    title: Optional[str] = None
    comment: Optional[str] = None
    punctuality_rating: Optional[float] = None
    communication_rating: Optional[float] = None
    pet_care_rating: Optional[float] = None
    overall_experience: Optional[float] = None
    is_anonymous: bool = False

    @field_validator('rating')
    def validate_rating(cls, v: float) -> float:
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

    @field_validator('punctuality_rating', 'communication_rating', 'pet_care_rating', 'overall_experience')
    def validate_optional_rating(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


class OrderReviewResponse(BaseModel):
    """Ответ с отзывом о заказе"""
    id: str
    order_id: str
    reviewer_id: str
    reviewer_type: str
    reviewee_id: str
    reviewee_type: str
    rating: float
    title: Optional[str]
    comment: Optional[str]
    punctuality_rating: Optional[float]
    communication_rating: Optional[float]
    pet_care_rating: Optional[float]
    overall_experience: Optional[float]
    is_public: bool
    is_anonymous: bool
    is_moderated: bool
    moderated_by: Optional[str]
    moderated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Вычисляемые поля
    is_positive: Optional[bool] = None
    is_negative: Optional[bool] = None
    rating_category: Optional[str] = None


class OrdersListResponse(BaseModel):
    """Ответ со списком заказов"""
    orders: List[OrderProfile]
    total: int
    page: int
    limit: int
    pages: int


class OrderCancellationRequest(BaseModel):
    """Запрос на отмену заказа"""
    reason: Optional[str] = None


class OrderConfirmationRequest(BaseModel):
    """Запрос на подтверждение заказа"""
    notes: Optional[str] = None


class NearbyWalker(BaseModel):
    """Информация о выгульщике для заказа"""
    id: str
    first_name: str
    last_name: str
    avatar_url: Optional[str]
    rating: float
    total_orders: int
    completed_orders: int
    latitude: Optional[float]
    longitude: Optional[float]
    distance: float  # в метрах
    hourly_rate: Optional[float]
    services_offered: Optional[List[str]]
    bio: Optional[str]
    estimated_arrival_minutes: int


class OrderEstimateResponse(BaseModel):
    """Ответ с расчетом стоимости заказа"""
    estimated_cost: float
    platform_commission: float
    walker_earnings: float
    available_walkers: List[NearbyWalker]
    estimated_duration: int
