"""
Модель метаданных медиафайлов.

Используется `MediaProcessor` и `MediaService`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import uuid

from .base import Base


class MediaMetadata(Base):
    """Модель метаданных медиафайла"""
    __tablename__ = "media_metadata"

    id = Column(String, primary_key=True, index=True)
    media_file_id = Column(String, ForeignKey("media_files.id"), nullable=False, index=True, unique=True)

    # EXIF данные (для изображений)
    camera_make = Column(String, nullable=True)                  # Производитель камеры
    camera_model = Column(String, nullable=True)                 # Модель камеры
    lens_make = Column(String, nullable=True)                    # Производитель объектива
    lens_model = Column(String, nullable=True)                   # Модель объектива
    focal_length = Column(Float, nullable=True)                  # Фокусное расстояние
    aperture = Column(Float, nullable=True)                      # Диафрагма
    shutter_speed = Column(String, nullable=True)                # Выдержка
    iso = Column(Integer, nullable=True)                         # ISO
    flash = Column(Boolean, nullable=True)                       # Была ли вспышка
    exposure_program = Column(String, nullable=True)             # Программа экспозиции

    # Геолокация
    latitude = Column(Float, nullable=True)                      # Широта
    longitude = Column(Float, nullable=True)                     # Долгота
    altitude = Column(Float, nullable=True)                      # Высота
    location_name = Column(String, nullable=True)                # Название места
    location_country = Column(String, nullable=True)             # Страна
    location_city = Column(String, nullable=True)                # Город
    location_address = Column(Text, nullable=True)               # Полный адрес

    # Дата и время съемки
    date_taken = Column(DateTime, nullable=True)                 # Дата съемки
    date_digitized = Column(DateTime, nullable=True)             # Дата оцифровки
    date_original = Column(DateTime, nullable=True)              # Оригинальная дата

    # Цветовая информация
    color_space = Column(String, nullable=True)                  # Цветовое пространство
    color_profile = Column(String, nullable=True)                # Цветовой профиль
    dominant_colors = Column(JSON, nullable=True)                # Доминирующие цвета
    color_histogram = Column(JSON, nullable=True)                # Гистограмма цветов

    # Информация о изображении
    image_width = Column(Integer, nullable=True)                 # Ширина изображения
    image_height = Column(Integer, nullable=True)                # Высота изображения
    image_resolution = Column(Float, nullable=True)              # Разрешение
    image_orientation = Column(Integer, nullable=True)           # Ориентация
    image_compression = Column(String, nullable=True)            # Тип сжатия

    # Информация о видео
    video_codec = Column(String, nullable=True)                  # Кодек видео
    video_bitrate = Column(Integer, nullable=True)               # Битрейт видео
    video_frame_rate = Column(Float, nullable=True)              # Частота кадров
    video_aspect_ratio = Column(Float, nullable=True)            # Соотношение сторон
    audio_codec = Column(String, nullable=True)                  # Кодек аудио
    audio_channels = Column(Integer, nullable=True)              # Количество каналов аудио
    audio_sample_rate = Column(Integer, nullable=True)           # Частота дискретизации

    # Информация об устройстве
    software = Column(String, nullable=True)                     # ПО для создания
    device_name = Column(String, nullable=True)                  # Название устройства
    device_model = Column(String, nullable=True)                 # Модель устройства
    os_version = Column(String, nullable=True)                   # Версия ОС

    # Ключевые слова и категории
    keywords = Column(JSON, nullable=True)                       # Ключевые слова
    categories = Column(JSON, nullable=True)                     # Категории
    tags = Column(JSON, nullable=True)                          # Теги

    # Авторские права
    copyright = Column(String, nullable=True)                    # Авторские права
    artist = Column(String, nullable=True)                       # Автор
    creator = Column(String, nullable=True)                      # Создатель

    # Рейтинг и оценки
    rating = Column(Integer, nullable=True)                      # Рейтинг (1-5)
    quality_score = Column(Float, nullable=True)                 # Оценка качества (0-1)

    # Дополнительные метаданные
    raw_metadata = Column(JSON, nullable=True)                   # Сырые метаданные EXIF
    custom_metadata = Column(JSON, nullable=True)                # Пользовательские метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    extracted_at = Column(DateTime, nullable=True)               # Время извлечения метаданных

    def __repr__(self):
        return f"<MediaMetadata(id={self.id}, file={self.media_file_id})>"

    @property
    def has_location(self) -> bool:
        """Проверка наличия геолокации"""
        return self.latitude is not None and self.longitude is not None

    @property
    def has_camera_info(self) -> bool:
        """Проверка наличия информации о камере"""
        return self.camera_make is not None or self.camera_model is not None

    @property
    def has_color_info(self) -> bool:
        """Проверка наличия цветовой информации"""
        return self.dominant_colors is not None or self.color_histogram is not None

    @property
    def coordinates(self) -> Optional[tuple[float, float]]:
        """Координаты в виде кортежа"""
        if self.has_location:
            return (self.latitude, self.longitude)
        return None

    @property
    def aspect_ratio(self) -> Optional[float]:
        """Соотношение сторон изображения"""
        if self.image_width and self.image_height:
            return self.image_width / self.image_height
        return None

    @property
    def megapixels(self) -> Optional[float]:
        """Количество мегапикселей"""
        if self.image_width and self.image_height:
            return (self.image_width * self.image_height) / 1000000
        return None

    def set_location(self, latitude: float, longitude: float, altitude: Optional[float] = None):
        """Установка геолокации"""
        self.latitude = latitude
        self.longitude = longitude
        if altitude is not None:
            self.altitude = altitude
        self.updated_at = datetime.utcnow()

    def set_camera_info(self, make: Optional[str] = None, model: Optional[str] = None,
                       lens_make: Optional[str] = None, lens_model: Optional[str] = None):
        """Установка информации о камере"""
        if make:
            self.camera_make = make
        if model:
            self.camera_model = model
        if lens_make:
            self.lens_make = lens_make
        if lens_model:
            self.lens_model = lens_model
        self.updated_at = datetime.utcnow()

    def set_image_info(self, width: int, height: int, resolution: Optional[float] = None):
        """Установка информации об изображении"""
        self.image_width = width
        self.image_height = height
        if resolution:
            self.image_resolution = resolution
        self.updated_at = datetime.utcnow()

    def set_video_info(self, codec: str, bitrate: Optional[int] = None, frame_rate: Optional[float] = None):
        """Установка информации о видео"""
        self.video_codec = codec
        if bitrate:
            self.video_bitrate = bitrate
        if frame_rate:
            self.video_frame_rate = frame_rate
        self.updated_at = datetime.utcnow()

    def set_colors(self, dominant_colors: list, histogram: Optional[dict] = None):
        """Установка цветовой информации"""
        self.dominant_colors = dominant_colors
        if histogram:
            self.color_histogram = histogram
        self.updated_at = datetime.utcnow()

    def add_keyword(self, keyword: str):
        """Добавление ключевого слова"""
        if not self.keywords:
            self.keywords = []
        if keyword not in self.keywords:
            self.keywords.append(keyword)
        self.updated_at = datetime.utcnow()

    def remove_keyword(self, keyword: str):
        """Удаление ключевого слова"""
        if self.keywords and keyword in self.keywords:
            self.keywords.remove(keyword)
        self.updated_at = datetime.utcnow()

    def add_category(self, category: str):
        """Добавление категории"""
        if not self.categories:
            self.categories = []
        if category not in self.categories:
            self.categories.append(category)
        self.updated_at = datetime.utcnow()

    def remove_category(self, category: str):
        """Удаление категории"""
        if self.categories and category in self.categories:
            self.categories.remove(category)
        self.updated_at = datetime.utcnow()

    def set_rating(self, rating: int):
        """Установка рейтинга"""
        if 1 <= rating <= 5:
            self.rating = rating
            self.updated_at = datetime.utcnow()

    def mark_extracted(self):
        """Отметить как извлеченное"""
        self.extracted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "media_file_id": self.media_file_id,
            "camera_make": self.camera_make,
            "camera_model": self.camera_model,
            "lens_make": self.lens_make,
            "lens_model": self.lens_model,
            "focal_length": self.focal_length,
            "aperture": self.aperture,
            "shutter_speed": self.shutter_speed,
            "iso": self.iso,
            "flash": self.flash,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "location_name": self.location_name,
            "location_country": self.location_country,
            "location_city": self.location_city,
            "date_taken": self.date_taken.isoformat() if self.date_taken else None,
            "color_space": self.color_space,
            "dominant_colors": self.dominant_colors,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "video_codec": self.video_codec,
            "video_bitrate": self.video_bitrate,
            "video_frame_rate": self.video_frame_rate,
            "software": self.software,
            "keywords": self.keywords,
            "categories": self.categories,
            "copyright": self.copyright,
            "artist": self.artist,
            "rating": self.rating,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_for_image(media_file_id: str) -> 'MediaMetadata':
        """Создание метаданных для изображения"""
        metadata = MediaMetadata(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id
        )
        return metadata

    @staticmethod
    def create_for_video(media_file_id: str) -> 'MediaMetadata':
        """Создание метаданных для видео"""
        metadata = MediaMetadata(
            id=str(uuid.uuid4()),
            media_file_id=media_file_id
        )
        return metadata
