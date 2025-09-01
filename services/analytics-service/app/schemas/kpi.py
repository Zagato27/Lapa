"""
Pydantic схемы для KPI
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class KPICategory(str, enum.Enum):
    """Категории KPI"""
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    OPERATIONAL = "operational"
    MARKETING = "marketing"
    PRODUCT = "product"
    EMPLOYEE = "employee"


class KPIType(str, enum.Enum):
    """Типы KPI"""
    REVENUE = "revenue"
    GROWTH = "growth"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    SATISFACTION = "satisfaction"
    RETENTION = "retention"
    CONVERSION = "conversion"
    UTILIZATION = "utilization"


class KPITrend(str, enum.Enum):
    """Тренды KPI"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class KPIStatus(str, enum.Enum):
    """Статусы KPI"""
    ON_TRACK = "on_track"
    BEHIND = "behind"
    AHEAD = "ahead"
    CRITICAL = "critical"


class KPICreate(BaseModel):
    """Создание KPI"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    kpi_type: KPIType
    category: KPICategory
    current_value: float = 0
    target_value: Optional[float] = None
    baseline_value: Optional[float] = None
    calculation_formula: Optional[str] = None
    calculation_parameters: Optional[Dict[str, Any]] = None
    related_metrics: Optional[List[str]] = None
    owner_id: Optional[str] = None
    department: Optional[str] = None
    team: Optional[str] = None
    priority: str = "medium"
    weight: float = 1.0
    alert_enabled: bool = False
    alert_threshold: Optional[float] = None
    alert_condition: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('KPI name too long')
        return v

    @field_validator('weight')
    def validate_weight(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Weight must be positive')
        return v


class KPIResponse(BaseModel):
    """Ответ с данными KPI"""
    id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    kpi_type: KPIType
    category: KPICategory
    current_value: float
    target_value: Optional[float]
    baseline_value: Optional[float]
    trend: Optional[KPITrend]
    trend_strength: Optional[float]
    change_percentage: Optional[float]
    status: Optional[KPIStatus]
    progress_percentage: Optional[float]
    calculation_period: str
    last_calculated_at: Optional[datetime]
    calculation_formula: Optional[str]
    calculation_parameters: Optional[Dict[str, Any]]
    related_metrics: Optional[List[str]]
    owner_id: Optional[str]
    department: Optional[str]
    team: Optional[str]
    priority: str
    weight: float
    alert_enabled: bool
    alert_threshold: Optional[float]
    alert_condition: Optional[str]
    tags: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class KPIUpdate(BaseModel):
    """Обновление KPI"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    baseline_value: Optional[float] = None
    calculation_formula: Optional[str] = None
    calculation_parameters: Optional[Dict[str, Any]] = None
    related_metrics: Optional[List[str]] = None
    owner_id: Optional[str] = None
    department: Optional[str] = None
    team: Optional[str] = None
    priority: Optional[str] = None
    weight: Optional[float] = None
    alert_enabled: Optional[bool] = None
    alert_threshold: Optional[float] = None
    alert_condition: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class KPITargetUpdate(BaseModel):
    """Обновление цели KPI"""
    target_value: float
    baseline_value: Optional[float] = None
    reason: Optional[str] = None


class KPICalculationRequest(BaseModel):
    """Запрос на расчет KPI"""
    kpi_id: str
    force_recalculation: bool = False


class KPIBatchUpdate(BaseModel):
    """Пакетное обновление KPI"""
    kpi_updates: List[Dict[str, Any]]

    @field_validator('kpi_updates')
    def validate_updates(cls, v):
        if not v:
            raise ValueError('At least one KPI update required')
        if len(v) > 100:
            raise ValueError('Too many KPI updates in batch')
        return v


class KPIAlertCreate(BaseModel):
    """Создание алерта для KPI"""
    kpi_id: str
    condition: str  # below_target, above_target, trend_change, etc.
    threshold: Optional[float] = None
    alert_message: str
    severity: str = "medium"
    cooldown_minutes: int = 60
    enabled: bool = True


class KPIStatisticsResponse(BaseModel):
    """Ответ со статистикой KPI"""
    total_kpis: int
    kpis_on_track: int
    kpis_behind: int
    kpis_ahead: int
    kpis_critical: int
    average_progress: float
    kpis_by_category: Dict[str, int]
    kpis_by_type: Dict[str, int]
    kpis_with_alerts: int
    period_start: datetime
    period_end: datetime


class KPITrendAnalysis(BaseModel):
    """Анализ тренда KPI"""
    kpi_id: str
    trend: KPITrend
    trend_strength: float
    change_percentage: float
    data_points: List[Dict[str, Any]]
    forecast: Optional[List[Dict[str, Any]]] = None


class KPIPerformanceReport(BaseModel):
    """Отчет о производительности KPI"""
    kpi_id: str
    period_start: datetime
    period_end: datetime
    target_achievement: float
    trend_analysis: KPITrendAnalysis
    related_metrics_performance: Dict[str, Any]
    recommendations: List[str]


class KPIBenchmarkingRequest(BaseModel):
    """Запрос на бенчмаркинг KPI"""
    kpi_ids: List[str]
    benchmark_period: str = "month"  # week, month, quarter, year
    include_industry_averages: bool = False
    include_competitor_data: bool = False


class KPIPredictiveAnalysis(BaseModel):
    """Предиктивный анализ KPI"""
    kpi_id: str
    forecast_periods: int = 12
    confidence_level: float = 0.95
    forecast_data: List[Dict[str, Any]]
    influencing_factors: Dict[str, float]
    recommendations: List[str]


class KPICorrelationAnalysis(BaseModel):
    """Анализ корреляции KPI"""
    kpi_ids: List[str]
    date_from: datetime
    date_to: datetime
    correlation_matrix: Dict[str, Dict[str, float]]
    strongest_correlations: List[Dict[str, Any]]
    causal_relationships: Optional[List[Dict[str, Any]]] = None
