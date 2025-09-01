"""
Модель ключевых показателей эффективности (KPI)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Float, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class KPICategory(str, enum.Enum):
    """Категории KPI"""
    FINANCIAL = "financial"                  # Финансовые
    CUSTOMER = "customer"                    # Клиентские
    OPERATIONAL = "operational"              # Операционные
    MARKETING = "marketing"                  # Маркетинговые
    PRODUCT = "product"                      # Продуктовые
    EMPLOYEE = "employee"                    # Сотруднические


class KPIType(str, enum.Enum):
    """Типы KPI"""
    REVENUE = "revenue"                      # Доход
    GROWTH = "growth"                        # Рост
    EFFICIENCY = "efficiency"                # Эффективность
    QUALITY = "quality"                      # Качество
    SATISFACTION = "satisfaction"            # Удовлетворенность
    RETENTION = "retention"                  # Удержание
    CONVERSION = "conversion"                # Конверсия
    UTILIZATION = "utilization"              # Использование


class KPITrend(str, enum.Enum):
    """Тренды KPI"""
    IMPROVING = "improving"                  # Улучшается
    DECLINING = "declining"                  # Ухудшается
    STABLE = "stable"                        # Стабильный
    VOLATILE = "volatile"                    # Волатильный


class KPIStatus(str, enum.Enum):
    """Статусы KPI"""
    ON_TRACK = "on_track"                    # По плану
    BEHIND = "behind"                        # Отстает
    AHEAD = "ahead"                          # Опережает
    CRITICAL = "critical"                    # Критическое состояние


class KPI(Base):
    """Модель ключевого показателя эффективности"""
    __tablename__ = "analytics_kpis"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)          # Название KPI
    display_name = Column(String, nullable=True)               # Отображаемое название
    description = Column(Text, nullable=True)                  # Описание KPI

    # Тип и категория
    kpi_type = Column(Enum(KPIType), nullable=False)
    category = Column(Enum(KPICategory), nullable=False, index=True)

    # Текущие значения
    current_value = Column(Float, nullable=False)              # Текущее значение
    target_value = Column(Float, nullable=True)                # Целевое значение
    baseline_value = Column(Float, nullable=True)              # Базовое значение

    # Показатели тренда
    trend = Column(Enum(KPITrend), nullable=True)              # Тренд
    trend_strength = Column(Float, nullable=True)              # Сила тренда (0-1)
    change_percentage = Column(Float, nullable=True)           # Изменение в процентах

    # Статус и прогресс
    status = Column(Enum(KPIStatus), nullable=True)            # Статус достижения цели
    progress_percentage = Column(Float, nullable=True)         # Процент достижения цели

    # Периодичность
    calculation_period = Column(String, default="daily")       # Период расчета
    last_calculated_at = Column(DateTime, nullable=True)       # Последний расчет

    # Формула расчета
    calculation_formula = Column(Text, nullable=True)          # Формула расчета
    calculation_parameters = Column(JSON, nullable=True)       # Параметры расчета

    # Связанные метрики
    related_metrics = Column(JSON, nullable=True)              # Связанные метрики

    # Ответственность
    # Межсервисная ссылка на пользователя
    owner_id = Column(String, nullable=True, index=True)
    department = Column(String, nullable=True)                 # Отдел
    team = Column(String, nullable=True)                       # Команда

    # Важность и приоритеты
    priority = Column(String, default="medium")                # Приоритет
    weight = Column(Float, default=1.0)                        # Вес в расчетах

    # Настройки алертов
    alert_enabled = Column(Boolean, default=False)             # Включены ли алерты
    alert_threshold = Column(Float, nullable=True)             # Порог алерта
    alert_condition = Column(String, nullable=True)            # Условие алерта

    # Метаданные
    tags = Column(JSON, nullable=True)                        # Теги
    metadata = Column(JSON, nullable=True)                    # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<KPI(id={self.id}, name={self.name}, value={self.current_value}, status={self.status.value if self.status else None})>"

    @property
    def is_on_track(self) -> bool:
        """Проверка, идет ли KPI по плану"""
        return self.status == KPIStatus.ON_TRACK

    @property
    def is_behind(self) -> bool:
        """Проверка, отстает ли KPI"""
        return self.status == KPIStatus.BEHIND

    @property
    def is_ahead(self) -> bool:
        """Проверка, опережает ли KPI план"""
        return self.status == KPIStatus.AHEAD

    @property
    def is_critical(self) -> bool:
        """Проверка, в критическом ли состоянии KPI"""
        return self.status == KPIStatus.CRITICAL

    @property
    def progress_to_target(self) -> Optional[float]:
        """Расчет прогресса к цели"""
        if not self.target_value or not self.baseline_value:
            return None

        total_range = self.target_value - self.baseline_value
        if total_range == 0:
            return 100.0

        current_progress = self.current_value - self.baseline_value
        return (current_progress / total_range) * 100

    @property
    def days_since_last_calculation(self) -> Optional[float]:
        """Количество дней с последнего расчета"""
        if not self.last_calculated_at:
            return None
        return (datetime.utcnow() - self.last_calculated_at).total_seconds() / 86400

    def calculate_status(self):
        """Расчет статуса KPI"""
        if not self.target_value:
            self.status = None
            return

        if self.progress_percentage is None:
            self.progress_percentage = self.progress_to_target

        if not self.progress_percentage:
            self.status = None
            return

        # Определение статуса на основе прогресса
        if self.progress_percentage >= 100:
            self.status = KPIStatus.AHEAD
        elif self.progress_percentage >= 75:
            self.status = KPIStatus.ON_TRACK
        elif self.progress_percentage >= 50:
            self.status = KPIStatus.BEHIND
        else:
            self.status = KPIStatus.CRITICAL

    def calculate_trend(self, historical_values: list):
        """Расчет тренда на основе исторических значений"""
        if len(historical_values) < 2:
            self.trend = None
            return

        # Простой расчет тренда (можно улучшить с помощью статистических методов)
        recent_avg = sum(historical_values[-3:]) / len(historical_values[-3:])
        older_avg = sum(historical_values[:-3]) / len(historical_values[:-3]) if len(historical_values) > 3 else historical_values[0]

        if older_avg == 0:
            change_rate = 0
        else:
            change_rate = (recent_avg - older_avg) / abs(older_avg)

        if abs(change_rate) < 0.05:
            self.trend = KPITrend.STABLE
        elif change_rate > 0.05:
            self.trend = KPITrend.IMPROVING
        elif change_rate < -0.05:
            self.trend = KPITrend.DECLINING
        else:
            self.trend = KPITrend.VOLATILE

        self.trend_strength = abs(change_rate)

    def should_trigger_alert(self) -> bool:
        """Проверка необходимости алерта"""
        if not self.alert_enabled or not self.alert_threshold:
            return False

        if self.alert_condition == "below":
            return self.current_value < self.alert_threshold
        elif self.alert_condition == "above":
            return self.current_value > self.alert_threshold
        elif self.alert_condition == "equals":
            return abs(self.current_value - self.alert_threshold) < 0.01

        return False

    def update_value(self, new_value: float):
        """Обновление значения KPI"""
        if self.current_value != new_value:
            # Расчет изменения в процентах
            if self.current_value and self.current_value != 0:
                self.change_percentage = ((new_value - self.current_value) / abs(self.current_value)) * 100
            else:
                self.change_percentage = None

            self.current_value = new_value
            self.last_calculated_at = datetime.utcnow()

            # Перерасчет статуса и прогресса
            self.calculate_status()

            self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "kpi_type": self.kpi_type.value,
            "category": self.category.value,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "baseline_value": self.baseline_value,
            "trend": self.trend.value if self.trend else None,
            "trend_strength": self.trend_strength,
            "change_percentage": self.change_percentage,
            "status": self.status.value if self.status else None,
            "progress_percentage": self.progress_percentage,
            "calculation_period": self.calculation_period,
            "last_calculated_at": self.last_calculated_at.isoformat() if self.last_calculated_at else None,
            "calculation_formula": self.calculation_formula,
            "calculation_parameters": self.calculation_parameters,
            "related_metrics": self.related_metrics,
            "owner_id": self.owner_id,
            "department": self.department,
            "team": self.team,
            "priority": self.priority,
            "weight": self.weight,
            "alert_enabled": self.alert_enabled,
            "alert_threshold": self.alert_threshold,
            "alert_condition": self.alert_condition,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @staticmethod
    def create_revenue_kpi(
        name: str,
        target_value: float,
        owner_id: str,
        department: str = "finance"
    ) -> 'KPI':
        """Создание KPI дохода"""
        kpi = KPI(
            id=str(uuid.uuid4()),
            name=name,
            kpi_type=KPIType.REVENUE,
            category=KPICategory.FINANCIAL,
            current_value=0,
            target_value=target_value,
            baseline_value=0,
            owner_id=owner_id,
            department=department
        )
        return kpi

    @staticmethod
    def create_customer_satisfaction_kpi(
        name: str,
        target_value: float,
        owner_id: str,
        department: str = "customer_success"
    ) -> 'KPI':
        """Создание KPI удовлетворенности клиентов"""
        kpi = KPI(
            id=str(uuid.uuid4()),
            name=name,
            kpi_type=KPIType.SATISFACTION,
            category=KPICategory.CUSTOMER,
            current_value=0,
            target_value=target_value,
            baseline_value=0,
            owner_id=owner_id,
            department=department
        )
        return kpi

    @staticmethod
    def create_conversion_kpi(
        name: str,
        target_value: float,
        owner_id: str,
        department: str = "marketing"
    ) -> 'KPI':
        """Создание KPI конверсии"""
        kpi = KPI(
            id=str(uuid.uuid4()),
            name=name,
            kpi_type=KPIType.CONVERSION,
            category=KPICategory.MARKETING,
            current_value=0,
            target_value=target_value,
            baseline_value=0,
            owner_id=owner_id,
            department=department
        )
        return kpi
