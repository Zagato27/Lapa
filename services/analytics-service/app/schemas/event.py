"""
Pydantic схемы для событий аналитики
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class EventType(str, enum.Enum):
    """Типы событий"""
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    BUSINESS_EVENT = "business_event"
    ERROR = "error"
    PERFORMANCE = "performance"
    SECURITY = "security"


class EventCategory(str, enum.Enum):
    """Категории событий"""
    AUTHENTICATION = "authentication"
    REGISTRATION = "registration"
    PROFILE = "profile"
    PET_MANAGEMENT = "pet_management"
    ORDER = "order"
    PAYMENT = "payment"
    LOCATION = "location"
    CHAT = "chat"
    MEDIA = "media"
    NOTIFICATION = "notification"
    NAVIGATION = "navigation"
    SEARCH = "search"
    SOCIAL = "social"


class EventPriority(str, enum.Enum):
    """Приоритеты событий"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventCreate(BaseModel):
    """Создание события аналитики"""
    event_type: EventType
    category: EventCategory
    priority: EventPriority = EventPriority.NORMAL
    service_name: str
    event_name: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None
    order_id: Optional[str] = None
    pet_id: Optional[str] = None
    chat_id: Optional[str] = None
    payment_id: Optional[str] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    revenue_impact: Optional[float] = None
    user_engagement_score: Optional[float] = None

    @field_validator('service_name')
    def validate_service_name(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError('Service name too long')
        return v

    @field_validator('event_name')
    def validate_event_name(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('Event name too long')
        return v


class EventResponse(BaseModel):
    """Ответ с данными события"""
    id: str
    event_type: EventType
    category: EventCategory
    priority: EventPriority
    service_name: str
    user_id: Optional[str]
    session_id: Optional[str]
    device_id: Optional[str]
    event_name: str
    description: Optional[str]
    properties: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    user_agent: Optional[str]
    ip_address: Optional[str]
    location_data: Optional[Dict[str, Any]]
    device_info: Optional[Dict[str, Any]]
    event_timestamp: datetime
    processed_at: Optional[datetime]
    created_at: datetime
    order_id: Optional[str]
    pet_id: Optional[str]
    chat_id: Optional[str]
    payment_id: Optional[str]
    duration_ms: Optional[float]
    memory_usage_mb: Optional[float]
    cpu_usage_percent: Optional[float]
    is_processed: bool
    processing_errors: Optional[List[Dict[str, Any]]]
    is_suspicious: bool
    anomaly_score: Optional[float]
    revenue_impact: Optional[float]
    user_engagement_score: Optional[float]


class EventSearchRequest(BaseModel):
    """Запрос на поиск событий"""
    event_type: Optional[EventType] = None
    category: Optional[EventCategory] = None
    service_name: Optional[str] = None
    user_id: Optional[str] = None
    event_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_suspicious: Optional[bool] = None
    min_anomaly_score: Optional[float] = None
    limit: int = 100
    offset: int = 0


class EventBatchCreate(BaseModel):
    """Создание пакета событий"""
    events: List[EventCreate]

    @field_validator('events')
    def validate_events(cls, v):
        if not v:
            raise ValueError('At least one event required')
        if len(v) > 1000:
            raise ValueError('Too many events in batch')
        return v


class EventStatisticsResponse(BaseModel):
    """Ответ со статистикой событий"""
    total_events: int
    events_today: int
    events_this_week: int
    events_this_month: int
    events_by_type: Dict[str, int]
    events_by_category: Dict[str, int]
    events_by_service: Dict[str, int]
    suspicious_events: int
    processing_errors: int
    average_processing_time: float
    period_start: datetime
    period_end: datetime


class EventAggregationRequest(BaseModel):
    """Запрос на агрегацию событий"""
    group_by: List[str]  # поля для группировки
    metrics: List[str]   # метрики для расчета
    filters: Optional[Dict[str, Any]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    interval: Optional[str] = None  # hour, day, week, month


class EventTrendAnalysisRequest(BaseModel):
    """Запрос на анализ трендов"""
    event_name: str
    metric: str = "count"  # count, sum, avg, etc.
    date_from: datetime
    date_to: datetime
    interval: str = "day"
    filters: Optional[Dict[str, Any]] = None


class EventAnomalyDetectionRequest(BaseModel):
    """Запрос на обнаружение аномалий"""
    service_name: Optional[str] = None
    event_name: Optional[str] = None
    threshold: float = 0.95
    date_from: datetime
    date_to: datetime
    min_sample_size: int = 100


class EventFunnelAnalysisRequest(BaseModel):
    """Запрос на анализ воронки"""
    steps: List[str]  # последовательность событий
    user_id: Optional[str] = None
    date_from: datetime
    date_to: datetime
    conversion_window_days: int = 30


class EventRetentionAnalysisRequest(BaseModel):
    """Запрос на анализ удержания"""
    cohort_period: str = "month"  # day, week, month
    retention_periods: int = 12
    date_from: datetime
    date_to: datetime
    filters: Optional[Dict[str, Any]] = None


class EventSegmentationRequest(BaseModel):
    """Запрос на сегментацию пользователей"""
    criteria: List[Dict[str, Any]]
    segment_name: str
    description: Optional[str] = None
    min_segment_size: int = 10
