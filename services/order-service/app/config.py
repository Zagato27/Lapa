"""
Конфигурация Order Service.

Назначение и использование:
- Параметры подключения к PostgreSQL/Redis
- Бизнес-настройки заказов/геопоиска/ценообразования
- URL других сервисов для интеграций (через API/внутренние вызовы)

Экспортируется как `settings` и используется по всему сервису, в том числе:
- `app.main` при инициализации приложения и middleware
- `app.database.*` для подключения к БД
- `app.services.*` для бизнес-логики, расчётов и интеграций
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa Order Service"
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

    # URL внешних сервисов (для сервис-ту-сервис взаимодействий)
    # Значения по умолчанию предполагают сетевые имена контейнеров в Docker Compose/K8s
    api_gateway_url: str = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")

    # CORS настройки
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://lapa-kolomna.ru"
    ]

    # Доверенные хосты
    allowed_hosts: List[str] = ["*"]

    # Настройки заказов
    max_orders_per_day: int = int(os.getenv("MAX_ORDERS_PER_DAY", "20"))  # Максимум заказов в день на выгульщика
    order_confirmation_timeout: int = int(os.getenv("ORDER_CONFIRMATION_TIMEOUT", "300"))  # 5 минут на подтверждение
    order_cancellation_timeout: int = int(os.getenv("ORDER_CANCELLATION_TIMEOUT", "3600"))  # 1 час до начала

    # Финансовые настройки
    platform_commission: float = float(os.getenv("PLATFORM_COMMISSION", "0.1"))  # 10% комиссия платформы
    walker_hourly_rate_min: float = float(os.getenv("WALKER_HOURLY_RATE_MIN", "200"))  # Минимальная ставка выгульщика
    walker_hourly_rate_max: float = float(os.getenv("WALKER_HOURLY_RATE_MAX", "800"))  # Максимальная ставка выгульщика

    # Геолокационные настройки
    max_search_distance: float = float(os.getenv("MAX_SEARCH_DISTANCE", "10000"))  # Максимальная дистанция поиска в метрах
    default_search_radius: float = float(os.getenv("DEFAULT_SEARCH_RADIUS", "3000"))  # Радиус поиска по умолчанию

    # Временные ограничения
    min_order_duration: int = int(os.getenv("MIN_ORDER_DURATION", "30"))  # Минимальная продолжительность заказа в минутах
    max_order_duration: int = int(os.getenv("MAX_ORDER_DURATION", "180"))  # Максимальная продолжительность заказа в минутах
    max_advance_booking_days: int = int(os.getenv("MAX_ADVANCE_BOOKING_DAYS", "30"))  # Максимум дней вперед для бронирования

    # Настройки уведомлений
    enable_push_notifications: bool = os.getenv("ENABLE_PUSH_NOTIFICATIONS", "true").lower() == "true"
    enable_sms_notifications: bool = os.getenv("ENABLE_SMS_NOTIFICATIONS", "false").lower() == "true"

    # Настройки рейтинга
    min_rating_for_orders: float = float(os.getenv("MIN_RATING_FOR_ORDERS", "3.0"))  # Минимальный рейтинг для приема заказов
    review_reminder_delay: int = int(os.getenv("REVIEW_REMINDER_DELAY", "3600"))  # Напоминание об отзыве через 1 час

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
