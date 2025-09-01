"""
Конфигурация Media Service
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa Media Service"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Серверные настройки
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # JWT настройки (для валидации токенов от API Gateway/User Service)
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    # PostgreSQL настройки
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "lapa_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "lapa_password")
    postgres_db: str = os.getenv("POSTGRES_DB", "lapa")

    # Redis настройки
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")

    # MongoDB настройки
    mongo_host: str = os.getenv("MONGO_HOST", "localhost")
    mongo_port: int = int(os.getenv("MONGO_PORT", "27017"))
    mongo_user: str = os.getenv("MONGO_USER", "lapa_user")
    mongo_password: str = os.getenv("MONGO_PASSWORD", "lapa_password")
    mongo_db: str = os.getenv("MONGO_DB", "lapa")

    # CORS настройки
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://lapa-kolomna.ru"
    ]

    # Доверенные хосты
    allowed_hosts: List[str] = ["*"]

    # Настройки хранения
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local")  # local, s3, cloudinary, imgur
    upload_path: str = os.getenv("UPLOAD_PATH", "/data/media_uploads")
    temp_path: str = os.getenv("TEMP_PATH", "/tmp/media_temp")

    # Максимальные размеры файлов
    max_image_size_mb: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "20"))  # Максимальный размер изображения
    max_video_size_mb: int = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))  # Максимальный размер видео
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))    # Максимальный размер файла

    # Допустимые форматы файлов
    allowed_image_types: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"]
    allowed_video_types: List[str] = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"]
    allowed_audio_types: List[str] = [".mp3", ".wav", ".aac", ".ogg", ".m4a"]

    # Настройки обработки изображений
    enable_image_processing: bool = os.getenv("ENABLE_IMAGE_PROCESSING", "true").lower() == "true"
    image_quality: int = int(os.getenv("IMAGE_QUALITY", "85"))  # Качество JPEG (1-100)
    max_image_width: int = int(os.getenv("MAX_IMAGE_WIDTH", "2048"))  # Максимальная ширина
    max_image_height: int = int(os.getenv("MAX_IMAGE_HEIGHT", "2048"))  # Максимальная высота
    thumbnail_sizes: List[str] = os.getenv("THUMBNAIL_SIZES", "150x150,300x300,600x600").split(",")

    # Настройки обработки видео
    enable_video_processing: bool = os.getenv("ENABLE_VIDEO_PROCESSING", "true").lower() == "true"
    video_quality: str = os.getenv("VIDEO_QUALITY", "medium")  # low, medium, high
    max_video_duration: int = int(os.getenv("MAX_VIDEO_DURATION", "300"))  # Максимальная длительность в секундах
    video_formats: List[str] = ["mp4", "webm"]  # Выходные форматы видео

    # Настройки миниатюр
    enable_thumbnails: bool = os.getenv("ENABLE_THUMBNAILS", "true").lower() == "true"
    thumbnail_format: str = os.getenv("THUMBNAIL_FORMAT", "jpg")  # jpg, png, webp
    thumbnail_quality: int = int(os.getenv("THUMBNAIL_QUALITY", "80"))

    # Настройки CDN
    cdn_enabled: bool = os.getenv("CDN_ENABLED", "false").lower() == "true"
    cdn_url: Optional[str] = os.getenv("CDN_URL")
    cdn_key: Optional[str] = os.getenv("CDN_KEY")

    # Настройки AWS S3
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket_name: Optional[str] = os.getenv("S3_BUCKET_NAME")
    s3_public_read: bool = os.getenv("S3_PUBLIC_READ", "true").lower() == "true"

    # Настройки Cloudinary
    cloudinary_cloud_name: Optional[str] = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: Optional[str] = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret: Optional[str] = os.getenv("CLOUDINARY_API_SECRET")

    # Настройки водяных знаков
    watermark_enabled: bool = os.getenv("WATERMARK_ENABLED", "false").lower() == "true"
    watermark_image: Optional[str] = os.getenv("WATERMARK_IMAGE")
    watermark_opacity: float = float(os.getenv("WATERMARK_OPACITY", "0.3"))
    watermark_position: str = os.getenv("WATERMARK_POSITION", "bottom_right")  # top_left, top_right, bottom_left, bottom_right, center

    # Настройки оптимизации
    enable_optimization: bool = os.getenv("ENABLE_OPTIMIZATION", "true").lower() == "true"
    jpeg_optimization: bool = os.getenv("JPEG_OPTIMIZATION", "true").lower() == "true"
    png_optimization: bool = os.getenv("PNG_OPTIMIZATION", "true").lower() == "true"
    webp_conversion: bool = os.getenv("WEBP_CONVERSION", "true").lower() == "true"

    # Настройки кэширования
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # Время жизни кэша в секундах
    max_cache_size_mb: int = int(os.getenv("MAX_CACHE_SIZE_MB", "1024"))  # Максимальный размер кэша

    # Настройки безопасности
    enable_encryption: bool = os.getenv("ENABLE_ENCRYPTION", "false").lower() == "true"
    encryption_key: Optional[str] = os.getenv("ENCRYPTION_KEY")
    enable_rate_limiting: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    uploads_per_hour: int = int(os.getenv("UPLOADS_PER_HOUR", "100"))  # Максимум загрузок в час на пользователя

    # Настройки очистки
    cleanup_enabled: bool = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"
    cleanup_interval_hours: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
    max_storage_days: int = int(os.getenv("MAX_STORAGE_DAYS", "90"))  # Максимальное время хранения
    max_total_storage_gb: int = int(os.getenv("MAX_TOTAL_STORAGE_GB", "100"))  # Максимальный объем хранилища

    # Настройки метаданных
    extract_metadata: bool = os.getenv("EXTRACT_METADATA", "true").lower() == "true"
    extract_gps: bool = os.getenv("EXTRACT_GPS", "false").lower() == "true"
    extract_colors: bool = os.getenv("EXTRACT_COLORS", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
