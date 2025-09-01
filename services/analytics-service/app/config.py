"""
Конфигурация Analytics Service
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa Analytics Service"
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

    # ClickHouse настройки (для аналитики)
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", "9000"))
    clickhouse_user: str = os.getenv("CLICKHOUSE_USER", "default")
    clickhouse_password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    clickhouse_database: str = os.getenv("CLICKHOUSE_DATABASE", "lapa_analytics")

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

    # Настройки аналитики
    enable_data_collection: bool = os.getenv("ENABLE_DATA_COLLECTION", "true").lower() == "true"
    collection_interval_minutes: int = int(os.getenv("COLLECTION_INTERVAL_MINUTES", "5"))
    retention_period_days: int = int(os.getenv("RETENTION_PERIOD_DAYS", "365"))
    max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "1000"))

    # Настройки отчетов
    enable_scheduled_reports: bool = os.getenv("ENABLE_SCHEDULED_REPORTS", "true").lower() == "true"
    report_generation_timeout: int = int(os.getenv("REPORT_GENERATION_TIMEOUT", "300"))
    max_concurrent_reports: int = int(os.getenv("MAX_CONCURRENT_REPORTS", "5"))

    # Настройки дашбордов
    enable_dashboard_caching: bool = os.getenv("ENABLE_DASHBOARD_CACHING", "true").lower() == "true"
    dashboard_cache_ttl: int = int(os.getenv("DASHBOARD_CACHE_TTL", "300"))
    max_dashboard_widgets: int = int(os.getenv("MAX_DASHBOARD_WIDGETS", "50"))

    # Настройки KPI
    kpi_calculation_interval: int = int(os.getenv("KPI_CALCULATION_INTERVAL", "60"))
    enable_real_time_kpi: bool = os.getenv("ENABLE_REAL_TIME_KPI", "true").lower() == "true"

    # Настройки сегментации
    enable_user_segmentation: bool = os.getenv("ENABLE_USER_SEGMENTATION", "true").lower() == "true"
    segmentation_update_interval: int = int(os.getenv("SEGMENTATION_UPDATE_INTERVAL", "1440"))
    max_segments_per_user: int = int(os.getenv("MAX_SEGMENTS_PER_USER", "10"))

    # Настройки A/B тестирования
    enable_ab_testing: bool = os.getenv("ENABLE_AB_TESTING", "true").lower() == "true"
    ab_test_confidence_level: float = float(os.getenv("AB_TEST_CONFIDENCE_LEVEL", "0.95"))
    min_sample_size_per_variant: int = int(os.getenv("MIN_SAMPLE_SIZE_PER_VARIANT", "100"))

    # Настройки прогнозирования
    enable_forecasting: bool = os.getenv("ENABLE_FORECASTING", "true").lower() == "true"
    forecast_horizon_days: int = int(os.getenv("FORECAST_HORIZON_DAYS", "30"))
    forecast_update_interval: int = int(os.getenv("FORECAST_UPDATE_INTERVAL", "3600"))

    # Настройки персонализации
    enable_personalization: bool = os.getenv("ENABLE_PERSONALIZATION", "true").lower() == "true"
    personalization_model_update_interval: int = int(os.getenv("PERSONALIZATION_MODEL_UPDATE_INTERVAL", "86400"))

    # Настройки интеграции с внешними сервисами
    user_service_url: Optional[str] = os.getenv("USER_SERVICE_URL")
    order_service_url: Optional[str] = os.getenv("ORDER_SERVICE_URL")
    payment_service_url: Optional[str] = os.getenv("PAYMENT_SERVICE_URL")
    notification_service_url: Optional[str] = os.getenv("NOTIFICATION_SERVICE_URL")
    chat_service_url: Optional[str] = os.getenv("CHAT_SERVICE_URL")

    # Настройки внешних аналитических систем
    google_analytics_tracking_id: Optional[str] = os.getenv("GOOGLE_ANALYTICS_TRACKING_ID")
    mixpanel_token: Optional[str] = os.getenv("MIXPANEL_TOKEN")
    amplitude_api_key: Optional[str] = os.getenv("AMPLITUDE_API_KEY")
    segment_write_key: Optional[str] = os.getenv("SEGMENT_WRITE_KEY")

    # Настройки экспорта данных
    enable_data_export: bool = os.getenv("ENABLE_DATA_EXPORT", "true").lower() == "true"
    export_formats: List[str] = ["csv", "json", "xlsx", "parquet"]
    max_export_rows: int = int(os.getenv("MAX_EXPORT_ROWS", "100000"))

    # Настройки визуализации
    enable_chart_generation: bool = os.getenv("ENABLE_CHART_GENERATION", "true").lower() == "true"
    chart_cache_ttl: int = int(os.getenv("CHART_CACHE_TTL", "3600"))
    max_chart_data_points: int = int(os.getenv("MAX_CHART_DATA_POINTS", "10000"))

    # Настройки алертов
    enable_alerts: bool = os.getenv("ENABLE_ALERTS", "true").lower() == "true"
    alert_check_interval: int = int(os.getenv("ALERT_CHECK_INTERVAL", "300"))
    alert_notification_channels: List[str] = ["email", "slack"]

    # Настройки очистки данных
    enable_data_cleanup: bool = os.getenv("ENABLE_DATA_CLEANUP", "true").lower() == "true"
    cleanup_interval_hours: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
    data_backup_before_cleanup: bool = os.getenv("DATA_BACKUP_BEFORE_CLEANUP", "true").lower() == "true"

    # Настройки безопасности
    enable_data_encryption: bool = os.getenv("ENABLE_DATA_ENCRYPTION", "false").lower() == "true"
    encryption_key: Optional[str] = os.getenv("ENCRYPTION_KEY")
    enable_pii_masking: bool = os.getenv("ENABLE_PII_MASKING", "true").lower() == "true"

    # Настройки производительности
    enable_query_caching: bool = os.getenv("ENABLE_QUERY_CACHING", "true").lower() == "true"
    query_cache_ttl: int = int(os.getenv("QUERY_CACHE_TTL", "600"))
    max_query_execution_time: int = int(os.getenv("MAX_QUERY_EXECUTION_TIME", "300"))

    # Настройки геоаналитики
    enable_geo_analytics: bool = os.getenv("ENABLE_GEO_ANALYTICS", "true").lower() == "true"
    geo_data_update_interval: int = int(os.getenv("GEO_DATA_UPDATE_INTERVAL", "86400"))

    # Настройки машинного обучения
    enable_ml_features: bool = os.getenv("ENABLE_ML_FEATURES", "true").lower() == "true"
    ml_model_update_interval: int = int(os.getenv("ML_MODEL_UPDATE_INTERVAL", "604800"))
    ml_model_accuracy_threshold: float = float(os.getenv("ML_MODEL_ACCURACY_THRESHOLD", "0.8"))

    # Настройки интеграции с BI инструментами
    enable_superset_integration: bool = os.getenv("ENABLE_SUPERSET_INTEGRATION", "false").lower() == "true"
    superset_base_url: Optional[str] = os.getenv("SUPERSET_BASE_URL")

    # Настройки бизнес-метрик
    business_metrics_update_interval: int = int(os.getenv("BUSINESS_METRICS_UPDATE_INTERVAL", "3600"))
    enable_custom_metrics: bool = os.getenv("ENABLE_CUSTOM_METRICS", "true").lower() == "true"

    # Настройки временных зон
    default_timezone: str = os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow")
    supported_timezones: List[str] = ["UTC", "Europe/Moscow", "Europe/London", "America/New_York"]

    # Настройки локализации
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "ru")
    supported_languages: List[str] = ["ru", "en", "es", "fr", "de"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
