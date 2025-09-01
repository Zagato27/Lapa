"""
Pydantic-схемы (v2) для питомцев.

Используются в эндпоинтах `app.api.v1.pets`, `photos`, `medical` и сервисах.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator


class PetCreate(BaseModel):
    """Создание питомца"""
    name: str
    breed: str
    date_of_birth: Optional[datetime] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    gender: str
    color: Optional[str] = None
    weight_kg: Optional[float] = None
    size: Optional[str] = None
    energy_level: Optional[str] = None
    friendliness: Optional[str] = None

    # Здоровье
    is_vaccinated: bool = False
    is_neutered: bool = False
    has_allergies: bool = False
    allergies_description: Optional[str] = None
    special_needs: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = None
    medical_conditions: Optional[List[Dict[str, Any]]] = None

    # Поведение
    is_friendly_with_dogs: Optional[bool] = None
    is_friendly_with_cats: Optional[bool] = None
    is_friendly_with_children: Optional[bool] = None
    behavioral_notes: Optional[str] = None

    # Выгул и уход
    walking_frequency: Optional[str] = None
    walking_duration_minutes: Optional[int] = None
    feeding_schedule: Optional[Dict[str, Any]] = None
    favorite_activities: Optional[List[str]] = None
    walking_notes: Optional[str] = None

    # Экстренная информация
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    veterinarian_name: Optional[str] = None
    veterinarian_phone: Optional[str] = None
    veterinarian_address: Optional[str] = None

    @field_validator('gender')
    def validate_gender(cls, v: str) -> str:
        if v not in ['male', 'female']:
            raise ValueError('Gender must be either "male" or "female"')
        return v

    @field_validator('breed')
    def validate_breed(cls, v: str) -> str:
        from app.config import settings
        # Нормализация ввода и синонимы → канонические названия
        raw = (v or '').strip()
        synonyms_map = {
            'хаски': 'Сибирский Хаски',
            'шарпей': 'Шар Пей',
            'далматинец': 'Далматин',
        }
        if raw.lower() in synonyms_map:
            raw = synonyms_map[raw.lower()]

        # Поиск без учета регистра для совпадений из settings.supported_breeds
        supported_lower = {b.lower(): b for b in settings.supported_breeds}
        canonical = supported_lower.get(raw.lower(), raw)

        if canonical not in settings.supported_breeds:
            raise ValueError(f'Breed must be one of: {", ".join(settings.supported_breeds)}')
        return canonical

    @field_validator('size')
    def validate_size(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ['small', 'medium', 'large', 'extra_large']:
            raise ValueError('Size must be one of: small, medium, large, extra_large')
        return v


class PetUpdate(BaseModel):
    """Обновление питомца"""
    name: Optional[str] = None
    breed: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    gender: Optional[str] = None
    color: Optional[str] = None
    weight_kg: Optional[float] = None
    size: Optional[str] = None
    energy_level: Optional[str] = None
    friendliness: Optional[str] = None

    # Здоровье
    is_vaccinated: Optional[bool] = None
    is_neutered: Optional[bool] = None
    has_allergies: Optional[bool] = None
    allergies_description: Optional[str] = None
    special_needs: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = None
    medical_conditions: Optional[List[Dict[str, Any]]] = None

    # Поведение
    is_friendly_with_dogs: Optional[bool] = None
    is_friendly_with_cats: Optional[bool] = None
    is_friendly_with_children: Optional[bool] = None
    behavioral_notes: Optional[str] = None

    # Выгул и уход
    walking_frequency: Optional[str] = None
    walking_duration_minutes: Optional[int] = None
    feeding_schedule: Optional[Dict[str, Any]] = None
    favorite_activities: Optional[List[str]] = None
    walking_notes: Optional[str] = None

    # Экстренная информация
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    veterinarian_name: Optional[str] = None
    veterinarian_phone: Optional[str] = None
    veterinarian_address: Optional[str] = None


class PetProfile(BaseModel):
    """Профиль питомца"""
    id: str
    user_id: str
    name: str
    breed: str
    date_of_birth: Optional[datetime]
    age_years: Optional[int]
    age_months: Optional[int]
    gender: str
    color: Optional[str]
    weight_kg: Optional[float]
    size: Optional[str]
    energy_level: Optional[str]
    friendliness: Optional[str]

    # Здоровье
    is_vaccinated: bool
    is_neutered: bool
    has_allergies: bool
    allergies_description: Optional[str]
    special_needs: Optional[str]
    medications: Optional[List[Dict[str, Any]]]
    medical_conditions: Optional[List[Dict[str, Any]]]

    # Поведение
    is_friendly_with_dogs: Optional[bool]
    is_friendly_with_cats: Optional[bool]
    is_friendly_with_children: Optional[bool]
    behavioral_notes: Optional[str]

    # Выгул и уход
    walking_frequency: Optional[str]
    walking_duration_minutes: Optional[int]
    feeding_schedule: Optional[Dict[str, Any]]
    favorite_activities: Optional[List[str]]
    walking_notes: Optional[str]

    # Экстренная информация
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    veterinarian_name: Optional[str]
    veterinarian_phone: Optional[str]
    veterinarian_address: Optional[str]

    # Фото
    avatar_url: Optional[str]
    photos_count: int

    # Метаданные
    created_at: datetime
    updated_at: datetime

    # Вычисляемые поля
    age_string: Optional[str] = None
    size_category: Optional[str] = None


class PetResponse(BaseModel):
    """Ответ с данными питомца"""
    pet: PetProfile


class PetPhotoCreate(BaseModel):
    """Создание фотографии питомца"""
    filename: str
    description: Optional[str] = None
    photo_type: str = "general"
    tags: Optional[List[str]] = None


class PetPhotoResponse(BaseModel):
    """Ответ с фотографией питомца"""
    id: str
    pet_id: str
    filename: str
    original_filename: str
    file_url: str
    file_size: int
    mime_type: str
    width: Optional[int]
    height: Optional[int]
    thumbnail_url: Optional[str]
    photo_type: str
    description: Optional[str]
    tags: Optional[List[str]]
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    # Вычисляемые поля
    file_size_mb: Optional[float] = None
    is_image: Optional[bool] = None
    is_avatar: Optional[bool] = None


class PetMedicalCreate(BaseModel):
    """Создание медицинской записи"""
    record_type: str
    title: str
    description: Optional[str] = None

    # Медицинские детали
    medication_name: Optional[str] = None
    medication_dosage: Optional[str] = None
    medication_frequency: Optional[str] = None

    # Ветеринарная информация
    veterinarian_name: Optional[str] = None
    veterinarian_phone: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None

    # Даты
    event_date: datetime
    next_visit_date: Optional[datetime] = None
    vaccination_due_date: Optional[datetime] = None

    # Стоимость
    cost: Optional[float] = None

    # Результаты и рекомендации
    results: Optional[str] = None
    recommendations: Optional[str] = None

    @field_validator('record_type')
    def validate_record_type(cls, v: str) -> str:
        valid_types = ['vaccination', 'medication', 'illness', 'surgery', 'checkup', 'other']
        if v not in valid_types:
            raise ValueError(f'Record type must be one of: {", ".join(valid_types)}')
        return v


class PetMedicalUpdate(BaseModel):
    """Обновление медицинской записи"""
    record_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    medication_name: Optional[str] = None
    medication_dosage: Optional[str] = None
    medication_frequency: Optional[str] = None
    veterinarian_name: Optional[str] = None
    veterinarian_phone: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    event_date: Optional[datetime] = None
    next_visit_date: Optional[datetime] = None
    vaccination_due_date: Optional[datetime] = None
    cost: Optional[float] = None
    results: Optional[str] = None
    recommendations: Optional[str] = None
    is_completed: Optional[bool] = None
    requires_follow_up: Optional[bool] = None


class PetMedicalResponse(BaseModel):
    """Ответ с медицинской записью"""
    id: str
    pet_id: str
    record_type: str
    title: str
    description: Optional[str]
    medication_name: Optional[str]
    medication_dosage: Optional[str]
    medication_frequency: Optional[str]
    veterinarian_name: Optional[str]
    veterinarian_phone: Optional[str]
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    event_date: datetime
    next_visit_date: Optional[datetime]
    vaccination_due_date: Optional[datetime]
    cost: Optional[float]
    results: Optional[str]
    recommendations: Optional[str]
    is_completed: bool
    requires_follow_up: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    # Вычисляемые поля
    is_vaccination: Optional[bool] = None
    is_medication: Optional[bool] = None
    is_past_due: Optional[bool] = None
    days_until_next_visit: Optional[int] = None
    days_until_vaccination: Optional[int] = None


class PetsListResponse(BaseModel):
    """Ответ со списком питомцев"""
    pets: List[PetProfile]
    total: int
    page: int
    limit: int
    pages: int
