"""
Конфигурация Location Service
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa Location Service"
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

    # Настройки геолокации
    tracking_interval_seconds: int = int(os.getenv("TRACKING_INTERVAL_SECONDS", "30"))  # Интервал отслеживания
    max_tracking_duration_hours: int = int(os.getenv("MAX_TRACKING_DURATION_HOURS", "12"))  # Макс. продолжительность трекинга
    location_accuracy_threshold: float = float(os.getenv("LOCATION_ACCURACY_THRESHOLD", "100"))  # Порог точности в метрах

    # Настройки геофенсинга
    geofence_enabled: bool = os.getenv("GEOFENCE_ENABLED", "true").lower() == "true"
    geofence_radius_meters: float = float(os.getenv("GEOFENCE_RADIUS_METERS", "2000"))  # Радиус геофенсинга
    geofence_alert_distance: float = float(os.getenv("GEOFENCE_ALERT_DISTANCE", "500"))  # Дистанция для предупреждения

    # Настройки маршрутов
    route_optimization_enabled: bool = os.getenv("ROUTE_OPTIMIZATION_ENABLED", "true").lower() == "true"
    route_max_points: int = int(os.getenv("ROUTE_MAX_POINTS", "1000"))  # Максимум точек в маршруте
    route_simplification_tolerance: float = float(os.getenv("ROUTE_SIMPLIFICATION_TOLERANCE", "10"))  # Упрощение маршрута

    # Настройки WebSocket
    websocket_ping_interval: int = int(os.getenv("WEBSOCKET_PING_INTERVAL", "30"))  # Интервал пинга в секундах
    websocket_timeout: int = int(os.getenv("WEBSOCKET_TIMEOUT", "60"))  # Таймаут соединения
    max_websocket_connections: int = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "1000"))  # Макс. количество соединений

    # Настройки безопасности геолокации
    location_sharing_enabled: bool = os.getenv("LOCATION_SHARING_ENABLED", "true").lower() == "true"
    location_history_retention_days: int = int(os.getenv("LOCATION_HISTORY_RETENTION_DAYS", "90"))  # Хранение истории
    emergency_location_enabled: bool = os.getenv("EMERGENCY_LOCATION_ENABLED", "true").lower() == "true"

    # Интеграция с картами
    yandex_maps_api_key: Optional[str] = os.getenv("YANDEX_MAPS_API_KEY")
    google_maps_api_key: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")

    # Настройки InfluxDB для временных рядов
    influxdb_host: str = os.getenv("INFLUXDB_HOST", "localhost")
    influxdb_port: int = int(os.getenv("INFLUXDB_PORT", "8086"))
    influxdb_token: str = os.getenv("INFLUXDB_TOKEN", "lapa_token")
    influxdb_org: str = os.getenv("INFLUXDB_ORG", "lapa")
    influxdb_bucket: str = os.getenv("INFLUXDB_BUCKET", "lapa")

    # Настройки очистки данных
    cleanup_interval_hours: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))  # Интервал очистки
    old_location_data_days: int = int(os.getenv("OLD_LOCATION_DATA_DAYS", "30"))  # Удаление старых данных

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
