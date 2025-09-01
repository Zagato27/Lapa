"""
Модель событий аналитики
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Float, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class EventType(str, enum.Enum):
    """Типы событий"""
    USER_ACTION = "user_action"              # Действие пользователя
    SYSTEM_EVENT = "system_event"            # Системное событие
    BUSINESS_EVENT = "business_event"        # Бизнес-событие
    ERROR = "error"                          # Ошибка
    PERFORMANCE = "performance"              # Производительность
    SECURITY = "security"                    # Безопасность


class EventCategory(str, enum.Enum):
    """Категории событий"""
    AUTHENTICATION = "authentication"        # Аутентификация
    REGISTRATION = "registration"            # Регистрация
    PROFILE = "profile"                      # Профиль
    PET_MANAGEMENT = "pet_management"        # Управление питомцами
    ORDER = "order"                          # Заказы
    PAYMENT = "payment"                      # Платежи
    LOCATION = "location"                    # Локация
    CHAT = "chat"                            # Чат
    MEDIA = "media"                          # Медиа
    NOTIFICATION = "notification"            # Уведомления
    NAVIGATION = "navigation"                # Навигация
    SEARCH = "search"                        # Поиск
    SOCIAL = "social"                        # Социальные действия


class EventPriority(str, enum.Enum):
    """Приоритеты событий"""
    LOW = "low"                              # Низкий
    NORMAL = "normal"                        # Обычный
    HIGH = "high"                            # Высокий
    CRITICAL = "critical"                    # Критический


class Event(Base):
    """Модель события аналитики"""
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, index=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    category = Column(Enum(EventCategory), nullable=False, index=True)
    priority = Column(Enum(EventPriority), nullable=False, default=EventPriority.NORMAL)

    # Источник события
    service_name = Column(String, nullable=False, index=True)  # Название сервиса
    # Межсервисная ссылка: хранится как строка без внешнего ключа
    user_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)
    device_id = Column(String, nullable=True, index=True)

    # Описание события
    event_name = Column(String, nullable=False, index=True)    # Название события
    description = Column(Text, nullable=True)                  # Описание

    # Данные события
    properties = Column(JSON, nullable=True)                   # Свойства события
    metadata = Column(JSON, nullable=True)                     # Метаданные

    # Контекст
    user_agent = Column(Text, nullable=True)                   # User-Agent
    ip_address = Column(String, nullable=True)                 # IP адрес
    location_data = Column(JSON, nullable=True)                # Геолокационные данные
    device_info = Column(JSON, nullable=True)                  # Информация об устройстве

    # Временные метки
    event_timestamp = Column(DateTime, nullable=False, index=True)  # Время события
    processed_at = Column(DateTime, nullable=True)             # Время обработки
    created_at = Column(DateTime, default=func.now())

    # Связанные объекты
    # Межсервисные ссылки: храним идентификаторы без внешних ключей
    order_id = Column(String, nullable=True, index=True)
    pet_id = Column(String, nullable=True, index=True)
    chat_id = Column(String, nullable=True, index=True)
    payment_id = Column(String, nullable=True, index=True)

    # Метрики производительности
    duration_ms = Column(Float, nullable=True)                 # Длительность в мс
    memory_usage_mb = Column(Float, nullable=True)             # Использование памяти
    cpu_usage_percent = Column(Float, nullable=True)           # Использование CPU

    # Статус обработки
    is_processed = Column(Boolean, default=False)              # Обработано ли событие
    processing_errors = Column(JSON, nullable=True)            # Ошибки обработки

    # Признаки мошенничества/аномалий
    is_suspicious = Column(Boolean, default=False)             # Подозрительное ли событие
    anomaly_score = Column(Float, nullable=True)               # Счет аномалии

    # Бизнес-метрики
    revenue_impact = Column(Float, nullable=True)              # Влияние на доход
    user_engagement_score = Column(Float, nullable=True)       # Оценка вовлеченности

    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type.value}, name={self.event_name}, user={self.user_id})>"

    @property
    def is_user_event(self) -> bool:
        """Проверка, является ли событие пользовательским"""
        return self.event_type == EventType.USER_ACTION

    @property
    def is_system_event(self) -> bool:
        """Проверка, является ли событие системным"""
        return self.event_type == EventType.SYSTEM_EVENT

    @property
    def is_business_event(self) -> bool:
        """Проверка, является ли событие бизнесовым"""
        return self.event_type == EventType.BUSINESS_EVENT

    @property
    def is_error_event(self) -> bool:
        """Проверка, является ли событие ошибкой"""
        return self.event_type == EventType.ERROR

    @property
    def processing_time(self) -> Optional[float]:
        """Время обработки события в секундах"""
        if self.processed_at and self.event_timestamp:
            return (self.processed_at - self.event_timestamp).total_seconds()
        return None

    @property
    def event_age_days(self) -> float:
        """Возраст события в днях"""
        return (datetime.utcnow() - self.event_timestamp).total_seconds() / 86400

    def mark_as_processed(self):
        """Отметить как обработанное"""
        self.is_processed = True
        self.processed_at = datetime.utcnow()

    def mark_as_suspicious(self, score: float):
        """Отметить как подозрительное"""
        self.is_suspicious = True
        self.anomaly_score = score

    def add_processing_error(self, error: str, details: Optional[dict] = None):
        """Добавить ошибку обработки"""
        if not self.processing_errors:
            self.processing_errors = []

        error_data = {
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }

        self.processing_errors.append(error_data)

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "service_name": self.service_name,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "event_name": self.event_name,
            "description": self.description,
            "properties": self.properties,
            "metadata": self.metadata,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "location_data": self.location_data,
            "device_info": self.device_info,
            "event_timestamp": self.event_timestamp.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat(),
            "order_id": self.order_id,
            "pet_id": self.pet_id,
            "chat_id": self.chat_id,
            "payment_id": self.payment_id,
            "duration_ms": self.duration_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "is_processed": self.is_processed,
            "processing_errors": self.processing_errors,
            "is_suspicious": self.is_suspicious,
            "anomaly_score": self.anomaly_score,
            "revenue_impact": self.revenue_impact,
            "user_engagement_score": self.user_engagement_score
        }

    @staticmethod
    def create_user_event(
        service_name: str,
        user_id: str,
        event_name: str,
        category: EventCategory,
        properties: Optional[dict] = None,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> 'Event':
        """Создание пользовательского события"""
        event = Event(
            id=str(uuid.uuid4()),
            event_type=EventType.USER_ACTION,
            category=category,
            service_name=service_name,
            user_id=user_id,
            event_name=event_name,
            properties=properties or {},
            session_id=session_id,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            event_timestamp=datetime.utcnow()
        )
        return event

    @staticmethod
    def create_business_event(
        service_name: str,
        event_name: str,
        category: EventCategory,
        properties: dict,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        revenue_impact: Optional[float] = None
    ) -> 'Event':
        """Создание бизнес-события"""
        event = Event(
            id=str(uuid.uuid4()),
            event_type=EventType.BUSINESS_EVENT,
            category=category,
            service_name=service_name,
            user_id=user_id,
            event_name=event_name,
            properties=properties,
            order_id=order_id,
            revenue_impact=revenue_impact,
            event_timestamp=datetime.utcnow()
        )
        return event

    @staticmethod
    def create_system_event(
        service_name: str,
        event_name: str,
        category: EventCategory,
        properties: dict,
        priority: EventPriority = EventPriority.NORMAL,
        description: Optional[str] = None
    ) -> 'Event':
        """Создание системного события"""
        event = Event(
            id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_EVENT,
            category=category,
            priority=priority,
            service_name=service_name,
            event_name=event_name,
            description=description,
            properties=properties,
            event_timestamp=datetime.utcnow()
        )
        return event

    @staticmethod
    def create_error_event(
        service_name: str,
        event_name: str,
        error_message: str,
        error_details: Optional[dict] = None,
        user_id: Optional[str] = None,
        priority: EventPriority = EventPriority.HIGH
    ) -> 'Event':
        """Создание события ошибки"""
        event = Event(
            id=str(uuid.uuid4()),
            event_type=EventType.ERROR,
            category=EventCategory.SECURITY if "security" in event_name.lower() else EventCategory.NAVIGATION,
            priority=priority,
            service_name=service_name,
            user_id=user_id,
            event_name=event_name,
            description=error_message,
            properties=error_details or {},
            event_timestamp=datetime.utcnow()
        )
        return event
