"""
Модель метрик аналитики
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Float, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class MetricType(str, enum.Enum):
    """Типы метрик"""
    COUNT = "count"                          # Счетчик
    GAUGE = "gauge"                          # Измеритель
    HISTOGRAM = "histogram"                  # Гистограмма
    SUMMARY = "summary"                      # Сводка
    RATE = "rate"                            # Скорость
    PERCENTAGE = "percentage"                # Процент
    RATIO = "ratio"                          # Соотношение
    DURATION = "duration"                    # Длительность
    SIZE = "size"                            # Размер


class MetricCategory(str, enum.Enum):
    """Категории метрик"""
    USER_ENGAGEMENT = "user_engagement"      # Вовлеченность пользователей
    BUSINESS_PERFORMANCE = "business_performance"  # Бизнес-производительность
    SYSTEM_PERFORMANCE = "system_performance"      # Производительность системы
    FINANCIAL = "financial"                  # Финансовые метрики
    QUALITY = "quality"                      # Метрики качества
    SECURITY = "security"                    # Метрики безопасности
    OPERATIONAL = "operational"              # Операционные метрики


class MetricGranularity(str, enum.Enum):
    """Гранулярность метрик"""
    SECOND = "second"                        # Секунда
    MINUTE = "minute"                        # Минута
    HOUR = "hour"                            # Час
    DAY = "day"                              # День
    WEEK = "week"                            # Неделя
    MONTH = "month"                          # Месяц
    QUARTER = "quarter"                      # Квартал
    YEAR = "year"                            # Год


class Metric(Base):
    """Модель метрики аналитики"""
    __tablename__ = "analytics_metrics"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)          # Название метрики
    display_name = Column(String, nullable=True)               # Отображаемое название
    description = Column(Text, nullable=True)                  # Описание метрики

    # Тип и категория
    metric_type = Column(Enum(MetricType), nullable=False)
    category = Column(Enum(MetricCategory), nullable=False, index=True)

    # Гранулярность и агрегация
    granularity = Column(Enum(MetricGranularity), nullable=False)
    aggregation_function = Column(String, default="sum")       # Функция агрегации

    # Значение метрики
    value = Column(Float, nullable=False)                     # Числовое значение
    previous_value = Column(Float, nullable=True)             # Предыдущее значение
    change_percentage = Column(Float, nullable=True)          # Изменение в процентах

    # Контекст метрики
    dimensions = Column(JSON, nullable=True)                  # Измерения (фильтры)
    tags = Column(JSON, nullable=True)                        # Теги для категоризации
    metadata = Column(JSON, nullable=True)                    # Дополнительные метаданные

    # Временной контекст
    timestamp = Column(DateTime, nullable=False, index=True)  # Время метрики
    period_start = Column(DateTime, nullable=True)            # Начало периода
    period_end = Column(DateTime, nullable=True)              # Конец периода

    # Качество данных
    data_quality_score = Column(Float, nullable=True)         # Оценка качества данных
    confidence_interval = Column(JSON, nullable=True)         # Доверительный интервал
    sample_size = Column(Integer, nullable=True)             # Размер выборки

    # Статус и валидация
    is_calculated = Column(Boolean, default=False)            # Вычислена ли метрика
    is_validated = Column(Boolean, default=False)             # Провалидирована ли
    validation_errors = Column(JSON, nullable=True)           # Ошибки валидации

    # Связанные объекты
    dashboard_id = Column(String, ForeignKey("analytics_dashboards.id"), nullable=True, index=True)
    report_id = Column(String, ForeignKey("analytics_reports.id"), nullable=True, index=True)
    kpi_id = Column(String, ForeignKey("analytics_kpis.id"), nullable=True, index=True)

    # Создал
    calculated_by = Column(String, nullable=True)             # Кто вычислил метрику
    calculation_method = Column(String, nullable=True)        # Метод вычисления

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)              # Время истечения

    def __repr__(self):
        return f"<Metric(id={self.id}, name={self.name}, value={self.value}, category={self.category.value})>"

    @property
    def is_expired(self) -> bool:
        """Проверка, истекла ли метрика"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def has_improved(self) -> Optional[bool]:
        """Проверка, улучшилась ли метрика"""
        if self.previous_value is None or self.change_percentage is None:
            return None
        return self.change_percentage > 0

    @property
    def change_direction(self) -> Optional[str]:
        """Направление изменения"""
        if self.change_percentage is None:
            return None
        if self.change_percentage > 0:
            return "up"
        elif self.change_percentage < 0:
            return "down"
        else:
            return "stable"

    @property
    def period_duration_days(self) -> Optional[float]:
        """Длительность периода в днях"""
        if self.period_start and self.period_end:
            return (self.period_end - self.period_start).total_seconds() / 86400
        return None

    def calculate_change_percentage(self):
        """Расчет процента изменения"""
        if self.previous_value is None or self.previous_value == 0:
            self.change_percentage = None
            return

        self.change_percentage = ((self.value - self.previous_value) / abs(self.previous_value)) * 100

    def mark_as_calculated(self, calculated_by: str, method: str):
        """Отметить как вычисленную"""
        self.is_calculated = True
        self.calculated_by = calculated_by
        self.calculation_method = method
        self.updated_at = datetime.utcnow()

    def mark_as_validated(self):
        """Отметить как валидированную"""
        self.is_validated = True
        self.updated_at = datetime.utcnow()

    def add_validation_error(self, error: str, details: Optional[dict] = None):
        """Добавить ошибку валидации"""
        if not self.validation_errors:
            self.validation_errors = []

        error_data = {
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }

        self.validation_errors.append(error_data)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "metric_type": self.metric_type.value,
            "category": self.category.value,
            "granularity": self.granularity.value,
            "aggregation_function": self.aggregation_function,
            "value": self.value,
            "previous_value": self.previous_value,
            "change_percentage": self.change_percentage,
            "dimensions": self.dimensions,
            "tags": self.tags,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "data_quality_score": self.data_quality_score,
            "confidence_interval": self.confidence_interval,
            "sample_size": self.sample_size,
            "is_calculated": self.is_calculated,
            "is_validated": self.is_validated,
            "validation_errors": self.validation_errors,
            "dashboard_id": self.dashboard_id,
            "report_id": self.report_id,
            "kpi_id": self.kpi_id,
            "calculated_by": self.calculated_by,
            "calculation_method": self.calculation_method,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }

    @staticmethod
    def create_count_metric(
        name: str,
        value: float,
        category: MetricCategory,
        granularity: MetricGranularity,
        timestamp: datetime,
        dimensions: Optional[dict] = None
    ) -> 'Metric':
        """Создание метрики типа счетчик"""
        metric = Metric(
            id=str(uuid.uuid4()),
            name=name,
            metric_type=MetricType.COUNT,
            category=category,
            granularity=granularity,
            value=value,
            timestamp=timestamp,
            dimensions=dimensions or {}
        )
        return metric

    @staticmethod
    def create_gauge_metric(
        name: str,
        value: float,
        category: MetricCategory,
        timestamp: datetime,
        dimensions: Optional[dict] = None
    ) -> 'Metric':
        """Создание метрики типа измеритель"""
        metric = Metric(
            id=str(uuid.uuid4()),
            name=name,
            metric_type=MetricType.GAUGE,
            category=category,
            granularity=MetricGranularity.SECOND,
            value=value,
            timestamp=timestamp,
            dimensions=dimensions or {}
        )
        return metric

    @staticmethod
    def create_percentage_metric(
        name: str,
        value: float,
        category: MetricCategory,
        granularity: MetricGranularity,
        timestamp: datetime,
        dimensions: Optional[dict] = None
    ) -> 'Metric':
        """Создание метрики типа процент"""
        metric = Metric(
            id=str(uuid.uuid4()),
            name=name,
            metric_type=MetricType.PERCENTAGE,
            category=category,
            granularity=granularity,
            value=value,
            timestamp=timestamp,
            dimensions=dimensions or {}
        )
        return metric

    @staticmethod
    def create_duration_metric(
        name: str,
        value: float,
        category: MetricCategory,
        timestamp: datetime,
        dimensions: Optional[dict] = None
    ) -> 'Metric':
        """Создание метрики типа длительность"""
        metric = Metric(
            id=str(uuid.uuid4()),
            name=name,
            metric_type=MetricType.DURATION,
            category=category,
            granularity=MetricGranularity.SECOND,
            value=value,
            timestamp=timestamp,
            dimensions=dimensions or {}
        )
        return metric
