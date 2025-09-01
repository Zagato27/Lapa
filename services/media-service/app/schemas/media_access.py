"""
Pydantic-схемы (v2) для доступа к медиафайлам.

Используются роутами `app.api.v1.access` и сервисом `MediaService`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import enum


class AccessType(str, enum.Enum):
    """Типы доступа"""
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"


class AccessLevel(str, enum.Enum):
    """Уровни доступа"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class AccessStatus(str, enum.Enum):
    """Статусы доступа"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class MediaAccessCreate(BaseModel):
    """Создание доступа к файлу"""
    access_type: AccessType = AccessType.VIEW
    access_level: AccessLevel = AccessLevel.READ
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    max_views: Optional[int] = None
    max_downloads: Optional[int] = None
    expires_at: Optional[datetime] = None
    password: Optional[str] = None


class MediaAccessUpdate(BaseModel):
    """Обновление доступа к файлу"""
    access_type: Optional[AccessType] = None
    access_level: Optional[AccessLevel] = None
    max_views: Optional[int] = None
    max_downloads: Optional[int] = None
    expires_at: Optional[datetime] = None
    password: Optional[str] = None


class MediaAccessResponse(BaseModel):
    """Ответ с данными доступа"""
    id: str
    media_file_id: str
    access_type: AccessType
    access_level: AccessLevel
    status: AccessStatus
    user_id: Optional[str]
    group_id: Optional[str]
    token: Optional[str]
    max_views: Optional[int]
    max_downloads: Optional[int]
    expires_at: Optional[datetime]
    view_count: int
    download_count: int
    last_access_at: Optional[datetime]
    granted_by: str
    granted_at: datetime
    description: Optional[str]

    # Вычисляемые поля
    is_active: Optional[bool] = None
    is_expired: Optional[bool] = None
    is_revoked: Optional[bool] = None
    is_pending: Optional[bool] = None
    can_view: Optional[bool] = None
    can_download: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_share: Optional[bool] = None
    is_public_link: Optional[bool] = None
    has_password: Optional[bool] = None
    views_left: Optional[int] = None
    downloads_left: Optional[int] = None


class MediaAccessGrantRequest(BaseModel):
    """Запрос на предоставление доступа"""
    media_file_id: str
    access_type: AccessType = AccessType.VIEW
    access_level: AccessLevel = AccessLevel.READ
    recipient_type: str = "user"  # user, group, public
    recipient_id: Optional[str] = None  # ID пользователя или группы
    max_views: Optional[int] = None
    max_downloads: Optional[int] = None
    expires_at: Optional[datetime] = None
    password: Optional[str] = None
    description: Optional[str] = None


class MediaAccessGrantResponse(BaseModel):
    """Ответ на предоставление доступа"""
    access_id: str
    access_url: Optional[str]
    token: Optional[str]
    expires_at: Optional[datetime]
    password_protected: bool


class MediaAccessRevokeRequest(BaseModel):
    """Запрос на отзыв доступа"""
    access_id: str
    reason: Optional[str] = None


class MediaAccessBulkGrantRequest(BaseModel):
    """Запрос на массовое предоставление доступа"""
    media_file_ids: List[str]
    access_type: AccessType = AccessType.VIEW
    access_level: AccessLevel = AccessLevel.READ
    recipient_type: str = "user"
    recipient_id: Optional[str] = None
    max_views: Optional[int] = None
    max_downloads: Optional[int] = None
    expires_at: Optional[datetime] = None


class MediaAccessBulkGrantResponse(BaseModel):
    """Ответ на массовое предоставление доступа"""
    granted_count: int
    failed_count: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class MediaAccessStatisticsResponse(BaseModel):
    """Ответ со статистикой доступа"""
    media_file_id: str
    total_access_rules: int
    active_access_rules: int
    expired_access_rules: int
    revoked_access_rules: int
    total_views: int
    total_downloads: int
    unique_viewers: int
    top_viewers: List[Dict[str, Any]]
    access_by_type: Dict[str, int]
    period_start: datetime
    period_end: datetime


class MediaAccessLogResponse(BaseModel):
    """Ответ с логом доступа"""
    media_file_id: str
    access_logs: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    pages: int


class MediaAccessCheckRequest(BaseModel):
    """Запрос на проверку доступа"""
    media_file_id: str
    access_token: Optional[str] = None
    password: Optional[str] = None


class MediaAccessCheckResponse(BaseModel):
    """Ответ на проверку доступа"""
    has_access: bool
    access_type: Optional[AccessType]
    access_level: Optional[AccessLevel]
    can_view: bool
    can_download: bool
    can_edit: bool
    can_delete: bool
    can_share: bool
    views_left: Optional[int]
    downloads_left: Optional[int]
    expires_at: Optional[datetime]
