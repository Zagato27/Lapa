"""
Модель вложений к сообщениям.

Используется `FileManager`, `MessageService` и роутами файлов/сообщений.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class AttachmentType(str, enum.Enum):
    """Типы вложений"""
    IMAGE = "image"          # Изображение
    VIDEO = "video"          # Видео
    AUDIO = "audio"          # Аудио
    DOCUMENT = "document"    # Документ
    VOICE = "voice"          # Голосовое сообщение
    LOCATION = "location"    # Геолокация
    CONTACT = "contact"      # Контакт


class AttachmentStatus(str, enum.Enum):
    """Статусы вложений"""
    UPLOADING = "uploading"    # Загружается
    UPLOADED = "uploaded"      # Загружено
    PROCESSING = "processing"  # Обрабатывается
    READY = "ready"           # Готово
    FAILED = "failed"         # Ошибка
    DELETED = "deleted"       # Удалено


class MessageAttachment(Base):
    """Модель вложения к сообщению"""
    __tablename__ = "message_attachments"

    id = Column(String, primary_key=True, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)
    uploader_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Тип и статус
    attachment_type = Column(Enum(AttachmentType), nullable=False)
    status = Column(Enum(AttachmentStatus), nullable=False, default=AttachmentStatus.UPLOADING)

    # Файловая информация
    original_filename = Column(String, nullable=False)    # Оригинальное имя файла
    file_path = Column(String, nullable=True)             # Путь к файлу
    file_url = Column(String, nullable=True)              # URL файла
    thumbnail_path = Column(String, nullable=True)        # Путь к миниатюре
    thumbnail_url = Column(String, nullable=True)         # URL миниатюры

    # Метаданные файла
    file_size = Column(Integer, nullable=False)           # Размер файла в байтах
    mime_type = Column(String, nullable=True)             # MIME-тип
    file_hash = Column(String, nullable=True)             # Хэш файла для проверки

    # Изображения и видео
    width = Column(Integer, nullable=True)                # Ширина (для изображений/видео)
    height = Column(Integer, nullable=True)               # Высота (для изображений/видео)
    duration = Column(Integer, nullable=True)             # Длительность (для видео/аудио)

    # Геолокация
    latitude = Column(Float, nullable=True)               # Широта
    longitude = Column(Float, nullable=True)              # Долгота
    location_name = Column(String, nullable=True)         # Название места

    # Контакты
    contact_name = Column(String, nullable=True)          # Имя контакта
    contact_phone = Column(String, nullable=True)         # Телефон контакта

    # Дополнительная информация
    caption = Column(Text, nullable=True)                 # Подпись к вложению
    metadata = Column(JSON, nullable=True)                # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    uploaded_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MessageAttachment(id={self.id}, type={self.attachment_type.value}, filename={self.original_filename})>"

    @property
    def is_image(self) -> bool:
        """Проверка, является ли изображением"""
        return self.attachment_type == AttachmentType.IMAGE

    @property
    def is_video(self) -> bool:
        """Проверка, является ли видео"""
        return self.attachment_type == AttachmentType.VIDEO

    @property
    def is_audio(self) -> bool:
        """Проверка, является ли аудио"""
        return self.attachment_type in [AttachmentType.AUDIO, AttachmentType.VOICE]

    @property
    def is_document(self) -> bool:
        """Проверка, является ли документом"""
        return self.attachment_type == AttachmentType.DOCUMENT

    @property
    def is_media(self) -> bool:
        """Проверка, является ли медиафайлом"""
        return self.attachment_type in [AttachmentType.IMAGE, AttachmentType.VIDEO, AttachmentType.AUDIO, AttachmentType.VOICE]

    @property
    def is_ready(self) -> bool:
        """Проверка, готово ли вложение"""
        return self.status == AttachmentStatus.READY

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка"""
        return self.status == AttachmentStatus.FAILED

    @property
    def file_size_mb(self) -> float:
        """Размер файла в мегабайтах"""
        return self.file_size / (1024 * 1024) if self.file_size else 0

    @property
    def has_thumbnail(self) -> bool:
        """Проверка наличия миниатюры"""
        return self.thumbnail_path is not None or self.thumbnail_url is not None

    @property
    def dimensions(self) -> Optional[tuple[int, int]]:
        """Размеры изображения/видео"""
        if self.width and self.height:
            return (self.width, self.height)
        return None

    def mark_as_uploaded(self):
        """Отметить как загруженное"""
        self.status = AttachmentStatus.UPLOADED
        self.uploaded_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_as_processing(self):
        """Отметить как обрабатываемое"""
        self.status = AttachmentStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_as_ready(self, file_path: Optional[str] = None, file_url: Optional[str] = None):
        """Отметить как готовое"""
        self.status = AttachmentStatus.READY
        self.processed_at = datetime.utcnow()
        if file_path:
            self.file_path = file_path
        if file_url:
            self.file_url = file_url
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, reason: Optional[str] = None):
        """Отметить как неудачное"""
        self.status = AttachmentStatus.FAILED
        if reason:
            self.metadata = self.metadata or {}
            self.metadata["failure_reason"] = reason
        self.updated_at = datetime.utcnow()

    def mark_as_deleted(self):
        """Отметить как удаленное"""
        self.status = AttachmentStatus.DELETED
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def set_dimensions(self, width: int, height: int):
        """Установка размеров"""
        self.width = width
        self.height = height
        self.updated_at = datetime.utcnow()

    def set_duration(self, duration: int):
        """Установка длительности"""
        self.duration = duration
        self.updated_at = datetime.utcnow()

    def set_location(self, latitude: float, longitude: float, name: Optional[str] = None):
        """Установка геолокации"""
        self.latitude = latitude
        self.longitude = longitude
        if name:
            self.location_name = name
        self.updated_at = datetime.utcnow()

    def set_contact(self, name: str, phone: Optional[str] = None):
        """Установка контактной информации"""
        self.contact_name = name
        if phone:
            self.contact_phone = phone
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "uploader_id": self.uploader_id,
            "attachment_type": self.attachment_type.value,
            "status": self.status.value,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "thumbnail_path": self.thumbnail_path,
            "thumbnail_url": self.thumbnail_url,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_hash": self.file_hash,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "caption": self.caption,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }

    @staticmethod
    def create_image_attachment(uploader_id: str, filename: str, file_size: int,
                              width: Optional[int] = None, height: Optional[int] = None) -> 'MessageAttachment':
        """Создание вложения-изображения"""
        attachment = MessageAttachment(
            id=str(uuid.uuid4()),
            uploader_id=uploader_id,
            attachment_type=AttachmentType.IMAGE,
            original_filename=filename,
            file_size=file_size,
            width=width,
            height=height
        )
        return attachment

    @staticmethod
    def create_video_attachment(uploader_id: str, filename: str, file_size: int,
                              duration: Optional[int] = None) -> 'MessageAttachment':
        """Создание вложения-видео"""
        attachment = MessageAttachment(
            id=str(uuid.uuid4()),
            uploader_id=uploader_id,
            attachment_type=AttachmentType.VIDEO,
            original_filename=filename,
            file_size=file_size,
            duration=duration
        )
        return attachment

    @staticmethod
    def create_file_attachment(uploader_id: str, filename: str, file_size: int,
                             mime_type: Optional[str] = None) -> 'MessageAttachment':
        """Создание вложения-файла"""
        attachment = MessageAttachment(
            id=str(uuid.uuid4()),
            uploader_id=uploader_id,
            attachment_type=AttachmentType.DOCUMENT,
            original_filename=filename,
            file_size=file_size,
            mime_type=mime_type
        )
        return attachment
