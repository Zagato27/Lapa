"""
Модель отслеживания геолокации.

Используется `LocationService` и роутами `app.api.v1.locations`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from .base import Base


class LocationTrack(Base):
    """Модель отслеживания геолокации"""
    __tablename__ = "location_tracks"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Геолокационные данные
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)  # Точность определения координат в метрах
    altitude = Column(Float, nullable=True)  # Высота над уровнем моря
    speed = Column(Float, nullable=True)     # Скорость движения (м/с)
    heading = Column(Float, nullable=True)   # Направление движения (градусы)

    # Тип точки отслеживания
    track_type = Column(String, nullable=False)  # 'current', 'walking', 'start', 'end', 'emergency'

    # Дополнительная информация
    battery_level = Column(Float, nullable=True)  # Уровень заряда батареи
    network_type = Column(String, nullable=True)  # Тип сети (wifi, cellular, etc.)
    device_info = Column(JSON, nullable=True)    # Информация об устройстве

    # Адрес (определяется геокодированием)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)

    # Статус точки
    is_valid = Column(Boolean, default=True)     # Валидность точки
    is_processed = Column(Boolean, default=False)  # Обработана ли точка

    # Временная метка
    timestamp = Column(DateTime, nullable=False, index=True)

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LocationTrack(id={self.id}, order_id={self.order_id}, lat={self.latitude}, lon={self.longitude}, type={self.track_type})>"

    @property
    def coordinates(self) -> tuple[float, float]:
        """Координаты в виде кортежа"""
        return (self.latitude, self.longitude)

    @property
    def speed_kmh(self) -> Optional[float]:
        """Скорость в км/ч"""
        if self.speed is not None:
            return self.speed * 3.6  # м/с в км/ч
        return None

    @property
    def is_walking_point(self) -> bool:
        """Проверка, является ли точка частью прогулки"""
        return self.track_type in ['walking', 'current']

    @property
    def is_emergency_point(self) -> bool:
        """Проверка, является ли точка экстренной"""
        return self.track_type == 'emergency'

    @property
    def has_location_data(self) -> bool:
        """Проверка наличия основных геоданных"""
        return (
            self.latitude is not None and
            self.longitude is not None and
            self.accuracy is not None
        )

    def to_geojson(self) -> dict:
        """Преобразование в GeoJSON формат"""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "id": self.id,
                "order_id": self.order_id,
                "user_id": self.user_id,
                "track_type": self.track_type,
                "accuracy": self.accuracy,
                "altitude": self.altitude,
                "speed": self.speed,
                "heading": self.heading,
                "battery_level": self.battery_level,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "address": self.address
            }
        }

    def distance_to(self, other_lat: float, other_lon: float) -> float:
        """Расчет расстояния до другой точки"""
        from app.services.location_service import LocationService
        return LocationService.calculate_distance(
            self.latitude, self.longitude, other_lat, other_lon
        )

    def is_within_geofence(self, geofence_lat: float, geofence_lon: float, radius_meters: float) -> bool:
        """Проверка нахождения в геофенсе"""
        distance = self.distance_to(geofence_lat, geofence_lon)
        return distance <= radius_meters
