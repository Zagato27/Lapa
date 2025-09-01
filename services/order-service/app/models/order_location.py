"""
Модель геолокационной информации заказов.

Используется:
- Для сохранения ключевых геоточек (pickup/dropoff/points) по заказу
- Может использоваться при аналитике маршрутов и споров
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from .base import Base


class OrderLocation(Base):
    """Модель геолокационной информации заказа"""
    __tablename__ = "order_locations"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)

    # Геолокация
    # Геометрия точки
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)  # Точность определения координат в метрах

    # Адрес
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)

    # Тип точки
    location_type = Column(String, nullable=False)  # 'pickup', 'dropoff', 'walking_point', 'current'

    # Временная метка
    timestamp = Column(DateTime, nullable=False, index=True)

    # Дополнительная информация
    speed = Column(Float, nullable=True)  # Скорость движения (м/с)
    altitude = Column(Float, nullable=True)  # Высота над уровнем моря
    heading = Column(Float, nullable=True)  # Направление движения (градусы)

    # Метаданные
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<OrderLocation(id={self.id}, order_id={self.order_id}, type={self.location_type}, lat={self.latitude}, lon={self.longitude})>"

    @property
    def coordinates(self) -> tuple[float, float]:
        """Координаты в виде кортежа"""
        return (self.latitude, self.longitude)

    @property
    def is_pickup_location(self) -> bool:
        """Проверка, является ли точка местом встречи"""
        return self.location_type == 'pickup'

    @property
    def is_dropoff_location(self) -> bool:
        """Проверка, является ли точка местом высадки"""
        return self.location_type == 'dropoff'

    @property
    def is_walking_point(self) -> bool:
        """Проверка, является ли точка частью прогулки"""
        return self.location_type == 'walking_point'

    @property
    def is_current_location(self) -> bool:
        """Проверка, является ли точка текущим местоположением"""
        return self.location_type == 'current'
