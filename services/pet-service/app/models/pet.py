"""
Модель питомца.

Используется:
- `PetService` для CRUD операций
- Эндпоинты `app.api.v1.pets`
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, JSON
from sqlalchemy.sql import func

from .base import Base


class Pet(Base):
    """Модель питомца"""
    __tablename__ = "pets"

    id = Column(String, primary_key=True, index=True)
    # Внешние идентификаторы из других сервисов храним как строки без FK
    user_id = Column(String, nullable=False, index=True)

    # Основная информация
    name = Column(String, nullable=False)
    breed = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    age_years = Column(Integer, nullable=True)
    age_months = Column(Integer, nullable=True)
    gender = Column(String, nullable=False)  # male, female
    color = Column(String, nullable=True)
    weight_kg = Column(Float, nullable=True)

    # Характеристики
    size = Column(String, nullable=True)  # small, medium, large, extra_large
    energy_level = Column(String, nullable=True)  # low, medium, high
    friendliness = Column(String, nullable=True)  # low, medium, high

    # Здоровье и особенности
    is_vaccinated = Column(Boolean, default=False)
    is_neutered = Column(Boolean, default=False)
    has_allergies = Column(Boolean, default=False)
    allergies_description = Column(Text, nullable=True)
    special_needs = Column(Text, nullable=True)
    medications = Column(JSON, nullable=True)  # JSON array of medications
    medical_conditions = Column(JSON, nullable=True)  # JSON array of conditions

    # Поведение
    is_friendly_with_dogs = Column(Boolean, nullable=True)
    is_friendly_with_cats = Column(Boolean, nullable=True)
    is_friendly_with_children = Column(Boolean, nullable=True)
    behavioral_notes = Column(Text, nullable=True)

    # Выгул и уход
    walking_frequency = Column(String, nullable=True)  # daily, twice_daily, etc.
    walking_duration_minutes = Column(Integer, nullable=True)
    feeding_schedule = Column(JSON, nullable=True)  # JSON object with feeding times
    favorite_activities = Column(JSON, nullable=True)  # JSON array of activities
    walking_notes = Column(Text, nullable=True)

    # Экстренная информация
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    veterinarian_name = Column(String, nullable=True)
    veterinarian_phone = Column(String, nullable=True)
    veterinarian_address = Column(Text, nullable=True)

    # Фото
    avatar_url = Column(String, nullable=True)
    photos_count = Column(Integer, default=0)

    # Статус
    is_active = Column(Boolean, default=True)

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Pet(id={self.id}, name={self.name}, breed={self.breed})>"

    @property
    def age_string(self) -> str:
        """Возраст питомца в читаемом виде"""
        if self.age_years and self.age_years > 0:
            if self.age_months and self.age_months > 0:
                return f"{self.age_years} лет {self.age_months} месяцев"
            return f"{self.age_years} лет"
        elif self.age_months and self.age_months > 0:
            return f"{self.age_months} месяцев"
        elif self.date_of_birth:
            # Расчет возраста по дате рождения
            today = datetime.utcnow()
            age_years = today.year - self.date_of_birth.year
            age_months = today.month - self.date_of_birth.month
            if age_months < 0:
                age_years -= 1
                age_months += 12
            if age_years > 0:
                return f"{age_years} лет {age_months} месяцев"
            return f"{age_months} месяцев"
        return "Не указан"

    @property
    def size_category(self) -> str:
        """Категория размера питомца"""
        if self.weight_kg:
            if self.weight_kg < 10:
                return "small"
            elif self.weight_kg < 25:
                return "medium"
            elif self.weight_kg < 40:
                return "large"
            else:
                return "extra_large"
        return self.size or "medium"

    def calculate_age(self) -> None:
        """Расчет возраста на основе даты рождения"""
        if self.date_of_birth:
            today = datetime.utcnow()
            self.age_years = today.year - self.date_of_birth.year
            self.age_months = today.month - self.date_of_birth.month

            if self.age_months < 0:
                self.age_years -= 1
                self.age_months += 12
