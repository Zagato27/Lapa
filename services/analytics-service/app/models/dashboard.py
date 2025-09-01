"""
Модель дашбордов аналитики
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Float, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class DashboardType(str, enum.Enum):
    """Типы дашбордов"""
    EXECUTIVE = "executive"                  # Руководительский
    OPERATIONAL = "operational"              # Операционный
    ANALYTICAL = "analytical"                # Аналитический
    CUSTOM = "custom"                        # Пользовательский
    REAL_TIME = "real_time"                  # Реального времени


class DashboardStatus(str, enum.Enum):
    """Статусы дашбордов"""
    DRAFT = "draft"                          # Черновик
    PUBLISHED = "published"                  # Опубликован
    ARCHIVED = "archived"                    # Архивный


class WidgetType(str, enum.Enum):
    """Типы виджетов"""
    CHART = "chart"                          # График
    TABLE = "table"                          # Таблица
    METRIC = "metric"                        # Метрика
    MAP = "map"                              # Карта
    TEXT = "text"                            # Текст
    IMAGE = "image"                          # Изображение


class Dashboard(Base):
    """Модель дашборда"""
    __tablename__ = "analytics_dashboards"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)                    # Название дашборда
    description = Column(Text, nullable=True)                 # Описание
    dashboard_type = Column(Enum(DashboardType), nullable=False)

    # Статус и настройки
    status = Column(Enum(DashboardStatus), nullable=False, default=DashboardStatus.DRAFT)
    is_public = Column(Boolean, default=False)                # Публичный доступ
    is_default = Column(Boolean, default=False)               # Дашборд по умолчанию

    # Конфигурация
    layout_config = Column(JSON, nullable=True)               # Конфигурация раскладки
    theme_config = Column(JSON, nullable=True)                # Конфигурация темы
    refresh_interval = Column(Integer, default=300)           # Интервал обновления (секунды)

    # Виджеты дашборда
    widgets = Column(JSON, nullable=True)                     # Конфигурация виджетов

    # Фильтры
    default_filters = Column(JSON, nullable=True)             # Фильтры по умолчанию
    allowed_filters = Column(JSON, nullable=True)             # Разрешенные фильтры

    # Доступ
    # Межсервисная ссылка на владельца дашборда
    owner_id = Column(String, nullable=False, index=True)
    shared_with = Column(JSON, nullable=True)                 # С кем поделен
    access_permissions = Column(JSON, nullable=True)          # Права доступа

    # Категория и теги
    category = Column(String, nullable=True)                  # Категория
    tags = Column(JSON, nullable=True)                        # Теги

    # Статистика использования
    view_count = Column(Integer, default=0)                   # Количество просмотров
    last_viewed_at = Column(DateTime, nullable=True)          # Последний просмотр
    average_load_time = Column(Float, nullable=True)          # Среднее время загрузки

    # Метаданные
    metadata = Column(JSON, nullable=True)                    # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Dashboard(id={self.id}, name={self.name}, type={self.dashboard_type.value}, status={self.status.value})>"

    @property
    def is_draft(self) -> bool:
        """Проверка, является ли черновиком"""
        return self.status == DashboardStatus.DRAFT

    @property
    def is_published(self) -> bool:
        """Проверка, опубликован ли дашборд"""
        return self.status == DashboardStatus.PUBLISHED

    @property
    def is_archived(self) -> bool:
        """Проверка, архивный ли дашборд"""
        return self.status == DashboardStatus.ARCHIVED

    @property
    def widget_count(self) -> int:
        """Количество виджетов"""
        if not self.widgets:
            return 0
        return len(self.widgets)

    def publish(self):
        """Публикация дашборда"""
        self.status = DashboardStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def archive(self):
        """Архивация дашборда"""
        self.status = DashboardStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def increment_view_count(self):
        """Увеличение счетчика просмотров"""
        self.view_count += 1
        self.last_viewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_widget(self, widget_config: dict):
        """Добавление виджета"""
        if not self.widgets:
            self.widgets = []

        widget_config["id"] = str(uuid.uuid4())
        widget_config["created_at"] = datetime.utcnow().isoformat()

        self.widgets.append(widget_config)
        self.updated_at = datetime.utcnow()

    def remove_widget(self, widget_id: str):
        """Удаление виджета"""
        if self.widgets:
            self.widgets = [w for w in self.widgets if w.get("id") != widget_id]
        self.updated_at = datetime.utcnow()

    def update_layout(self, layout_config: dict):
        """Обновление раскладки"""
        self.layout_config = layout_config
        self.updated_at = datetime.utcnow()

    def share_with_user(self, user_id: str, permissions: list):
        """Поделиться с пользователем"""
        if not self.shared_with:
            self.shared_with = {}

        self.shared_with[user_id] = {
            "permissions": permissions,
            "shared_at": datetime.utcnow().isoformat()
        }

        self.updated_at = datetime.utcnow()

    def revoke_access(self, user_id: str):
        """Отозвать доступ"""
        if self.shared_with and user_id in self.shared_with:
            del self.shared_with[user_id]
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dashboard_type": self.dashboard_type.value,
            "status": self.status.value,
            "is_public": self.is_public,
            "is_default": self.is_default,
            "layout_config": self.layout_config,
            "theme_config": self.theme_config,
            "refresh_interval": self.refresh_interval,
            "widgets": self.widgets,
            "default_filters": self.default_filters,
            "allowed_filters": self.allowed_filters,
            "owner_id": self.owner_id,
            "shared_with": self.shared_with,
            "access_permissions": self.access_permissions,
            "category": self.category,
            "tags": self.tags,
            "view_count": self.view_count,
            "last_viewed_at": self.last_viewed_at.isoformat() if self.last_viewed_at else None,
            "average_load_time": self.average_load_time,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None
        }

    @staticmethod
    def create_executive_dashboard(name: str, owner_id: str, description: Optional[str] = None) -> 'Dashboard':
        """Создание руководительского дашборда"""
        dashboard = Dashboard(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            dashboard_type=DashboardType.EXECUTIVE,
            owner_id=owner_id,
            refresh_interval=600  # 10 минут
        )
        return dashboard

    @staticmethod
    def create_operational_dashboard(name: str, owner_id: str, description: Optional[str] = None) -> 'Dashboard':
        """Создание операционного дашборда"""
        dashboard = Dashboard(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            dashboard_type=DashboardType.OPERATIONAL,
            owner_id=owner_id,
            refresh_interval=60  # 1 минута
        )
        return dashboard

    @staticmethod
    def create_real_time_dashboard(name: str, owner_id: str, description: Optional[str] = None) -> 'Dashboard':
        """Создание дашборда реального времени"""
        dashboard = Dashboard(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            dashboard_type=DashboardType.REAL_TIME,
            owner_id=owner_id,
            refresh_interval=10  # 10 секунд
        )
        return dashboard
