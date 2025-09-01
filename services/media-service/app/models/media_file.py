"""
Модель медиафайлов.

Используется:
- `MediaService` для CRUD и бизнес-логики
- Эндпоинты `app.api.v1.files`
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class MediaType(str, enum.Enum):
    """Типы медиафайлов"""
    IMAGE = "image"          # Изображение
    VIDEO = "video"          # Видео
    AUDIO = "audio"          # Аудио
    DOCUMENT = "document"    # Документ
    ARCHIVE = "archive"      # Архив


class MediaStatus(str, enum.Enum):
    """Статусы медиафайлов"""
    UPLOADING = "uploading"    # Загружается
    UPLOADED = "uploaded"      # Загружен
    PROCESSING = "processing"  # Обрабатывается
    READY = "ready"           # Готов
    FAILED = "failed"         # Ошибка
    DELETED = "deleted"       # Удален


class StorageBackend(str, enum.Enum):
    """Типы хранилищ"""
    LOCAL = "local"          # Локальное хранилище
    S3 = "s3"               # Amazon S3
    CLOUDINARY = "cloudinary"  # Cloudinary
    IMGUR = "imgur"         # Imgur


class MediaFile(Base):
    """Модель медиафайла"""
    __tablename__ = "media_files"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)                  # Оригинальное имя файла
    file_path = Column(String, nullable=True)                  # Путь к файлу
    file_url = Column(String, nullable=True)                   # URL файла
    public_url = Column(String, nullable=True)                 # Публичный URL

    # Тип и статус
    media_type = Column(Enum(MediaType), nullable=False)
    status = Column(Enum(MediaStatus), nullable=False, default=MediaStatus.UPLOADING)
    storage_backend = Column(Enum(StorageBackend), nullable=False, default=StorageBackend.LOCAL)

    # Владелец и доступ
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=False)                 # Публичный доступ
    album_id = Column(String, ForeignKey("media_albums.id"), nullable=True, index=True)

    # Размеры и метаданные
    file_size = Column(Integer, nullable=False)                # Размер в байтах
    mime_type = Column(String, nullable=True)                  # MIME-тип
    width = Column(Integer, nullable=True)                     # Ширина (для изображений/видео)
    height = Column(Integer, nullable=True)                    # Высота (для изображений/видео)
    duration = Column(Float, nullable=True)                    # Длительность (для видео/аудио)
    bitrate = Column(Integer, nullable=True)                   # Битрейт

    # Обработка
    processed_at = Column(DateTime, nullable=True)
    processing_errors = Column(JSON, nullable=True)            # Ошибки обработки

    # Миниатюры
    thumbnail_path = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    thumbnail_width = Column(Integer, nullable=True)
    thumbnail_height = Column(Integer, nullable=True)

    # Оптимизация
    optimized_path = Column(String, nullable=True)
    optimized_url = Column(String, nullable=True)
    optimized_size = Column(Integer, nullable=True)
    original_size = Column(Integer, nullable=True)

    # Безопасность
    file_hash = Column(String, nullable=True)                  # Хэш файла
    is_encrypted = Column(Boolean, default=False)
    encryption_key = Column(String, nullable=True)

    # Метаданные
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)                         # Теги
    colors = Column(JSON, nullable=True)                       # Основные цвета (для изображений)
    location = Column(JSON, nullable=True)                     # Геолокация
    camera_info = Column(JSON, nullable=True)                  # Информация о камере

    # Статистика
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)               # Срок действия
    last_accessed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename={self.filename}, type={self.media_type.value}, status={self.status.value})>"

    @property
    def is_image(self) -> bool:
        """Проверка, является ли изображением"""
        return self.media_type == MediaType.IMAGE

    @property
    def is_video(self) -> bool:
        """Проверка, является ли видео"""
        return self.media_type == MediaType.VIDEO

    @property
    def is_audio(self) -> bool:
        """Проверка, является ли аудио"""
        return self.media_type == MediaType.AUDIO

    @property
    def is_ready(self) -> bool:
        """Проверка, готов ли файл"""
        return self.status == MediaStatus.READY

    @property
    def is_expired(self) -> bool:
        """Проверка, истек ли срок действия"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def file_size_mb(self) -> float:
        """Размер файла в мегабайтах"""
        return self.file_size / (1024 * 1024) if self.file_size else 0

    @property
    def compression_ratio(self) -> Optional[float]:
        """Коэффициент сжатия"""
        if self.original_size and self.optimized_size:
            return self.original_size / self.optimized_size
        return None

    @property
    def aspect_ratio(self) -> Optional[float]:
        """Соотношение сторон"""
        if self.width and self.height:
            return self.width / self.height
        return None

    @property
    def has_thumbnail(self) -> bool:
        """Проверка наличия миниатюры"""
        return self.thumbnail_path is not None or self.thumbnail_url is not None

    def mark_as_uploaded(self, file_path: str, file_url: str):
        """Отметить как загруженное"""
        self.status = MediaStatus.UPLOADED
        self.file_path = file_path
        self.file_url = file_url
        self.updated_at = datetime.utcnow()

    def mark_as_processing(self):
        """Отметить как обрабатываемое"""
        self.status = MediaStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_as_ready(self, processed_path: Optional[str] = None, processed_url: Optional[str] = None):
        """Отметить как готовое"""
        self.status = MediaStatus.READY
        self.processed_at = datetime.utcnow()
        if processed_path:
            self.optimized_path = processed_path
        if processed_url:
            self.optimized_url = processed_url
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, error: str):
        """Отметить как неудачное"""
        self.status = MediaStatus.FAILED
        self.processing_errors = {"error": error, "timestamp": datetime.utcnow().isoformat()}
        self.updated_at = datetime.utcnow()

    def mark_as_deleted(self):
        """Отметить как удаленное"""
        self.status = MediaStatus.DELETED
        self.updated_at = datetime.utcnow()

    def increment_view_count(self):
        """Увеличить счетчик просмотров"""
        self.view_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_download_count(self):
        """Увеличить счетчик скачиваний"""
        self.download_count += 1
        self.updated_at = datetime.utcnow()

    def set_dimensions(self, width: int, height: int):
        """Установить размеры"""
        self.width = width
        self.height = height
        self.updated_at = datetime.utcnow()

    def set_duration(self, duration: float):
        """Установить длительность"""
        self.duration = duration
        self.updated_at = datetime.utcnow()

    def set_thumbnail(self, thumbnail_path: str, thumbnail_url: str, width: int, height: int):
        """Установить миниатюру"""
        self.thumbnail_path = thumbnail_path
        self.thumbnail_url = thumbnail_url
        self.thumbnail_width = width
        self.thumbnail_height = height
        self.updated_at = datetime.utcnow()

    def set_optimization(self, optimized_path: str, optimized_url: str, optimized_size: int):
        """Установить оптимизированную версию"""
        self.optimized_path = optimized_path
        self.optimized_url = optimized_url
        self.optimized_size = optimized_size
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str):
        """Добавить тег"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
        self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str):
        """Удалить тег"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "public_url": self.public_url,
            "media_type": self.media_type.value,
            "status": self.status.value,
            "storage_backend": self.storage_backend.value,
            "owner_id": self.owner_id,
            "is_public": self.is_public,
            "album_id": self.album_id,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "bitrate": self.bitrate,
            "thumbnail_path": self.thumbnail_path,
            "thumbnail_url": self.thumbnail_url,
            "optimized_path": self.optimized_path,
            "optimized_url": self.optimized_url,
            "file_hash": self.file_hash,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "colors": self.colors,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }

    def to_public_dict(self) -> dict:
        """Преобразование в публичный словарь"""
        data = self.to_dict()
        # Убираем чувствительную информацию
        sensitive_fields = ['file_path', 'encryption_key', 'processing_errors']
        for field in sensitive_fields:
            data.pop(field, None)
        return data

    @staticmethod
    def create_image(owner_id: str, filename: str, file_size: int, width: Optional[int] = None, height: Optional[int] = None) -> 'MediaFile':
        """Создание записи изображения"""
        media_file = MediaFile(
            id=str(uuid.uuid4()),
            filename=filename,
            media_type=MediaType.IMAGE,
            owner_id=owner_id,
            file_size=file_size,
            width=width,
            height=height,
            original_size=file_size
        )
        return media_file

    @staticmethod
    def create_video(owner_id: str, filename: str, file_size: int, duration: Optional[float] = None) -> 'MediaFile':
        """Создание записи видео"""
        media_file = MediaFile(
            id=str(uuid.uuid4()),
            filename=filename,
            media_type=MediaType.VIDEO,
            owner_id=owner_id,
            file_size=file_size,
            duration=duration,
            original_size=file_size
        )
        return media_file

    @staticmethod
    def create_audio(owner_id: str, filename: str, file_size: int, duration: Optional[float] = None) -> 'MediaFile':
        """Создание записи аудио"""
        media_file = MediaFile(
            id=str(uuid.uuid4()),
            filename=filename,
            media_type=MediaType.AUDIO,
            owner_id=owner_id,
            file_size=file_size,
            duration=duration,
            original_size=file_size
        )
        return media_file
