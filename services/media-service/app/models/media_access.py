"""
Модель доступа к медиафайлам.

Используется эндпоинтами доступа и `MediaService` для валидации.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class AccessType(str, enum.Enum):
    """Типы доступа"""
    VIEW = "view"              # Просмотр
    DOWNLOAD = "download"      # Скачивание
    EDIT = "edit"              # Редактирование
    DELETE = "delete"          # Удаление
    SHARE = "share"            # Публикация


class AccessLevel(str, enum.Enum):
    """Уровни доступа"""
    NONE = "none"              # Нет доступа
    READ = "read"              # Только чтение
    WRITE = "write"            # Чтение и запись
    ADMIN = "admin"            # Полный доступ


class AccessStatus(str, enum.Enum):
    """Статусы доступа"""
    ACTIVE = "active"          # Активный
    EXPIRED = "expired"        # Истекший
    REVOKED = "revoked"        # Отозванный
    PENDING = "pending"        # Ожидающий подтверждения


class MediaAccess(Base):
    """Модель доступа к медиафайлу"""
    __tablename__ = "media_access"

    id = Column(String, primary_key=True, index=True)
    media_file_id = Column(String, ForeignKey("media_files.id"), nullable=False, index=True)

    # Тип доступа и уровень
    access_type = Column(Enum(AccessType), nullable=False)
    access_level = Column(Enum(AccessLevel), nullable=False, default=AccessLevel.READ)
    status = Column(Enum(AccessStatus), nullable=False, default=AccessStatus.ACTIVE)

    # Кому предоставлен доступ
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    group_id = Column(String, nullable=True)                      # ID группы пользователей
    token = Column(String, nullable=True, unique=True, index=True)  # Токен для публичного доступа

    # Ограничения
    max_views = Column(Integer, nullable=True)                   # Максимум просмотров
    max_downloads = Column(Integer, nullable=True)               # Максимум скачиваний
    expires_at = Column(DateTime, nullable=True)                 # Срок действия
    password_hash = Column(String, nullable=True)                # Пароль для доступа

    # Статистика использования
    view_count = Column(Integer, default=0)                       # Количество просмотров
    download_count = Column(Integer, default=0)                  # Количество скачиваний
    last_access_at = Column(DateTime, nullable=True)             # Последний доступ

    # Создал доступ
    granted_by = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    granted_at = Column(DateTime, default=func.now())

    # Метаданные
    description = Column(Text, nullable=True)                    # Описание доступа
    metadata = Column(JSON, nullable=True)                       # Дополнительные данные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MediaAccess(id={self.id}, file={self.media_file_id}, type={self.access_type.value}, level={self.access_level.value}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли доступ"""
        return self.status == AccessStatus.ACTIVE

    @property
    def is_expired(self) -> bool:
        """Проверка, истек ли доступ"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Проверка, отозван ли доступ"""
        return self.status == AccessStatus.REVOKED

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли подтверждения"""
        return self.status == AccessStatus.PENDING

    @property
    def can_view(self) -> bool:
        """Проверка возможности просмотра"""
        return (
            self.is_active and
            not self.is_expired and
            not self.is_revoked and
            (self.access_type == AccessType.VIEW or self.access_level in [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN])
        )

    @property
    def can_download(self) -> bool:
        """Проверка возможности скачивания"""
        return (
            self.is_active and
            not self.is_expired and
            not self.is_revoked and
            (self.access_type == AccessType.DOWNLOAD or self.access_level in [AccessLevel.WRITE, AccessLevel.ADMIN])
        )

    @property
    def can_edit(self) -> bool:
        """Проверка возможности редактирования"""
        return (
            self.is_active and
            not self.is_expired and
            not self.is_revoked and
            (self.access_type == AccessType.EDIT or self.access_level in [AccessLevel.WRITE, AccessLevel.ADMIN])
        )

    @property
    def can_delete(self) -> bool:
        """Проверка возможности удаления"""
        return (
            self.is_active and
            not self.is_expired and
            not self.is_revoked and
            (self.access_type == AccessType.DELETE or self.access_level == AccessLevel.ADMIN)
        )

    @property
    def can_share(self) -> bool:
        """Проверка возможности публикации"""
        return (
            self.is_active and
            not self.is_expired and
            not self.is_revoked and
            (self.access_type == AccessType.SHARE or self.access_level == AccessLevel.ADMIN)
        )

    @property
    def is_public_link(self) -> bool:
        """Проверка, является ли публичной ссылкой"""
        return self.token is not None

    @property
    def has_password(self) -> bool:
        """Проверка наличия пароля"""
        return self.password_hash is not None

    @property
    def views_left(self) -> Optional[int]:
        """Количество оставшихся просмотров"""
        if not self.max_views:
            return None
        return max(0, self.max_views - self.view_count)

    @property
    def downloads_left(self) -> Optional[int]:
        """Количество оставшихся скачиваний"""
        if not self.max_downloads:
            return None
        return max(0, self.max_downloads - self.download_count)

    def record_view(self):
        """Запись просмотра"""
        self.view_count += 1
        self.last_access_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def record_download(self):
        """Запись скачивания"""
        self.download_count += 1
        self.last_access_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def revoke(self):
        """Отзыв доступа"""
        self.status = AccessStatus.REVOKED
        self.updated_at = datetime.utcnow()

    def expire(self):
        """Истечение срока действия"""
        self.status = AccessStatus.EXPIRED
        self.updated_at = datetime.utcnow()

    def set_password(self, password_hash: str):
        """Установка пароля"""
        self.password_hash = password_hash
        self.updated_at = datetime.utcnow()

    def remove_password(self):
        """Удаление пароля"""
        self.password_hash = None
        self.updated_at = datetime.utcnow()

    def set_limits(self, max_views: Optional[int] = None, max_downloads: Optional[int] = None):
        """Установка ограничений"""
        if max_views is not None:
            self.max_views = max_views
        if max_downloads is not None:
            self.max_downloads = max_downloads
        self.updated_at = datetime.utcnow()

    def set_expiration(self, expires_at: datetime):
        """Установка срока действия"""
        self.expires_at = expires_at
        self.updated_at = datetime.utcnow()

    def generate_token(self) -> str:
        """Генерация токена для публичного доступа"""
        import secrets
        self.token = secrets.token_urlsafe(32)
        self.updated_at = datetime.utcnow()
        return self.token

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "media_file_id": self.media_file_id,
            "access_type": self.access_type.value,
            "access_level": self.access_level.value,
            "status": self.status.value,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "token": self.token,
            "max_views": self.max_views,
            "max_downloads": self.max_downloads,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "last_access_at": self.last_access_at.isoformat() if self.last_access_at else None,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat(),
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_public_access(media_file_id: str, granted_by: str, access_type: AccessType = AccessType.VIEW,
                           expires_at: Optional[datetime] = None, max_views: Optional[int] = None) -> 'MediaAccess':
        """Создание публичного доступа"""
        access = MediaAccess(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id,
            access_type=access_type,
            access_level=AccessLevel.READ,
            granted_by=granted_by,
            expires_at=expires_at,
            max_views=max_views
        )
        access.generate_token()
        return access

    @staticmethod
    def create_user_access(media_file_id: str, user_id: str, granted_by: str,
                         access_level: AccessLevel = AccessLevel.READ) -> 'MediaAccess':
        """Создание доступа для пользователя"""
        access = MediaAccess(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id,
            access_type=AccessType.VIEW,
            access_level=access_level,
            user_id=user_id,
            granted_by=granted_by
        )
        return access
