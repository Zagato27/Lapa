"""
Модель маршрутов прогулок.

Используется сервисом `LocationService` и роутами `app.api.v1.tracking`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from .base import Base


class Route(Base):
    """Модель маршрута прогулки"""
    __tablename__ = "routes"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Геометрия маршрута
    route_geometry = Column(Geometry(geometry_type='LINESTRING', srid=4326), nullable=True)
    simplified_geometry = Column(Geometry(geometry_type='LINESTRING', srid=4326), nullable=True)

    # Статистика маршрута
    total_distance_meters = Column(Float, nullable=True)  # Общая дистанция
    total_duration_seconds = Column(Integer, nullable=True)  # Общая продолжительность
    average_speed_kmh = Column(Float, nullable=True)     # Средняя скорость
    max_speed_kmh = Column(Float, nullable=True)         # Максимальная скорость

    # Точки маршрута
    start_point = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    end_point = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    waypoints = Column(JSON, nullable=True)  # Массив точек маршрута в JSON

    # Временные метки
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Статус маршрута
    is_completed = Column(Boolean, default=False)
    is_optimized = Column(Boolean, default=False)

    # Качество маршрута
    accuracy_score = Column(Float, nullable=True)  # Оценка точности (0-1)
    completeness_score = Column(Float, nullable=True)  # Оценка полноты (0-1)

    # Дополнительная информация
    weather_conditions = Column(JSON, nullable=True)  # Погодные условия
    traffic_conditions = Column(JSON, nullable=True)  # Условия движения
    notes = Column(Text, nullable=True)

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Route(id={self.id}, order_id={self.order_id}, distance={self.total_distance_meters}m)>"

    @property
    def duration_minutes(self) -> Optional[int]:
        """Продолжительность маршрута в минутах"""
        if self.total_duration_seconds:
            return self.total_duration_seconds // 60
        return None

    @property
    def duration_hours(self) -> Optional[float]:
        """Продолжительность маршрута в часах"""
        if self.total_duration_seconds:
            return self.total_duration_seconds / 3600
        return None

    @property
    def distance_km(self) -> Optional[float]:
        """Дистанция в километрах"""
        if self.total_distance_meters:
            return self.total_distance_meters / 1000
        return None

    @property
    def pace_minutes_per_km(self) -> Optional[float]:
        """Темп в минутах на километр"""
        if self.total_distance_meters and self.total_duration_seconds:
            distance_km = self.total_distance_meters / 1000
            duration_minutes = self.total_duration_seconds / 60
            return duration_minutes / distance_km if distance_km > 0 else None
        return None

    def to_geojson(self) -> dict:
        """Преобразование маршрута в GeoJSON формат"""
        coordinates = []

        if self.waypoints:
            for point in self.waypoints:
                coordinates.append([point['longitude'], point['latitude']])

        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "id": self.id,
                "order_id": self.order_id,
                "user_id": self.user_id,
                "total_distance_meters": self.total_distance_meters,
                "total_duration_seconds": self.total_duration_seconds,
                "average_speed_kmh": self.average_speed_kmh,
                "is_completed": self.is_completed,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None
            }
        }

    def calculate_statistics(self, location_tracks: list) -> None:
        """Расчет статистики маршрута на основе точек трекинга"""
        if not location_tracks:
            return

        # Сортировка точек по времени
        sorted_tracks = sorted(location_tracks, key=lambda x: x.timestamp)

        # Расчет дистанции
        total_distance = 0
        for i in range(1, len(sorted_tracks)):
            distance = sorted_tracks[i-1].distance_to(
                sorted_tracks[i].latitude,
                sorted_tracks[i].longitude
            )
            total_distance += distance

        self.total_distance_meters = total_distance

        # Расчет продолжительности
        if len(sorted_tracks) > 1:
            start_time = sorted_tracks[0].timestamp
            end_time = sorted_tracks[-1].timestamp
            self.total_duration_seconds = int((end_time - start_time).total_seconds())

        # Расчет средней скорости
        if self.total_duration_seconds and self.total_duration_seconds > 0:
            distance_km = total_distance / 1000
            duration_hours = self.total_duration_seconds / 3600
            self.average_speed_kmh = distance_km / duration_hours if duration_hours > 0 else 0

        # Расчет максимальной скорости
        max_speed = 0
        for track in sorted_tracks:
            if track.speed_kmh and track.speed_kmh > max_speed:
                max_speed = track.speed_kmh
        self.max_speed_kmh = max_speed if max_speed > 0 else None

        # Сохранение waypoints
        self.waypoints = [
            {
                'latitude': track.latitude,
                'longitude': track.longitude,
                'timestamp': track.timestamp.isoformat(),
                'accuracy': track.accuracy,
                'speed': track.speed
            }
            for track in sorted_tracks
        ]

    def optimize_route(self) -> None:
        """Оптимизация маршрута"""
        if not self.waypoints or len(self.waypoints) < 3:
            self.is_optimized = True
            return

        # Простая оптимизация: удаление точек, которые находятся слишком близко друг к другу
        from app.config import settings
        tolerance = settings.route_simplification_tolerance

        optimized_points = [self.waypoints[0]]  # Начинаем с первой точки

        for point in self.waypoints[1:]:
            last_point = optimized_points[-1]

            # Расчет расстояния между точками
            from app.services.location_service import LocationService
            distance = LocationService.calculate_distance(
                last_point['latitude'], last_point['longitude'],
                point['latitude'], point['longitude']
            )

            # Добавляем точку только если расстояние достаточно большое
            if distance >= tolerance:
                optimized_points.append(point)

        # Добавляем последнюю точку, если она отличается от предыдущей
        if self.waypoints[-1] not in optimized_points:
            optimized_points.append(self.waypoints[-1])

        self.waypoints = optimized_points
        self.is_optimized = True

        # Пересчет статистики после оптимизации
        # (здесь можно добавить логику пересчета)
