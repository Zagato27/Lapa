"""
Модель тегов медиафайлов.

Используется `MediaService` для категоризации и фильтрации.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class TagType(str, enum.Enum):
    """Типы тегов"""
    USER = "user"              # Пользовательский тег
    SYSTEM = "system"          # Системный тег
    AUTO = "auto"              # Автоматически сгенерированный тег
    CATEGORY = "category"      # Категория


class TagStatus(str, enum.Enum):
    """Статусы тегов"""
    ACTIVE = "active"          # Активный
    DEPRECATED = "deprecated"  # Устаревший
    BANNED = "banned"          # Забаненный


class MediaTag(Base):
    """Модель тега медиафайла"""
    __tablename__ = "media_tags"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, unique=True, index=True)

    # Тип и статус
    tag_type = Column(Enum(TagType), nullable=False, default=TagType.USER)
    status = Column(Enum(TagStatus), nullable=False, default=TagStatus.ACTIVE)

    # Описание и цвет
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)                       # HEX цвет тега

    # Создал
    creator_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    # Настройки
    is_public = Column(Boolean, default=True)                   # Публичный тег
    is_featured = Column(Boolean, default=False)                # Рекомендуемый тег
    is_auto_tag = Column(Boolean, default=False)                # Автоматический тег

    # Статистика
    usage_count = Column(Integer, default=0)                    # Количество использований
    media_count = Column(Integer, default=0)                    # Количество медиафайлов с тегом

    # Иконка
    icon_url = Column(String, nullable=True)                    # URL иконки тега
    icon_emoji = Column(String, nullable=True)                  # Эмодзи иконки

    # Метаданные
    metadata = Column(JSON, nullable=True)                      # Дополнительные данные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MediaTag(id={self.id}, name={self.name}, type={self.tag_type.value}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли тег"""
        return self.status == TagStatus.ACTIVE

    @property
    def is_deprecated(self) -> bool:
        """Проверка, устарел ли тег"""
        return self.status == TagStatus.DEPRECATED

    @property
    def is_banned(self) -> bool:
        """Проверка, забанен ли тег"""
        return self.status == TagStatus.BANNED

    @property
    def is_system_tag(self) -> bool:
        """Проверка, является ли системным тегом"""
        return self.tag_type == TagType.SYSTEM

    @property
    def is_user_tag(self) -> bool:
        """Проверка, является ли пользовательским тегом"""
        return self.tag_type == TagType.USER

    @property
    def is_auto_tag(self) -> bool:
        """Проверка, является ли автоматическим тегом"""
        return self.tag_type == TagType.AUTO

    @property
    def display_name(self) -> str:
        """Отображаемое имя с эмодзи"""
        if self.icon_emoji:
            return f"{self.icon_emoji} {self.name}"
        return self.name

    def increment_usage(self):
        """Увеличение счетчика использования"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_media_count(self):
        """Увеличение счетчика медиафайлов"""
        self.media_count += 1
        self.updated_at = datetime.utcnow()

    def decrement_media_count(self):
        """Уменьшение счетчика медиафайлов"""
        if self.media_count > 0:
            self.media_count -= 1
        self.updated_at = datetime.utcnow()

    def make_featured(self):
        """Сделать рекомендуемым"""
        self.is_featured = True
        self.updated_at = datetime.utcnow()

    def remove_featured(self):
        """Убрать из рекомендуемых"""
        self.is_featured = False
        self.updated_at = datetime.utcnow()

    def deprecate(self):
        """Отметить как устаревший"""
        self.status = TagStatus.DEPRECATED
        self.updated_at = datetime.utcnow()

    def ban(self):
        """Забанить тег"""
        self.status = TagStatus.BANNED
        self.updated_at = datetime.utcnow()

    def unban(self):
        """Разбанить тег"""
        self.status = TagStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "tag_type": self.tag_type.value,
            "status": self.status.value,
            "description": self.description,
            "color": self.color,
            "creator_id": self.creator_id,
            "is_public": self.is_public,
            "is_featured": self.is_featured,
            "is_auto_tag": self.is_auto_tag,
            "usage_count": self.usage_count,
            "media_count": self.media_count,
            "icon_url": self.icon_url,
            "icon_emoji": self.icon_emoji,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }

    @staticmethod
    def generate_slug(name: str) -> str:
        """Генерация slug из имени"""
        import re
        from unicodedata import normalize

        # Нормализация unicode
        name = normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

        # Преобразование в нижний регистр и замена пробелов
        slug = re.sub(r'[^\w\s-]', '', name).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)

        return slug

    @staticmethod
    def create_user_tag(name: str, creator_id: str, description: Optional[str] = None, color: Optional[str] = None) -> 'MediaTag':
        """Создание пользовательского тега"""
        tag = MediaTag(
            id=str(uuid.uuid4()),
            name=name,
            slug=MediaTag.generate_slug(name),
            tag_type=TagType.USER,
            creator_id=creator_id,
            description=description,
            color=color
        )
        return tag

    @staticmethod
    def create_system_tag(name: str, description: Optional[str] = None, icon_emoji: Optional[str] = None) -> 'MediaTag':
        """Создание системного тега"""
        tag = MediaTag(
            id=str(uuid.uuid4()),
            name=name,
            slug=MediaTag.generate_slug(name),
            tag_type=TagType.SYSTEM,
            description=description,
            icon_emoji=icon_emoji,
            is_public=True
        )
        return tag

    @staticmethod
    def create_auto_tag(name: str, description: Optional[str] = None) -> 'MediaTag':
        """Создание автоматического тега"""
        tag = MediaTag(
            id=str(uuid.uuid4()),
            name=name,
            slug=MediaTag.generate_slug(name),
            tag_type=TagType.AUTO,
            description=description,
            is_auto_tag=True,
            is_public=True
        )
        return tag
