"""
Модель альбомов медиафайлов.

Используется `MediaService` и эндпоинтами `app.api.v1.albums`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class AlbumType(str, enum.Enum):
    """Типы альбомов"""
    USER = "user"              # Пользовательский альбом
    PET = "pet"                # Альбом питомца
    ORDER = "order"            # Альбом заказа
    SYSTEM = "system"          # Системный альбом
    SHARED = "shared"          # Общий альбом


class AlbumStatus(str, enum.Enum):
    """Статусы альбомов"""
    ACTIVE = "active"          # Активный
    ARCHIVED = "archived"      # Архивный
    DELETED = "deleted"        # Удаленный
    PRIVATE = "private"        # Приватный


class MediaAlbum(Base):
    """Модель альбома медиафайлов"""
    __tablename__ = "media_albums"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Тип и статус
    album_type = Column(Enum(AlbumType), nullable=False, default=AlbumType.USER)
    status = Column(Enum(AlbumStatus), nullable=False, default=AlbumStatus.ACTIVE)

    # Владелец
    owner_id = Column(String, nullable=False, index=True)

    # Связанные объекты
    pet_id = Column(String, nullable=True, index=True)
    order_id = Column(String, nullable=True, index=True)

    # Настройки доступа
    is_public = Column(Boolean, default=False)                 # Публичный доступ
    is_shared = Column(Boolean, default=False)                 # Общий альбом
    allow_upload = Column(Boolean, default=True)               # Разрешить загрузку
    allow_download = Column(Boolean, default=True)             # Разрешить скачивание

    # Ограничения
    max_files = Column(Integer, nullable=True)                 # Максимум файлов
    max_file_size_mb = Column(Integer, nullable=True)          # Максимальный размер файла
    allowed_types = Column(JSON, nullable=True)                # Разрешенные типы файлов

    # Обложка
    cover_file_id = Column(String, ForeignKey("media_files.id"), nullable=True)

    # Статистика
    total_files = Column(Integer, default=0)                   # Общее количество файлов
    total_size = Column(Integer, default=0)                    # Общий размер в байтах
    image_count = Column(Integer, default=0)                   # Количество изображений
    video_count = Column(Integer, default=0)                   # Количество видео
    audio_count = Column(Integer, default=0)                   # Количество аудио

    # Метаданные
    tags = Column(JSON, nullable=True)                         # Теги альбома
    settings = Column(JSON, nullable=True)                     # Настройки альбома

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_activity_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MediaAlbum(id={self.id}, name={self.name}, type={self.album_type.value}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли альбом"""
        return self.status == AlbumStatus.ACTIVE

    @property
    def is_archived(self) -> bool:
        """Проверка, архивный ли альбом"""
        return self.status == AlbumStatus.ARCHIVED

    @property
    def is_deleted(self) -> bool:
        """Проверка, удален ли альбом"""
        return self.status == AlbumStatus.DELETED

    @property
    def is_private(self) -> bool:
        """Проверка, приватный ли альбом"""
        return self.status == AlbumStatus.PRIVATE

    @property
    def total_size_mb(self) -> float:
        """Общий размер в мегабайтах"""
        return self.total_size / (1024 * 1024) if self.total_size else 0

    @property
    def total_size_gb(self) -> float:
        """Общий размер в гигабайтах"""
        return self.total_size / (1024 * 1024 * 1024) if self.total_size else 0

    @property
    def can_upload(self) -> bool:
        """Проверка возможности загрузки файлов"""
        return self.is_active and self.allow_upload

    @property
    def can_download(self) -> bool:
        """Проверка возможности скачивания файлов"""
        return self.is_active and self.allow_download

    @property
    def has_space(self) -> bool:
        """Проверка наличия места для новых файлов"""
        if not self.max_files:
            return True
        return self.total_files < self.max_files

    def archive(self):
        """Архивация альбома"""
        self.status = AlbumStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def delete(self):
        """Удаление альбома"""
        self.status = AlbumStatus.DELETED
        self.updated_at = datetime.utcnow()

    def make_private(self):
        """Сделать альбом приватным"""
        self.status = AlbumStatus.PRIVATE
        self.is_public = False
        self.updated_at = datetime.utcnow()

    def make_public(self):
        """Сделать альбом публичным"""
        self.is_public = True
        if self.status == AlbumStatus.PRIVATE:
            self.status = AlbumStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def update_last_activity(self):
        """Обновление времени последней активности"""
        self.last_activity_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_file(self, file_size: int, media_type: str):
        """Добавление файла в альбом"""
        self.total_files += 1
        self.total_size += file_size

        if media_type == "image":
            self.image_count += 1
        elif media_type == "video":
            self.video_count += 1
        elif media_type == "audio":
            self.audio_count += 1

        self.update_last_activity()

    def remove_file(self, file_size: int, media_type: str):
        """Удаление файла из альбома"""
        if self.total_files > 0:
            self.total_files -= 1
        if self.total_size >= file_size:
            self.total_size -= file_size

        if media_type == "image" and self.image_count > 0:
            self.image_count -= 1
        elif media_type == "video" and self.video_count > 0:
            self.video_count -= 1
        elif media_type == "audio" and self.audio_count > 0:
            self.audio_count -= 1

        self.updated_at = datetime.utcnow()

    def set_cover(self, file_id: str):
        """Установка обложки альбома"""
        self.cover_file_id = file_id
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str):
        """Добавление тега"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
        self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str):
        """Удаление тега"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "album_type": self.album_type.value,
            "status": self.status.value,
            "owner_id": self.owner_id,
            "pet_id": self.pet_id,
            "order_id": self.order_id,
            "is_public": self.is_public,
            "is_shared": self.is_shared,
            "allow_upload": self.allow_upload,
            "allow_download": self.allow_download,
            "max_files": self.max_files,
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_types": self.allowed_types,
            "cover_file_id": self.cover_file_id,
            "total_files": self.total_files,
            "total_size": self.total_size,
            "image_count": self.image_count,
            "video_count": self.video_count,
            "audio_count": self.audio_count,
            "tags": self.tags,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None
        }

    @staticmethod
    def create_user_album(owner_id: str, name: str, description: Optional[str] = None) -> 'MediaAlbum':
        """Создание пользовательского альбома"""
        album = MediaAlbum(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            album_type=AlbumType.USER,
            owner_id=owner_id
        )
        return album

    @staticmethod
    def create_pet_album(owner_id: str, pet_id: str, pet_name: str) -> 'MediaAlbum':
        """Создание альбома питомца"""
        album = MediaAlbum(
            id=str(uuid.uuid4()),
            name=f"Фото {pet_name}",
            description=f"Фотографии питомца {pet_name}",
            album_type=AlbumType.PET,
            owner_id=owner_id,
            pet_id=pet_id
        )
        return album

    @staticmethod
    def create_order_album(owner_id: str, order_id: str) -> 'MediaAlbum':
        """Создание альбома заказа"""
        album = MediaAlbum(
            id=str(uuid.uuid4()),
            name=f"Заказ #{order_id}",
            description=f"Медиафайлы заказа #{order_id}",
            album_type=AlbumType.ORDER,
            owner_id=owner_id,
            order_id=order_id
        )
        return album
