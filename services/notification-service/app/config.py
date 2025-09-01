"""
Конфигурация Notification Service
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa Notification Service"
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

    # Настройки уведомлений
    max_notifications_per_hour: int = int(os.getenv("MAX_NOTIFICATIONS_PER_HOUR", "1000"))  # Максимум уведомлений в час на пользователя
    max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "100"))  # Максимальный размер пакета
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "ru")  # Язык по умолчанию

    # Настройки каналов
    enable_push_notifications: bool = os.getenv("ENABLE_PUSH_NOTIFICATIONS", "true").lower() == "true"
    enable_email_notifications: bool = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"
    enable_sms_notifications: bool = os.getenv("ENABLE_SMS_NOTIFICATIONS", "false").lower() == "true"
    enable_telegram_notifications: bool = os.getenv("ENABLE_TELEGRAM_NOTIFICATIONS", "false").lower() == "true"

    # Настройки Push-уведомлений (Firebase)
    firebase_project_id: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    firebase_credentials_path: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")
    firebase_server_key: Optional[str] = os.getenv("FIREBASE_SERVER_KEY")

    # Настройки Email (SendGrid)
    sendgrid_api_key: Optional[str] = os.getenv("SENDGRID_API_KEY")
    sendgrid_from_email: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@lapa-kolomna.ru")
    sendgrid_from_name: str = os.getenv("SENDGRID_FROM_NAME", "Lapa Platform")

    # Настройки SMS (Twilio)
    twilio_account_sid: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from_phone: Optional[str] = os.getenv("TWILIO_FROM_PHONE")

    # Настройки Telegram
    telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = os.getenv("TELEGRAM_WEBHOOK_URL")

    # Настройки SMTP (резервный вариант для email)
    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # Настройки очередей
    queue_max_retries: int = int(os.getenv("QUEUE_MAX_RETRIES", "3"))  # Максимум попыток отправки
    queue_retry_delay: int = int(os.getenv("QUEUE_RETRY_DELAY", "60"))  # Задержка между попытками (секунды)
    queue_processing_interval: int = int(os.getenv("QUEUE_PROCESSING_INTERVAL", "10"))  # Интервал обработки очереди
    queue_batch_size: int = int(os.getenv("QUEUE_BATCH_SIZE", "50"))  # Размер пакета для обработки

    # Настройки шаблонов
    template_cache_ttl: int = int(os.getenv("TEMPLATE_CACHE_TTL", "3600"))  # Время жизни кэша шаблонов
    enable_template_caching: bool = os.getenv("ENABLE_TEMPLATE_CACHING", "true").lower() == "true"

    # Настройки персонализации
    enable_personalization: bool = os.getenv("ENABLE_PERSONALIZATION", "true").lower() == "true"
    enable_segmentation: bool = os.getenv("ENABLE_SEGMENTATION", "true").lower() == "true"

    # Настройки аналитики
    enable_delivery_tracking: bool = os.getenv("ENABLE_DELIVERY_TRACKING", "true").lower() == "true"
    enable_click_tracking: bool = os.getenv("ENABLE_CLICK_TRACKING", "true").lower() == "true"
    enable_open_tracking: bool = os.getenv("ENABLE_OPEN_TRACKING", "true").lower() == "true"

    # Настройки модерации
    enable_content_filtering: bool = os.getenv("ENABLE_CONTENT_FILTERING", "true").lower() == "true"
    enable_spam_detection: bool = os.getenv("ENABLE_SPAM_DETECTION", "true").lower() == "true"
    banned_words_file: str = os.getenv("BANNED_WORDS_FILE", "/app/config/banned_words.txt")

    # Настройки подписок
    enable_subscription_management: bool = os.getenv("ENABLE_SUBSCRIPTION_MANAGEMENT", "true").lower() == "true"
    default_subscription_preferences: dict = {
        "push": True,
        "email": True,
        "sms": False,
        "telegram": False
    }

    # Настройки приоритетов
    priority_levels: List[str] = ["low", "normal", "high", "urgent"]
    urgent_notification_ttl: int = int(os.getenv("URGENT_NOTIFICATION_TTL", "300"))  # Время жизни срочных уведомлений

    # Настройки расписания
    enable_scheduled_notifications: bool = os.getenv("ENABLE_SCHEDULED_NOTIFICATIONS", "true").lower() == "true"
    timezone: str = os.getenv("TIMEZONE", "Europe/Moscow")

    # Настройки очистки
    cleanup_enabled: bool = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"
    cleanup_interval_hours: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
    max_notification_age_days: int = int(os.getenv("MAX_NOTIFICATION_AGE_DAYS", "90"))  # Максимальный возраст уведомлений

    # Настройки интеграции
    user_service_url: Optional[str] = os.getenv("USER_SERVICE_URL")
    order_service_url: Optional[str] = os.getenv("ORDER_SERVICE_URL")
    chat_service_url: Optional[str] = os.getenv("CHAT_SERVICE_URL")

    # Настройки безопасности
    enable_encryption: bool = os.getenv("ENABLE_ENCRYPTION", "false").lower() == "true"
    encryption_key: Optional[str] = os.getenv("ENCRYPTION_KEY")
    enable_rate_limiting: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()