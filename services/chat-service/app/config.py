"""
Конфигурация Chat Service
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa Chat Service"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Серверные настройки
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

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

    # Настройки чата
    max_chat_participants: int = int(os.getenv("MAX_CHAT_PARTICIPANTS", "50"))  # Максимум участников в чате
    max_message_length: int = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))  # Максимальная длина сообщения
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))  # Максимальный размер файла
    message_history_limit: int = int(os.getenv("MESSAGE_HISTORY_LIMIT", "100"))  # Лимит истории сообщений

    # Настройки WebSocket
    websocket_ping_interval: int = int(os.getenv("WEBSOCKET_PING_INTERVAL", "30"))  # Интервал пинга в секундах
    websocket_timeout: int = int(os.getenv("WEBSOCKET_TIMEOUT", "300"))  # Таймаут соединения
    max_websocket_connections: int = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "10000"))  # Макс. количество соединений
    max_connections_per_user: int = int(os.getenv("MAX_CONNECTIONS_PER_USER", "5"))  # Макс. соединений на пользователя

    # Настройки файлов
    upload_path: str = os.getenv("UPLOAD_PATH", "/tmp/chat_uploads")
    allowed_file_types: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".pdf", ".doc", ".docx", ".txt"]
    image_max_width: int = int(os.getenv("IMAGE_MAX_WIDTH", "1920"))  # Максимальная ширина изображения
    image_max_height: int = int(os.getenv("IMAGE_MAX_HEIGHT", "1080"))  # Максимальная высота изображения
    thumbnail_size: int = int(os.getenv("THUMBNAIL_SIZE", "200"))  # Размер миниатюры

    # Настройки модерации
    enable_moderation: bool = os.getenv("ENABLE_MODERATION", "true").lower() == "true"
    banned_words_file: str = os.getenv("BANNED_WORDS_FILE", "/app/config/banned_words.txt")
    spam_detection_enabled: bool = os.getenv("SPAM_DETECTION_ENABLED", "true").lower() == "true"
    max_messages_per_minute: int = int(os.getenv("MAX_MESSAGES_PER_MINUTE", "10"))  # Максимум сообщений в минуту
    message_cooldown_seconds: int = int(os.getenv("MESSAGE_COOLDOWN_SECONDS", "1"))  # Задержка между сообщениями

    # Настройки уведомлений
    push_notifications_enabled: bool = os.getenv("PUSH_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    email_notifications_enabled: bool = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    sms_notifications_enabled: bool = os.getenv("SMS_NOTIFICATIONS_ENABLED", "false").lower() == "true"

    # Настройки типов чатов
    chat_types: List[str] = ["order", "support", "group", "private"]  # Типы чатов
    system_messages_enabled: bool = os.getenv("SYSTEM_MESSAGES_ENABLED", "true").lower() == "true"

    # Настройки хранения
    message_retention_days: int = int(os.getenv("MESSAGE_RETENTION_DAYS", "90"))  # Хранение сообщений
    file_retention_days: int = int(os.getenv("FILE_RETENTION_DAYS", "30"))  # Хранение файлов
    chat_archive_enabled: bool = os.getenv("CHAT_ARCHIVE_ENABLED", "true").lower() == "true"

    # Настройки безопасности
    encryption_enabled: bool = os.getenv("ENCRYPTION_ENABLED", "false").lower() == "true"
    rate_limiting_enabled: bool = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
    ip_blacklist_enabled: bool = os.getenv("IP_BLACKLIST_ENABLED", "true").lower() == "true"

    # Настройки интеграции
    notification_service_url: Optional[str] = os.getenv("NOTIFICATION_SERVICE_URL")
    media_service_url: Optional[str] = os.getenv("MEDIA_SERVICE_URL")

    # Настройки очистки
    cleanup_interval_hours: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))  # Интервал очистки
    old_messages_cleanup_days: int = int(os.getenv("OLD_MESSAGES_CLEANUP_DAYS", "30"))  # Удаление старых сообщений

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
