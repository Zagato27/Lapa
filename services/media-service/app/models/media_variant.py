"""
Модель вариантов медиафайлов.

Используется `MediaProcessor` для хранения результатов преобразований.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class VariantType(str, enum.Enum):
    """Типы вариантов"""
    ORIGINAL = "original"        # Оригинальный файл
    THUMBNAIL = "thumbnail"      # Миниатюра
    OPTIMIZED = "optimized"      # Оптимизированная версия
    RESIZED = "resized"          # Измененный размер
    COMPRESSED = "compressed"    # Сжатая версия
    CONVERTED = "converted"      # Конвертированная версия
    WATERMARKED = "watermarked"  # С водяным знаком


class VariantStatus(str, enum.Enum):
    """Статусы вариантов"""
    CREATING = "creating"        # Создается
    READY = "ready"              # Готов
    FAILED = "failed"           # Ошибка создания
    DELETED = "deleted"         # Удален


class MediaVariant(Base):
    """Модель варианта медиафайла"""
    __tablename__ = "media_variants"

    id = Column(String, primary_key=True, index=True)
    media_file_id = Column(String, ForeignKey("media_files.id"), nullable=False, index=True)

    # Тип и статус
    variant_type = Column(Enum(VariantType), nullable=False)
    status = Column(Enum(VariantStatus), nullable=False, default=VariantStatus.CREATING)

    # Название и описание
    name = Column(String, nullable=True)                          # Название варианта
    description = Column(Text, nullable=True)                     # Описание

    # Файловая информация
    file_path = Column(String, nullable=True)                     # Путь к файлу
    file_url = Column(String, nullable=True)                      # URL файла
    file_size = Column(Integer, nullable=True)                    # Размер файла
    mime_type = Column(String, nullable=True)                     # MIME-тип
    file_hash = Column(String, nullable=True)                     # Хэш файла

    # Параметры обработки
    width = Column(Integer, nullable=True)                        # Ширина
    height = Column(Integer, nullable=True)                      # Высота
    quality = Column(Integer, nullable=True)                     # Качество (для изображений)
    format = Column(String, nullable=True)                       # Формат файла
    compression_level = Column(Integer, nullable=True)           # Уровень сжатия

    # Для видео
    bitrate = Column(Integer, nullable=True)                     # Битрейт
    frame_rate = Column(Float, nullable=True)                    # Частота кадров
    duration = Column(Float, nullable=True)                      # Длительность

    # Параметры обработки
    processing_params = Column(JSON, nullable=True)               # Параметры обработки
    processing_time = Column(Float, nullable=True)                # Время обработки в секундах
    processing_errors = Column(JSON, nullable=True)               # Ошибки обработки

    # Статистика использования
    view_count = Column(Integer, default=0)                       # Количество просмотров
    download_count = Column(Integer, default=0)                   # Количество скачиваний
    last_accessed_at = Column(DateTime, nullable=True)            # Последний доступ

    # Метаданные
    metadata = Column(JSON, nullable=True)                        # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)                # Время завершения обработки

    def __repr__(self):
        return f"<MediaVariant(id={self.id}, file={self.media_file_id}, type={self.variant_type.value}, status={self.status.value})>"

    @property
    def is_original(self) -> bool:
        """Проверка, является ли оригиналом"""
        return self.variant_type == VariantType.ORIGINAL

    @property
    def is_thumbnail(self) -> bool:
        """Проверка, является ли миниатюрой"""
        return self.variant_type == VariantType.THUMBNAIL

    @property
    def is_optimized(self) -> bool:
        """Проверка, является ли оптимизированной версией"""
        return self.variant_type == VariantType.OPTIMIZED

    @property
    def is_ready(self) -> bool:
        """Проверка, готов ли вариант"""
        return self.status == VariantStatus.READY

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка"""
        return self.status == VariantStatus.FAILED

    @property
    def file_size_mb(self) -> Optional[float]:
        """Размер файла в мегабайтах"""
        return self.file_size / (1024 * 1024) if self.file_size else None

    @property
    def aspect_ratio(self) -> Optional[float]:
        """Соотношение сторон"""
        if self.width and self.height:
            return self.width / self.height
        return None

    @property
    def processing_success_rate(self) -> Optional[float]:
        """Успешность обработки"""
        if not self.processing_time:
            return None
        # Здесь можно реализовать расчет на основе размера файла и времени обработки
        return 1.0  # Заглушка

    def mark_as_ready(self, file_path: str, file_url: str, file_size: int):
        """Отметить как готовый"""
        self.status = VariantStatus.READY
        self.file_path = file_path
        self.file_url = file_url
        self.file_size = file_size
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, error: str):
        """Отметить как неудачный"""
        self.status = VariantStatus.FAILED
        self.processing_errors = {"error": error, "timestamp": datetime.utcnow().isoformat()}
        self.updated_at = datetime.utcnow()

    def mark_as_deleted(self):
        """Отметить как удаленный"""
        self.status = VariantStatus.DELETED
        self.updated_at = datetime.utcnow()

    def record_view(self):
        """Запись просмотра"""
        self.view_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def record_download(self):
        """Запись скачивания"""
        self.download_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def set_dimensions(self, width: int, height: int):
        """Установка размеров"""
        self.width = width
        self.height = height
        self.updated_at = datetime.utcnow()

    def set_processing_time(self, time_seconds: float):
        """Установка времени обработки"""
        self.processing_time = time_seconds
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "media_file_id": self.media_file_id,
            "variant_type": self.variant_type.value,
            "status": self.status.value,
            "name": self.name,
            "description": self.description,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_hash": self.file_hash,
            "width": self.width,
            "height": self.height,
            "quality": self.quality,
            "format": self.format,
            "compression_level": self.compression_level,
            "bitrate": self.bitrate,
            "frame_rate": self.frame_rate,
            "duration": self.duration,
            "processing_params": self.processing_params,
            "processing_time": self.processing_time,
            "processing_errors": self.processing_errors,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @staticmethod
    def create_original(media_file_id: str, file_path: str, file_url: str, file_size: int) -> 'MediaVariant':
        """Создание варианта оригинального файла"""
        variant = MediaVariant(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id,
            variant_type=VariantType.ORIGINAL,
            status=VariantStatus.READY,
            name="Original",
            description="Original file",
            file_path=file_path,
            file_url=file_url,
            file_size=file_size
        )
        return variant

    @staticmethod
    def create_thumbnail(media_file_id: str, size: str) -> 'MediaVariant':
        """Создание варианта миниатюры"""
        variant = MediaVariant(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id,
            variant_type=VariantType.THUMBNAIL,
            status=VariantStatus.CREATING,
            name=f"Thumbnail {size}",
            description=f"Thumbnail variant {size}"
        )
        return variant

    @staticmethod
    def create_optimized(media_file_id: str, quality: int) -> 'MediaVariant':
        """Создание оптимизированного варианта"""
        variant = MediaVariant(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id,
            variant_type=VariantType.OPTIMIZED,
            status=VariantStatus.CREATING,
            name=f"Optimized {quality}%",
            description=f"Optimized variant with {quality}% quality",
            quality=quality
        )
        return variant

    @staticmethod
    def create_resized(media_file_id: str, width: int, height: int) -> 'MediaVariant':
        """Создание варианта с измененным размером"""
        variant = MediaVariant(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id,
            variant_type=VariantType.RESIZED,
            status=VariantStatus.CREATING,
            name=f"Resized {width}x{height}",
            description=f"Resized variant {width}x{height}",
            width=width,
            height=height
        )
        return variant
