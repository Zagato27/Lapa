"""
Модель геофенсинга.

Используется сервисами геолокации и роутами `app.api.v1.geofences`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from .base import Base


class Geofence(Base):
    """Модель геофенсинга"""
    __tablename__ = "geofences"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Центр геофенса
    center_location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)

    # Параметры геофенса
    radius_meters = Column(Float, nullable=False)  # Радиус в метрах
    shape = Column(String, default="circle")  # circle, polygon (для будущих расширений)

    # Тип геофенса
    geofence_type = Column(String, nullable=False)  # 'safe_zone', 'danger_zone', 'walking_area'

    # Настройки предупреждений
    alert_on_enter = Column(Boolean, default=False)  # Предупреждение при входе
    alert_on_exit = Column(Boolean, default=True)   # Предупреждение при выходе
    alert_distance = Column(Float, nullable=True)   # Дистанция для предварительного предупреждения

    # Статус
    is_active = Column(Boolean, default=True)
    is_violated = Column(Boolean, default=False)  # Нарушена ли зона

    # Название и описание
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Временные ограничения
    active_from_time = Column(String, nullable=True)  # Время начала активности (HH:MM)
    active_until_time = Column(String, nullable=True)  # Время окончания активности (HH:MM)

    # Статистика
    enter_count = Column(Integer, default=0)  # Количество входов
    exit_count = Column(Integer, default=0)   # Количество выходов
    violation_count = Column(Integer, default=0)  # Количество нарушений

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_violation_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Geofence(id={self.id}, order_id={self.order_id}, type={self.geofence_type}, radius={self.radius_meters}m)>"

    @property
    def center_coordinates(self) -> tuple[float, float]:
        """Координаты центра геофенса"""
        return (self.center_latitude, self.center_longitude)

    @property
    def is_safe_zone(self) -> bool:
        """Проверка, является ли зона безопасной"""
        return self.geofence_type == 'safe_zone'

    @property
    def is_danger_zone(self) -> bool:
        """Проверка, является ли зона опасной"""
        return self.geofence_type == 'danger_zone'

    @property
    def area_square_meters(self) -> float:
        """Площадь зоны (для круга)"""
        import math
        return math.pi * (self.radius_meters ** 2)

    def contains_point(self, latitude: float, longitude: float) -> bool:
        """Проверка, находится ли точка внутри геофенса"""
        from app.services.location_service import LocationService
        distance = LocationService.calculate_distance(
            self.center_latitude, self.center_longitude, latitude, longitude
        )
        return distance <= self.radius_meters

    def distance_to_point(self, latitude: float, longitude: float) -> float:
        """Расстояние от центра геофенса до точки"""
        from app.services.location_service import LocationService
        return LocationService.calculate_distance(
            self.center_latitude, self.center_longitude, latitude, longitude
        )

    def is_time_active(self) -> bool:
        """Проверка, активна ли зона по времени"""
        if not self.active_from_time or not self.active_until_time:
            return True

        from datetime import datetime
        now = datetime.now().time()

        from_time = datetime.strptime(self.active_from_time, "%H:%M").time()
        until_time = datetime.strptime(self.active_until_time, "%H:%M").time()

        if from_time <= until_time:
            return from_time <= now <= until_time
        else:
            # Время переходит через полночь
            return now >= from_time or now <= until_time

    def record_enter(self):
        """Запись входа в зону"""
        self.enter_count += 1
        self.is_violated = False
        self.updated_at = datetime.utcnow()

    def record_exit(self):
        """Запись выхода из зоны"""
        self.exit_count += 1
        self.updated_at = datetime.utcnow()

    def record_violation(self):
        """Запись нарушения зоны"""
        self.violation_count += 1
        self.is_violated = True
        self.last_violation_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_geojson(self) -> dict:
        """Преобразование в GeoJSON формат"""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.center_longitude, self.center_latitude]
            },
            "properties": {
                "id": self.id,
                "order_id": self.order_id,
                "geofence_type": self.geofence_type,
                "radius_meters": self.radius_meters,
                "name": self.name,
                "description": self.description,
                "is_active": self.is_active,
                "is_violated": self.is_violated
            }
        }
