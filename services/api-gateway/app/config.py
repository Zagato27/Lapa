"""
Конфигурация API Gateway Service
"""

import os
from typing import List, Optional, Dict, Any

from pydantic_settings import BaseSettings
from pydantic import BaseModel


class ServiceConfig(BaseModel):
    """Конфигурация микросервиса"""
    name: str
    url: str
    enabled: bool = True
    timeout: int = 30
    retries: int = 3
    rate_limit: int = 1000
    health_check: str = "/health"


class RouteConfig(BaseModel):
    """Конфигурация маршрута"""
    path: str
    service: str
    methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    auth_required: bool = True
    rate_limit: Optional[int] = None
    cache_ttl: Optional[int] = None
    transform_request: bool = False
    transform_response: bool = False


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa API Gateway"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Серверные настройки
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8080"))

    # Redis настройки
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")

    # CORS настройки
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://lapa-kolomna.ru"
    ]

    # Доверенные хосты
    allowed_hosts: List[str] = ["*"]

    # Настройки безопасности
    enable_security_headers: bool = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
    enable_cors: bool = os.getenv("ENABLE_CORS", "true").lower() == "true"
    enable_rate_limiting: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    enable_request_logging: bool = os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true"
    enable_response_caching: bool = os.getenv("ENABLE_RESPONSE_CACHING", "true").lower() == "true"

    # Настройки аутентификации
    enable_auth: bool = os.getenv("ENABLE_AUTH", "true").lower() == "true"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Настройки User Service для аутентификации
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    pet_service_url: str = os.getenv("PET_SERVICE_URL", "http://pet-service:8000")
    order_service_url: str = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
    location_service_url: str = os.getenv("LOCATION_SERVICE_URL", "http://location-service:8000")
    payment_service_url: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
    chat_service_url: str = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8000")
    media_service_url: str = os.getenv("MEDIA_SERVICE_URL", "http://media-service:8000")
    notification_service_url: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
    analytics_service_url: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000")

    # Конфигурация микросервисов
    services: Dict[str, ServiceConfig] = {
        "user": ServiceConfig(
            name="user-service",
            url=os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
            rate_limit=int(os.getenv("USER_SERVICE_RATE_LIMIT", "1000"))
        ),
        "pet": ServiceConfig(
            name="pet-service",
            url=os.getenv("PET_SERVICE_URL", "http://pet-service:8000"),
            rate_limit=int(os.getenv("PET_SERVICE_RATE_LIMIT", "1000"))
        ),
        "order": ServiceConfig(
            name="order-service",
            url=os.getenv("ORDER_SERVICE_URL", "http://order-service:8000"),
            rate_limit=int(os.getenv("ORDER_SERVICE_RATE_LIMIT", "1000"))
        ),
        "location": ServiceConfig(
            name="location-service",
            url=os.getenv("LOCATION_SERVICE_URL", "http://location-service:8000"),
            rate_limit=int(os.getenv("LOCATION_SERVICE_RATE_LIMIT", "1000"))
        ),
        "payment": ServiceConfig(
            name="payment-service",
            url=os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000"),
            rate_limit=int(os.getenv("PAYMENT_SERVICE_RATE_LIMIT", "500"))
        ),
        "chat": ServiceConfig(
            name="chat-service",
            url=os.getenv("CHAT_SERVICE_URL", "http://chat-service:8000"),
            rate_limit=int(os.getenv("CHAT_SERVICE_RATE_LIMIT", "2000"))
        ),
        "media": ServiceConfig(
            name="media-service",
            url=os.getenv("MEDIA_SERVICE_URL", "http://media-service:8000"),
            rate_limit=int(os.getenv("MEDIA_SERVICE_RATE_LIMIT", "1500"))
        ),
        "notification": ServiceConfig(
            name="notification-service",
            url=os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000"),
            rate_limit=int(os.getenv("NOTIFICATION_SERVICE_RATE_LIMIT", "1000"))
        ),
        "analytics": ServiceConfig(
            name="analytics-service",
            url=os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000"),
            rate_limit=int(os.getenv("ANALYTICS_SERVICE_RATE_LIMIT", "500"))
        )
    }

    # Конфигурация маршрутов
    routes: Dict[str, RouteConfig] = {
        # User Service routes
        "/user": RouteConfig(
            path="/user",
            service="user",
            auth_required=False,
            rate_limit=200
        ),
        "/auth": RouteConfig(
            path="/auth",
            service="user",
            auth_required=False,
            rate_limit=100
        ),

        # Pet Service routes
        "/pet": RouteConfig(
            path="/pet",
            service="pet",
            auth_required=True,
            rate_limit=500
        ),

        # Order Service routes
        "/order": RouteConfig(
            path="/order",
            service="order",
            auth_required=True,
            rate_limit=300
        ),

        # Location Service routes
        "/location": RouteConfig(
            path="/location",
            service="location",
            auth_required=True,
            rate_limit=1000
        ),

        # Payment Service routes
        "/payment": RouteConfig(
            path="/payment",
            service="payment",
            auth_required=True,
            rate_limit=200
        ),

        # Chat Service routes
        "/chat": RouteConfig(
            path="/chat",
            service="chat",
            auth_required=True,
            rate_limit=1000
        ),

        # Media Service routes
        "/media": RouteConfig(
            path="/media",
            service="media",
            auth_required=True,
            rate_limit=800
        ),

        # Notification Service routes
        "/notification": RouteConfig(
            path="/notification",
            service="notification",
            auth_required=True,
            rate_limit=500
        ),

        # Analytics Service routes
        "/analytics": RouteConfig(
            path="/analytics",
            service="analytics",
            auth_required=True,
            rate_limit=200
        )
    }

    # Настройки rate limiting
    global_rate_limit: int = int(os.getenv("GLOBAL_RATE_LIMIT", "10000"))
    ip_rate_limit: int = int(os.getenv("IP_RATE_LIMIT", "1000"))
    user_rate_limit: int = int(os.getenv("USER_RATE_LIMIT", "5000"))

    # Настройки кэширования
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))
    cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "10000"))

    # Настройки circuit breaker
    circuit_breaker_enabled: bool = os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
    circuit_breaker_failure_threshold: int = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
    circuit_breaker_recovery_timeout: int = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))

    # Настройки мониторинга
    monitoring_enabled: bool = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))

    # Настройки логирования
    log_requests: bool = os.getenv("LOG_REQUESTS", "true").lower() == "true"
    log_responses: bool = os.getenv("LOG_RESPONSES", "false").lower() == "true"
    log_errors: bool = os.getenv("LOG_ERRORS", "true").lower() == "true"

    # Настройки трансформации
    enable_request_transformation: bool = os.getenv("ENABLE_REQUEST_TRANSFORMATION", "true").lower() == "true"
    enable_response_transformation: bool = os.getenv("ENABLE_RESPONSE_TRANSFORMATION", "true").lower() == "true"

    # Настройки service discovery
    service_discovery_enabled: bool = os.getenv("SERVICE_DISCOVERY_ENABLED", "false").lower() == "true"
    consul_host: str = os.getenv("CONSUL_HOST", "localhost")
    consul_port: int = int(os.getenv("CONSUL_PORT", "8500"))

    # Настройки API Gateway
    api_version: str = os.getenv("API_VERSION", "v1")
    enable_api_versioning: bool = os.getenv("ENABLE_API_VERSIONING", "true").lower() == "true"
    enable_swagger_docs: bool = os.getenv("ENABLE_SWAGGER_DOCS", "true").lower() == "true"

    # Настройки безопасности
    enable_https_redirect: bool = os.getenv("ENABLE_HTTPS_REDIRECT", "false").lower() == "true"
    enable_request_id: bool = os.getenv("ENABLE_REQUEST_ID", "true").lower() == "true"
    max_request_size: int = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB

    # Настройки WebSocket
    enable_websocket_support: bool = os.getenv("ENABLE_WEBSOCKET_SUPPORT", "true").lower() == "true"

    # Настройки GraphQL
    enable_graphql_support: bool = os.getenv("ENABLE_GRAPHQL_SUPPORT", "false").lower() == "true"

    # Настройки API composition
    enable_api_composition: bool = os.getenv("ENABLE_API_COMPOSITION", "true").lower() == "true"
    composition_timeout: int = int(os.getenv("COMPOSITION_TIMEOUT", "30"))

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()