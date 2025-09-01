"""
Pydantic-схемы (v2) для медиафайлов.

Используются роутами `app.api.v1.files` и сервисом `MediaService`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class MediaType(str, enum.Enum):
    """Типы медиафайлов"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"


class MediaStatus(str, enum.Enum):
    """Статусы медиафайлов"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class StorageBackend(str, enum.Enum):
    """Типы хранилищ"""
    LOCAL = "local"
    S3 = "s3"
    CLOUDINARY = "cloudinary"
    IMGUR = "imgur"


class MediaFileCreate(BaseModel):
    """Создание медиафайла"""
    filename: str
    media_type: MediaType
    album_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = False
    tags: Optional[List[str]] = None

    @field_validator('filename')
    def validate_filename(cls, v: str) -> str:
        from app.config import settings
        if len(v) > 255:
            raise ValueError('Filename too long')
        return v

    @field_validator('tags')
    def validate_tags(cls, v: Optional[List[str]]):
        if v and len(v) > 20:
            raise ValueError('Too many tags')
        return v


class MediaFileUpdate(BaseModel):
    """Обновление медиафайла"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    album_id: Optional[str] = None
    tags: Optional[List[str]] = None


class MediaFileResponse(BaseModel):
    """Ответ с данными медиафайла"""
    id: str
    filename: str
    file_path: Optional[str]
    file_url: Optional[str]
    public_url: Optional[str]
    media_type: MediaType
    status: MediaStatus
    storage_backend: StorageBackend
    owner_id: str
    is_public: bool
    album_id: Optional[str]
    file_size: int
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration: Optional[float]
    processed_at: Optional[datetime]
    thumbnail_path: Optional[str]
    thumbnail_url: Optional[str]
    optimized_path: Optional[str]
    optimized_url: Optional[str]
    file_hash: Optional[str]
    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    colors: Optional[List[Dict[str, Any]]]
    location: Optional[Dict[str, Any]]
    view_count: int
    download_count: int
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed_at: Optional[datetime]

    # Вычисляемые поля
    is_image: Optional[bool] = None
    is_video: Optional[bool] = None
    is_audio: Optional[bool] = None
    is_ready: Optional[bool] = None
    is_expired: Optional[bool] = None
    file_size_mb: Optional[float] = None
    compression_ratio: Optional[float] = None
    aspect_ratio: Optional[float] = None
    has_thumbnail: Optional[bool] = None


class MediaFilesListResponse(BaseModel):
    """Ответ со списком медиафайлов"""
    files: List[MediaFileResponse]
    total: int
    page: int
    limit: int
    pages: int


class MediaFileUploadResponse(BaseModel):
    """Ответ на загрузку файла"""
    file_id: str
    upload_url: str
    status: str
    message: str


class MediaFileVariantResponse(BaseModel):
    """Ответ с вариантом файла"""
    id: str
    variant_type: str
    status: str
    file_url: Optional[str]
    file_size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    quality: Optional[int]
    format: Optional[str]


class MediaFileSearchRequest(BaseModel):
    """Запрос на поиск файлов"""
    query: str
    media_type: Optional[MediaType] = None
    album_id: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50


class MediaFileSearchResponse(BaseModel):
    """Ответ с результатами поиска"""
    files: List[MediaFileResponse]
    total: int
    query: str
    search_time: float


class MediaFileBatchOperationRequest(BaseModel):
    """Запрос на пакетную операцию с файлами"""
    file_ids: List[str]
    operation: str  # delete, move, tag, etc.
    parameters: Optional[Dict[str, Any]] = None


class MediaFileBatchOperationResponse(BaseModel):
    """Ответ на пакетную операцию"""
    operation: str
    success_count: int
    failed_count: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class MediaFileStatisticsResponse(BaseModel):
    """Ответ со статистикой файлов"""
    total_files: int
    total_size: int
    total_size_mb: float
    total_size_gb: float
    files_by_type: Dict[str, int]
    files_by_status: Dict[str, int]
    storage_usage: Dict[str, Any]
    period_start: datetime
    period_end: datetime


class MediaFileOptimizeRequest(BaseModel):
    """Запрос на оптимизацию файла"""
    quality: Optional[int] = None
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    format: Optional[str] = None
    compression_level: Optional[int] = None


class MediaFileConvertRequest(BaseModel):
    """Запрос на конвертацию файла"""
    target_format: str
    quality: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class MediaFileResizeRequest(BaseModel):
    """Запрос на изменение размера"""
    width: Optional[int] = None
    height: Optional[int] = None
    maintain_aspect_ratio: bool = True
    upscale: bool = False


class MediaFileWatermarkRequest(BaseModel):
    """Запрос на добавление водяного знака"""
    watermark_type: str = "image"  # image, text
    watermark_image: Optional[str] = None
    watermark_text: Optional[str] = None
    position: str = "bottom_right"
    opacity: float = 0.3
    scale: float = 1.0
