"""
Модель пользователя.

Используется:
- В сервисах `auth_service` и `user_service` для CRUD и аутентификации
- В эндпоинтах `app.api.v1.users` и `app.api.v1.auth`
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from .base import Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="client")  # client или walker
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    # Геолокация (для выгульщиков)
    # Геометрия хранится в PostGIS, SRID=4326 (WGS84)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Статус и верификация
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_walker_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    phone_verified_at = Column(DateTime, nullable=True)

    # Рейтинг и статистика
    rating = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)

    # Настройки уведомлений
    notifications_enabled = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)

    # Для выгульщиков
    experience_years = Column(Integer, nullable=True)
    services_offered = Column(JSON, nullable=True)  # JSON array of services
    work_schedule = Column(JSON, nullable=True)    # JSON object with schedule
    hourly_rate = Column(Float, nullable=True)     # Стоимость услуг в час

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_walker(self) -> bool:
        """Проверка, является ли пользователь выгульщиком"""
        return self.role == "walker"

    @property
    def completion_rate(self) -> float:
        """Процент выполненных заказов"""
        if self.total_orders == 0:
            return 0.0
        return (self.completed_orders / self.total_orders) * 100

    def update_rating(self, new_rating: float):
        """Обновление рейтинга пользователя"""
        # Простая формула среднего рейтинга (в будущем можно улучшить)
        if self.total_orders == 0:
            self.rating = new_rating
        else:
            self.rating = (self.rating * (self.total_orders - 1) + new_rating) / self.total_orders
