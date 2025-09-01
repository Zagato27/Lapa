"""
Модель предупреждений о геолокации.

Используется сервисами локаций/геофенсов и роутами локаций.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from .base import Base


class LocationAlert(Base):
    """Модель предупреждения о геолокации"""
    __tablename__ = "location_alerts"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Тип предупреждения
    alert_type = Column(String, nullable=False)  # 'geofence_enter', 'geofence_exit', 'geofence_violation', 'emergency', 'low_battery', 'location_lost'

    # Геолокационная информация
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Детали предупреждения
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String, default="medium")  # 'low', 'medium', 'high', 'critical'

    # Связанные объекты
    geofence_id = Column(String, ForeignKey("geofences.id"), nullable=True)
    location_track_id = Column(String, ForeignKey("location_tracks.id"), nullable=True)

    # Дополнительные данные
    metadata_json = Column(JSON, nullable=True)  # Дополнительная информация в JSON

    # Статус обработки
    is_read = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    processed_by = Column(String, nullable=True)  # user_id того, кто обработал
    processed_at = Column(DateTime, nullable=True)

    # Автоматические действия
    auto_action_taken = Column(String, nullable=True)  # 'notification_sent', 'emergency_call', 'location_shared'

    # Временная метка
    timestamp = Column(DateTime, nullable=False, index=True)

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LocationAlert(id={self.id}, order_id={self.order_id}, type={self.alert_type}, severity={self.severity})>"

    @property
    def is_critical(self) -> bool:
        """Проверка, является ли предупреждение критическим"""
        return self.severity == 'critical'

    @property
    def is_high_priority(self) -> bool:
        """Проверка, является ли предупреждение высоким приоритетом"""
        return self.severity in ['high', 'critical']

    @property
    def is_geofence_alert(self) -> bool:
        """Проверка, является ли предупреждение геофенсингом"""
        return self.alert_type in ['geofence_enter', 'geofence_exit', 'geofence_violation']

    @property
    def is_emergency_alert(self) -> bool:
        """Проверка, является ли предупреждение экстренным"""
        return self.alert_type == 'emergency'

    def mark_as_read(self, user_id: str):
        """Отметить как прочитанное"""
        self.is_read = True
        self.processed_by = user_id
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_processed(self, user_id: str, action: Optional[str] = None):
        """Отметить как обработанное"""
        self.is_processed = True
        self.is_read = True
        self.processed_by = user_id
        self.processed_at = datetime.utcnow()
        if action:
            self.auto_action_taken = action
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "alert_type": self.alert_type,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geofence_id": self.geofence_id,
            "location_track_id": self.location_track_id,
            "metadata_json": self.metadata_json,
            "is_read": self.is_read,
            "is_processed": self.is_processed,
            "processed_by": self.processed_by,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "auto_action_taken": self.auto_action_taken,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_geofence_alert(order_id: str, user_id: str, alert_type: str,
                           latitude: float, longitude: float, geofence_id: str,
                           message: str) -> 'LocationAlert':
        """Создание предупреждения о геофенсинге"""
        alert = LocationAlert(
            id=str(uuid.uuid4()),
            order_id=order_id,
            user_id=user_id,
            alert_type=alert_type,
            title="Предупреждение геофенсинга",
            message=message,
            severity="high" if alert_type == "geofence_violation" else "medium",
            latitude=latitude,
            longitude=longitude,
            geofence_id=geofence_id,
            timestamp=datetime.utcnow()
        )
        return alert

    @staticmethod
    def create_emergency_alert(order_id: str, user_id: str, latitude: float,
                             longitude: float, message: str) -> 'LocationAlert':
        """Создание экстренного предупреждения"""
        alert = LocationAlert(
            id=str(uuid.uuid4()),
            order_id=order_id,
            user_id=user_id,
            alert_type="emergency",
            title="Экстренное предупреждение",
            message=message,
            severity="critical",
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.utcnow()
        )
        return alert

    @staticmethod
    def create_battery_alert(order_id: str, user_id: str, battery_level: float) -> 'LocationAlert':
        """Создание предупреждения о низком заряде батареи"""
        severity = "high" if battery_level < 15 else "medium"

        alert = LocationAlert(
            id=str(uuid.uuid4()),
            order_id=order_id,
            user_id=user_id,
            alert_type="low_battery",
            title="Низкий заряд батареи",
            message=f"Уровень заряда батареи: {battery_level}%",
            severity=severity,
            timestamp=datetime.utcnow()
        )
        return alert
