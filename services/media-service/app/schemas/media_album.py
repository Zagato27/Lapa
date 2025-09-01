"""
Pydantic-схемы (v2) для альбомов медиафайлов.

Используются роутами `app.api.v1.albums` и сервисом `MediaService`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class AlbumType(str, enum.Enum):
    """Типы альбомов"""
    USER = "user"
    PET = "pet"
    ORDER = "order"
    SYSTEM = "system"
    SHARED = "shared"


class AlbumStatus(str, enum.Enum):
    """Статусы альбомов"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PRIVATE = "private"


class MediaAlbumCreate(BaseModel):
    """Создание альбома"""
    name: str
    album_type: AlbumType = AlbumType.USER
    description: Optional[str] = None
    pet_id: Optional[str] = None
    order_id: Optional[str] = None
    is_public: bool = False
    is_shared: bool = False
    max_files: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    allowed_types: Optional[List[str]] = None

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError('Album name too long')
        return v

    @field_validator('max_files')
    def validate_max_files(cls, v: int | None):
        if v and v > 10000:
            raise ValueError('Max files limit too high')
        return v


class MediaAlbumUpdate(BaseModel):
    """Обновление альбома"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_shared: Optional[bool] = None
    allow_upload: Optional[bool] = None
    allow_download: Optional[bool] = None
    max_files: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    allowed_types: Optional[List[str]] = None


class MediaAlbumResponse(BaseModel):
    """Ответ с данными альбома"""
    id: str
    name: str
    description: Optional[str]
    album_type: AlbumType
    status: AlbumStatus
    owner_id: str
    pet_id: Optional[str]
    order_id: Optional[str]
    is_public: bool
    is_shared: bool
    allow_upload: bool
    allow_download: bool
    max_files: Optional[int]
    max_file_size_mb: Optional[int]
    allowed_types: Optional[List[str]]
    cover_file_id: Optional[str]
    total_files: int
    total_size: int
    image_count: int
    video_count: int
    audio_count: int
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime]

    # Вычисляемые поля
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_deleted: Optional[bool] = None
    total_size_mb: Optional[float] = None
    total_size_gb: Optional[float] = None
    can_upload: Optional[bool] = None
    can_download: Optional[bool] = None
    has_space: Optional[bool] = None


class MediaAlbumsListResponse(BaseModel):
    """Ответ со списком альбомов"""
    albums: List[MediaAlbumResponse]
    total: int
    page: int
    limit: int
    pages: int


class AlbumFileAddRequest(BaseModel):
    """Запрос на добавление файла в альбом"""
    file_id: str


class AlbumFileRemoveRequest(BaseModel):
    """Запрос на удаление файла из альбома"""
    file_id: str


class AlbumShareRequest(BaseModel):
    """Запрос на публикацию альбома"""
    share_type: str = "public"  # public, private, password
    password: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_views: Optional[int] = None


class AlbumShareResponse(BaseModel):
    """Ответ на публикацию альбома"""
    share_url: str
    share_type: str
    expires_at: Optional[datetime]
    password_protected: bool


class AlbumStatisticsResponse(BaseModel):
    """Ответ со статистикой альбома"""
    album_id: str
    total_files: int
    total_size: int
    total_size_mb: float
    files_by_type: Dict[str, int]
    upload_activity: List[Dict[str, Any]]
    top_tags: List[Dict[str, Any]]
    created_at: datetime


class AlbumExportRequest(BaseModel):
    """Запрос на экспорт альбома"""
    format: str = "zip"  # zip, tar, json
    include_metadata: bool = True
    include_thumbnails: bool = False
    quality: Optional[int] = None


class AlbumImportRequest(BaseModel):
    """Запрос на импорт альбома"""
    source_url: str
    import_type: str = "url"  # url, file, folder
    create_album: bool = True
    album_name: Optional[str] = None


class AlbumMoveFilesRequest(BaseModel):
    """Запрос на перемещение файлов между альбомами"""
    file_ids: List[str]
    target_album_id: str


class AlbumBulkTagRequest(BaseModel):
    """Запрос на массовое добавление тегов"""
    file_ids: Optional[List[str]] = None  # Если None - все файлы альбома
    tags: List[str]
    action: str = "add"  # add, remove, replace


class AlbumCleanupRequest(BaseModel):
    """Запрос на очистку альбома"""
    cleanup_type: str = "orphaned"  # orphaned, duplicates, old, size
    max_age_days: Optional[int] = None
    min_size_mb: Optional[float] = None
    confirm: bool = False
