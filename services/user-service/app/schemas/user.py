"""
Pydantic-схемы (v2) для пользователей.

Используются в `app.api.v1.users` и `app.api.v1.auth`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Создание пользователя"""
    email: EmailStr
    phone: str
    password: str
    first_name: str
    last_name: str
    role: str = "client"

    @field_validator('role')
    def validate_role(cls, v: str) -> str:
        if v not in ['client', 'walker']:
            raise ValueError('Role must be either "client" or "walker"')
        return v

    @field_validator('phone')
    def validate_phone(cls, v: str) -> str:
        # Простая валидация российского номера телефона
        if not v.startswith('+7') and not v.startswith('8'):
            raise ValueError('Phone must start with +7 or 8')
        # Удаляем все нецифровые символы кроме +
        clean_phone = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(clean_phone) < 11:
            raise ValueError('Phone number too short')
        return clean_phone


class UserUpdate(BaseModel):
    """Обновление пользователя"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notifications_enabled: Optional[bool] = None
    push_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    hourly_rate: Optional[float] = None


class UserProfile(BaseModel):
    """Профиль пользователя"""
    id: str
    email: EmailStr
    phone: str
    first_name: str
    last_name: str
    role: str
    avatar_url: Optional[str]
    bio: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    rating: float
    total_orders: int
    completed_orders: int
    is_active: bool
    is_verified: bool
    is_walker_verified: bool
    notifications_enabled: bool
    push_notifications: bool
    email_notifications: bool
    sms_notifications: bool
    experience_years: Optional[int]
    services_offered: Optional[List[str]]
    work_schedule: Optional[Dict[str, Any]]
    hourly_rate: Optional[float]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]


class UserResponse(BaseModel):
    """Ответ с данными пользователя"""
    user: UserProfile


class NearbyWalker(BaseModel):
    """Информация о выгульщике рядом"""
    id: str
    first_name: str
    last_name: str
    avatar_url: Optional[str]
    rating: float
    total_orders: int
    completed_orders: int
    latitude: Optional[float]
    longitude: Optional[float]
    distance: float  # в метрах
    hourly_rate: Optional[float]
    services_offered: Optional[List[str]]
    bio: Optional[str]


class NearbyWalkersResponse(BaseModel):
    """Ответ со списком выгульщиков рядом"""
    walkers: List[NearbyWalker]
    total: int


class WalkerVerificationRequest(BaseModel):
    """Запрос на верификацию выгульщика"""
    passport_number: str
    passport_series: str
    passport_issued_by: str
    passport_issued_date: str  # ISO format date string
    passport_expiry_date: str  # ISO format date string
    experience_years: int
    services_offered: List[str]
    work_schedule: Dict[str, Any]


class WalkerVerificationResponse(BaseModel):
    """Ответ на верификацию выгульщика"""
    verification_id: str
    status: str
    message: str
    submitted_at: datetime
