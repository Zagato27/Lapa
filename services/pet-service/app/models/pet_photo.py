"""
Модель фотографий питомцев.

Используется `PhotoService` для управления загрузками и связью с питомцем.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class PetPhoto(Base):
    """Модель фотографии питомца"""
    __tablename__ = "pet_photos"

    id = Column(String, primary_key=True, index=True)
    pet_id = Column(String, ForeignKey("pets.id"), nullable=False, index=True)

    # Информация о файле
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # в байтах
    mime_type = Column(String, nullable=False)

    # Метаданные изображения
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)

    # Тип фотографии
    photo_type = Column(String, default="general")  # avatar, general, medical, etc.

    # Описание
    description = Column(Text, nullable=True)
    # Храним теги в текстовом JSON; преобразование выполняется в сервисе
    tags = Column(Text, nullable=True)

    # Статус
    is_active = Column(Boolean, default=True)

    # Метаданные
    uploaded_by = Column(String, nullable=False)  # user_id
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PetPhoto(id={self.id}, pet_id={self.pet_id}, filename={self.filename})>"

    @property
    def file_size_mb(self) -> float:
        """Размер файла в мегабайтах"""
        return self.file_size / (1024 * 1024)

    @property
    def is_image(self) -> bool:
        """Проверка, является ли файл изображением"""
        return self.mime_type.startswith('image/')

    @property
    def is_avatar(self) -> bool:
        """Проверка, является ли фото аватаром"""
        return self.photo_type == "avatar"
