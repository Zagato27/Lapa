"""
Pydantic схемы для метрик аналитики
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class MetricType(str, enum.Enum):
    """Типы метрик"""
    COUNT = "count"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    RATE = "rate"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    DURATION = "duration"
    SIZE = "size"


class MetricCategory(str, enum.Enum):
    """Категории метрик"""
    USER_ENGAGEMENT = "user_engagement"
    BUSINESS_PERFORMANCE = "business_performance"
    SYSTEM_PERFORMANCE = "system_performance"
    FINANCIAL = "financial"
    QUALITY = "quality"
    SECURITY = "security"
    OPERATIONAL = "operational"


class MetricGranularity(str, enum.Enum):
    """Гранулярность метрик"""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class MetricCreate(BaseModel):
    """Создание метрики"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    metric_type: MetricType
    category: MetricCategory
    granularity: MetricGranularity
    aggregation_function: str = "sum"
    value: float
    dimensions: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('Metric name too long')
        return v


class MetricResponse(BaseModel):
    """Ответ с данными метрики"""
    id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    metric_type: MetricType
    category: MetricCategory
    granularity: MetricGranularity
    aggregation_function: str
    value: float
    previous_value: Optional[float]
    change_percentage: Optional[float]
    dimensions: Optional[Dict[str, Any]]
    tags: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    data_quality_score: Optional[float]
    confidence_interval: Optional[Dict[str, float]]
    sample_size: Optional[int]
    is_calculated: bool
    is_validated: bool
    validation_errors: Optional[List[Dict[str, Any]]]
    calculated_by: Optional[str]
    calculation_method: Optional[str]
    created_at: datetime
    updated_at: datetime


class MetricUpdate(BaseModel):
    """Обновление метрики"""
    value: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class MetricSearchRequest(BaseModel):
    """Запрос на поиск метрик"""
    name: Optional[str] = None
    metric_type: Optional[MetricType] = None
    category: Optional[MetricCategory] = None
    granularity: Optional[MetricGranularity] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    dimensions: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    limit: int = 100
    offset: int = 0


class MetricCalculationRequest(BaseModel):
    """Запрос на расчет метрики"""
    name: str
    metric_type: MetricType
    category: MetricCategory
    granularity: MetricGranularity
    aggregation_function: str = "sum"
    date_from: datetime
    date_to: datetime
    filters: Optional[Dict[str, Any]] = None
    dimensions: Optional[List[str]] = None


class MetricTrendRequest(BaseModel):
    """Запрос на анализ тренда метрики"""
    metric_name: str
    date_from: datetime
    date_to: datetime
    interval: str = "day"
    filters: Optional[Dict[str, Any]] = None


class MetricComparisonRequest(BaseModel):
    """Запрос на сравнение метрик"""
    metric_names: List[str]
    date_from: datetime
    date_to: datetime
    interval: str = "day"
    filters: Optional[Dict[str, Any]] = None


class MetricForecastRequest(BaseModel):
    """Запрос на прогноз метрики"""
    metric_name: str
    forecast_periods: int = 30
    forecast_method: str = "linear"  # linear, exponential, arima
    confidence_level: float = 0.95
    date_from: datetime
    date_to: datetime


class MetricAlertCreate(BaseModel):
    """Создание алерта для метрики"""
    metric_name: str
    condition: str  # above, below, equals, change_percent
    threshold: float
    alert_message: str
    severity: str = "medium"  # low, medium, high, critical
    cooldown_minutes: int = 60
    enabled: bool = True


class MetricBatchCreate(BaseModel):
    """Создание пакета метрик"""
    metrics: List[MetricCreate]

    @field_validator('metrics')
    def validate_metrics(cls, v):
        if not v:
            raise ValueError('At least one metric required')
        if len(v) > 1000:
            raise ValueError('Too many metrics in batch')
        return v


class MetricStatisticsResponse(BaseModel):
    """Ответ со статистикой метрик"""
    total_metrics: int
    metrics_today: int
    metrics_this_week: int
    metrics_this_month: int
    metrics_by_type: Dict[str, int]
    metrics_by_category: Dict[str, int]
    metrics_by_granularity: Dict[str, int]
    average_data_quality: float
    validation_errors_count: int
    period_start: datetime
    period_end: datetime


class MetricDashboardData(BaseModel):
    """Данные метрики для дашборда"""
    metric_name: str
    display_name: str
    value: float
    previous_value: Optional[float]
    change_percentage: Optional[float]
    trend: str  # up, down, stable
    data_points: List[Dict[str, Any]]
    last_updated: datetime


class MetricExportRequest(BaseModel):
    """Запрос на экспорт метрик"""
    metric_names: List[str]
    date_from: datetime
    date_to: datetime
    format: str = "csv"  # csv, json, excel
    include_metadata: bool = False


class MetricAggregationRequest(BaseModel):
    """Запрос на агрегацию метрик"""
    metrics: List[str]
    group_by: List[str]
    aggregation_functions: List[str]
    date_from: datetime
    date_to: datetime
    filters: Optional[Dict[str, Any]] = None


class MetricCorrelationRequest(BaseModel):
    """Запрос на анализ корреляции метрик"""
    metric_names: List[str]
    date_from: datetime
    date_to: datetime
    correlation_method: str = "pearson"  # pearson, spearman, kendall
    min_correlation: float = 0.1
