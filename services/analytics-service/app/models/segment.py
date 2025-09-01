"""
Модель сегментов пользователей
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Float, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class SegmentType(str, enum.Enum):
    """Типы сегментов"""
    DEMOGRAPHIC = "demographic"              # Демографический
    BEHAVIORAL = "behavioral"                # Поведенческий
    GEOGRAPHIC = "geographic"                # Географический
    TECHNOGRAPHIC = "technographic"          # Техно-графический
    PSYCHOGRAPHIC = "psychographic"          # Психо-графический
    CUSTOM = "custom"                        # Пользовательский


class SegmentStatus(str, enum.Enum):
    """Статусы сегментов"""
    ACTIVE = "active"                        # Активный
    INACTIVE = "inactive"                    # Неактивный
    DRAFT = "draft"                          # Черновик
    ARCHIVED = "archived"                    # Архивный


class Segment(Base):
    """Модель сегмента пользователей"""
    __tablename__ = "analytics_segments"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)          # Название сегмента
    description = Column(Text, nullable=True)                  # Описание

    # Тип и статус
    segment_type = Column(Enum(SegmentType), nullable=False)
    status = Column(Enum(SegmentStatus), nullable=False, default=SegmentStatus.DRAFT)

    # Критерии сегментации
    criteria = Column(JSON, nullable=False)                    # Критерии отбора
    filters = Column(JSON, nullable=True)                      # Дополнительные фильтры

    # Статистика сегмента
    estimated_size = Column(Integer, nullable=True)            # Оцениваемый размер
    actual_size = Column(Integer, nullable=True)               # Фактический размер
    last_calculated_at = Column(DateTime, nullable=True)       # Последний расчет

    # Качество сегмента
    quality_score = Column(Float, nullable=True)               # Оценка качества сегмента
    uniqueness_score = Column(Float, nullable=True)            # Оценка уникальности

    # Создал
    # Межсервисная ссылка на пользователя-создателя
    created_by = Column(String, nullable=False, index=True)

    # Настройки обновления
    auto_update = Column(Boolean, default=False)               # Автоматическое обновление
    update_frequency = Column(String, default="daily")         # Частота обновления

    # Связанные кампании
    campaign_ids = Column(JSON, nullable=True)                 # ID связанных кампаний

    # Метаданные
    tags = Column(JSON, nullable=True)                        # Теги
    metadata = Column(JSON, nullable=True)                    # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Segment(id={self.id}, name={self.name}, type={self.segment_type.value}, size={self.actual_size})>"

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли сегмент"""
        return self.status == SegmentStatus.ACTIVE

    @property
    def is_draft(self) -> bool:
        """Проверка, является ли черновиком"""
        return self.status == SegmentStatus.DRAFT

    @property
    def is_archived(self) -> bool:
        """Проверка, архивный ли сегмент"""
        return self.status == SegmentStatus.ARCHIVED

    @property
    def criteria_count(self) -> int:
        """Количество критериев"""
        if not self.criteria:
            return 0
        return len(self.criteria)

    @property
    def days_since_last_calculation(self) -> Optional[float]:
        """Количество дней с последнего расчета"""
        if not self.last_calculated_at:
            return None
        return (datetime.utcnow() - self.last_calculated_at).total_seconds() / 86400

    def activate(self):
        """Активация сегмента"""
        self.status = SegmentStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def deactivate(self):
        """Деактивация сегмента"""
        self.status = SegmentStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def archive(self):
        """Архивация сегмента"""
        self.status = SegmentStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def update_size(self, actual_size: int):
        """Обновление размера сегмента"""
        self.actual_size = actual_size
        self.last_calculated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_criterion(self, criterion: dict):
        """Добавление критерия"""
        if not self.criteria:
            self.criteria = []

        self.criteria.append(criterion)
        self.updated_at = datetime.utcnow()

    def remove_criterion(self, criterion_index: int):
        """Удаление критерия"""
        if self.criteria and 0 <= criterion_index < len(self.criteria):
            del self.criteria[criterion_index]
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "segment_type": self.segment_type.value,
            "status": self.status.value,
            "criteria": self.criteria,
            "filters": self.filters,
            "estimated_size": self.estimated_size,
            "actual_size": self.actual_size,
            "last_calculated_at": self.last_calculated_at.isoformat() if self.last_calculated_at else None,
            "quality_score": self.quality_score,
            "uniqueness_score": self.uniqueness_score,
            "created_by": self.created_by,
            "auto_update": self.auto_update,
            "update_frequency": self.update_frequency,
            "campaign_ids": self.campaign_ids,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @staticmethod
    def create_demographic_segment(
        name: str,
        criteria: list,
        created_by: str,
        description: Optional[str] = None
    ) -> 'Segment':
        """Создание демографического сегмента"""
        segment = Segment(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            segment_type=SegmentType.DEMOGRAPHIC,
            criteria=criteria,
            created_by=created_by
        )
        return segment

    @staticmethod
    def create_behavioral_segment(
        name: str,
        criteria: list,
        created_by: str,
        description: Optional[str] = None
    ) -> 'Segment':
        """Создание поведенческого сегмента"""
        segment = Segment(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            segment_type=SegmentType.BEHAVIORAL,
            criteria=criteria,
            created_by=created_by
        )
        return segment

    @staticmethod
    def create_geographic_segment(
        name: str,
        criteria: list,
        created_by: str,
        description: Optional[str] = None
    ) -> 'Segment':
        """Создание географического сегмента"""
        segment = Segment(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            segment_type=SegmentType.GEOGRAPHIC,
            criteria=criteria,
            created_by=created_by
        )
        return segment
